
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from cleaning import *

time_wait = 2
implicit_wait = 3
long_sleep = 10

def button_click(driver, css_tag, sleep = True):
    try:
        box = driver.find_element_by_css_selector(css_tag)
        box.click()
        if sleep:
            time.sleep(time_wait)
        return box
    except:
        return None


def perform_query(driver, query, df_name, size):
    """
    @param df_name: should be name excluding the extension
    """

    ## inputs query into query box
    id_box = driver.find_element_by_id('gql')
    id_box.clear()
    id_box.send_keys(query)
    time.sleep(time_wait)

    ## runs query
    button_click(driver, ".btn.btn-primary.btn-success")

    ### table grabbing
    table = driver.find_element_by_id("repository-files-table")
    text = table.text

    link_elems = table.find_elements_by_tag_name('a')
    links = [elem.get_attribute('href') for elem in link_elems]

    metadata_df = create_metadata_df(driver, to_csv = df_name + ".csv")

    create_url_df(links, metadata_df.columns, to_csv = df_name + "_url.csv")

    ### click on div above the dropdown menu (stops error behavior)
    button_click(driver, 'div[style="display: flex; flex-direction: row; box-sizing: border-box; position: relative; outline: none; align-items: center; padding: 1rem; border-top: 1px solid rgb(222, 222, 222); background-color: white;"]')

    ### clicks onto the dropdown menu
    select = button_click(driver, '.test-page-size-selection.dropdown')

    size_elems = select.find_elements_by_tag_name('div')
    curr = size_elems[0]

    new_url = ''
    for i in size_elems[1:]:
        if i.text == str(size):
            new_url = i.find_element_by_tag_name('a').get_attribute('href')
            break

    if new_url != '':
        driver.execute_script("window.open('');")
        time.sleep(time_wait)

        # Switch to the new window
        driver.switch_to.window(driver.window_handles[1])
        driver.get(new_url)

        time.sleep(time_wait*3)

        # close the active tab
        driver.close()

        ### switch to starting tab
        driver.switch_to.window(driver.window_handles[0])

def tcga_scrape(driver_loc, config, size):
    """

    """
    driver = webdriver.Chrome(executable_path = driver_loc)

    driver.get('https://portal.gdc.cancer.gov/query')
    driver.implicitly_wait(implicit_wait)

    ## accept gov warning when entering page
    button_click(driver, ".undefined.button.css-oe4so")

    string = create_query(config)

    ########### # TODO: BELOW SHOULD NOT BE CONFIG BUT USING FOR NAME CHANGE
    perform_query(driver, string, config, size)

    time.sleep(time_wait)
    driver.close()

if __name__ == "__main__":
    tcga_scrape("C:/Program Files/Drivers/chromedriver.exe", "hello", 100)
