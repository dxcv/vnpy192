# encoding: UTF-8

from __future__ import print_function
import json
from datetime import datetime, timedelta, time
import requests
from pymongo import MongoClient

#from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME, TICK_DB_NAME
#from vnpy.trader.app.vtUtility import get_VolSize
#from vnpy.trader.vtFunction import getJsonPath
#import time,datetime
import os,sys

def get_CustSetting():
    settingFileName = 'custom_setting.json'
    #settingfilePath = getJsonPath(settingFileName, __file__)
    #settingfilePath = os.path.join(sys.argv[0],settingFileName )    
    custCfg = [] 
    dataContent = ""
    with open(settingFileName, 'r') as fileObj:
        #print(f.read())
        dataContent = fileObj.read()
    custCfg = json.loads(dataContent)   
    return custCfg   

def get_VolSize():
    vol_Size = {}    
    dataContent = ""
    settingFileName = 'Symbol_volsize.json'
    #settingfilePath = getJsonPath(settingFileName, __file__)      
    with open(settingFileName, 'r') as fileObj:
        #print(f.read())
        dataContent = fileObj.read()
    vol_Size = json.loads(dataContent)   
    return vol_Size          
 

# ��������Ʒ�ڻ�Ϊ��
FUTURES_URL = "http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol="
INDEX_URL = "http://stock2.finance.sina.com.cn/futures/api/json.php/CffexFuturesService.getCffexFuturesMiniKLine5m?symbol="
FUTURES_DAYURL = "http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine?symbol="
INDEX_DAYURL = "http://stock2.finance.sina.com.cn/futures/api/json.php/CffexFuturesService.getCffexFuturesDailyKLine?symbol="
TICK_DB_NAME = 'VnTrader_Tick_Db'
DAILY_DB_NAME = 'VnTrader_Daily_Db'
MINUTE_DB_NAME = 'VnTrader_1Min_Db'

def getSymbolMapping(): 
    symbolMap = {}
    dataContent = ""
    settingFileName = 'DR_mapping.json'
    #settingfilePath = getJsonPath(settingFileName, __file__)      
    with open(settingFileName, 'r') as fileObj:
        #print(f.read())
        dataContent = fileObj.read()
        #print(dataContent)
    symbolMap = json.loads(dataContent)   
    return symbolMap     

def getXminBarData(dataUrl):  
    url_str = dataUrl
    r = requests.get(url_str)
    r.encoding = "gbk" 
    r_json = r.json()
    r_lists = list(r_json)
    return r_lists
    #print('future_code,date,open,high,low,close,vol')

def getDailyBarData(dataUrl):  
    url_str = dataUrl
    r = requests.get(url_str)
    r.encoding = "gbk" 
    r_json = r.json()
    r_lists = list(r_json)
    return r_lists
    #print('future_code,date,open,high,low,close,vol')

