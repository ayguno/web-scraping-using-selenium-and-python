import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pandas as pd
import numpy as np
import os
import re
import json
import shutil

working_dir = 'Path/To/Your/working/directory'
os.chdir(working_dir)

# Ingest the configuration file
with open("./data/config.json","r") as f:
    config = json.load(f)

# Extract global parameters
nasdaq_data_filename = config["nasdaq_data_filename"]
download_folder = config["download_folder"]
output_folder = config["output_folder"]
landing_base = config["landing_base"]
chromedriver_path = config["chromedriver_path"]
xpath_X = config["xpath_X"]
xpath_5Y = config["xpath_5Y"]
xpath_download = config["xpath_download"]
max_waiting_time = config['max_waiting_time'] 

# Read Nasdaq ticker symbols
# Downloaded from: https://www.nasdaq.com/market-activity/stocks/screener
nasdaq_data = pd.read_csv('./data/'+nasdaq_data_filename)
nasdaq_symbols = nasdaq_data["Symbol"].tolist()

# Utility function to launch chrome web driver
def launchChromeDriver(chromedriver = chromedriver_path):
    global driver
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--ignore-ssl-errors')
    
    driver = webdriver.Chrome(chrome_options=options,   
    executable_path = chromedriver)

# Utility function to perform clicks
def clickAction(landing_page,
    waiting_time = 30,
    xpathX = xpath_X, 
    xpath5Y = xpath_5Y, 
    xpathdownload = xpath_download):
    global driver
    driver.get(landing_page)
    driver.maximize_window() 
    driver.implicitly_wait(waiting_time) # Website has banner ads that takes time fully loading
    # Find the X to close the pop up window
    element = driver.find_element_by_xpath(xpathX)  
    element.click() # Click to "X" button
    # Find the "5Y" button to download the last 5Ys of data
    element = driver.find_element_by_xpath(xpath5Y)  
    element.click() # Click to "5Y" button
    # Find the Download button
    element = driver.find_element_by_xpath(xpathdownload)
    # Click to download entire stock time series data
    element.click()  # Click to "Download" button
    
# Iterate over Nasdaq symbols to download time-series stock data
nasdaq_tickers = nasdaq_data["Symbol"].str.lower().tolist()

# Main download loop
if __name__ == "__main__":
    for ticker in nasdaq_tickers:
        launchChromeDriver()
        continue_next = True
        print("*" * 75)
        print('Processing NASDAQ ticker: '+ ticker.upper())
        try:
            # First check if downloads folder have historical files remaining from earlier attempts
            dir_list = os.listdir(download_folder)
            search_list = [re.findall("^HistoricalData.*\\.csv$",x) for x in dir_list]
            search_list = [x[0] for x in search_list if x != []]
            # If any leftover found, delete them
            if len(search_list) > 0:
                for item in search_list:
                    os.unlink(download_folder + item)
                    print("Cleaned existing file...")
            # Attept to download new file        
            search_list = []
            waitingtime = 30
            while len(search_list) < 1:
                try:
                    clickAction(landing_page = landing_base + ticker +"/historical",
                                waiting_time = waitingtime)
                    dir_list = os.listdir(download_folder)
                    search_list = [re.findall("^HistoricalData.*\\.csv$",x) for x in dir_list]
                    search_list = [x[0] for x in search_list if x != []]
                    print(search_list)            
                except:
                    dir_list = os.listdir(download_folder)
                    search_list = [re.findall("^HistoricalData.*\\.csv$",x) for x in dir_list]
                    search_list = [x[0] for x in search_list if x != []]
                    if len(search_list) > 0:
                        break
                    else:
                        print("Unsucessful clickAction")
                        driver.quit()
                        launchChromeDriver()
                        waitingtime += 30
                        print("Still trying to find the target to click...increasing waiting time to: " + str(waitingtime))
                        if waitingtime <= max_waiting_time:
                            pass
                        else:
                            continue_next = False
                            break        
        except:
            print("Executed 4")
            pass
        
        if continue_next:    
            # Find and rename the downloaded file   
            print("Trying to download the file...") 
            while len(search_list) < 1:
                dir_list = os.listdir(download_folder)
                search_list = [re.findall("^HistoricalData.*\\.csv$",x) for x in dir_list]
                search_list = [x[0] for x in search_list if x != []]
                print("Still waiting file to download...")
            # Copy the file into storage location with appropriate ticker symbol
            src = download_folder + search_list[0]
            target = "./data/historical_data/" + ticker.upper() + ".csv"
            shutil.copyfile(src,target)    
            os.unlink(src) # Delete the file from downloads
            print('Processed NASDAQ ticker: '+ ticker.upper())
            driver.quit()
        else:
            print('Skipping NASDAQ ticker: '+ ticker.upper())

           
 