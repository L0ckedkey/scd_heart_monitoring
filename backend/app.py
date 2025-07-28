from flask import Flask, request, Blueprint, jsonify
import os
import pymysql
from dotenv import load_dotenv
import mysql.connector as mysql
from services.patientServices import *
from services.medicineServices import *
from services.ecgServices import *
from google.cloud.sql.connector import Connector
import json
import sqlalchemy

load_dotenv('../.env')  # Load isi file .env

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_connection_name = os.getenv("DB_CONNECTION_NAME")


api_bp = Blueprint("api", __name__, url_prefix="/api/")

connector = Connector()

app = Flask(__name__)

def getconn():
    conn = connector.connect(
        db_connection_name,
        "pymysql",
        user=db_user,
        password=db_password,
        db=db_name
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

@app.route("/")
def index():
    return "Flask API berjalan dengan sukses (tanpa MQTT)!"

# Menambahkan Blueprint
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8003, debug=True)
