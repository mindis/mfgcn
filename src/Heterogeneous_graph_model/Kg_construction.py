import numpy as np
import matplotlib.pyplot as plt
import random
import networkx as nx
import math
import time
import pandas as pd
from kg_model_modify import hetero_model_modify
from LSTM_model import LSTM_model
from kg_process_data import kg_process_data
from Shallow_nn_ehr import NN_model
from evaluation import cal_auc
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

class Kg_construct_ehr():
    """
    construct knowledge graph out of EHR data
    """
    def __init__(self):
        file_path = '/home/tingyi/MIMIC'
        self.diagnosis = file_path + '/DIAGNOSES_ICD.csv'
        self.diagnosis_d = file_path + '/D_ICD_DIAGNOSES.csv'
        self.prescription = file_path + '/PRESCRIPTIONS.csv'
        self.charteve = file_path + '/CHARTEVENTS.csv'
        self.d_item = file_path + '/D_ITEMS.csv'
        self.noteevents = file_path + '/NOTEEVENTS.csv'
        self.proc_icd = file_path + '/PROCEDURES_ICD.csv'
        self.labeve = file_path + '/LABEVENTS.csv'
        self.patient = file_path + '/PATIENTS.csv'
        self.ICU_stay = file_path + '/ICUSTAYS.csv'
        self.read_icustay()
        self.read_labeve()
        self.read_patient()
        self.read_diagnosis()
        self.read_charteve()
        self.read_diagnosis_d()
        self.read_prescription()
        self.read_ditem()
        #self.read_proc_icd()

    def read_icustay(self):
        self.icu = pd.read_csv(self.ICU_stay)
        self.icu_ar = np.array(self.icu)

    def read_patient(self):
        self.pat = pd.read_csv(self.patient)
        self.pat_ar = np.array(self.pat)

    def read_diagnosis(self):
        self.diag = pd.read_csv(self.diagnosis)
        self.diag_ar = np.array(self.diag)

    def read_diagnosis_d(self):
        self.diag_d = pd.read_csv(self.diagnosis_d)
        self.diag_d_ar = np.array(self.diag_d)

    def read_prescription(self):
        self.pres = pd.read_csv(self.prescription)

    def read_charteve(self):
        self.char = open(self.charteve)
        #self.char = pd.read_csv(self.charteve,chunksize=4000000)
        #self.char_ar = np.array(self.char.get_chunk())
        #self.num_char = self.char_ar.shape[0]

    def read_labeve(self):
        #self.lab = open(self.labeve)
        self.lab = pd.read_csv(self.labeve,chunksize=4000000)
        self.lab_ar = np.array(self.lab.get_chunk())
        self.num_lab = self.lab_ar.shape[0]

    def read_ditem(self):
        self.d_item = pd.read_csv(self.d_item)
        self.d_item_ar = np.array(self.d_item)

    def read_noteevent(self):
        self.note = pd.read_csv(self.noteevents,chunksize=1000)

    def read_proc_icd(self):
        self.proc_icd = pd.read_csv(self.proc_icd)


    def create_kg_dic(self):
        self.dic_patient = {}
        self.dic_diag = {}
        self.dic_item = {}
        self.dic_patient_addmission = {}
        index_item = 0
        index_diag = 0
        num_read = 0
        """
        for line in self.char:
            if num_read == 0:
                num_read += 1
                continue
            if num_read > 4000000:
                break
            num_read += 1
            line = line.rstrip('\n')
            line = line.split(',')
            itemid = np.int(line[4])
            value = np.float(line[9])
            hadm_id = np.int(line[2])
            patient_id = np.int(line[1])
            date_time = line[5].split(' ')
            date = [np.int(i) for i in date_time[0].split('-')]
            date_value = date[0]*10000+date[1]*100+date[2]
            time = [np.int(i) for i in date_time[1].split(':')]
            time_value = time[0]*100 + time[1]
            date_time_value = date_value*10000+time_value
            if itemid not in self.dic_item:
                self.dic_item[itemid] = {}
                self.dic_item[itemid]['nodetype'] = 'item'
                self.dic_item[itemid].setdefault('neighbor_patient', []).append(hadm_id)
                self.dic_item[itemid]['item_index'] = index_item
                self.dic_item[itemid].setdefault('value', []).append(value)
                #self.dic_item[itemid]['mean_value'] = []
                index_item += 1
            else:
                self.dic_item[itemid].setdefault('value', []).append(value)
                if hadm_id not in self.dic_item[itemid]['neighbor_patient']:
                    self.dic_item[itemid].setdefault('neighbor_patient', []).append(hadm_id)

            if hadm_id not in self.dic_patient:
                self.dic_patient[hadm_id] = {}
                self.dic_patient[hadm_id]['itemid'] = {}
                self.dic_patient[hadm_id]['nodetype'] = 'patient'
                self.dic_patient[hadm_id]['next_admission'] = None
                self.dic_patient[hadm_id]['itemid'].setdefault(itemid, []).append(value)
                #self.dic_patient[patient_id]['neighbor_presc'] = {}
            else:
                self.dic_patient[hadm_id]['itemid'].setdefault(itemid,[]).append(value)

            if patient_id not in self.dic_patient_addmission:
                self.dic_patient_addmission[patient_id] = {}
                self.dic_patient_addmission[patient_id][hadm_id] = {}
                self.dic_patient_addmission[patient_id][hadm_id]['date_time'] = date_time
                self.dic_patient_addmission[patient_id][hadm_id]['date'] = date
                self.dic_patient_addmission[patient_id][hadm_id]['date_value'] = date_value
                self.dic_patient_addmission[patient_id][hadm_id]['time'] = time
                self.dic_patient_addmission[patient_id][hadm_id]['time_value'] = time_value
                self.dic_patient_addmission[patient_id][hadm_id]['date_time_value'] = date_time_value
                self.dic_patient_addmission[patient_id].setdefault('time_series',[]).append(hadm_id)
            else:
                if hadm_id not in self.dic_patient_addmission[patient_id]['time_series']:
                    self.dic_patient_addmission[patient_id][hadm_id] = {}
                    self.dic_patient_addmission[patient_id][hadm_id]['date_time'] = date_time
                    self.dic_patient_addmission[patient_id][hadm_id]['date'] = date
                    self.dic_patient_addmission[patient_id][hadm_id]['time'] = time
                    self.dic_patient_addmission[patient_id][hadm_id]['date_value'] = date_value
                    self.dic_patient_addmission[patient_id][hadm_id]['time_value'] = time_value
                    self.dic_patient_addmission[patient_id][hadm_id]['date_time_value'] = date_time_value
                    index = 0
                    flag = 0
                    for i in self.dic_patient_addmission[patient_id]['time_series']:
                        if date_time_value < self.dic_patient_addmission[patient_id][i]['date_time_value']:
                            self.dic_patient_addmission[patient_id]['time_series'].insert(index,hadm_id)
                            self.dic_patient[hadm_id]['next_admission'] = i
                            if not index == 0:
                                self.dic_patient[self.dic_patient_addmission[patient_id]['time_series'][index-1]]['next_admission'] = hadm_id
                            flag = 1
                            break
                        index += 1
                    if flag == 0:
                        self.dic_patient[self.dic_patient_addmission[patient_id]['time_series'][-1]]['next_admission'] = hadm_id
                        self.dic_patient_addmission[patient_id].setdefault('time_series', []).append(hadm_id)
        """
        self.icu_total = self.icu_ar[np.where(kg.icu_ar[:,-1]>1)[0]]
        self.total_data = np.intersect1d(list(self.icu_total[:,2]),list(self.lab_ar[:,2]))
        index_count = 0
        for i in self.total_data:
            print(index_count)
            index_count += 1
            hadm_id = i
            self.index_total = i
            single_patient_hadm_lab = np.where(self.lab_ar[:,2] == i)[0]
            self.single_patient_hadm_icu = np.where(self.icu_total[:,2] == i)
            subject_id = self.icu_total[self.single_patient_hadm_icu][0][1]
            sub_id_pat = np.where(self.pat_ar[:,1]== subject_id)[0]
            flag = self.pat_ar[sub_id_pat][0][-1]
            out_hospital_time = self.icu_total[self.single_patient_hadm_icu][0][-2]
            out_date_time = out_hospital_time.split(' ')
            out_date = [np.int(i) for i in out_date_time[0].split('-')]
            out_date_value = out_date[0]*365 + out_date[1]*30 + out_date[2]
            out_time = [np.int(i) for i in out_date_time[1].split(':')]
            out_time_value = out_time[0]*60 + out_time[1]
            if hadm_id not in self.dic_patient.keys():
                self.dic_patient[hadm_id] = {}
                self.dic_patient[hadm_id]['itemid'] = {}
                self.dic_patient[hadm_id]['flag'] = flag
                self.dic_patient[hadm_id]['prior_time'] = {}
            for k in single_patient_hadm_lab:
                value = self.lab_ar[k][6]
                itemid = self.lab_ar[k][3]
                if math.isnan(value):
                    continue
                self.dic_patient[hadm_id]['nodetype'] = 'patient'
                self.dic_patient[hadm_id]['next_admission'] = None
                self.dic_patient[hadm_id]['itemid'].setdefault(itemid, []).append(value)
                if itemid not in self.dic_item.keys():
                    self.dic_item[itemid] = {}
                    self.dic_item[itemid].setdefault('neighbor_patient', []).append(hadm_id)
                    self.dic_item[itemid]['item_index'] = index_item
                    self.dic_item[itemid].setdefault('value', []).append(value)
                    index_item += 1
                else:
                    self.dic_item[itemid].setdefault('value', []).append(value)
                    if hadm_id not in self.dic_item[itemid]['neighbor_patient']:
                        self.dic_item[itemid].setdefault('neighbor_patient', []).append(hadm_id)

            for k in single_patient_hadm_lab:
                value = self.lab_ar[k][6]
                itemid = self.lab_ar[k][3]
                if math.isnan(value):
                    continue
                date_time = self.lab_ar[k][4].split(' ')
                date = [np.int(i) for i in date_time[0].split('-')]
                date_value = date[0] * 365 + date[1] * 30 + date[2]
                time = [np.int(i) for i in date_time[1].split(':')]
                time_value = time[0] * 60 + time[1]
                if (out_date_value - date_value)>2:
                    continue
                self.prior_time = np.int(np.floor(np.float((out_time_value - time_value)/60)))
                if self.prior_time < 0:
                    self.prior_time = 0
                if self.prior_time not in self.dic_patient[hadm_id]['prior_time']:
                    self.dic_patient[hadm_id]['prior_time'][self.prior_time] = {}
                    self.dic_patient[hadm_id]['prior_time'][self.prior_time].setdefault(itemid,[]).append(value)
                else:
                    self.dic_patient[hadm_id]['prior_time'][self.prior_time].setdefault(itemid,[]).append(value)

        for i in range(self.diag_ar.shape[0]):
            hadm_id = self.diag_ar[i][2]
            diag_icd = self.diag_ar[i][4]
            if hadm_id in self.dic_patient:
                if diag_icd not in self.dic_diag:
                    self.dic_diag[diag_icd] = {}
                    self.dic_diag[diag_icd].setdefault('neighbor_patient', []).append(hadm_id)
                    self.dic_diag[diag_icd]['nodetype'] = 'diagnosis'
                    self.dic_diag[diag_icd]['diag_index'] = index_diag
                    self.dic_patient[hadm_id].setdefault('neighbor_diag', []).append(diag_icd)
                    index_diag += 1
                else:
                    self.dic_patient[hadm_id].setdefault('neighbor_diag',[]).append(diag_icd)
                    self.dic_diag[diag_icd].setdefault('neighbor_patient',[]).append(hadm_id)

        for i in self.dic_item.keys():
            self.dic_item[i]['mean_value'] = np.mean(self.dic_item[i]['value'])
            self.dic_item[i]['std'] = np.std(self.dic_item[i]['value'])





    def create_kg(self):
        self.g = nx.DiGraph()
        for i in range(self.num_char):
            patient_id = self.char_ar[i][1]/home/tingyi/ecgtoolkit-cs-git/ECGToolkit/libs/ECGConversion/MUSEXML/MUSEXML/MUSEXMLFormat.cs
            itemid = self.char_ar[i][4]
            value = self.char_ar[i][8]
            itemid_list = np.where(self.d_item_ar == itemid)
            diag_list = np.where(self.diag_ar[:,1] == patient_id)
            diag_icd9_list = self.diag_ar[:,4][diag_list]
            diag_d_list = [np.where(self.diag_d_ar[:,1] == diag_icd9_list[x])[0] for x in range(diag_icd9_list.shape[0])]
            """
            Add patient node
            """
            self.g.add_node(patient_id, item_id=itemid)
            self.g.add_node(patient_id, test_value=value)
            self.g.add_node(patient_id, node_type='patient')
            self.g.add_node(patient_id, itemid_list=itemid_list)
            self.g.add_node(itemid, node_type='ICD9')
            """
            Add diagnosis ICD9 node
            """
            self.g.add_edge(patient_id, itemid, type='')




