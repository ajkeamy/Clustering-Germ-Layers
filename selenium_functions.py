
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import re
from cleaning import *

time_wait = 2
implicit_wait = 3
long_sleep = 10

########### generic functions

def button_click(driver, css_tag, sleep = True):
    try:
        box = driver.find_element_by_css_selector(css_tag)
        box.click()
        if sleep:
            time.sleep(time_wait)
        return box
    except:
        return None

def accept_gov_warning(driver, start = False):
    if start:
        driver.get('https://portal.gdc.cancer.gov/query')
        driver.implicitly_wait(implicit_wait)

    ## accept gov warning when entering page
    button_click(driver, ".undefined.button.css-oe4so")


################# query functions
def enter_query(driver, query, enter = True):
    ## inputs query into query box
    query_box = driver.find_element_by_id('gql')
    query_box.clear()
    query_box.send_keys(query)
    time.sleep(time_wait)

    if enter: ## runs query if true
        valid_check = driver.find_elements_by_css_selector("div[class=\"text"
                                                    + "-success ng-scope\"]")
        ## if query fails, prints error message
        if valid_check == []:
            error_box = driver.find_element_by_css_selector("div[class=\"text"
                                                    + "-danger ng-scope\"]")
            elem = error_box.find_element_by_tag_name('a')
            elem.click()

            error_msg = error_box.find_elements_by_tag_name('span')[1].text
            elem.click() ## reset error message state

            assert False, ("Query is invalid. Please try again. \n" +
                                   f"Query is currently \"{query}\" \n" +
                                   f"Error message: \"{error_msg}\"")

        button_click(driver, ".btn.btn-primary.btn-success")
    return query_box

def results_check(driver, query):
    div_attr = "position: relative; width: 100%; min-height: 387px;"
    div_box = driver.find_element_by_css_selector(f"div[style=\"{div_attr}\"]")

    if div_box.text == 'No results found':
        print(f"Current query \"{query}\" has no results.")
        return False
    return True

############# data dictionary creator
def get_keywords(driver_loc, data_file):
    assert driver_loc.endswith('.exe'), "Invalid executable. Need correct exe path"
    assert data_file.endswith('.csv'), "Unusable name. Format should be \"name.csv\""

    driver = webdriver.Chrome(executable_path = driver_loc)
    accept_gov_warning(driver, True)

    #### vague query entry that results in all autocompletions occurring
    query = 'and '
    id_box = enter_query(driver, query, False)

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
    create_data_dict(info_lst, data_file)


############# data layout changes (url manipulation using selenium)
def change_amount_viewed(driver, size = 100):
    ### click on div above the dropdown menu (stops error behavior)
    button_click(driver, 'div[style="display: flex; flex-direction: row;' +
        ' box-sizing: border-box; position: relative; outline: none; ' +
        'align-items: center; padding: 1rem; border-top: 1px solid ' +
        'rgb(222, 222, 222); background-color: white;"]')

    ### clicks onto the dropdown menu
    select = button_click(driver, '.test-page-size-selection.dropdown')

    size_elems = select.find_elements_by_tag_name('div')
    curr = size_elems[0]

    new_url = ''
    for i in size_elems[1:]:
        if i.text == str(size):
            new_url = i.find_element_by_tag_name('a').get_attribute('href')
            break
    return new_url

def get_new_urls(driver):
    elem = driver.find_element_by_css_selector(f"div[style=\"display: flex; "+
            "flex-direction: row; box-sizing: border-box; position: relative; "+
            "outline: none; margin-left: auto;\"]")

    ## to make selection work for any page
    new_page_links = elem.find_elements_by_tag_name('a')

    #### since first 2 are inactivate on on page 1 so check if
        ## offset (indicates not on page 1)
    if 'files_offset' not in driver.current_url:
        start = 0
    elif 'files_offset=0&' in driver.current_url:
        start = 0
    else:
        start = 2

    offset_url_lst = []
    ## only want the middle 10 so start gives end too
    for link in new_page_links[start:start + 10]:
        offset_url_lst.append(link.get_attribute('href'))

    return offset_url_lst


