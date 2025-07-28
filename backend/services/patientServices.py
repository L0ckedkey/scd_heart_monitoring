from misc.utils import *
import bcrypt 
from pypika import Query, Table
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
            for key,val in resp_dict.items:
                if val == None:
                    resp_dict[key] == ""
            resp_dict['token'] = generate_token(secret_key, resp_dict)
            
#            cursor.close()
            if "pin" in key_list:
                return {'status':True}
            return jsonify(resp_dict)

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
    
def login_patient(curr_data,cnx,key_list=['email','password']):
    try:
        status,_ = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        tgt_tab = Table('patients')
        q = Query.from_(tgt_tab).select('email','password','patientID','gender','cholesterolLevel','isSmoker','isHavingHypertension').where(tgt_tab["email"] == curr_data['email'])
#        cursor = cnx.cursor(buffered=True)
        row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchone()
        
#        cursor.execute(str(q).replace('"','`'))
#        row = cursor.fetchone()
#        cursor.close()
       
        curr_data['password'] = curr_data['password'].encode('utf-8') 
        salt = bcrypt.gensalt() 
        try:
            if bcrypt.checkpw(curr_data['password'],row[1].encode('utf-8')):
                resp_dict = {}
                resp_dict["email"] = curr_data["email"]
                new_keys = ['patientID','gender','cholesterolLevel','isSmoker','isHavingHypertension']
                resp_dict['id'] = row[2]
#                return row

                for i in range(3,len(new_keys)+2):
                    if row[i] != None:
                        resp_dict[new_keys[i-2]] = row[i]
                    else:
                        resp_dict[new_keys[i-2]] = ""
#                    print(resp_dict)
#                    if resp_dict[new_keys[i-2]] == None:
#                        resp_dict[new_keys[i-2]] = ""

                secret_key = 'dvf3-342-3-402-5'
                resp_dict['token'] = generate_token(secret_key, resp_dict)   
        except:
            return {'status':False}
        return jsonify(resp_dict)
