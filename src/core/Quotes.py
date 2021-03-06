import logging

from core.Controller import Controller
from models.Quote import Quote
from models.OptionBuying import OptionBuying

class Quotes:
  @staticmethod
  def getQuote(tradingSymbol, isFnO = False):
    broker = Controller.getBrokerName()
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    quote = None
    if broker == "zerodha":
      key = ('NFO:' + tradingSymbol) if isFnO == True else ('NSE:' + tradingSymbol)
      bQuoteResp = brokerHandle.quote(key) 
      bQuote = bQuoteResp[key]
      # convert broker quote to our system quote
      quote = Quote(tradingSymbol)
      quote.tradingSymbol = tradingSymbol
      quote.lastTradedPrice = bQuote['last_price']
      quote.lastTradedQuantity = bQuote['last_quantity']
      quote.avgTradedPrice = bQuote['average_price']
      quote.volume = bQuote['volume']
      quote.totalBuyQuantity = bQuote['buy_quantity']
      quote.totalSellQuantity = bQuote['sell_quantity']
      ohlc = bQuote['ohlc']
      quote.open = ohlc['open']
      quote.high = ohlc['high']
      quote.low = ohlc['low']
      quote.close = ohlc['close']
      quote.change = bQuote['net_change']
      quote.oiDayHigh = bQuote['oi_day_high']
      quote.oiDayLow = bQuote['oi_day_low']
      quote.lowerCiruitLimit = bQuote['lower_circuit_limit']
      quote.upperCircuitLimit = bQuote['upper_circuit_limit']
    else:
      # The logic may be different for other brokers
      quote = None
    return quote

  @staticmethod
  def getCMP(tradingSymbol):
    quote = Quotes.getQuote(tradingSymbol)
    if quote:
      return quote.lastTradedPrice
    else:
      return 0
  
  @staticmethod
  def getStrikePrice(tradingSymbol):
    broker = Controller.getBrokerName()
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    quote = None
    if broker == "zerodha":
      key = 'NSE:' + tradingSymbol
      bQuoteResp = brokerHandle.quote(key) 
      quote = bQuoteResp[key]
      if quote:
        return quote['last_price']
      else:
        return 0
    else:
      # The logic may be different for other brokers
      quote = None
    return quote

  @staticmethod
  def getOptionBuyingQuote(tradingSymbol,isFnO):
    quote = Quotes.getQuote(tradingSymbol,isFnO)
    if quote:
      # convert quote to Option buying details
      optionBuying = OptionBuying(tradingSymbol)
      optionBuying.lastTradedPrice = quote.lastTradedPrice
      optionBuying.high = quote.high
      optionBuying.low = quote.low
      optionBuying.entryPrice= (quote.low*1.8)
      optionBuying.stopLoss=(quote.low*1.8)-20
      optionBuying.target=(quote.low*1.8)+40
      optionBuying.isTradeLive=False
    else:
      optionBuying= None
    return optionBuying    