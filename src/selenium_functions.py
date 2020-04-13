
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import time
from cleaning import *

time_wait = 3
implicit_wait = 3
after_sort_wait = 6

############################### functions used in multiple command line actions
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

def time_change(params):
    for key,item in params.items():
        if key == 'time_wait':
            global time_wait;           time_wait = item
        elif key == 'implicit_wait':
            global implicit_wait;       implicit_wait = item
        elif key == 'after_sort_wait':
            global after_sort_wait;     after_sort_wait = item


############################### chrome initializations before running
def convert_to_headless(chrome_options):
    ## browser is "headless" meaning it doesn't appear when running
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument('log-level=3') ## suppresses info msgs
    return chrome_options

def chrome_warning():
    print('WARNING: CURRENTLY ONLY WORKS ON COMPUTERS WITH CHROME')
    print("If inappropriate driver for chrome version, go to https://" + \
          "chromedriver.chromium.org/downloads to download the right one.")

def chrome_setup(params, download = False):
    chrome_warning()

    headless_check = ('headless' in params.keys()) and (params['headless'])
    if headless_check or download:
        chrome_options = Options()
        if headless_check and download:
            chrome_options = convert_to_headless(chrome_options)
            tar_path = params['tar_dir'].replace('/', '\\')
            check_file(tar_path, True, True)
            prefs = {"download.default_directory" : tar_path}
            chrome_options.add_experimental_option('prefs', prefs)
        elif download:
            tar_path = params['tar_dir'].replace('/', '\\')
            check_file(tar_path, True, True)
            prefs = {"download.default_directory" : tar_path}
            chrome_options.add_experimental_option('prefs', prefs)
        else:
            chrome_options = convert_to_headless(chrome_options)
    else:
        chrome_options = None

    driver = webdriver.Chrome(options = chrome_options,
                              executable_path = params['chrome_driver_location'])
    accept_gov_warning(driver, True)
    return driver


################################## query functions
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

def results_check(driver, query, first_page = True):
    div_attr = "position: relative; width: 100%; min-height: 387px;"
    div_box = driver.find_element_by_css_selector(f"div[style=\"{div_attr}\"]")

    ### oddly, in pages after the first, can't scrape to know if no results
    if (div_box.text is None ) or (div_box.text == 'No results found'):
        if first_page:
            print(f"Current query \"{query}\" has no results.")
        else:
            print(f"\nCurrent query \"{query}\" does not have enough results to "+
                  "satisfy num_samples. \nInstead, table will only go up to " +
                  "maximum possible results.\n")
        return False
    return True


############################# data dictionary creator
def get_keywords(param_file, data_file = None):
    assert param_file.endswith('.json'), ("Invalid file chosen. Param config " +
                                             "needs to be a json file.")

    params = json_load(param_file)
    check_driver_location(params['chrome_driver_location'])
    time_change(params)

    if check_file(params['data_dict']) and data_file is None:
        print(f"Data Dictionary file \"{params['data_dict']}\" already exists.")
        return
    if (data_file is not None):
        assert data_file.endswith('.csv'), ("Unusable name. Format should be " +
                                            "\"name.csv\"")
        if check_file(data_file):
            print(f"Data Dictionary file \"{data_file}\" already exists.")
            return

    driver = chrome_setup(params)

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
            if bool(re_search("^case_id\s", i.text)):
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
    if data_file is None:
        create_data_dict(info_lst, params['data_dict'])
    else:
        create_data_dict(info_lst, data_file)
    print("FINISHED")


####################### data layout changes (url manipulation using selenium)
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


######################## data sorting done once before the queries are run
def sort_data(driver, param_config):
    """ param_config is a dictionary from param_config.json """

    ### don't need to sort by anything if given nothing to sort by
    if 'sort_using' not in param_config.keys():
        print("\n\nWarning: Sort not specified. If intended, ignore warning.\n\n")
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
        sort_table = driver.find_elements_by_css_selector(f"div[style = \"{loc}\"]")
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


