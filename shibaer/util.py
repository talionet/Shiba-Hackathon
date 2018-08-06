"""
Utility to read the ER data
"""

import pandas as pd
import numpy as np
import os
import re


# These are the columns that we load
fields = pd.read_excel(os.path.abspath("../docs/ER/fields.xlsx"))
use_columns = fields[fields.is_load.astype(bool)].column_name.values


# ICD-9 columns
ICD9_columns = [c for c,m in zip(fields.column_name.values, fields["map"].values) if "ICD9" in str(m)]

# Drug columns
drug_columns = [c for c,m in zip(fields.column_name.values, fields["map"].values) if "take drug name" in str(m)]

# categoirical columns
categorical_columns = [c for c,m in zip(fields.column_name.values, fields["map"].values) if "Hebrew" in str(m)]


def read_process_data(data_file):
    f = pd.read_excel(data_file)

    # Restrict to the columns we need -- anything that was in the config (../docs/ER/fields.xlsx) and in the input
    use_columns_ = [c for c in f.columns.values if c in use_columns]
    f = f[use_columns_]

    # remove duplicates
    print("De-duplicating data. Number of rows before: ", f.shape[0])
    f.drop_duplicates(inplace=True, keep='first', subset="id_coded admission_date_chameleon".split())
    print("De-duplicating data. Number of rows after: ", f.shape[0])

    # parse ICD-9 fields -- collect list of numbers in this field
    for col in ICD9_columns:
        if col not in f.columns:
            continue
        f[col] = f[col].apply(lambda s: re.findall("\d+\.\d+", str(s)))

    # parse drug fields
    for col in drug_columns:
        if col not in f.columns:
            continue
        f[col] = f[col].apply(lambda s: re.findall("Drug name: ([A-Z]*) ", str(s)))
        
    
    # add/process some columns
    f.birth_date = pd.DatetimeIndex(f.birth_date)
    f.esi_chameleon = f.esi_chameleon.fillna("UNKNOWN")
    f.allergy = f.allergy.apply(lambda s: re.sub(r'\([^)]*\)', '', str(s)).split(";"))
    f.sensitivity = f.sensitivity.apply(lambda s: re.sub(r'\([^)]*\)', '', str(s)).split(";"))
    return f


def category2codes(f, inplace=True):
    """
    convert all categorical columns in a dataframe to label codes. Conversion table is printed but not saved.
    :param f: pd.DataFrame
    :param inplace:
    """

    if not inplace:
        f = f.copy()

    for col in f.select_dtypes(include="category"):

        # Print the conversion table
        print("="*80)
        print(col)
        print(pd.Series(f[col].cat.categories))

        # Do conversion
        f[col] = f[col].cat.codes

    return f

def read_metadata():
    meta_data= pd.read_csv(os.path.abspath("../docs/ER/meta_data.csv"), index_col='column_name')
    hebrew_map= {'כאב':'pain',
     'חום' :'fever',
     'דופק': 'pulse',
     'לחץ סיסטולי': 'sbp',
     'לחץ דיאסטולי': 'dbp' ,
     'סטורציה באויר חדר': 'in_room_saturation',
     'סטורציה': 'saturation',
     'מספר נשימות' : 'respiratory_rate'}
    meta_data = meta_data.rename(hebrew_map,axis=0)
    return meta_data

