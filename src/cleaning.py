import pandas as pd
import json


def create_query(config):
    return 'files.data_category in ["Simple Nucleotide Variation"] ' #+ \
            # 'and files.data_format in ["maf"] and cases.primary_site in ' + \
            # '["bronchus and lung"] and files.access in ["open"]'


def split_lst(lst, partition_size):
    return [lst[i:i + partition_size] for i in
            range(0, len(lst), partition_size)]



def create_metadata_df(driver, to_csv = None):
    ### pandas creation of file metadata
    metadata_df = pd.read_html(driver.page_source)[0]

    if to_csv != None:
        metadata_df.to_csv(to_csv, index = False)
    return metadata_df


def create_url_df(links, metadata_cols, to_csv = None):
    url_df = pd.DataFrame.from_records(split_lst(links, 3),
                columns = [x +"_Url" for x in metadata_cols[1:4]])

    if to_csv != None:
        url_df.to_csv(to_csv, index = False)
    return url_df