def fillMissingDailyData(dbName, collectionName, start,end,cfgdata,cfgMap):
    """
    �����������û�У�������ץȡ�����俪��9�㣩�ߣ�����4��K�ߡ�
    """
    print(u'\n�����������ݣ�%s, ���ϣ�%s, ��ʼ�գ�%s' %(dbName, collectionName, start))
    
    var_Symbol = ""
    var_Symbol = var_Symbol.join(list(filter(lambda x: x.isalpha(),collectionName)))            

    startDate = start.replace(hour=9, minute=0, second=0, microsecond=0)
    endDate = end.replace(hour=15, minute=30, second=0, microsecond=0)
    conMonth = collectionName[-3:]
    if conMonth == '901':
        return
    contractCode = cfgMap[collectionName][0]
    urlType = cfgMap[collectionName][1]
    #minKLineNo = 0
    dataUrl = ""
    if urlType == "url2":
        dataUrl = INDEX_DAYURL + contractCode
        #minKLineNo = 240
    else:
        dataUrl = FUTURES_DAYURL + contractCode
        
    dailyBar = getDailyBarData(dataUrl)
    if dailyBar == None:
        print("Cannot read data from Sina, check it!")
        return
    dailyBar.sort()
    startString = datetime.strftime(startDate,'%Y-%m-%d %H:%M:%S')
    print(startString) 
    print(startString[:10]) 
    endString = datetime.strftime(endDate,'%Y-%m-%d %H:%M:%S') 
    
    mc = MongoClient('localhost', 27017)    # ����MongoClient
    cl = mc[dbName][collectionName]         # ��ȡ���ݼ��� 
    sampleData = cl.find_one()
    #del sampleData["_id"]
    theBarDate = startDate
    for theBar in dailyBar:
        if theBar[0] < startString[:10]:
            continue
        if theBar[0] > endString:
            continue
        #barDatetime = datetime.strptime(theBar[0],'%Y-%m-%d %H:%M:%S')
        #if theBar[0][11:13] == '15':
        #    continue
        dateString = datetime.strftime(theBarDate,'%Y-%m-%d')
        searchItem = {'date':dateString}  
        searchResult = cl.find(searchItem)
        if searchResult.count() < 4:  
            
            #insert open
            del sampleData["_id"]            
            sampleData["volume"] = int(float(theBar[5])/4)
            sampleData["datetime"] = theBarDate
            print(theBarDate)
            sampleData["high"] = float(float(theBar[2]))
            sampleData["time"] = datetime.strftime(theBarDate,'%H:%M:%S')
            sampleData["date"] = datetime.strftime(theBarDate,'%Y%m%d')
            sampleData["close"]= float(theBar[4]) 
            sampleData["open"]= float(theBar[1]) 
            sampleData["low"]= float(float(theBar[3]))   
            #print(sampleData)       
            insertResult = cl.insert_one(sampleData) 

            #insert High
            theBarDate = theBarDate + timedelta(hours=1)
            del sampleData["_id"]            
            sampleData["volume"] = int(float(theBar[5])/4)
            sampleData["datetime"] = theBarDate
            sampleData["high"] = float(float(theBar[2]))
            sampleData["time"] = datetime.strftime(theBarDate,'%H:%M:%S')
            sampleData["date"] = datetime.strftime(theBarDate,'%Y%m%d')
            sampleData["close"]= float(theBar[4]) 
            sampleData["open"]= float(theBar[1]) 
            sampleData["low"]= float(float(theBar[3]))   
            #print(sampleData)       
            insertResult = cl.insert_one(sampleData) 

            #insert Low
            theBarDate = theBarDate + timedelta(hours=1)
            del sampleData["_id"]            
            sampleData["volume"] = int(float(theBar[5])/4)
            sampleData["datetime"] = theBarDate
            sampleData["high"] = float(float(theBar[2]))
            sampleData["time"] = datetime.strftime(theBarDate,'%H:%M:%S')
            sampleData["date"] = datetime.strftime(theBarDate,'%Y%m%d')
            sampleData["close"]= float(theBar[4]) 
            sampleData["open"]= float(theBar[1]) 
            sampleData["low"]= float(float(theBar[3]))   
            #print(sampleData)       
            insertResult = cl.insert_one(sampleData) 
            
            #insert close
            theBarDate = theBarDate + timedelta(minutes=239)
            del sampleData["_id"]            
            sampleData["volume"] = int(float(theBar[5])/4)
            sampleData["datetime"] = theBarDate
            sampleData["high"] = float(float(theBar[2]))
            sampleData["time"] = datetime.strftime(theBarDate,'%H:%M:%S')
            sampleData["date"] = datetime.strftime(theBarDate,'%Y%m%d')
            sampleData["close"]= float(theBar[4]) 
            sampleData["open"]= float(theBar[1]) 
            sampleData["low"]= float(float(theBar[3]))   
            #print(sampleData)       
            insertResult = cl.insert_one(sampleData)   
            theBarDate = theBarDate + timedelta(minutes=1081)                      
            print("fill in data for:",dateString)  
    print(u'\n����������ɣ�%s, ���ϣ�%s, ��ʼ�գ�%s' %(dbName, collectionName, start))             
