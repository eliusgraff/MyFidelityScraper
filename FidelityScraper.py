#FidelityScraper.py 
from sys import executable
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as exceptions
from selenium.webdriver.support.ui import Select
import time
import pathlib
import glob
import csv
import os
import pandas as pd
from datetime import datetime
import yfinance as yf
#import numpy as numpee


class FidelityScraper:

    #will be assigned based on user's fidelity account info
    __username = None
    __password = None
    validCreds = False
    #used for getting data
    __webSession = None
    #pathname where csv data will be sent
    __pathName = str(pathlib.Path().absolute()) + '\\bin\\'

    #constructor takes in userame, and pw for the fidelity account
    def __init__(self, *args):

        if len(args) == 2:  #shoretened this for testing purposes, and assumption that user knows their un and pw
            self.__username = args[0]
            self.__password = args[1]
            print("UN and PW added")
        else:
            print("No Credentials added, please add them")
            return None
        return None

    #if user needs to manually set creds, do it here!
    def setCreds(self, username, password):
        if self.__validateCreds(username, password) == True :
            self.__username = username
            self.__username = password
            print("account un and pw validated and saved")
            return True

        print("could not validate credentails, try again")
        self.ValidCreds = False
        return False
        
    #Function to check if username and password can log in to a Fidelity account. Return True if we can get into account, false if not.
    def __validateCreds(self,username,password):
        self.__username = username
        self.__password = password
        if self.__login() == True:
            print("validation successful!")
            self.ValidCreds = True
            return True

        self.__userame = None
        self.__password = None
        print("couldnt validate credentials")
        return False

    #This function will double for both signing into Fidelity web session and validating credentials
    #Returns True if and only if web browser is able to long into Fidelity with credentials sent to it
    #This function will leave the __webSession variable at the account summary page of desired Fidelity account
    def __login(self):

        #stops us from making multiple web sessions unnecessarily
        if self.__webSession != None:
            return True

        #setting web driver so that automation is smooth and downloads go to right place
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("detach", True)
        options.add_experimental_option("prefs", { "download.default_directory" : self.__pathName } )
        self.__webSession = webdriver.Chrome(chrome_options=options)   #only works if chromedriver is inatalled on your PATH, need another argument if not

        #getting into account
        self.__webSession.get("https://digital.fidelity.com/prgw/digital/login/full-page?AuthRedUrl=https://oltx.fidelity.com/ftgw/fbc/ofsummary/defaultPage")
        time.sleep(1.5)
        self.__webSession.find_element_by_xpath('//*[@id="userId-input"]').send_keys(self.__username)
        self.__webSession.find_element_by_xpath('//*[@id="password"]').send_keys(self.__password)
        self.__webSession.find_element_by_xpath('//*[@id="fs-login-button"]').click()
        time.sleep(3)
        ##########just validates that we did indeed get into page, probably a better way to do this exists##########
        #self.__webSession.find_element_by_xpath('//*[@id="tab-2"]').click() 
        time.sleep(0.5)

        print("Login sucessful")
        return True

    #function will download just the existing postions of the account with credentials in the class,
    #returns True if and only if account positions are downloaded from web session, else its false
    def __scrape_account_positions(self):

        if self.__login() == False:
            print("Account positions scrape failed")
            return False

        try:
            time.sleep(1)
            self.__webSession.find_element_by_xpath('//*[@id="moretab-area"]/div[2]/ul/li[2]').click()
            time.sleep(2)
            self.__webSession.find_element_by_xpath('//*[@id="tabContentPositions"]/div[2]/div/div[1]/div[4]/div[3]/div[2]/a').click()
            time.sleep(3)
        except Exception as exe:
            self.__webSession.quit()
            print("downloading positions failed")
            print(type(exe)) 
            print(exe.args) 
            print(exe)
            return False
        
        print("account positions downloaded")
        return True

    #This like likely be the most called function. This should be called pretty much daily to retrieve
    #any trades happening on the account. This is also how dividends will be accounted for.
    def scrape_activity(self):

        #clearing bin and acnts directories that we need to store/download data in
        for f in os.listdir('./bin//'): os.remove(os.path.join( './bin//' , f ))
        for f in os.listdir('./acnts//'): os.remove(os.path.join('./acnts//' , f ))

        self.__login()
        self.__webSession.execute_script("window.scrollTo(0, 512)")
        self.__webSession.find_element_by_xpath('//*[@id="tab-4"]').click()
        time.sleep(3)
        pastQuarters = Select(self.__webSession.find_element_by_xpath('//*[@id="activity--history-range-dropdown"]'))
        print(pastQuarters)
        
        for i in range(3, len(pastQuarters.options)-1) : 

            if len(pastQuarters.options[i].text) > 0 :

                pastQuarters.options[i].click()
                time.sleep(2)
                self.__webSession.find_element_by_xpath('//*[@id="AccountActivityTabHistory"]/div/div/div/div[3]/a').click()
                time.sleep(0.5) 

        self.__scrape_account_positions()

        print("all activity downloaded")
        self.close_web_session()
        return True

    #this will compile all scraped data into one file so all data is consolidated this will remove any
    #existing files from relevant directories so that each 
    def compile_data(self):

        #Cleans and moves active positions data to another directory
        activePos = glob.glob(self.__pathName + 'Portfolio*')
        assert( len( activePos ) > 0)  # make sure there is and active posistions file
        myPos = pd.read_csv( activePos[ 0 ] , header = 0 )
        myPos.dropna( subset = [ 'Symbol' ] , inplace = True )
        filtCash = myPos['Symbol'].str.find('**') == -1 #Fidelity denotes cash positions with '**' this gets rid of cash positions
        myPos = myPos[filtCash]
        myPos.to_csv('./acnts/ActivePositions.csv')
        os.remove(activePos[0])

        #Goes through each file of trades and aggregates all trades to one file in another directory
        currentQuarter = self.__pathName + "Accounts_History.csv"   #need at least one file here
        assert(os.path.isfile(currentQuarter)) #make sure data is there
        masterList = pd.read_csv(currentQuarter, skiprows=3, header=0)
        masterList.dropna(subset=['Action'], inplace=True)
        masterList['Run Date'] = pd.to_datetime(masterList['Run Date'])
        lastDate = masterList['Run Date'].min()

        os.remove(currentQuarter)

        activityFiles = glob.glob(self.__pathName + "*.csv")

        for pastQuarter in activityFiles:

            if (os.stat(pastQuarter).st_size > 2000) : #opening only files that have data in them   
                
                tempDF = pd.read_csv(pastQuarter, skiprows=3, header=0)
                tempDF.dropna(subset=['Action'], inplace=True)
                tempDF['Run Date'] = pd.to_datetime(tempDF['Run Date'])
                dateFilt = (tempDF['Run Date'] < lastDate)
                tempDF = tempDF[dateFilt]
                masterList = pd.concat([masterList,tempDF])

            os.remove(pastQuarter)

        masterList.to_csv('acnts\\AllTrades.csv')

        return True

    #Functions only close web session if something fails. This can be called by user in case everything
    #works right and they need to close the session gracefully. Not sure if this will ever be needed but
    #better to be safe than sorry!
    def close_web_session(self):

        if self.__webSession != None:
            self.__webSession.quit()
            self.__webSession = None
            print("web sesssion ended successfully!")
            return
        
        print("web session already closed")
        return


    #This function takes in a ticker symbol and will add stock history CSV to the acnts\StockData
    #directory if it does not already exist
    def getStockData(self):

        activePos = pd.read_csv('./acnts//ActivePositions.csv')

        for ticker in activePos['Symbol']:

            fn = './bin//' + ticker + '.csv'

            if os.path.isfile( fn ):

                with open( fn , 'r' ) as f: 
                    dateStr = str( f.readlines()[ -1 ][ 0 : 10 ])   #get last date info was added so we only import whats needed

                if datetime.strptime( dateStr , '%Y-%m-%d').date() == datetime.today().date() : continue #makes sure that we are only getting data if there is missng data
                
                tickerData = yf.Ticker(ticker).history(start=dateStr)
                tickerData = tickerData.iloc[ 1: ]    #prevents data from being doubled in csv file
                tickerData.to_csv( fn , mode = 'a' , header = False)

            else:
                tickerData = yf.Ticker(ticker).history(period = "max")
                tickerData.to_csv('./bin//' + ticker + '.csv')

            time.sleep(0.5)

        return