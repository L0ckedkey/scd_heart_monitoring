import jwt
from pypika import Query, Table
import sqlalchemy
from datetime import datetime

def validate_dict(curr_dict,key_list):
    data_list = []
    for i in key_list:
        if i not in list(curr_dict.keys()):
            return False
        data_list.append(curr_dict[i])
    return True, data_list

def generate_token(secret_key, data_dict):
    token = jwt.encode(data_dict, secret_key, algorithm='HS256')
    return token

def get_user_by_id(id,cnx):
    tgt_tab = Table('patients')
    q = Query.from_(tgt_tab).select('email','password').where(tgt_tab["patientID"] == id)
#    cursor = cnx.cursor(buffered=True)
    row = cnx.execute(sqlalchemy.text(str(q).replace('"','`'))).fetchone()
#    row = cursor.fetchone()
#    cursor.close()
    return row

def map_dict(keys,value_list):
    new_dict = {}
    for i in range(len(keys)):
        if isinstance(value_list[i],datetime):
            new_dict[keys[i]]=value_list[i].strftime('%Y-%m-%d %H:%M:%S')
        else:
            new_dict[keys[i]]=value_list[i]
    return new_dict
