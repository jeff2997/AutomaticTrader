import requests
# import PySimpleGUI as sg
import src.bank as b
from src.stock_trader import StockTrader

URL_CURRENT_PRICE = "https://api.binance.us/api/v3/ticker/price"
URL_24HR_CHANGE = "https://api.binance.us/api/v3/ticker/24hr"
URL_AVG_PRICE = "https://api.binance.us/api/v3/avgPrice"
parameters = {
    "symbol": "ETHUSD"
}

# Test values:
wallet = 7000.0000
my_bank = b.bank(wallet)

# Init user interface
print("CP = Current ETH Price")
print("T = Time Elapsed")
print("H = High Price")
print("L = Low Price")
print("ST = Sell Target")
print("BT = Buy Target")
print("ET = Elapsed Time")
print("PV = Current Portfolio Value")
print("RC = Current Rate of Change")

trader = StockTrader(my_bank,
    URL_CURRENT_PRICE = URL_CURRENT_PRICE,
    URL_24HR_CHANGE = URL_24HR_CHANGE,
    URL_AVG_PRICE = URL_AVG_PRICE,
    parameters = parameters,

    # sleep-time between runs
    frequency = 2,

    # 0 = valley, 1 = peak
    last = 0, 

    # The amount which the price must decrease or increase before a 
    # a sale or purchase can happen
    percent_change = 0.015,

    # The amount which the price must either increase or decrease
    # after hitting a peak or valley before a transaction can occur
    trend_set_percentage = 0.003,

    # The amount which the price must fall before triggering a stop loss sell
    stop_loss_percentage = 0.05,

    # Enable the stop loss function
    stop_loss_enabled = True,

    # Log File Name
    log_file = "transaction_log.log",

    # Trend of coin value
    ascending = False,

    # 5 min init time for rate of change
    init = 300 
)
trader.run()