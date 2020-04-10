
import os
import sys
import json

sys.path.insert(0, f"{sys.path[0]}/src")
from selenium_functions import *


if __name__ == "__main__":
    args = sys.argv

    if 'createDict' in args[1]:
        print('Order is Parameter_json Dict_filename ')
        inp = input("Did your parameters fit this order? (y/n) \n")
        if inp.lower() != 'y': assert False, "Redo with correct order"

        params = json_load(args[2])
        if os.path.isfile(args[3]):
            print('Dictionary File already exists')
        else:
            get_keywords(params['chrome_driver_location'], args[3])

    elif 'queryData' in args[1]:
        print('Order is Parameter_json Query_json ')
        inp = input("Did your parameters fit this order? (y/n) \n")
        if inp.lower() != 'y': assert False, "Redo with correct order"

        if os.path.isfile(args[2]) and os.path.isfile(args[3]):
            tcga_scrape(args[2], args[3])
        else:
            if os.path.isfile(args[2]) == False:
                print(f'{args[2]} does not exist')
            if os.path.isfile(args[3]) == False:
                print(f'{args[3]} does not exist')

    else:
        print("Choices are currently only createDict and queryDict")
    # if 'downloadData' in args[1]:
