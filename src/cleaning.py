
import pandas as pd
import json

import sys
import glob
import os
import tarfile
import shutil

import math
import re

################################## Added functions to avoid imports
def json_load(filename):
    """ Allows me to put all non-selenium imports in this file """
    assert check_file(filename), f"{filename} does not exist"
    return json.load(open(filename))

def re_search(pattern, text):
    return re.search(pattern, text)

def glob_glob(pattern):
    return glob.glob(pattern)

def check_driver_location(path):
    assert check_file(path), "Invalid Chrome Driver Location"
    assert path.endswith('exe'), "Chrome Driver needs to be an executable"

def check_file(path, dir = False, make = False):
    if dir:
        present = os.path.isdir(path)
        if make and (not present):
            os.mkdir(path)
            present = True
        return present
    return os.path.isfile(path)


################################## Data Dictionary Creation Functions
def create_data_dict(info_lst, data_file):
    ### not a even multiple of 10 so hardcoded the ending ones
        ## included all possible overlap/missing to ensure all keywords are obtained
        ## done by getting 9 of last 10 as they can be possibly skipped going by 10s
    missing = ["proportion_reads_mapped long",
               "proportion_targets_no_coverage long","read_pair_number keyword",
               "revision long", "stain_type keyword", "tags keyword",
               "total_reads long", "tumor_ploidy long", "tumor_purity long"]

    info_lst += missing

    ### final item is a duplicate in both cases and files so manually placed in
    fixed_lst = list(pd.unique(info_lst)) + ['updated_datetime keyword']

    ##### data broken into 2 distinct classes and checked where that occurs
    break_occurred = False
    split = []

    for i in fixed_lst:
        sp = i.split('\n')
        info = sp[0].split()

        ### when the keyword starts with 'a' means that we are at second class
        if (info[0][0] == 'a') and (break_occurred == False):
            split.append(["BREAK"])
            break_occurred = True

        if len(sp) == 2:
            info += [sp[1]]

        split.append(info)

    middle_ind = split.index(["BREAK"]) ## so we know the location of the switch

    ####### create pandas data_dictionary to avoid scraping continuously
    df = pd.DataFrame.from_records(split[:middle_ind] + split[middle_ind+1:],
                        columns = ['Attribute', 'Data_Type', 'Description'])
    df.loc[:,'Description'] = df.Description.fillna('N/A')

    ####### give labels by their classes
    classes_lst = ['cases'] * (middle_ind) + ['files'] * (len(df)-middle_ind)
    df.insert(0, 'Class', classes_lst)

    #create data_dict file
    df.to_csv(data_file, index = False)


######################### List Partitioning / Number Array Conversion
def split_lst(lst, partition_size):
    return [lst[i:i + partition_size] for i in
            range(0, len(lst), partition_size)]

def array_conv(arr):
    comb = []
    for item in arr:
        lst = []
        for ind in item.split(','):
            try:
                ind = list( map(int, re.split('-|:', ind) ) )
            except ValueError:
                assert False, "Example of csv_ind: ['1-10,15', '1-5']"

            if len(ind) > 1:
                lst += range(ind[0], ind[1]+1)
            else:
                lst += ind
        comb.append(set(lst))
    return comb


################################ Query functions
def query_config(queries):
    """ Param is a dictionary file """
    new_dict = dict()

    for key,val in queries.items():
        lst = []
        split = split_lst(val, 2)
        assert all([len(x)==2 for x in split]), ("Query config for an item "+
            "needs to be in the format parameter, number_of_occurrences. " +
            "\n \t Example: [\"maf\", 1, \"vcf\", 2]. ")

        for item, amt in split:
            lst += [item] * amt

        try:
            new_dict[key] += lst
        except:
            new_dict[key] = lst

    arr = [len(x) for x in new_dict.values()]
    start = arr[0]

    assert all([x == start for x in arr]), ("Length mismatch. Query conversion"+
                                     "failed. Remember to remove unused keys.")
    return new_dict

def query_assemble(queries, data_dict = None):
    """ Param is a dictionary """
    assert isinstance(queries, dict), "Invalid file type. Dictionary object needed"

    if data_dict is not None:
        assert check_file(data_dict), f"\"{data_dict}\" does not exist"
        data_df = pd.read_csv(data_dict, header = 0)

    queries_lst = []

    for index in range(len(list(queries.values())[0])):

        query = ''
        for pair in queries.items():
            class_ = pair[0]

            if "file_size" in class_:
                class_ = "file_size"

            if (not (class_.startswith('files.') or class_.startswith('cases.'))
                    and (data_dict is not None)):
                try:
                    res = data_df.query("Attribute == @class_").iloc[0,0]
                    class_ = res + '.' + class_
                except IndexError as e:
                    assert False, f"Invalid query name. Please change \"{pair[0]}\""

            assert (class_.startswith('files.') or class_.startswith('cases.')), (
               "Invalid query names. Change config file or add data dictionary")

            if "file_size" in class_:
                query += f'{class_} {pair[1][index]} AND '
            else:
                query += f'{class_} in ["{pair[1][index]}"] AND '

        queries_lst.append(query[:-5])

    return queries_lst

