import pickle, os, json, shutil, hrvanalysis as hrva
from pandas import read_csv
import numpy as np
from time import time
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler as mms
from misc.utils import *
import sqlalchemy
from scipy.stats import entropy

def load_model(selected_model):
    model_path = "models/{}/".format(selected_model)
    latest_pkl = sorted([p for p in os.listdir(model_path) if p.endswith(".pkl")], reverse=True)[0]
    model = pickle.load(open(model_path + latest_pkl, 'rb'))
    print("[DONE] Model `{}` was successfully loaded.".format(model))
    return model

def rr_preproc(rr_interval : list) -> list:
    nn_interval = hrva.remove_outliers(rr_intervals=rr_interval, verbose=False)

    # @param method: "malik", "kamath", "karlsson", "acar"
    nn_interval = hrva.remove_ectopic_beats(rr_intervals=nn_interval, method="malik", verbose=False)

    # @param interpolation_method: 'linear', 'time', 'index', 'values', 'nearest', 'zero', 'slinear',
    # 'quadratic', 'cubic', 'barycentric', 'krogh', 'spline', 'polynomial', 'from_derivatives',
    # 'piecewise_polynomial', 'pchip', 'akima', 'cubicspline'
    nn_interval = hrva.interpolate_nan_values(rr_intervals=nn_interval, interpolation_method="cubic")

    # remove NaN values which weren't filtered during interpolation; e.g., in the last index
    nn_interval = [i for i in nn_interval if str(i) != "nan"]
    
    return nn_interval

def extract_ftr(nn_interval : list, *args, **kwargs) -> dict:
    FEATURES = {}
    nn_interval = rr_preproc(nn_interval)

    # TIME DOMAIN
    ftr_time_domain = hrva.get_time_domain_features(nn_interval)
    FEATURES.update(ftr_time_domain)

    ftr_geometric_time_domain = hrva.get_geometrical_features(nn_interval)
    FEATURES.update(ftr_geometric_time_domain)

    # Frequency Domain
    ftr_freq_domain = hrva.get_frequency_domain_features(nn_interval)
    FEATURES.update(ftr_freq_domain)

    # Non-linear Domain
#    ftr_entropy = hrva.get_sampen(nn_interval) # sample entropy
#    FEATURES.update({"entropy" : ftr_entropy["sampen"]})

    entropy_val = entropy(nn_interval) # to avoid entropy value becomes INF
    FEATURES.update({"entropy" : entropy_val})

    ftr_poincare = hrva.get_poincare_plot_features(nn_interval)
    FEATURES.update(ftr_poincare)

    # CVI (Cardiac Sympathetic Index), CSI (Cardiac Vagal Index)
    ftr_csi_cvi = hrva.get_csi_cvi_features(nn_interval)
    FEATURES.update(ftr_csi_cvi)
    
    return FEATURES

def predict(samples,model_id=1):
    # assume sample is list\

    model = load_model('mlp')
    scaler = mms()
    timestamp1 = datetime.now()
    selected_ftr = ['mean_nni', 'rmssd', 'mean_hr', 'triangular_index', \
                    'total_power', 'csi', 'cvi', 'entropy']

    FINAL_RESULT = []
    PREDICTION_FTRS = []

    for i in samples:
        result = {}
        all_features = extract_ftr(i["rr_interval_ms"])
        result.update(all_features)
        FINAL_RESULT.append(result)

        input_features = list({key : all_features[key] for key in selected_ftr}.values())
        PREDICTION_FTRS.append(input_features)

    # model prediction
    input_scaled = scaler.fit_transform(np.array(PREDICTION_FTRS))
    prediction = model.predict(input_scaled).tolist()
    timestamp2 = datetime.now()

    for f, p, s in zip(FINAL_RESULT, prediction, samples):
        desc = "Malignant Ventricular Ectopy" if p == 0 else "Normal Sinus Rhythm"
        f.update({
            "patientId": s['patientId'],
            "modelId": model_id,
            "prediction_label" : int(p),
            "prediction_desc" : desc,
            "exc_time_sec": (timestamp2 - timestamp1).total_seconds(),
            "src_created_at" : s["created_at"],
            "prc_dt" : datetime.now().strftime("%Y-%m-%d %X")
        })

    return FINAL_RESULT

def get_feature_store(cur_dict):
    key_list = ['mean_nni','sdnn','sdsd','nni_50','pnni_50','nni_20','pnni_20','rmssd','median_nni','range_nni','cvsd','cvnni','mean_hr','max_hr','min_hr','std_hr','triangular_index','lf','hf','lf_hf_ratio','lfnu','hfnu','total_power','vlf','entropy','sd1','sd2','ratio_sd2_sd1','csi','cvi','Modified_csi']
    d = {k: v for k, v in cur_dict.items() if k in key_list}
    return str(d).replace('\'','*')

def map_pred_results_to_tuple(preds):
    res_list = []
    for i in range(len(preds)):
        res_list.append((preds[i]['patientId'],get_feature_store(preds[i]),preds[i]['modelId'],preds[i]['prediction_label'],
                         preds[i]['exc_time_sec'],preds[i]['src_created_at'],preds[i]['prc_dt']
        ))
    return tuple(res_list)

def save_prediction_results(data,cnx):
    key_list = ['mean_nni','sdnn','sdsd','nni_50','pnni_50','nni_20','pnni_20','rmssd','median_nni','range_nni','cvsd','cvnni','mean_hr','max_hr','min_hr','std_hr','triangular_index','lf','hf','lf_hf_ratio','lfnu','hfnu','total_power','vlf','entropy','sd1','sd2','ratio_sd2_sd1','csi','cvi','Modified_csi','prediction_label','prediction_desc','src_created_at','prc_dt']
    try:
        status,_ = validate_dict(data[0],key_list)
    except:
        return "Key Error!"
    if status: 
        column_list = ['patientId','feature_store','model_id','model_prediction','exc_time_sec','data_snapshot_dt','prc_dt']
        tgt_tab = Table('model_results')
        q = Query.into(tgt_tab).columns(tuple(column_list)).insert(map_pred_results_to_tuple(data))
#        cursor = cnx.cursor(buffered=True)
        q = str(q).replace('"','`').replace('((','(').replace('))',')').replace('*','"')
        cnx.execute(sqlalchemy.text(q)) 
#        cursor.execute(str(q).replace('"','`').replace('((','(').replace('))',')'))
        cnx.commit()

#        cursor.close()

