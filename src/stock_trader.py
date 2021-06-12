import requests
import queue
import time
from . import delayed_interupt as di
from . import bank as Bank

class StockTrader():
    def __init__(self, bank: Bank, **kwargs):
        self.__bank = bank

        self.__URL_CURRENT_PRICE = kwargs.get("URL_CURRENT_PRICE", None)
        self.__URL_24HR_CHANGE = kwargs.get("URL_CURRENT_PRICE", None)
        self.__URL_AVG_PRICE = kwargs.get("URL_CURRENT_PRICE", None)
        self.__parameters = kwargs.get("parameters", None)
        if (self.__URL_CURRENT_PRICE == None or
        self.__URL_24HR_CHANGE == None or
        self.__URL_AVG_PRICE == None or
        self.__parameters == None):
            raise Exception("Must Provide urls for price checks")

        self.__frequency = kwargs.get("frequency", 2)
        self.__percent_change = kwargs.get("percent_change", 0.015)
        self.__trend_set_percentage = kwargs.get("trend_set_percentage", 0.003)
        self.__stop_loss_percentage = kwargs.get("stop_loss_percentage", 0.05)
        self.__stop_loss_enabled = kwargs.get("stop_loss_enabled", True)
        self.__log_file = kwargs.get("log_file", "transaction_log.log")
        self.__log_header = "Type,Amount,Price/Coin,Total Cost,Bank Stats\n"
        self.__header_checked = False
        self.__ascending = kwargs.get("ascending", False)
        self.__count = 0
        self.__sell_target = -1
        self.__buy_target = 0
        self.__rate_of_change = None
        self.__rate_of_rate_of_change = None
        self.__init = kwargs.get("init", 300)
        self.__avg_five_min = queue.Queue()
        self.__rrc_queue = queue.Queue()
        self.__rrc_average = None
        self.__rrc_sum = 0
        self.__arc_sum = 0
        self.__arc_average = None

    def set_log_file(self, log_file):
        self.__log_file = log_file

    def __log_headers(self, f):
        if (self.__header_checked):
            pass

        header_present = False
        f.seek(0, 0)
        line = f.readline()
        while ((not header_present) and (line != "")):
            if (line == self.__log_header):
                header_present = True

            line = f.readline()
        
        f.seek(0, 2)
        if (not header_present):
            f.write("\n")
            f.write(self.__log_header)

        self.__header_checked = True

    def __log_field(self, f, value, last = False):
        f.write(value + ("," if (not last) else "\n"))

    def __log(self, buy, amount_of_coin, currency, usd_total, usd_per_coin):
        f = open(self.__log_file, 'a+')
        self.__log_headers(f)

        self.__log_field(f, ("BUY" if buy else "SELL"))
        self.__log_field(f, str(amount_of_coin) + " " + currency)
        self.__log_field(f, "$" + str(usd_per_coin) + "/" + currency)
        self.__log_field(f, "$" + str(usd_total))

        stat  = "DOGE Balance: " + str(self.__bank.getDOGEBalance()) + "\t"
        stat += "ETH Balance: " + str(self.__bank.getETHBalance()) + "\t"
        stat += "BTC Balance: " + str(self.__bank.getBTCBalance()) + "\t"
        stat += "USD Balance: " + str(self.__bank.getUSDBalance()) + "\t"
        stat += "Total Portfolio Value: $" + str(self.__bank.getPortfolioValue(0, 0, usd_per_coin)) + "\t" # will need to fix later to handle other currencies
        stat += "Current Return: " + str(self.__bank.getReturn(0, 0, usd_per_coin)) + "\t"
        self.__log_field(f, stat, True)
        f.close()

    def set_percent_change(self, percent_change):
        self.__percent_change = percent_change

    def set_trend_set_percentage(self, trend_set_percentage):
        self.__trend_set_percentage = trend_set_percentage

    def set_stop_loss_percentage(self, stop_loss_percentage):
        self.__stop_loss_percentage = stop_loss_percentage

    def set_stop_loss_enabled(self, stop_loss_enabled):
        self.__stop_loss_enabled = stop_loss_enabled

    def get_current_price(self):
        response = requests.get(self.__URL_CURRENT_PRICE, params=self.__parameters)
        return float(response.json()["price"])

    def get_avg_price(self):
        response = requests.get(self.__URL_AVG_PRICE, params=self.__parameters)
        return float(response.json()["price"])

    def get_starting_price(self):
        return self.__starting_price

    def get_starting_avg(self):
        return self.__starting_avg

    def get_last_price_avg(self):
        return self.__last_price_avg

    def get_last_price(self):
        return self.__last_price

    def get_low_price(self):
        return self.__low_price

    def get_high_price(self):
        return self.__high_price

    def run(self):
        self.__starting_price = self.get_current_price()
        self.__starting_avg = self.get_avg_price()
        self.__last_price_avg = self.__starting_avg
        self.__last_price = self.__starting_price
        self.__low_price = self.__starting_price
        self.__high_price = self.__starting_price
        while (True):
            with di.DelayedKeyboardInterrupt():
                eth_price = self.get_current_price()
                eth_price_avg = self.get_avg_price()
                if eth_price_avg >= self.__last_price_avg:
                    self.__ascending = True
                else:
                    self.__ascending = False

                if self.__count >= self.__init:
                    self.__rate_of_change = (eth_price_avg - self.__avg_five_min.get())
                    num_arc_samples = 150
                    self.__arc_sum += self.__rate_of_change
                    if self.__count >= self.__init + num_arc_samples * self.__frequency:
                        self.__arc_average = (self.__arc_sum / num_arc_samples)  

                
                self.__avg_five_min.put(eth_price_avg)

                #instantaneous rate of change
                irc = eth_price - self.__last_price
                num_samples = 30
                samples_taken = 0
                if self.__count >= self.__frequency * num_samples:
                    self.__rrc_queue.put(irc)
                    self.__rrc_sum -= self.__rrc_queue.get()
                    self.__rrc_average = (self.__rrc_sum / num_samples) * (60/self.__frequency)
                else:
                    self.__rrc_queue.put(irc)
                    self.__rrc_sum += irc
                    samples_taken += 1
                    self.__rrc_average = (self.__rrc_sum / samples_taken) * (60/self.__frequency)

                # average rate of change
                

                if eth_price < self.__low_price:
                    self.__low_price = eth_price
                        
                if eth_price > self.__high_price:
                    self.__high_price = eth_price
                
                self.__buy_target = self.__low_price * (1 + self.__percent_change)    
                
                # Buy if Low
                if eth_price >= self.__low_price * (1 + self.__percent_change) and self.__ascending == True and eth_price >= self.__low_price * (1 + self.__trend_set_percentage) and self.__bank.getUSDBalance() != 0:
                    amount_usd = self.__bank.getUSDBalance()
                    eth_purchased = self.__bank.buyETH(amount_usd, eth_price)
                    print("You bought ", eth_purchased, " ETH!\n\n")
                    log(True, eth_purchased, "ETH", amount_usd, eth_price)
                    self.__low_price = eth_price
                    self.__high_price = eth_price
                    self.__sell_target = eth_price * (1 + self.__percent_change)
                
                # Sell if made 5% and trending down
                if self.__sell_target != -1 and eth_price >= self.__sell_target and not self.__ascending and eth_price <= self.__high_price * (1 - self.__trend_set_percentage) and self.__bank.getETHBalance() != 0:
                    eth_sold = self.__bank.sellETH(self.__bank.getETHBalance(), eth_price)
                    print("You sold ", eth_sold, " ETH!\n\n")
                    amount_usd = eth_sold * eth_price
                    log(False, eth_sold, "ETH", amount_usd, eth_price)
                    self.__low_price = eth_price
                    self.__high_price = eth_price

                # Trigger Stop Loss if necessary
                if self.__stop_loss_enabled and eth_price < (1 - self.__stop_loss_percentage) * self.__bank.getAvgETHPurchasePrice() and not self.__ascending and self.__bank.getETHBalance() > 0:
                    eth_sold = self.__bank.sellETH(self.__bank.getETHBalance(), eth_price)
                    print("Stop loss triggered - you sold ", eth_sold, " ETH!\n\n")
                    self.__low_price = eth_price
                    self.__high_price = eth_price
                    self.__sell_target = 100000000000 # change to -1 (already used as -1 elsewhere) or float('inf')


                self.__last_price = eth_price
                
                if self.__ascending == False:
                    status = "Desc"
                else:
                    status = "Asce"

                print("CP: $", round(eth_price,2), ", RC: ", (str(round(self.__rate_of_change, 4)) + "/min" if self.__rate_of_change != None else "..."),
                        ", RRC: ", str(round(self.__rrc_average, 4)) + "/min" if self.__rrc_average != None else "...",
                        ", ARC: ", str(round(self.__arc_average, 4)) + "/min" if self.__arc_average != None else "...", ", T: ", status,
                        ", H: $", round(self.__high_price,2), ", L: $", round(self.__low_price,2), ", ST: $", round(self.__sell_target,2), ", BT: $",
                        round(self.__buy_target,2), ", PV: $", self.__bank.getPortfolioValue(0, 0, eth_price), end="      \r") 

                self.__count += self.__frequency
                time.sleep(self.__frequency)


# test application
if (__name__ == "__main__"):
    import bank as b
    trader = StockTrader(b.bank(7000),
        URL_CURRENT_PRICE = "https://api.binance.us/api/v3/ticker/price",
        URL_24HR_CHANGE = "https://api.binance.us/api/v3/ticker/24hr",
        URL_AVG_PRICE = "https://api.binance.us/api/v3/avgPrice",
        parameters = {
            "symbol": "ETHUSD"
        }
    )
    trader.run()