class bank():
    def __init__(self, initial_balance):
        self.usd = initial_balance
        self.doge = 0
        self.eth = 0
        self.btc = 0
        self.avgETHPurchasePrice = 0
        self.avgBTCPurchasePrice = 0
        self.avgDOGEPurchasePrice = 0
        self.totalCost = self.usd
        self.currentReturn = 1
        self.buySellFee = 0.001

    def buyDOGE(self, usd, dogeprice):
        if usd > self.usd:
            return 0
        self.usd -= usd
        new_doge = (usd / dogeprice)
        new_doge -= new_doge * (self.buySellFee)
        # Update Average Purchase Price
        self.avgDOGEPurchasePrice = (self.avgDOGEPurchasePrice * self.doge + new_doge * dogeprice) / (self.doge + new_doge)
        self.doge += new_doge
        return usd / dogeprice # Returns the amount of doge purchased
    
    def sellDOGE(self, doge, dogeprice):
        if doge > self.doge:
            return 0
        self.doge -= doge
        new_usd = doge * dogeprice
        self.usd += new_usd - new_usd * self.buySellFee

        if self.doge == 0:
            self.avgDOGEPurchasePrice = 0
        return doge * dogeprice # Returns the amount of doge sold

    def buyETH(self, usd, ethprice):
        if usd > self.usd:
            return 0
        self.usd -= usd
        usable_usd = usd * (1 - self.buySellFee)
        new_eth = usable_usd / ethprice
        # Update Average Purchase Price
        self.avgETHPurchasePrice = (self.avgETHPurchasePrice * self.eth + new_eth * ethprice) / (self.eth + new_eth)
        self.eth += new_eth
        return new_eth
    
    def sellETH(self, eth, ethprice):
        if eth > self.eth:
            return 0
        self.eth -= eth
        new_usd = eth * ethprice
        new_usd = new_usd * (1 - self.buySellFee)
        self.usd += new_usd
        
        if self.eth == 0:
            self.avgETHPurchasePrice = 0
        return eth * ethprice
 
    def buyBTC(self, usd, btcprice):
        if usd > self.usd:
            return 0
        self.usd -= usd 
        new_btc = usd / btcprice
        new_btc = new_btc * (1 - self.buySellFee)
        # Update Average Purchase Price
        self.avgBTCPurchasePrice = (self.avgBTCPurchasePrice * self.btc + new_btc * btcprice) / (self.btc + new_btc)
        self.btc += new_btc
        return new_btc
    
    def sellBTC(self, btc, btcprice):
        if btc > self.btc:
            return 0
        self.btc -= btc
        new_usd = btc * btcprice
        new_usd = new_usd * (1 - self.buySellFee)
        self.usd += new_usd
        if self.btc == 0:
            self.avgBTCPurchasePrice = 0
        return new_usd
    
    def getUSDBalance(self):
        return self.usd
    
    def getDOGEBalance(self):
        return self.doge

    def getETHBalance(self):
        return self.eth

    def getBTCBalance(self):
        return self.btc

    def getPortfolioValue(self, dogeprice, btcprice, ethprice):
        return round(self.usd + self.doge * dogeprice + self.eth * ethprice + self.btc * btcprice,2)

    def getAvgETHPurchasePrice(self):
        return self.avgETHPurchasePrice

    def getAvgBTCPurchasePrice(self):
        return self.avgBTCPurchasePrice

    def getAvgDOGEPurchasePrice(self):
        return self.avgDOGEPurchasePrice

    def getReturn(self, dogeprice, btcprice, ethprice):
        self.currentReturn = self.getPortfolioValue(dogeprice, btcprice, ethprice) / self.totalCost
        return self.currentReturn * 100
    
    def depositUSD(self, usd):
        self.usd += usd
        self.totalCost += usd
        return self.usd

    def withdrawUSD(self, usd):
        self.usd -= usd
        self.totalCost -= usd
        return self.usd
