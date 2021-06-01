
class OptionBuying:
  def __init__(self, tradingSymbol):
    self.tradingSymbol = tradingSymbol
    self.lastTradedPrice = 0
    self.high = 0
    self.low = 0
    self.entryPrice=0
    self.stopLoss=0
    self.target=0
    self.isTradeLive=False
    
    

    