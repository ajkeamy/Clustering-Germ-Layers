# Import Statements 
import pandas as pd
import numpy as np
import gzip
import shutil
import time 
import matplotlib.pyplot as plt
import os 
import shlex
import sys
import subprocess as sp
import json
import os
sys.path.insert(0,sys.path[0] +'/src')
from etl import *

def main(): 
    # Import Json file
    dictionary = json.load(open("config/test-params.json"))

    arguments= sys.argv
    print(arguments)
    #if arguments[1] == 'test-project':
    
if __name__ == '__main__':
    main()
