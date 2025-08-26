from misc.utils import *
import bcrypt 
from pypika import Query, Table
from datetime import datetime, timedelta
from flask import jsonify
import sqlalchemy

def register_patient_data(curr_data,cnx,key_list = ["email","password"]):
    try:
        status,data = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        data[1] = data[1].encode('utf-8') 
        salt = bcrypt.gensalt() 
        data[1] = bcrypt.hashpw(data[1], salt) 
        data[1] = str(data[1])[2:-1]
        
        tgt_tab = Table('patients')
        q = Query.into(tgt_tab).columns(tuple(key_list)).insert(tuple(data))
#        cursor = cnx.cursor(buffered=True)
        cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
#        cursor.execute(str(q).replace('"','`'))
        cnx.commit()
        
        resp_dict = {}
        
        resp_dict["email"] = curr_data["email"]
        new_keys = ['gender','cholesterolLevel','isSmoker','isHavingHypertension']
        for i in new_keys:
            resp_dict[i] = ""
        
        secret_key = 'dvf3-342-3-402-5'
        lastrowid = cnx.execute(sqlalchemy.text('SELECT LAST_INSERT_ID()')).fetchone()
        resp_dict['id'] = lastrowid[0]

        resp_dict['token'] = generate_token(secret_key, resp_dict)
        
#        cursor.close()
        return jsonify(resp_dict)
    
def update_patient_data(curr_data,cnx,key_list=[]):
    try:
        status,_ = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        tgt_tab = Table('patients')
        
        curr_patient = get_user_by_id(curr_data['id'],cnx)
        if len(curr_patient)<1:
            return False
        else:
            resp_dict = {}
            resp_dict["email"] = curr_patient[0]
            q = Query.update(tgt_tab)
            for key in key_list:
                if key != 'id':
                    q = q.set(key, curr_data[key])
                    resp_dict[key] = curr_data[key]

            q = q.where(tgt_tab["patientID"] == curr_data['id'])
#            cursor = cnx.cursor(buffered=True)
            cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
#            cursor.execute(str(q).replace('"','`')) 
            cnx.commit()

            secret_key = 'dvf3-342-3-402-5'
            resp_dict['id'] = curr_data['id']
            print(resp_dict.items())
            for key,val in resp_dict.items():
                if val is None:
                    resp_dict[key] == ""
            resp_dict['token'] = generate_token(secret_key, resp_dict)
            
#            cursor.close()
            if "pin" in key_list:
                return {'status':True}
            return jsonify(resp_dict)
        
def get_patient_additional_info(patient_id, cnx):
    tgt_tab = Table('patients')
    
    # build query SELECT *
    q = Query.from_(tgt_tab).select("*").where(tgt_tab["patientID"] == patient_id)
    
    # eksekusi query
    row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchone()
    
    if not row:
        return jsonify({"error": "Patient not found"}), 404
    
    # ubah row jadi dict
    if hasattr(row, '_mapping'):  # SQLAlchemy 1.4+
        result = dict(row._mapping)
    elif hasattr(row, 'keys'):
        result = dict(zip(row.keys(), row))
    else:
        result = dict(row)
    
    # replace None dengan string kosong
    for key, val in result.items():
        if val is None:
            result[key] = ""
    
    # exclude beberapa key sensitif
    exclude_keys = ["isDeleted", "password", "pin", "createdAt", "updatedAt"]
    for key in exclude_keys:
        if key in result:
            result.pop(key)
    
    return jsonify(result)

def validate_pin(curr_data,cnx,key_list=['id','pin']):
    try:
        status,_ = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        tgt_tab = Table('patients')
        q = Query.from_(tgt_tab).select('pin').where(tgt_tab["patientID"] == curr_data['id'])
#        cursor = cnx.cursor(buffered=True)
        row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchone()
#        cursor.execute(str(q).replace('"','`'))
#        row = cursor.fetchone()
#        cursor.close()
        try:
            if row[0] == curr_data['pin']:
                return {'status':True}
        except:
            return {'status':False}
        return {'status':False}
    
