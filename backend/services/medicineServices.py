from pypika import Query, Table,Criterion
from flask import jsonify
import sqlalchemy
from misc.utils import *

# def insert_medicine(curr_data,cnx,key_list=['patientId','image','name','frequency','time','additionalInfo']):
#     try:
#         status,data = validate_dict(curr_data,key_list)
#     except:
#         return "Key Error!"
#     if status: 
#         tgt_tab = Table('medicines')
#         q = Query.into(tgt_tab).columns(tuple(key_list)).insert(tuple(data))
# #        cursor = cnx.cursor(buffered=True)
#         row = cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
# #        cursor.execute(str(q).replace('"','`'))
#         cnx.commit()
        
#         resp_dict = {}
#         lastrowid = cnx.execute(sqlalchemy.text('SELECT LAST_INSERT_ID()')).fetchone()
#         resp_dict['id'] = lastrowid[0]
#         for i in key_list:
#             resp_dict[i] = curr_data[i]
# #        cursor.close()
#         return jsonify(resp_dict)

def get_medicine(patientId,medId,cnx,key_list=['medicineId','patientId','image','name','frequency','time','additionalInfo']):
    tgt_tab = Table('medicines')
    q = Query.from_(tgt_tab).select('medicineId','patientId','image','name','frequency','time','additionalInfo').where(
        Criterion.all([
            tgt_tab["medicineId"] == medId,
            tgt_tab['patientId'] == patientId
        ])
    )
#    cursor = cnx.cursor(buffered=True)
    row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchone()
#    cursor.execute(str(q).replace('"','`'))
#    row = cursor.fetchone()
    resp_dict = {}
    
    for i in range(len(key_list)):
        resp_dict[key_list[i]] = row[i]
#    cursor.close()
    return jsonify(resp_dict)

# def get_all_medicines(patientId,cnx,key_list=['medicineId','patientId','image','name','frequency','time','additionalInfo']):
#     tgt_tab = Table('medicines')
#     q = Query.from_(tgt_tab).select('medicineId','patientId','image','name','frequency','time','additionalInfo').where(
#         tgt_tab['patientId'] == patientId)
# #    cursor = cnx.cursor(buffered=True)
#     row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchall()
# #    row = cnx.fetchall()
#     resp_list = map(lambda x:map_dict(key_list,x),row)
# #    cursor.close()

#     return list(resp_list)

# def delete_medicine(medicineId,cnx):
#     tgt_tab = Table('medicines')
#     q = Query.from_(tgt_tab).delete().where(tgt_tab['medicineId'] == medicineId)
# #    cursor = cnx.cursor(buffered=True)
#     cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
# #    cursor.execute(str(q).replace('"','`'))
#     cnx.commit()
    
#     return {'status':True}



def get_all_medicines(cnx):
    tgt_tab = Table('master_medicine')
    q = Query.from_(tgt_tab).select('medID','medName','dosage','category')
    rows = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchall()
    
    result = [dict(row._mapping) for row in rows]
    return jsonify(result)


def update_medicine(curr_data, cnx, key_list=['medName','dosage','category']):
    try:
        # medID harus ada
        if "medID" not in curr_data:
            return jsonify({
                "status": False,
                "error": "Key Error!",
                "message": "medID is required"
            }), 400

        medID = curr_data["medID"]

        # ambil hanya field yang ada di key_list
        update_data = {k: curr_data[k] for k in key_list if k in curr_data}

        if not update_data:
            return jsonify({
                "status": False,
                "error": "No valid fields to update"
            }), 400

        tgt_tab = Table('master_medicine')
        q = Query.update(tgt_tab)

        # set kolom yang diupdate
        for k, v in update_data.items():
            q = q.set(getattr(tgt_tab, k), v)

        # where pakai medID
        q = q.where(tgt_tab.medID == medID)

        # eksekusi
        cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
        cnx.commit()

        return jsonify({
            "status": True,
            "message": "Medication updated successfully",
            "data": {
                "medID": medID,
                **update_data
            }
        })

    except Exception as e:
        return jsonify({
            "status": False,
            "error": str(e)
        }), 500
        
        
def delete_medicine(curr_data, cnx):
    med_id = curr_data['medID']
    try:
        # Hapus data dari tabel master_medicine
        q = f"DELETE FROM master_medicine WHERE medID = :medID"
        cnx.execute(sqlalchemy.text(q), {"medID": med_id})
        cnx.commit()

        resp_dict = {
            "status": True,
            "message": f"Medication with medID {med_id} deleted successfully",
            "deleted_id": med_id
        }
        return jsonify(resp_dict), 200
    except Exception as e:
        return jsonify({
            "status": False,
            "error": str(e)
        }), 500
        
def delete_detail_medicine(curr_data, cnx):
    med_id = curr_data['detailID']
    try:
        # Hapus data dari tabel master_medicine
        q = f"DELETE FROM detail_medicine WHERE ID = :medID"
        cnx.execute(sqlalchemy.text(q), {"medID": med_id})
        cnx.commit()

        resp_dict = {
            "status": True,
            "message": f"Medication with medID {med_id} deleted successfully",
            "deleted_id": med_id
        }
        return jsonify(resp_dict), 200
    except Exception as e:
        return jsonify({
            "status": False,
            "error": str(e)
        }), 500

        
def insert_medicine(curr_data, cnx, key_list=['medName','dosage','category']):
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
            tgt_tab = Table('master_medicine')
            q = Query.into(tgt_tab).columns(tuple(key_list)).insert(tuple(data))
            cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
            cnx.commit()
            
            # Ambil last inserted id
            lastrowid = cnx.execute(sqlalchemy.text('SELECT LAST_INSERT_ID()')).fetchone()
            
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
        
        
def insert_detail_medicine(curr_data, cnx, key_list=['patientID','medID','frequency','notes']):
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
            tgt_tab = Table('detail_medicine')
            q = Query.into(tgt_tab).columns(tuple(key_list)).insert(tuple(data))
            cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
            cnx.commit()
            
            # Ambil last inserted id
            lastrowid = cnx.execute(sqlalchemy.text('SELECT LAST_INSERT_ID()')).fetchone()
            
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


