from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import pandas as pd
from selenium_functions import button_click

def get_keywords(driver_loc, data_file):
    driver = webdriver.Chrome(executable_path = driver_loc)

    driver.get('https://portal.gdc.cancer.gov/query')
    driver.implicitly_wait(3)

    ## accept gov warning when entering page
    button_click(driver, ".undefined.button.css-oe4so")

    ### vague query entry that results in all possible autocompletion to scrape
    query = 'and '

    ## inputs query into query box
    id_box = driver.find_element_by_id('gql')
    id_box.clear()
    id_box.send_keys(query)

    #### gets the autocompletion results (only can do 10 at a time)
    dropdown = driver.find_element_by_css_selector('.list-unstyled.Gql_dropdown.Gql_dropdown-0')

    info_lst = []

    start = True
    continuation = True ## tells loop to stop
    second_time = False ## so continuation doesnt stop on first loop

    while continuation:
        ### get all top elements it gives us
        items = dropdown.find_elements_by_tag_name('li')

        ### items is 12 elements but first and last are blanks
        for i in items[1:-1]:
            ## case_id only appears at start so end when seen a second time
            if bool(re.search("^case_id\s", i.text)):
                if second_time:
                    continuation = False
                second_time = True
            info_lst.append(i.text)

        times = 10 # normal amount as 10 downs gives max number of new results (10)

        if start:
            times = 19 #down 19 times to get from element 1 to 20 so all 10 are new
            start = False

        for _ in range(times):
            id_box.send_keys(Keys.DOWN)

    driver.close()

    ### not a even multiple of 10 so hardcoded the ending ones
    fixed_lst = list(pd.unique(info_lst)) + ['tumor_ploidy long',
                                             'tumor_purity long',
                                             'updated_datetime keyword']

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

    df.to_csv(data_file, index = False) #create data_dict file


if __name__ == '__main__':
    get_keywords("C:/Program Files/Drivers/chromedriver.exe", 'data_dictionary.csv')