def login_patient(curr_data, cnx, key_list=['email','password']):
    try:
        status,_ = validate_dict(curr_data,key_list)
    except:
        return jsonify({"status": False, "message": "Key Error!"})
    
    if status: 
        tgt_tab = Table('patients')
        q = Query.from_(tgt_tab).select(
            'email','password','patientID','gender','cholesterolLevel','isSmoker','isHavingHypertension'
        ).where(tgt_tab["email"] == curr_data['email'])
        
        row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchone()
        if not row:  # email tidak ketemu
            return jsonify({"status": False, "message": "User not found"})
        
        # encode password input
        curr_data['password'] = curr_data['password'].encode('utf-8') 
        
        # cek hash
        if bcrypt.checkpw(curr_data['password'], row[1].encode('utf-8')):
            resp_dict = {
                "email": curr_data["email"],
                "id": row[2]
            }
            new_keys = ['patientID','gender','cholesterolLevel','isSmoker','isHavingHypertension']
            
            for i in range(3,len(new_keys)+2):
                resp_dict[new_keys[i-2]] = row[i] if row[i] is not None else ""
            
            secret_key = 'dvf3-342-3-402-5'
            resp_dict['token'] = generate_token(secret_key, resp_dict)   
            
            return jsonify(resp_dict)
        else:
            return jsonify({"status": False, "message": "Invalid password"})
    
    return jsonify({"status": False, "message": "Validation failed"})