if __name__ == "__main__":
    kg = Kg_construct_ehr()
    #kg.create_kg_dic()
    #process_data = kg_process_data(kg)
    #test_accur = []
    #process_data.seperate_train_test()
   # print("finished loading")

    #for i in range(3):
    """
    process_data.cross_validation_seperate(0)
    hetro_model = hetero_model_modify(kg,process_data)
    #LSTM_model = LSTM_model(kg,hetro_model,process_data)
    hetro_model.config_model()
    print("in get train")
    hetro_model.get_train_graph()
    hetro_model.train()
    hetro_model.test()

    embed_patient = hetro_model.embed_patient_norm
    embed_diag = hetro_model.embed_diag
    embed_item = hetro_model.embed_item
    embed_total = np.concatenate((embed_diag,embed_patient,embed_item),axis=0)
    embed_total_2d = TSNE(n_components=2).fit_transform(embed_total)
    label = np.zeros(4510)
    label[0:2922] = 0
    label[2922:2922+1141] = 18
    label[2922+1141:] = 19
    for i in kg.dic_diag.keys():
        index_class = kg.dic_diag[i]['icd']
        index = kg.dic_diag[i]['diag_index']
        label[index] = index_class
    for i in range(4510):
        if label[i] == 0:
            color_ = "blue"
            makersize_ = 4
        if label[i] == 18:
            color_ = "red"
            makersize_ = 5
        if label[i] == 19:
            color_ = "green"
            makersize_ = 6
        plt.plot(embed_total_2d[i][0],embed_total_2d[i][1],'.',color=color_,markersize=makersize_)


    for i in kg.dic_patient_addmission.keys():
        patient_dob = np.float(patient_info_ar[np.where(patient_info_ar[:, 1] == i)[0][0], 3].split(' ')[0].split('-')[0])
        admit_time = kg.dic_patient_addmission[i][kg.dic_patient_addmission[i]['time_series'][0]]['date'][0]
        age = admit_time - patient_dob
        kg.dic_patient_addmission[i]['age'] = age

    for i in kg.dic_patient.keys():
        for j in kg.dic_patient_addmission.keys():
            if i in kg.dic_patient_addmission[j]['time_series']:
                kg.dic_patient[i]['age'] = kg.dic_patient_addmission[j]['age']


    patient_age = np.zeros(len(process_data.test_hadm_id))
    index_patient = 0
    for i in process_data.test_hadm_id:
        #print(index_patient)
        age_patient = kg.dic_patient[i]['age']
        patient_age[index_patient] = age_patient
        index_patient += 1
    """

    """
    if label[i] == 1:
        color_ = "orange"
    if label[i] == 2:
        color_ = "purple"
    if label[i] == 3:
        color_ = "brown"
    if label[i] == 4:
        color_ = "pink"
    if label[i] == 5:
        color_ = "gray"
    if label[i] == 6:
        color_ = "olive"
    if label[i] == 7:
        color_ = "cyan"
    if label[i] == 8:
        color_ = "black"
    if label[i] == 9:
        color_ = "darkorange"
    if label[i] == 10:
        color_ = "burlywood"
    if label[i] == 11:
        color_ = "indianred"
    if label[i] == 12:
        color_ = "tan"
    if label[i] == 13:
        color_ = "darkgoldenrod"
    if label[i] == 14:
        color_ = "gold"
    if label[i] == 15:
        color_ = "khaki"
    if label[i] == 16:
        color_ = "darkkhaki"
    if label[i] == 17:
        color_ = "yellow"
    """




        #single_test_accur = np.mean(hetro_model.tp_test)
        #test_accur.append(hetro_model.tp_test)
        #del hetro_model
    """
    file = open("/home/tingyi/mfgcn/src/bl_100_sigmoid_fp_73.txt")
    for line in file:
        fp_rate = line.rstrip('\n')
    fp_rate = fp_rate.split(',')
    fp_rate = [i.replace('[','') for i in fp_rate]
    fp_rate = [i.replace(']','') for i in fp_rate]
    fp_rate = [np.float(i) for i in fp_rate]

    file = open("/home/tingyi/mfgcn/src/bl_100_sigmoid_tp_73.txt")
    for line in file:
        tp_rate = line.rstrip('\n')
    tp_rate = tp_rate.split(',')
    tp_rate = [i.replace('[','') for i in tp_rate]
    tp_rate = [i.replace(']','') for i in tp_rate]
    tp_rate = [np.float(i) for i in tp_rate]
    """







    """
    test_accur = []
    for i in range(process_data.cross_validation_folder):
        process_data.cross_validation_seperate(i)
        hetro_model = hetero_model_modify(kg, process_data)
        LSTM_model_ = LSTM_model(kg,hetro_model,process_data)
        LSTM_model_.config_model()
        LSTM_model_.train()
        LSTM_model_.test()
        test_accur.append(LSTM_model_.f1_test)
        del LSTM_model_
    """

    #test_accur = []
    #for i in range(process_data.cross_validation_folder):
    """
    process_data.cross_validation_seperate(0)
    hetro_model_ = hetero_model_modify(kg,process_data)
    nn_model = NN_model(kg,hetro_model_,process_data)
    nn_model.config_model()
    nn_model.train()
    """
    #nn_model.test()
        #test_accur.append(nn_model.tp_test)
        #del nn_model

    #for i in range(2920):