def fillMissingData(dbName, collectionName, start,cfgdata,cfgMap):
    """
    �����������,����14��59����û�У�ʹ��ǰһ��K�ߵ����ݡ�
    """
    print(u'\n�����������ݣ�%s, ���ϣ�%s, ��ʼ�գ�%s' %(dbName, collectionName, start))
    
    var_Symbol = ""
    var_Symbol = var_Symbol.join(list(filter(lambda x: x.isalpha(),collectionName)))            
    var_Time = cfgdata[var_Symbol][1]
    timeList = var_Time.split(":")
    startDate = start.replace(hour=int(timeList[0]), minute=int(timeList[1]), second=int(timeList[2]), microsecond=0)

    conMonth = collectionName[-3:]
    if conMonth == '901':
        return
    contractCode = cfgMap[collectionName][0]
    urlType = cfgMap[collectionName][1]
    #minKLineNo = 0
    dataUrl = ""
    if urlType == "url2":
        dataUrl = INDEX_URL + contractCode
        #minKLineNo = 240
    else:
        dataUrl = FUTURES_URL + contractCode
        
    fiveMinBar = getXminBarData(dataUrl)
    if fiveMinBar == None:
        print("Cannot read data from Sina, check it!")
        return
    fiveMinBar.sort()
    startString = datetime.strftime(startDate,'%Y-%m-%d %H:%M:%S') 

    mc = MongoClient('localhost', 27017)    # ����MongoClient
    cl = mc[dbName][collectionName]         # ��ȡ���ݼ��� 
    sampleData = cl.find_one()
    #del sampleData["_id"]
    for theBar in fiveMinBar:
        if theBar[0] < startString:
            continue
        barDatetime = datetime.strptime(theBar[0],'%Y-%m-%d %H:%M:%S')
        if theBar[0][11:13] == '15':
            #print(theBar[0])
            continue
        searchItem = {'datetime':barDatetime}  
        searchResult = cl.find_one(searchItem)
        if searchResult == None:  
            del sampleData["_id"]            
            sampleData["volume"] = int(float(theBar[5])/5)
            sampleData["datetime"] = barDatetime
            sampleData["high"] = float(float(theBar[2]))
            sampleData["time"] = theBar[0][11:]
            sampleData["date"] = datetime.strftime(barDatetime,'%Y%m%d')
            sampleData["close"]= float(float(theBar[4])) 
            sampleData["open"]= float(float(theBar[1])) 
            sampleData["low"]= float(float(float(theBar[3])))   
            #print(sampleData)       
            insertResult = cl.insert_one(sampleData) 
            print("fill in data for:",theBar[0])  
    print(u'\n����������ɣ�%s, ���ϣ�%s, ��ʼ�գ�%s' %(dbName, collectionName, start))        
#----------------------------------------------------------------------
def runDataRefilling():
    """����������ϴ"""
    print(u'��ʼ������ϴ����')
    
    # ��������
    setting = {}
    with open("DR_setting.json") as f:
        setting = json.load(f)
    
    volSize = get_VolSize()  
    symbolMap = getSymbolMapping() 
    print(symbolMap)
    # ����ִ����ϴ
    today = datetime.now()
    start = today - timedelta( hours=14)   # ��ϴ��ȥ10������
    end = start + timedelta(9)
    start.replace(hour=0, minute=0, second=0, microsecond=0)
    start = datetime.strptime('2019-06-11 00:00:00', '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime('2019-06-14 00:00:00', '%Y-%m-%d %H:%M:%S')
        
    for l in setting['bar']:
        symbol = l[0]
        
        #fillMissingData(MINUTE_DB_NAME, symbol, start,volSize,symbolMap)
        fillMissingDailyData(MINUTE_DB_NAME, symbol, start,end,volSize,symbolMap)
    
    print(u'������ϴ�������')
    

if __name__ == '__main__':
    runDataRefilling()
