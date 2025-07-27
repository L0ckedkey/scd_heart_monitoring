from flask import Flask, request, Blueprint
import os
import pymysql
from kafka import KafkaConsumer, KafkaProducer
import mysql.connector as mysql
from paho.mqtt.client import Client
from services.patientServices import *
from services.medicineServices import *
from services.ecgServices import *
from google.cloud.sql.connector import Connector
import sqlalchemy
import threading
from flask_mqtt import Mqtt
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.sql import func

api_bp = Blueprint("api", __name__, url_prefix="/api/")

db_user = ""
db_password = ""
db_name = ""
db_connection_name = ""
app = Flask(__name__)
broker_ip = ''

app.config['MQTT_BROKER_URL'] = broker_ip  # Alamat broker MQTT
app.config['MQTT_BROKER_PORT'] = 1883  # Port broker
app.config['MQTT_USERNAME'] = ''  # Username jika diperlukan (kosongkan jika tidak ada)
app.config['MQTT_PASSWORD'] = ''  # Password jika diperlukan (kosongkan jika tidak ada)
app.config['MQTT_KEEPALIVE'] = 60  # Waktu keepalive dalam detik
app.config['MQTT_TLS_ENABLED'] = False  # Tidak menggunakan TLS
app.config['MQTT_CLIENT_ID'] = 'python-123'  # Tidak menggunakan TLS

mqtt = Mqtt(app)
mqtt.init_app(app)

# Kafka Configuration
KAFKA_BROKER = broker_ip + ':2902'  # Ganti dengan alamat Kafka broker
CONSUMER_TOPIC = 'sensor-data'

connector = Connector()

def getconn():
    conn = connector.connect(
        "",
        "pymysql",
        user="",
        password="",
        db=""
    )
    return conn

#cnx = mysql.connect(
#    user='scd', 
#    password='scd2023', 
#    database='scd',
#    host='10.20.39.104', 
#    port=3306
#)

pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

cnx = pool.connect()

#def open_connection():
#    unix_socket = '/cloudsql/{}'.format(db_connection_name)
#    try:
#        if os.environ.get('GAE_ENV') == 'standard':
#    conn = pymysql.connect(user=db_user, password=db_password,
#                                unix_socket=unix_socket, db=db_name,
#                                cursorclass=pymysql.cursors.DictCursor
#                                )
#    except pymysql.MySQLError as e:
#        print(e)

#    return conn

#cnx = open_connection()

@api_bp.route('/test', methods=['POST'])
def test():
    return "ok"

@api_bp.route('/register', methods=['POST'])
def register_patient():
    return register_patient_data(request.get_json(),cnx)

@api_bp.route('/patient/additional-info', methods=['POST'])
def update_patient():
    return update_patient_data(request.get_json(),cnx,key_list = ["id","gender","cholesterollevel","isSmoker","isHavingHypertension"])

@api_bp.route('/patient/pin', methods=['POST'])
def set_pin():
    return update_patient_data(request.get_json(),cnx, key_list = ["id","pin"])

@api_bp.route('/patient/pin/validate', methods=['POST'])
def valid_pin():
    return validate_pin(request.get_json(),cnx, key_list = ["id","pin"])

@api_bp.route('/login', methods=['POST'])
def login():
    return login_patient(request.get_json(),cnx)

@api_bp.route('/patient/<patientId>/medicine', methods=['POST'])
def register_medicine(patientId):
    curr_data = request.get_json()
    curr_data['patientId'] = patientId
    return insert_medicine(curr_data,cnx)
    
@api_bp.route('/patient/<patientId>/medicine/<medicineId>', methods=['GET'])
def get_a_medicine(patientId,medicineId):
    return get_medicine(patientId,medicineId,cnx)

@api_bp.route('/patient/<patientId>/medicine', methods=['GET'])
def get_all_medicine(patientId):
    return get_all_medicines(patientId,cnx)

@api_bp.route('/patient/<patientId>/medicine/<medicineId>', methods=['DELETE'])
def remove_medicine(patientId,medicineId):
    return delete_medicine(medicineId,cnx)

@api_bp.route('/publisher/ecg', methods=['POST'])
def insert_ecg_data():
    return insert_ecg(request.get_json(),cnx=cnx)

# Adapted, previously get
@api_bp.route('/ecg/graph', methods=['post'])
def get_ecg_data_in_range():
    return get_ecg_list_by_patient_id_in_range(request.get_json(),cnx)

@api_bp.route('/ecg/histories/<userId>', methods=['get'])
def get_history(userId):
    return get_histories(userId,cnx)

# predict
@api_bp.route('/predict', methods=['post'])
def get_predictions():
    return make_predictions(request.get_json(),cnx)



def kafka_consumer():
    consumer = KafkaConsumer(
        CONSUMER_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='flask-kafka-group'
    )

    for message in consumer:
        try:
            # Ambil data dari Kafka
            data = message.value
            print(f"Received message from Kafka: {data}", flush=True)
            
            # Ambil atau buat sessionId
            session_id = data.get('sessionId', 'default_session')

            # Proses data untuk membuat format JSON baru
            # formatted_data = {
            #     "patientId": data['data'].get('patientId', 'unknown_patient'),
            #     "startTime": data['data'].get('startTime', 'unknown_start'),
            #     "endTime": data['data'].get('endTime', 'unknown_end')
                
            # }
            
            formatted_data = {}
            formatted_data['patientId'] = data['data'].get('patientId', 'unknown_patient')
            formatted_data['startTime'] = data['data'].get('startTime', 'unknown_patient')
            formatted_data['endTime'] = data['data'].get('endTime', 'unknown_patient')
            
            print(formatted_data)
            # Ubah ke JSON string untuk dikirim ke MQTT
            # payload_to_publish = json.dumps(formatted_data)
            # print(payload_to_publish)
            result = make_predictions(formatted_data,cnx)
            result = result['result']
            result = result[0].get('prediction_desc')
            # prediction_desc = data['result'].get('prediction_desc', 'Unknown')  # Jika tidak ada, 'Unknown'
            prediction_desc =result
            print(result, flush=True)
            # Publish ke MQTT
            publish_result = mqtt.publish(f'sensor/ans/{session_id}', payload=prediction_desc, retain=True, qos=1)
            print(f"Published to MQTT: {publish_result}", flush=True)

            # Opsional: Call make_predictions
            # response = make_predictions(formatted_data, cnx)
            # print(f"Prediction response: {response}")

        except Exception as e:
            print(f"Error processing Kafka message: {e}")
            publish_result = mqtt.publish(f'sensor/ans/{session_id}', payload=json.dumps({'error': str(e)}))

def start_kafka_consumer():
    threading.Thread(target=kafka_consumer, daemon=True).start()


# Setup MQTT Client



#temp = {
#    "email":"natan1@nomail.com",
#    "password":"asdfg"
#}

if __name__ == '__main__':
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3306/scd'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # db = SQLAlchemy(app)
    start_kafka_consumer()
    app.run(host="0.0.0.0", port=8003, debug=True)
    
    

    