def load_pickle_files(thumbdrive, folder, is_small=False):
    """
    Utility to load the data from the thumbdrives. The data will be placed on the drives as several pickle files in a
    single folder.

    :param thumbdrive: str
        The name of the drive the data is on (ls -l /Volumes/ to find)
    :param folder: str
        The name of the folder in the drive the data is stored on
    :return: pd.DataFrame
        The concatenated data as a single frame
    """
    
        
    # Find the pickle files
    base_path = os.path.join("/Volumes", thumbdrive, folder)
    
    if is_small:
        pickle_files = ['small_pickle.pkl']
    else:
        pickle_files = os.listdir(base_path)
        pickle_files = [f for f in pickle_files if f.endswith(".pkl")]
    
    
        
    print("Found the following pickle files: ", pickle_files)

    # Load all data
    all_frames = []
    for f in pickle_files:
        print("Loading :", f)
        saved_data = pd.read_pickle(os.path.join(base_path, f))
        all_frames.append(saved_data)

    # Combine
    data = pd.concat(all_frames)
    
    # Process
    ## change hebrew columns to english
    hebrew_map= {'כאב':'pain',
     'חום' :'fever',
     'דופק': 'pulse',
     'לחץ סיסטולי': 'sbp',
     'לחץ דיאסטולי': 'dbp' ,
     'סטורציה באויר חדר': 'in_room_saturation',
     'סטורציה': 'saturation',
     'מספר נשימות' : 'respiratory_rate'}

    data = data.rename(hebrew_map,axis=1)

    print("Finished loading data")
    print("Total number of rows: ", data.shape[0])
    return data

def get_triaj_data(data,include_targets=True):
    md= pd.read_csv(os.path.abspath("../docs/ER/meta_data.csv"))
    md= md.loc[md.is_load==1]
    triaj_columns = md.loc[md['when (b=before, a=after)']== 'b']['column_name']
    if include_targets:
        target_columns = get_target_columns[data]
        triaj_columns.extend(target_columns)
    return data[triaj_columns]

def get_target_columns(data):
    return [c for c in data.columns if '_T' in c]
    

def convert_to_numeric(data, numeric_cols = [], ignore_strs=['<','>'],convert_str_map= {}):   
    print('converting numeric columns to numeric...')
    data_numeric= data[numeric_cols].copy()
    for st in ignore_strs:
        data_numeric=data_numeric.applymap(lambda s: s.replace(st,'') if type(s)==str else s)
    for st in convert_str_map.keys():
        data_numeric=data_numeric.applymap(lambda s: s.replace(st,convert_str_map[st]) if type(s)==str else s)
    data_numeric = data_numeric.apply(pd.to_numeric, errors='coerce')
    data[numeric_cols] = data_numeric
    return data

def remove_outliers(data, high=0.9999, low=0.00001, numeric_cols = []):
    print('removing outliers from numeric columns...')
    for name in numeric_cols:
        q_low, q_high = data[name].quantile([low, high]) 
        print('%s : %.2f - %.2f' %(name,q_low,q_high))
        data[name].mask(data[name]>q_high,q_high,inplace=True)
        data[name].mask(data[name]<q_low,q_low,inplace=True)       
    return data

def preprocess_data(data, numeric_cols = 'all', meta_data = None, percentiles=[0.001,0.999]):   
    if type(numeric_cols)==str:
        if numeric_cols == 'all':
            if meta_data is None:
                meta_data=read_metadata()
            numeric_cols = meta_data.loc[meta_data.data_type == 'numeric'].index
    
    processed_data= convert_to_numeric(data, numeric_cols = numeric_cols)
    proessed_data = remove_outliers(data, high=percentiles[1], low=percentiles[0], numeric_cols = numeric_cols)
    return processed_data

    
# --- Test ---
if __name__ == "__main__":
    BASE_PATH = os.path.expanduser("/Volumes/data/ER")
    INPUT_FILE = "2017 PROC 4.8.18.xlsx"
    OUTPUT_PKL = "2017 PROC 4.8.18.pkl"

    # Read and pre-process the data
    data = read_process_data(os.path.join(BASE_PATH, INPUT_FILE))

    # Print a random record
    with pd.option_context('display.max_rows', None):
        print("="*30, "Example Record: ", "="*30)
        print(data.sample(1).T)

    # Save .csv file
    data.to_pickle(os.path.join(BASE_PATH, OUTPUT_PKL))

    # assert that when re-loaded it is exactly what was saved
    saved_data = pd.read_pickle(os.path.join(BASE_PATH, OUTPUT_PKL))
    assert saved_data.equals(data)





