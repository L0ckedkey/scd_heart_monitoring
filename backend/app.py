from flask import Flask, request, Blueprint, jsonify, g
import os
import pymysql
from dotenv import load_dotenv
from services.patientServices import *
from services.medicineServices import *
from services.ecgServices import *
from google.cloud.sql.connector import Connector
import sqlalchemy
from flask_cors import CORS

# Load .env
load_dotenv('../.env')

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_connection_name = os.getenv("DB_CONNECTION_NAME")

# Flask app
app = Flask(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api/")
CORS(app, supports_credentials=True)

# Google Cloud SQL Connector
connector = Connector()

# Fungsi untuk buat koneksi MySQL
def getconn():
    conn = connector.connect(
        db_connection_name,
        "pymysql",
        user=db_user,
        password=db_password,
        db=db_name
    )
    return conn

# SQLAlchemy engine dengan connection pool
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# Ambil koneksi per request
@app.before_request
def before_request():
    g.db_conn = pool.connect()

# Tutup koneksi setelah request selesai
@app.teardown_request
def teardown_request(exception):
    db_conn = getattr(g, 'db_conn', None)
    if db_conn is not None:
        if exception:
            db_conn.rollback()  # Rollback kalau ada error
        db_conn.close()

# Routes
@api_bp.route('/test', methods=['POST'])
def test():
    return "ok"

@api_bp.route('/register', methods=['POST'])
def register_patient():
    return register_patient_data(request.get_json(), g.db_conn)

@api_bp.route('/patient/additional-info', methods=['POST'])
def update_patient():
    return update_patient_data(
        request.get_json(),
        g.db_conn,
        key_list=["id", "gender", "cholesterollevel", "isSmoker", "isHavingHypertension"]
    )
    
@api_bp.route('/patient/additional-info/<patientId>', methods=['GET'])
def get_additional_info(patientId):
    return get_patient_additional_info(
        patientId,
        g.db_conn
    )

@api_bp.route('/patient/pin', methods=['POST'])
def set_pin():
    return update_patient_data(request.get_json(), g.db_conn, key_list=["id", "pin"])

@api_bp.route('/schedule-consultation', methods=['POST'])
def schedule_consul():
    return schedule_consultation(request.get_json(), g.db_conn)

@api_bp.route('/patient/pin/validate', methods=['POST'])
def valid_pin():
    return validate_pin(request.get_json(), g.db_conn, key_list=["id", "pin"])

@api_bp.route('/pending-consultations', methods=['GET'])
def pending_consultations():
    return get_pending_consultations(g.db_conn)

@api_bp.route('/patients', methods=['GET'])
def getPatients():
    return get_patients_with_consultation(g.db_conn)

@api_bp.route('/login', methods=['POST'])
def login():
    return login_patient(request.get_json(), g.db_conn)

# @api_bp.route('/patient/<patientId>/medicine', methods=['POST'])
# def register_medicine(patientId):
#     curr_data = request.get_json()
#     curr_data['patientId'] = patientId
#     return insert_medicine(curr_data, g.db_conn)

@api_bp.route('/medicine', methods=['POST'])
def register_medicine():
    curr_data = request.get_json()
    return insert_medicine(curr_data, g.db_conn)

@api_bp.route('/update-medicine', methods=['POST'])
def up_medicine():
    curr_data = request.get_json()
    return update_medicine(curr_data, g.db_conn)

@api_bp.route('/medicine', methods=['DELETE'])
def del_medicine():
    curr_data = request.get_json()
    return delete_medicine(curr_data, g.db_conn)

@api_bp.route('/detail-medicine', methods=['DELETE'])
def del_detail_medicine():
    curr_data = request.get_json()
    return delete_detail_medicine(curr_data, g.db_conn)

@api_bp.route('/detail-medicine', methods=['POST'])
def ins_detail_medicine():
    curr_data = request.get_json()
    return insert_detail_medicine(curr_data, g.db_conn)

@api_bp.route('/med-assign-consultation', methods=['POST'])
def assign_schedule():
    curr_data = request.get_json()
    return med_assign_schedule(curr_data, g.db_conn)



@api_bp.route('/patient/<patientId>/medicine/<medicineId>', methods=['GET'])
def get_a_medicine(patientId, medicineId):
    return get_medicine(patientId, medicineId, g.db_conn)

# @api_bp.route('/patient/<patientId>/medicine', methods=['GET'])
# def get_all_medicine(patientId):
#     return get_all_medicines(patientId, g.db_conn)

@api_bp.route('/medicines', methods=['GET'])
def get_all_medicine():
    return get_all_medicines(g.db_conn)

# @api_bp.route('/patient/<patientId>/medicine/<medicineId>', methods=['DELETE'])
# def remove_medicine(patientId, medicineId):
#     return delete_medicine(medicineId, g.db_conn)

@api_bp.route('/publisher/ecg', methods=['POST'])
def insert_ecg_data():
    return insert_ecg(request.get_json(), cnx=g.db_conn)

@api_bp.route('/ecg/graph', methods=['POST'])
def get_ecg_data_in_range():
    return get_ecg_list_by_patient_id_in_range(request.get_json(), g.db_conn)

@api_bp.route('/ecg/histories/<userId>', methods=['GET'])
def get_history(userId):
    return get_histories(userId, g.db_conn)

@api_bp.route('/predict', methods=['POST'])
def get_predictions():
    return make_predictions(request.get_json(), g.db_conn)

@api_bp.route('/consultation', methods=['POST'])
def set_consul():
    return set_consultation(request.get_json(), g.db_conn)


@app.route("/")
def index():
    return "Flask API berjalan dengan sukses"

# Register blueprint
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8003, debug=True)