def pre_scraping_config_check(params, query_dict):
    """
    Params is dictionary from json_load
    query_dict is dictionary from query_config
    """
    check_dict = dict() ## values say if element is in keys and valid or not
    to_check = ['samples', 'file_names', 'keep_files']
    for item in to_check:
        present = item in params.keys()
        if present:
            assert len(list(query_dict.values())[0]) == len(params[item]), (
                        "Error in parameter config file. Size mismatch. " +
                        f"\"{item}\" do not match to query length")
        check_dict[item] = present

    return check_dict


######################## Pandas dataframe functions
def create_metadata_df(page_source, to_csv = None):
    ### pandas creation of file metadata
    metadata_df = pd.read_html(page_source)[0]
    metadata_df = metadata_df.drop(labels = ['Add all files to cart'], axis = 1)

    if to_csv is not None:
        metadata_df.to_csv(to_csv, index = False)
    return metadata_df

def create_url_df(links, metadata_cols, to_csv = None):
    url_df = pd.DataFrame.from_records(split_lst(links, 3),
                columns = [x +"_Url" for x in metadata_cols[1:4]])

    if to_csv is not None:
        url_df.to_csv(to_csv, index = False)
    return url_df

def download_dataframes(page_source, links, df_name):
    url_name = None

    if df_name is not None:
        url_name = df_name[:-4] + "_url.csv"

    ## create dataframes
    metadata_df = create_metadata_df(page_source, to_csv = df_name)
    url_df = create_url_df(links, metadata_df.columns, to_csv = url_name)
    return metadata_df, url_df

def combine_dataframes(df_name, num_samples, keep_files, together = False):
    def read_concat(df_name):
        file_lst = glob_glob(f"*_{df_name}.csv")
        assert file_lst != [], f"No files with name: {df_name}"
        df_lst = [pd.read_csv(file, header = 0) for file in file_lst]
        df = pd.concat(df_lst).reset_index(drop = True).iloc[:num_samples]

        if keep_files: ### if keep, make combined files to keep as well
            df.to_csv(f'{df_name}.csv', index = False)
        ### delete starting files as they are already in either seperate
            ## meta and url CSVs or in the combined CSV
        [os.system(f"rm -r -f {file}") for file in file_lst]
        return df

    meta, url = read_concat(df_name), read_concat(f"{df_name}_url")
    if together:
        name = f'{df_name}.csv'
        if keep_files:
            name = f'{df_name}_comb.csv'
        pd.concat([meta, url], axis=1).to_csv(name, index = False)
    return meta, url


############################ Url Altering Functions through String Manipulation
def str_change_amount_viewed(current_url, size = 100):
    if '?' not in current_url:
        return f"{current_url}?files_size={size}"

    break_pt = current_url.find('?') + 1
    start, end = current_url[:break_pt], current_url[break_pt:]

    return f'{start}files_size={size}&{end}'

def str_get_new_urls(current_url, num_samples, size = 100):
    # import math
    amt = math.ceil(num_samples/size)

    break_pt = current_url.find('?') + 1
    start, end = current_url[:break_pt], current_url[break_pt:]

    new_urls = []
    for offset in range(amt):
        new_urls.append(f'{start}files_offset={offset*size}&{end}')
    return new_urls


########################### Data Download from CSVs
def pandas_reindex(path, ind):
    df = pd.read_csv(path)
    return df.reindex(index = ind).dropna().loc[:, "File Name_Url"]

def maf_extract_move(maf_dir, target_dir):
    assert os.listdir(maf_dir), f'{maf_dir} is empty'
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)

    for file in os.listdir(maf_dir):
        if file.endswith('.tar.gz'):
            try:
                tar = tarfile.open(maf_dir + '/'+ file, "r:gz")
                tar.extractall(path = maf_dir)
                tar.close()
            except PermissionError:
                print(f'{file} already inside of {maf_dir}')

    subdirs = [created_dir for created_dir in os.listdir(maf_dir)
               if os.path.isdir(os.path.join(maf_dir, created_dir))]

    for sub in subdirs:
        curr_dir = maf_dir + '/' + sub
        for file in os.listdir(curr_dir):
            if file.endswith('.maf.gz'):
                renamed_file = curr_dir + '/' + file[:-7] +'_annotations.txt'
                if os.path.isfile(renamed_file):
                    print(f'{file} already created')
                else:
                    os.rename(curr_dir + '/annotations.txt', renamed_file)

    for sub in subdirs:
        curr_dir = maf_dir + '/' + sub
        for file in os.listdir(curr_dir):
            if os.path.isfile(target_dir + '/' + file):
                print(f'{file} already exists in {target_dir}')
            else:
                shutil.move(curr_dir + '/' + file, target_dir)
