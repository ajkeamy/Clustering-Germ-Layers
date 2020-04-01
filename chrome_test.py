
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

def button_click(driver, css_tag, sleep = True):

    try:
        box = driver.find_element_by_css_selector(css_tag)
        box.click()
        if sleep:
            time.sleep(3)
        return box
    except:
        return None

driver = webdriver.Chrome(executable_path="C:/Program Files/Drivers/chromedriver.exe")

driver.find_element_by_css_selector
driver.get('https://portal.gdc.cancer.gov/query')
driver.implicitly_wait(3)

## accept gov warning when entering page
button_click(driver, ".undefined.button.css-oe4so")

## runs query
button_click(driver, ".btn.btn-primary.btn-success")
time.sleep(3)

## inputs query into query box
id_box = driver.find_element_by_id('gql')
string = 'files.data_category in ["Simple Nucleotide Variation"] ' + \
             'and files.data_format in ["maf"] and cases.primary_site in ' + \
             '["bronchus and lung"] and files.access in ["open"]'
id_box.send_keys(string)
time.sleep(3)

## runs query
button_click(driver, ".btn.btn-primary.btn-success")
time.sleep(3)

### table grabbing
table = driver.find_element_by_id("repository-files-table")
text = table.text

link_elems = table.find_elements_by_tag_name('a')
links = [elem.get_attribute('href') for elem in link_elems]

### string editting
lst = []
for i in text.split('\n'):
    string = i
    string = string.replace('File ', "File_")
    string = string.replace(" KB", "KB")
    string = string.replace(" MB", "MB")
    string = string.replace(" GB", "GB")
    lst.append(string.split())

### pandas creation of file metadata
metadata_df = pd.DataFrame.from_records(lst[1:], columns=lst[0])
# df.to_csv('locations.csv', index = False)

def split_lst(lst, partition_size):
    return [lst[i:i + partition_size] for i in
            range(0, len(lst), partition_size)]

links_df = pd.DataFrame.from_records(split_lst(links, 3),
            columns = [x +"_Url" for x in metadata_df.columns[1:4]])


time.sleep(5)
driver.close()