############# data sorting done once before the queries are run
def sort_data(driver, param_config):
    """ param_config is a dictionary from param_config.json """

    ### don't need to sort by anything if given nothing to sort by
    if 'sort_using' not in param_config.keys():
        print("Warning: Sort not specified. If intended, ignore warning.")
        return

    ## css location value for sort button div location
    loc = "display: flex; flex-direction: column; box-sizing: border-box; " + \
        "position: absolute; outline: none; box-shadow: rgba(0, 0, 0, 0.16) " + \
        "0px 2px 5px 0px, rgba(0, 0, 0, 0.12) 0px 2px 10px 0px; z-index: 200; " + \
        "min-width: 165px; background-color: white; text-align: left; right: " + \
        "0px; border-radius: 5px; top: 100%; margin-top: 5px; white-space: nowrap;"

    sort_table = driver.find_elements_by_css_selector(f"div[style = \"{loc}\"]")

    if sort_table == []:
        button_click(driver, "button[class=\"undefined button css-14x0dj7\"]")
        sort_table = driver.find_element_by_css_selector(f"div[style = \"{loc}\"]")
    else:
        sort_table = sort_table[0]

    elems = sort_table.find_elements_by_tag_name('div')
    #### Each section to sort by holds 5 other Drivers
    split_elems = split_lst(elems, 6)

    sort_names = ["Access", "File Name", "Project", "Data Category",
                  "Data Format", "Size"] ## names of all possible sort_by

    ### if nothing specified for direction, go default
    use_default_sort = 'sort_direction' not in param_config.keys()
    for index, using in enumerate(param_config['sort_using']):
        items = split_elems[sort_names.index(using)]

        if use_default_sort:
            ## default actually 2, but 5 is same result and prevents bugs
            items[5].click()
        else: ## if direction of sort was specified, then go that way
            if "up" in param_config['sort_direction'][index].lower():
                items[5].click()
            elif "down" in param_config['sort_direction'][index].lower():
                items[4].click()
            else:
                assert False, "Sort Directions should be either UP or DOWN"


############# ran by each query and assembles dataframe
def perform_query(driver, query, df_name, num_samples = 150, keep_files = True):
    """
    @param df_name: should be name excluding the extension
    """
    assert df_name.endswith('.csv'), "Unusable name. Format should be \"name.csv\""

    ## inputs query into query box and runs it
    enter_query(driver, query)

    ## if query has no results, then leave early
    if results_check(driver, query) == False:  return

    ## alternative way using selenium
    # new_url = change_amount_viewed(driver)
    # new_url_lst = get_new_urls(driver)

    new_url = str_change_amount_viewed(driver.current_url)
    new_url_lst = str_get_new_urls(new_url, num_samples)

    for index, url in enumerate(new_url_lst):
        driver.execute_script("window.open('');")

        # Switch to the new window
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)
        driver.implicitly_wait(implicit_wait)

        ### table grabbing
        table = driver.find_element_by_id("repository-files-table")
        # text = table.text

        link_elems = table.find_elements_by_tag_name('a')
        links = [elem.get_attribute('href') for elem in link_elems]

        ## create dataframes
        download_dataframes(driver.page_source, links, str(index)+'_'+df_name)

        # close the active tab
        driver.close()

        ### switch to starting tab
        driver.switch_to.window(driver.window_handles[0])

    combine_dataframes(df_name[:-4], num_samples, keep_files)

#################################################################################################################


def tcga_scrape(driver_loc, config, size):
    """

    """
    print('WARNING: CURRENTLY ONLY WORKS ON COMPUTERS WITH CHROME')
    driver = webdriver.Chrome(executable_path = driver_loc)
    accept_gov_warning(driver, True)

    import json
    sort_data(driver,json.load(open('param_config.json')))

    string = create_query(config)
    print(query_assemble(config))
    ########### # TODO: BELOW SHOULD NOT BE CONFIG BUT USING FOR NAME CHANGE
    perform_query(driver, string, config, size)

    time.sleep(time_wait)
    driver.close()

if __name__ == "__main__":
    import os
    import sys
    import json

    params = json.load(open('param_config.json'))
    args = sys.argv

    if args[1] == 'createDict':
        if os.path.isfile(args[2]):
            print('Dictionary File already exists')
        else:
            get_keywords(params['chrome_driver_location'], args[2])
            # get_keywords("C:/Program Files/Drivers/chromedriver.exe", 'data_test.csv')

    # tcga_scrape("C:/Program Files/Drivers/chromedriver.exe", "hello")