########################### ran by each query and assembles dataframe
def perform_query(driver, query, params, df_name, num_samples = 150, keep_files = False):
    """
    @param df_name: should be name excluding the extension
    """
    if df_name.endswith('.csv') == False:
        df_name = df_name + '.csv'

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

        #### if current page has no results, then stop downloads
        if results_check(driver, query, False) == False:  break

        sort_data(driver, params)
        time.sleep(after_sort_wait) ## needs longer time to sort so doesn't break

        ### table grabbing
        table = driver.find_element_by_id("repository-files-table")

        link_elems = table.find_elements_by_tag_name('a')
        links = [elem.get_attribute('href') for elem in link_elems]

        ## create dataframes
        download_dataframes(driver.page_source, links, str(index)+'_'+df_name)

        # close the active tab
        driver.close()

        ### switch to starting tab
        driver.switch_to.window(driver.window_handles[0])

    if 'together' in params.keys():
        combine_dataframes(df_name[:-4], num_samples, keep_files,
                           params['together'])
    else:
        combine_dataframes(df_name[:-4], num_samples, keep_files)


############ Combines all functions to scrape URLs using configuration files
def tcga_scrape(param_file, query_file):
    """

    """
    assert param_file.endswith('.json'), ("Invalid file chosen. Param config " +
                                             "needs to be a json file.")
    assert query_file.endswith('.json'), ("Invalid file chosen. Query config " +
                                             "needs to be a json file.")

    params = json_load(param_file)
    queries = json_load(query_file)
    check_driver_location(params['chrome_driver_location'])

    query_dict = query_config(queries)

    data_dict = None
    if 'data_dict' in params.keys():
        data_dict = params['data_dict']
    assembled_query = query_assemble(query_dict, data_dict)

    present_dict = pre_scraping_config_check(params, query_dict)
    time_change(params)

    ########## Reached here means config files are valid

    driver = chrome_setup(params)

    for index, query in enumerate(assembled_query):
        name = str(f'Query_{index}.csv')
        if present_dict["file_names"]:
            name = params["file_names"][index]

        ### which combination of defaults to use based on parameters
        if present_dict["samples"] and present_dict['keep_files']:
            perform_query(driver, query, params, name, params['samples'][index],
                          params['keep_files'][index])
        elif present_dict["samples"]:
            perform_query(driver, query, params, name, params['samples'][index])
        elif present_dict['keep_files']:
            perform_query(driver, query, params, name, params['keep_files'][index])
        else:
            perform_query(driver, query, params, name)

    driver.close()
    print("FINISHED")


#################################### Download Data
def download_data(param_file, csv_patterns = None):
    csv_lst = []

    params = json_load(param_file)
    if 'manual_csv_files' in params.keys():
        csv_lst = set(params['manual_csv_files'])
        csv_lst = [file for file in csv_lst if check_file(file)]

    if csv_patterns:
        for pattern in csv_patterns:
            csv_lst += glob_glob(pattern)

        csv_lst = [file for file in csv_lst if file.endswith('.csv')]
        csv_lst = list(set(csv_lst))

    assert csv_lst != [], 'No matching CSV files found by pattern or by json.'

    time_change(params)
    check_driver_location(params['chrome_driver_location'])
    driver = chrome_setup(params, download = True)
    downloader(driver, params, csv_lst)

def downloader(driver, params, csv_lst):
    tar_dir, maf_dir = params['tar_dir'], params['maf_dir']
    keep_tar_files = params['keep_tar']

    assert check_file(tar_dir, True), f'{tar_dir} does not exist'
    assert len(params['download_inds']) == len(csv_lst), (
                "Download indicies do not match to csv_files")

    for index, ind in enumerate(array_conv(params['download_inds'])):
        assert csv_lst[index].endswith('csv'), "Invalid File "
        links = pandas_reindex(csv_lst[index],ind)

        for link in links:
            driver.get(link)
            driver.implicitly_wait(implicit_wait)

            accept_gov_warning(driver)
            button_click(driver, ".test-download-button.button")

    driver.close()
    maf_extract_move(tar_dir, maf_dir)

    if keep_tar_files:
        [os.system(f'rm -r -f {tar_dir}/{file}') for file in os.listdir(tar_dir)
         if not file.endswith('.tar.gz')]
    else:
        [os.system(f'rm -r -f {tar_dir}/{file}') for file in os.listdir(tar_dir)]



if __name__ == "__main__":
    get_keywords('config/param_config.json')
    tcga_scrape('config/param_config.json', 'config/query_config.json')
    download_data('config/param_config.json', ['Query_0.csv', '*.csv'])
