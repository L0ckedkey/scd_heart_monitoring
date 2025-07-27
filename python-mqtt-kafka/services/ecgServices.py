import ast
from datetime import datetime
from datetime import timedelta
from pypika import Query, Table,Order
from misc.utils import *
import sqlalchemy
from services.inferenceServices import *

def convert_ecg_dict_to_tuple(ecgdict):
    res_list = []
    for i in range(len(ecgdict['rr'])):
        cur_time = datetime.strptime(ecgdict['startTime'], '%Y-%m-%d %H:%M:%S') + timedelta(seconds=i)
        res_list.append((ecgdict['patientId'],ecgdict['rr'][i],60000//ecgdict['rr'][i],cur_time.strftime('%Y-%m-%d %H:%M:%S')))
    return tuple(res_list)

def insert_ecg(curr_data,cnx,key_list=['patientId','startTime','rr']):
    curr_data['rr'] = ast.literal_eval(curr_data['rr'])

    try:
        status,_ = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        data = convert_ecg_dict_to_tuple(curr_data)
        tgt_tab = Table('ecg')
        
        column_list = ['patientId','ecgValue','bpmValue','createdAt']
        q = Query.into(tgt_tab).columns(tuple(column_list)).insert(data)
#        cursor = cnx.cursor(buffered=True)
        cnx.execute(sqlalchemy.text(str(q).replace('"','`').replace('((','(').replace('))',')')))
#        cursor.execute(str(q).replace('"','`').replace('((','(').replace('))',')'))
        cnx.commit()
        
#        cursor.close()
        samples = [{"patientId":curr_data['patientId'],
           "rr_interval_ms": curr_data['rr'],
           "created_at": curr_data['startTime']}]
        curr_results = predict(samples)
        save_prediction_results(curr_results,cnx)

        return {'status':True}
    
def get_ecg_list_by_patient_id_in_range(curr_data,cnx,key_list=['patientId','startTime','endTime']):
    try:
        status,_ = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        tgt_tab = Table('ecg')
        q = Query.from_(tgt_tab).where(tgt_tab.createdAt[curr_data['startTime']:curr_data['endTime']]).select(tgt_tab.star)
#         print(q)
#        cursor = cnx.cursor(buffered=True)
        row = cnx.execute(sqlalchemy.text(str(q).replace('"','`').replace('((','(').replace('))',')'))).fetchall()
#        cursor.execute(str(q).replace('"','`').replace('((','(').replace('))',')'))
#        row = cursor.fetchall()
        resp_list = map(lambda x:map_dict(['id','userId','ecgValue','bpmValue','createdAt'],x),row)
#        cursor.close()
        return list(resp_list)
    
def get_histories(patientId,cnx):
    tgt_tab = Table('model_results')
    q = Query.from_(tgt_tab).where(tgt_tab.patientId==patientId).select("record_id","patientId","model_prediction"
                                                                         ,"prc_dt","exc_time_sec")
#         print(q)
#    cursor = cnx.cursor(buffered=True)
    row = cnx.execute(sqlalchemy.text(str(q).replace('"','`').replace('((','(').replace('))',')'))).fetchall()
#    cursor.execute(str(q).replace('"','`').replace('((','(').replace('))',')'))
#    row = cursor.fetchall()
    row = list(map(list, row))
    endTimes = list(map(lambda x:(x[:][3]+timedelta(seconds=x[:][4])),row))

    for i in range(len(endTimes)):
        row[i][4] = endTimes[i]
    
    resp_list = map(lambda x:map_dict(['id','userId','havingScd','startPredictionTime','endPredictionTime'],x),row)
#    cursor.close()

    return list(resp_list)

def make_predictions(curr_data,cnx,key_list=['patientId','startTime','endTime']):
    print("on make predictions")
    try:
        status,_ = validate_dict(curr_data,key_list)
    except:
        return "Key Error!"
    if status: 
        print(status)
        print("predicting")
        tgt_tab = Table('ecg')
        q = Query.from_(tgt_tab).where(tgt_tab.createdAt[curr_data['startTime']:curr_data['endTime']]).select('ecgValue','createdAt').orderby('createdAt',order=Order.asc)
 #       cursor = cnx.cursor(buffered=True)
        row = cnx.execute(sqlalchemy.text(str(q).replace('"','`').replace('((','(').replace('))',')'))).fetchall()
#        cursor.execute(str(q).replace('"','`').replace('((','(').replace('))',')'))
#        row = cursor.fetchall()
#        cursor.close()

        data = [t[0] for t in row]
        createdAt = row[0][1].strftime('%Y-%m-%d %H:%M:%S')
        samples = [{"patientId":curr_data['patientId'],
           "rr_interval_ms": data,
           "created_at": createdAt}]
        curr_results = predict(samples)
        save_prediction_results(curr_results,cnx)
        print(curr_results)
        return {'status':True, 'result': curr_results}
