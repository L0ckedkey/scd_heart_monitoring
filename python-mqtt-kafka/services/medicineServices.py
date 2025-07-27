from pypika import Query, Table,Criterion
from flask import jsonify
import sqlalchemy
from misc.utils import *

def insert_medicine(curr_data,cnx,key_list=['patientId','image','name','frequency','time','additionalInfo']):
    try:
        status,data = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        tgt_tab = Table('medicines')
        q = Query.into(tgt_tab).columns(tuple(key_list)).insert(tuple(data))
#        cursor = cnx.cursor(buffered=True)
        row = cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
#        cursor.execute(str(q).replace('"','`'))
        cnx.commit()
        
        resp_dict = {}
        lastrowid = cnx.execute(sqlalchemy.text('SELECT LAST_INSERT_ID()')).fetchone()
        resp_dict['id'] = lastrowid[0]
        for i in key_list:
            resp_dict[i] = curr_data[i]
#        cursor.close()
        return jsonify(resp_dict)

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

def get_all_medicines(patientId,cnx,key_list=['medicineId','patientId','image','name','frequency','time','additionalInfo']):
    tgt_tab = Table('medicines')
    q = Query.from_(tgt_tab).select('medicineId','patientId','image','name','frequency','time','additionalInfo').where(
        tgt_tab['patientId'] == patientId)
#    cursor = cnx.cursor(buffered=True)
    row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchall()
#    row = cnx.fetchall()
    resp_list = map(lambda x:map_dict(key_list,x),row)
#    cursor.close()

    return list(resp_list)

def delete_medicine(medicineId,cnx):
    tgt_tab = Table('medicines')
    q = Query.from_(tgt_tab).delete().where(tgt_tab['medicineId'] == medicineId)
#    cursor = cnx.cursor(buffered=True)
    cnx.execute(sqlalchemy.text(str(q).replace('"','`')))
#    cursor.execute(str(q).replace('"','`'))
    cnx.commit()
    
    return {'status':True}
