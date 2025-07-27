from flask import Flask, request, Blueprint, jsonify
import os
import pymysql
import mysql.connector as mysql
from services.patientServices import *
from services.medicineServices import *
from services.ecgServices import *
from google.cloud.sql.connector import Connector
import json
import sqlalchemy
from flask_mqtt import Mqtt

api_bp = Blueprint("api", __name__, url_prefix="/api/")

db_user = ""
db_password = ""
db_name = ""
db_connection_name = ""

connector = Connector()

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = 'deployment-mqtt-service'  # Alamat broker MQTT
app.config['MQTT_BROKER_PORT'] = 1883  # Port broker
app.config['MQTT_USERNAME'] = ''  # Username jika diperlukan (kosongkan jika tidak ada)
app.config['MQTT_PASSWORD'] = ''  # Password jika diperlukan (kosongkan jika tidak ada)
app.config['MQTT_KEEPALIVE'] = 60  # Waktu keepalive dalam detik
app.config['MQTT_TLS_ENABLED'] = False  # Tidak menggunakan TLS
app.config['MQTT_CLIENT_ID'] = 'python-123'  # Tidak menggunakan TLS

mqtt = Mqtt(app)
mqtt.init_app(app)

def getconn():
    conn = connector.connect(
        "",
        "pymysql",
        user="",
        password="",
        db=""
    )
    return conn

# Setup SQLAlchemy connection pool
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

cnx = pool.connect()

@api_bp.route('/test', methods=['POST'])
def test():
    return "ok"

@api_bp.route('/register', methods=['POST'])
def register_patient():
    return register_patient_data(request.get_json(), cnx)

@api_bp.route('/patient/additional-info', methods=['POST'])
def update_patient():
    return update_patient_data(request.get_json(), cnx, key_list=["id", "gender", "cholesterollevel", "isSmoker", "isHavingHypertension"])

@api_bp.route('/patient/pin', methods=['POST'])
def set_pin():
    return update_patient_data(request.get_json(), cnx, key_list=["id", "pin"])

@api_bp.route('/patient/pin/validate', methods=['POST'])
def valid_pin():
    return validate_pin(request.get_json(), cnx, key_list=["id", "pin"])

@api_bp.route('/login', methods=['POST'])
def login():
    return login_patient(request.get_json(), cnx)

@api_bp.route('/patient/<patientId>/medicine', methods=['POST'])
def register_medicine(patientId):
    curr_data = request.get_json()
    curr_data['patientId'] = patientId
    return insert_medicine(curr_data, cnx)

@api_bp.route('/patient/<patientId>/medicine/<medicineId>', methods=['GET'])
def get_a_medicine(patientId, medicineId):
    return get_medicine(patientId, medicineId, cnx)

@api_bp.route('/patient/<patientId>/medicine', methods=['GET'])
def get_all_medicine(patientId):
    return get_all_medicines(patientId, cnx)

@api_bp.route('/patient/<patientId>/medicine/<medicineId>', methods=['DELETE'])
def remove_medicine(patientId, medicineId):
    return delete_medicine(medicineId, cnx)

@api_bp.route('/publisher/ecg', methods=['POST'])
def insert_ecg_data():
    return insert_ecg(request.get_json(), cnx=cnx)

@api_bp.route('/ecg/graph', methods=['post'])
def get_ecg_data_in_range():
    return get_ecg_list_by_patient_id_in_range(request.get_json(), cnx)

@api_bp.route('/ecg/histories/<userId>', methods=['get'])
def get_history(userId):
    return get_histories(userId, cnx)

@api_bp.route('/predict', methods=['post'])
def get_predictions():
    return make_predictions(request.get_json(), cnx)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        # Decode payload dan parsing JSON
        payload_json = json.loads(message.payload.decode())
        data = {
            "topic": message.topic,
            "payload": payload_json
        }
        session_id = data['payload']['sessionId']
        data = data['payload'].get('data')
        print(data, flush=True)
        formatted_data = {}
        formatted_data['patientId'] = data.get('patientId', 'unknown_patient')
        formatted_data['startTime'] = data.get('startTime', 'unknown_patient')
        formatted_data['endTime'] = data.get('endTime', 'unknown_patient')
            
        print(formatted_data, flush=True)
        result = make_predictions(formatted_data,cnx)
        result = result['result']
        result = result[0].get('prediction_desc')
        
        prediction_desc = result
        print(result, flush=True)
        # Publish response dengan sessionId yang benar
        publish_result = mqtt.publish('sensor/ans/' + session_id, result, qos=1)
        print(f"Published to MQTT: {publish_result}", flush=True)
    except json.JSONDecodeError as e:
        # Tangani error jika payload bukan JSON valid
        print(f"Failed to decode JSON payload: {e}")

@mqtt.on_subscribe()
def handle_subscribe(client, userdata, mid, granted_qos):
    print("Berhasil subscribe ke topik!")
    
    
@app.route("/")
def index():
    return "Flask-MQTT berjalan dengan sukses!"

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
       print('Connected successfully')
       mqtt.subscribe('sensor/data') # subscribe topic
    else:
       print('Bad connection. Code:', rc)



# Menjalankan Flask app


# Menambahkan Blueprint
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8003, debug=True)