def get_patients_with_consultation(cnx):
    try:
        patients_tab = Table('patients')

        # Ambil semua pasien
        q_patients = Query.from_(patients_tab).select(
            patients_tab.patientID,
            patients_tab.email,
            patients_tab.gender,
            patients_tab.cholesterolLevel,
            patients_tab.isSmoker,
            patients_tab.isHavingHypertension
        )

        patients_result = cnx.execute(sqlalchemy.text(str(q_patients).replace('"','`'))).fetchall()
        data = []
        
        sql_last_prediction = """
            SELECT model_prediction
            FROM model_results
            WHERE patientID = :pid
            ORDER BY prc_dt DESC
            LIMIT 1
        """
        

        for row in patients_result:
            patient_id = row[0]

            # Ambil last consultation sebelum sekarang
            sql_last_visit = """
                SELECT consultation_time, consultationID
                FROM consultation
                WHERE patientID = :pid AND consultation_time <= NOW()
                ORDER BY consultation_time DESC
                LIMIT 1
            """
            last_visit_row = cnx.execute(sqlalchemy.text(sql_last_visit), {'pid': patient_id}).fetchone()
            last_visit = str(last_visit_row[0]) if last_visit_row else ""
            consultation_id = str(last_visit_row[1]) if last_visit_row else ""

            # Ambil daftar obat (medName dan dosage) untuk pasien ini
            sql_meds = """
                SELECT mm.medName, mm.dosage, dm.frequency, dm.notes, dm.ID
                FROM detail_medicine dm
                JOIN master_medicine mm ON mm.medID = dm.medID
                WHERE dm.patientID = :pid
            """
            meds_result = cnx.execute(sqlalchemy.text(sql_meds), {'pid': patient_id}).fetchall()
            medications = [{"name": med[0], "dosage": med[1], "frequency":med[2], "notes": med[3],"detailID": med[4]} for med in meds_result] if meds_result else []

            last_prediction_row = cnx.execute(sqlalchemy.text(sql_last_prediction), {'pid': patient_id}).fetchone()
            last_prediction = last_prediction_row[0] if last_prediction_row else None

            data.append({
                'patientID': row[0],
                'email': row[1],
                'gender': row[2] if row[2] is not None else "",
                'cholesterolLevel': row[3] if row[3] is not None else "",
                'isSmoker': row[4] if row[4] is not None else "",
                'isHavingHypertension': row[5] if row[5] is not None else "",
                'last_visit': last_visit,
                'consultation_id': consultation_id,
                'medications': medications,
                'classification': last_prediction
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({'status': False, 'error': str(e)})
    
def schedule_consultation(curr_data, cnx):
    try:
        data = curr_data
        consultation_id = data["consultationID"]
        if not consultation_id:
            return jsonify({"status": False, "error": "consultationID is required"}), 400

        # hitung 3 hari dari sekarang
        new_consult_time = datetime.now() + timedelta(days=3)

        # query update
        update_query = f"""
            UPDATE consultation
            SET consultation_time = :new_time,
                status = 'scheduled'
            WHERE consultationID = :cid
        """

        cnx.execute(sqlalchemy.text(update_query), {"new_time": new_consult_time, "cid": consultation_id})
        cnx.commit()

        return jsonify({
            "status": True,
            "consultationID": consultation_id,
            "new_consultation_time": new_consult_time.strftime("%Y-%m-%d %H:%M:%S"),
            "new_status": "scheduled"
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})
    
def med_assign_schedule(curr_data, cnx):
    try:
        data = curr_data
        consultation_id = data["consultationID"]
        if not consultation_id:
            return jsonify({"status": False, "error": "consultationID is required"}), 400

        # hitung 3 hari dari sekarang
        new_consult_time = datetime.now() + timedelta(days=3)

        # query update
        update_query = f"""
            UPDATE consultation
            SET status = 'med_assign'
            WHERE consultationID = :cid
        """

        cnx.execute(sqlalchemy.text(update_query), {"new_time": new_consult_time, "cid": consultation_id})
        cnx.commit()

        return jsonify({
            "status": True,
            "consultationID": consultation_id,
            "new_status": "med_assign"
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

def get_pending_consultations(cnx):
    try:
        sql = """
        SELECT c.patientID,
               c.consultation_time,
               c.status,
               p.email,
               p.gender,
               p.cholesterolLevel,
               p.isSmoker,
               p.isHavingHypertension,
               c.consultationID
        FROM consultation c
        JOIN patients p ON c.patientID = p.patientID
        WHERE c.status = 'pending'
        ORDER BY c.created_at DESC
        """

        result = cnx.execute(sqlalchemy.text(sql)).fetchall()
        data = []

        for row in result:
            patient_id = row[0]

            # Ambil daftar obat (medName dan dosage) untuk pasien ini
            sql_meds = """
                SELECT mm.medName, mm.dosage
                FROM detail_medicine dm
                JOIN master_medicine mm ON mm.medID = dm.medID
                WHERE dm.patientID = :pid
            """
            meds_result = cnx.execute(sqlalchemy.text(sql_meds), {'pid': patient_id}).fetchall()
            medications = [{"name": med[0], "dosage": med[1]} for med in meds_result] if meds_result else []

            data.append({
                'patientID': patient_id,
                'consultation_time': str(row[1]) if row[1] else "",
                'status': row[2],
                'email': row[3],
                'gender': row[4] if row[4] else "",
                'cholesterolLevel': row[5] if row[5] else "",
                'isSmoker': row[6] if row[6] else "",
                'isHavingHypertension': row[7] if row[7] else "",
                'medications': medications,
                'consultation_id' : row[8] if row[8] else ""
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({'status': False, 'error': str(e)})


def set_consultation(curr_data, cnx, key_list=['patientID']):
    try:
        status, data = validate_dict(curr_data, key_list)
    except Exception as e:
        return jsonify({
            "status": False,
            "error": "Key Error!",
            "message": str(e)
        }), 400

    if status: 
        try:
            tgt_tab = Table('consultation')
            q = Query.into(tgt_tab).columns(tuple(key_list)).insert(tuple(data))
            cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
            cnx.commit()
            
            resp_dict = {
                "status": True,
                "message": "Medication inserted successfully",
                "data": {
                    "id": lastrowid[0],
                    **{i: curr_data[i] for i in key_list}
                }
            }
            return jsonify(resp_dict)
        except Exception as e:
            return jsonify({
                "status": False,
                "error": str(e)
            }), 500
    else:
        return jsonify({
            "status": False,
            "error": "Validation failed",
            "missing_keys": key_list
        }), 400