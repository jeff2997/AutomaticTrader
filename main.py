import requests
# import PySimpleGUI as sg
import json
import time
import collections
import bank as b
import queue

URL_CURRENT_PRICE = "https://api.binance.us/api/v3/ticker/price"
URL_24HR_CHANGE = "https://api.binance.us/api/v3/ticker/24hr"
URL_AVG_PRICE = "https://api.binance.us/api/v3/avgPrice"
parameters = {
    "symbol": "ETHUSD"
}



# Test values:
wallet = 700.0000
frequency = 2
last = 0 # 0 = valley, 1 = peak
my_bank = b.bank(wallet)

# The amount which the price must decrease or increase before a 
# a sale or purchase can happen
percent_change = 0.015

# The amount which the price must either increase or decrease
# after hitting a peak or valley before a transaction can occur
trend_set_percentage = 0.003

# The amount which the price must fall before triggering a stop loss sell
stop_loss_percentage = 0.05

# Enable the stop loss function
stop_loss_enabled = True

# Log File Name
log_file = "transaction_log.log"

def log(buy, amount_of_coin, currency, usd_total, usd_per_coin):
    f = open(log_file, 'a')
    if buy:
        f.write("BUY ORDER: \n")
        f.write("Amount: " + str(amount_of_coin) + " " + currency + "\n")
        f.write("Purchase Price: $" + str(usd_per_coin) + "/" + currency + "\n")
        f.write("Total Cost: $" + str(usd_total) + "\n")
    else: 
        f.write("SELL ORDER: \n")
        f.write("Amount: " + str(amount_of_coin) + " " + currency + "\n")
        f.write("Purchase Price: $" + str(usd_per_coin) + "/" + currency + "\n")
        f.write("Total Cost: $" + str(usd_total) + "\n")
    f.write("CURRENT BANK STATS: \n")
    f.write("DOGE Balance: " + str(my_bank.getDOGEBalance()) + "\n")
    f.write("ETH Balance: " + str(my_bank.getETHBalance()) + "\n")
    f.write("BTC Balance: " + str(my_bank.getBTCBalance()) + "\n")
    f.write("USD Balance: " + str(my_bank.getUSDBalance()) + "\n")
    f.write("Total Portfolio Value: $" + str(my_bank.getPortfolioValue(0, 0, usd_per_coin)) + "\n") # will need to fix later to handle other currencies
    f.write("Current Return: " + str(my_bank.getReturn(0, 0, usd_per_coin)) + "\n")
    f.close()

# internal variables
ascending = False
response = requests.get(URL_CURRENT_PRICE, params=parameters)
starting_price = float(response.json()["price"])
response_avg = requests.get(URL_AVG_PRICE, params=parameters)
starting_avg = float(response.json()["price"])
last_price_avg = starting_avg
last_price = starting_price
low_price = starting_price
high_price = starting_price
count = 0
sell_target = -1
buy_target = 0
rate_of_change = None
rate_of_rate_of_change = None
init = 300 # 5 min init time for rate of change
avg_five_min = queue.Queue()
rrc_queue = queue.Queue()
rrc_average = None
rrc_sum = 0
arc_sum = 0
arc_average = None

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

while True:
    response = requests.get(URL_CURRENT_PRICE, params=parameters)
    eth_price = float(response.json()["price"])
    response_avg = requests.get(URL_AVG_PRICE, params=parameters)
    eth_price_avg = float(response.json()["price"])
    if eth_price_avg >= last_price_avg:
        ascending = True
    else:
        ascending = False

    if count >= init:
        rate_of_change = (eth_price_avg - avg_five_min.get())
        num_arc_samples = 150
        arc_sum += rate_of_change
        if count >= init + num_arc_samples * frequency:
            arc_average = (arc_sum / num_arc_samples)  

    
    avg_five_min.put(eth_price_avg)

    #instantaneous rate of change
    irc = eth_price - last_price
    num_samples = 30
    samples_taken = 0
    if count >= frequency * num_samples:
        rrc_queue.put(irc)
        rrc_sum -= rrc_queue.get()
        rrc_average = (rrc_sum / num_samples) * (60/frequency)
    else:
        rrc_queue.put(irc)
        rrc_sum += irc
        samples_taken += 1
        rrc_average = (rrc_sum / samples_taken) * (60/frequency)

    # average rate of change
    

    if eth_price < low_price:
        low_price = eth_price
            
    if eth_price > high_price:
        high_price = eth_price
    
    buy_target = low_price * (1 + percent_change)    
    
    # Buy if Low
    if eth_price >= low_price * (1 + percent_change) and ascending == True and eth_price >= low_price * (1 + trend_set_percentage) and my_bank.getUSDBalance() != 0:
        amount_usd = my_bank.getUSDBalance()
        eth_purchased = my_bank.buyETH(amount_usd, eth_price)
        print("You bought ", eth_purchased, " ETH!\n\n")
        log(True, eth_purchased, "ETH", amount_usd, eth_price)
        low_price = eth_price
        high_price = eth_price
        sell_target = eth_price * (1 + percent_change)
    
    # Sell if made 5% and trending down
    if sell_target != -1 and eth_price >= sell_target and not ascending and eth_price <= high_price * (1 - trend_set_percentage) and my_bank.getETHBalance() != 0:
        eth_sold = my_bank.sellETH(my_bank.getETHBalance(), eth_price)
        print("You sold ", eth_sold, " ETH!\n\n")
        amount_usd = eth_sold * eth_price
        log(False, eth_sold, "ETH", amount_usd, eth_price)
        low_price = eth_price
        high_price = eth_price

    # Trigger Stop Loss if necessary
    if stop_loss_enabled and eth_price < (1 - stop_loss_percentage) * my_bank.getAvgETHPurchasePrice() and not ascending and my_bank.getETHBalance() > 0:
        eth_sold = my_bank.sellETH(my_bank.getETHBalance(), eth_price)
        print("Stop loss triggered - you sold ", eth_sold, " ETH!\n\n")
        low_price = eth_price
        high_price = eth_price
        sell_target = 100000000000


    last_price = eth_price
    
    if ascending == False:
        status = "Desc"
    else:
        status = "Asce"

    print("CP: $", round(eth_price,2), ", RC: ", (str(round(rate_of_change, 4)) + "/min" if rate_of_change != None else "..."),
            ", RRC: ", str(round(rrc_average, 4)) + "/min" if rrc_average != None else "...",
            ", ARC: ", str(round(arc_average, 4)) + "/min" if arc_average != None else "...", ", T: ", status,
            ", H: $", round(high_price,2), ", L: $", round(low_price,2), ", ST: $", round(sell_target,2), ", BT: $",
            round(buy_target,2), ", PV: $", my_bank.getPortfolioValue(0, 0, eth_price), end="      \r") 

    count += frequency
    time.sleep(frequency)

    


