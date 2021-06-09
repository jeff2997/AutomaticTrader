import queue
import time
import delayed_interupt as di

class StockTrader():
    def __init__(self, bank, **kwargs):
        self.__bank = bank
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

    def set_starting_price(self, starting_price):
        self.__starting_price = starting_price

    def set_starting_average(self, starting_avg):
        self.__starting_avg = starting_avg

    def run(self):
        while (True):
            with di.DelayedKeyboardInterrupt():
                self.__log(True, 10, "ETH", 100, 10)
                self.__log(False, 10, "ETH", 100, 10)
                time.sleep(self.__frequency)


# test application
if (__name__ == "__main__"):
    import bank as b
    trader = StockTrader(b.bank(700))
    trader.run()