import logging
import time
import json
import os
from models.OptionBuying import OptionBuying
from trademgmt.TradeEncoder import TradeEncoder
from core.Controller import Controller
from ticker.ZerodhaTicker import ZerodhaTicker
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
from ordermgmt.Order import Order
from core.Quotes import Quotes
from utils.Utils import Utils

class OptionBuyingStrategy:
  __instance = None

  @staticmethod
  def getInstance(): # singleton class
    if OptionBuyingStrategy.__instance == None:
      OptionBuyingStrategy()
    return OptionBuyingStrategy.__instance
  
  def __init__(self):
    if OptionBuyingStrategy.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      OptionBuyingStrategy.__instance = self

  def run(self):
    logging.info('Inititated the OptionBuyingStrategy: Run called')
    self.strikeRunner()

  @staticmethod
  def strikeRunner():
     # Get current market price of Nifty Future
    #futureSymbol = Utils.prepareMonthlyExpiryFuturesSymbol('BANKNIFTY')
    strikesFilepath='G:\Algo Trading\python\git\python-deploy\stikes\stikes.json'
   
    #quote = Quotes.getQuote(futureSymbol,True)

    futureSymbol='NIFTY BANK'
    quote = Quotes.getStrikePrice(futureSymbol) 
    if quote == None:
      logging.error('OptionBuyingStrategy: Could not get quote for %s', futureSymbol)
      return
    
    ATMStrike = Utils.getNearestStrikePrice(quote, 100)
    logging.info('OptionBuyingStrategy: Bank Nifty CMP = %f, ATMStrike = %d', quote, ATMStrike)
    
    initialATMStrike=ATMStrike+100
    OptionBuyingStrategy.trades = []
    OptionBuyingStrategy.loadAndUpdateStrikesFromFile(strikesFilepath)
    if(len(OptionBuyingStrategy.trades)==0):
      logging.info("As strikes data is empty , it will be added to the file")
      # Increment from current ATM strike price to find strike that condition met to CE strike 
      while True:
        optionQuote = Quotes.getOptionBuyingQuote(Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", initialATMStrike, 'CE'),True)
        if(OptionBuyingStrategy.isWithinTradingRange(optionQuote.low)):
          OptionBuyingStrategy.trades.append(optionQuote)
          message="{0} : low is {1} satisfies to trade".format(optionQuote.tradingSymbol,optionQuote.low)
          Utils.sendMessageTelegramBot(message)
          logging.info(message)
          break
        initialATMStrike=initialATMStrike+100
      
      # Increment from current ATM strike price to find strike that condition met to PE strike 
      initialATMStrike=ATMStrike-100
      while True:
        optionQuote = Quotes.getOptionBuyingQuote(Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", initialATMStrike, 'PE'),True)
        if(OptionBuyingStrategy.isWithinTradingRange(optionQuote.low)):
          OptionBuyingStrategy.trades.append(optionQuote)
          message="{0} : low is {1} satisfies to trade".format(optionQuote.tradingSymbol,optionQuote.low)
          Utils.sendMessageTelegramBot(message)
          logging.info(message)
          break
        initialATMStrike=initialATMStrike-100
          
      with open(strikesFilepath,'w') as tFile:
            json.dump(OptionBuyingStrategy.trades, tFile, indent=2, cls=TradeEncoder)

      message="Option details are saved to file successfully, it will be updated regularly"
      Utils.sendMessageTelegramBot(message)
      OptionBuyingStrategy.loadAndUpdateStrikesFromFile(strikesFilepath)    
      
    else:
      logging.info("Update the low Price ")
    
    

  def loadAndUpdateStrikesFromFile(strikesFilepath):
    if os.path.exists(strikesFilepath) == False:
      logging.warn('loadAndUpdateStrikesFromFile() stikes Filepath %s does not exist', strikesFilepath)
      return
    OptionBuyingStrategy.trades = []
    OptionBuyingStrategy.updatedTrades = []
    tFile = open(strikesFilepath, 'r')
    tradesData = json.loads(tFile.read())
    if not tradesData:
      return 
    else:
      while True:
        isDataUpdate=False
        OptionBuyingStrategy.trades = []
        tFile = open(strikesFilepath, 'r')
        tradesData = json.loads(tFile.read())
        for tr in tradesData:
          
          trade = OptionBuyingStrategy.convertJSONToTrade(tr)
          if(trade.isTradeLive==False):
            #logging.info("As trade is not live , low will be verified")
            optionQuote=Quotes.getOptionBuyingQuote(trade.tradingSymbol,True)
            if(OptionBuyingStrategy.isWithinTradingRange(optionQuote.low)):
              if(trade.low != optionQuote.low): # Check whether the low is still withing range else it has to be updated
                isDataUpdate=True
                message="OptionBuyingStrategy: Low is updated low for {0}".format(trade.tradingSymbol)
                Utils.sendMessageTelegramBot(message)
                logging.info(message)
                trade.low = optionQuote.low
                OptionBuyingStrategy.updatedTrades.append(trade)
            else:
              isDataUpdate=True
              newStrikeTrade=OptionBuyingStrategy.getUpdatedStrike(int(trade.tradingSymbol[-7:-2]),trade.tradingSymbol[-2:])
              message="OptionBuyingStrategy: Strike is updated from {0} to {1}".format(trade.tradingSymbol,newStrikeTrade.tradingSymbol)
              Utils.sendMessageTelegramBot(message)
              logging.info(message)
              trade=newStrikeTrade
          OptionBuyingStrategy.trades.append(trade)
        if(len(OptionBuyingStrategy.trades)!=0 and isDataUpdate):
          #OptionBuyingStrategy.trades=[]
          #OptionBuyingStrategy.trades=Test.updatedTrades
          OptionBuyingStrategy.writeStrikesToFile(OptionBuyingStrategy.trades)
       
        time.sleep(60)

  @staticmethod
  def convertJSONToTrade(jsonData):
    optionBuying = OptionBuying(jsonData['tradingSymbol'])
    optionBuying.lastTradedPrice = jsonData['lastTradedPrice']
    optionBuying.high = jsonData['high']
    optionBuying.low = jsonData['low']
    optionBuying.entryPrice= jsonData['entryPrice']
    optionBuying.stopLoss=jsonData['stopLoss']
    optionBuying.target=jsonData['target']
    optionBuying.isTradeLive=jsonData['isTradeLive']
    return optionBuying
 
  @staticmethod
  def isWithinTradingRange(low):
    if(low>=50.00 and low<=80.00):
      return True
    else:
      return False
  
  @staticmethod
  def getUpdatedStrike(strikePrice,optionType):
    optionQuote=None 
    if(optionType == "CE"):
      initialUpdateStrike=strikePrice-100
    else:
      initialUpdateStrike=strikePrice+100

    while True:
      optionQuote = Quotes.getOptionBuyingQuote(Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", initialUpdateStrike, optionType),True)
      if(OptionBuyingStrategy.isWithinTradingRange(optionQuote.low)):
        logging.info('Low is updated to %f with low is %f',initialUpdateStrike,optionQuote.low)
        break
   
      if(optionType == "CE" and initialUpdateStrike>strikePrice):
        initialUpdateStrike=initialUpdateStrike-100
      elif(optionType == "PE" and initialUpdateStrike<strikePrice):
        initialUpdateStrike=initialUpdateStrike+100
    
    return optionQuote
      
  @staticmethod
  def writeStrikesToFile(trade):
    strikesFilepath='G:\Algo Trading\python\git\python-deploy\stikes\stikes.json'
    with open(strikesFilepath,'w') as tFile:
      json.dump(OptionBuyingStrategy.trades, tFile, indent=2, cls=TradeEncoder)

