import time

symbols = "AXSUSDT,MANAUSDT,THETAUSDT,PEOPLEUSDT,APEUSDT,WAVESUSDT,GMTUSDT,ZILUSDT,KNCUSDT,OPUSDT"
symbols = symbols.replace("USDT", "_USDT")
symbols = symbols.split(",")

crypto_ratio = "0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1"
crypto_ratio = crypto_ratio.split(",")
for k in range(len(crypto_ratio)):
    crypto_ratio[k] = float(crypto_ratio[k])

account = None
position = None
balance = None
leverage = 2
ratio = 0.5
minQty = [0.01, 1, 0.1, 0.1, 0.01, 0.01, 0.1, 0.1, 0.1, 0.01]
precision = [2, 0, 1, 1, 2, 2, 1, 1, 1, 2]
maxQty = [59861.24083969, 1070040.72916666]
period = 60
num_Klines = 42

def OpenPrice():
    Sleep(6000) # 休眠6s等待k线更新
    OPEN = []
    for k in range(len(symbols)):
        exchange.SetCurrency(symbols[k])
        records = _C(exchange.GetRecords, period*60)
        open = []
        for i in range(len(records)):
            open.append(float(records[i]["Open"]))
        OPEN.append(open)
    return OPEN

def Buy(k, balance):
    global leverage, ratio, position, minQty, maxQty
    exchange.SetCurrency(symbols[k])
    exchange.SetPrecision(2, precision[k])
    ticker = _C(exchange.GetTicker)
    amount = _N(ratio * leverage * balance / ticker.Last, precision[k])
    if amount >= minQty[k]:
        exchange.SetDirection("buy")
        while amount > maxQty:
            Log("下单量大于最大下单量：需要拆单")
            exchange.Buy(-1, maxQty)
            amount = amount - maxQty
        exchange.Buy(-1, amount)
        position = _C(exchange.GetPosition)
        balance = balance - position["Margin"]
    else:
        Log("下单失败：小于最小下单量", "余额：", balance, "最新成交价：", ticker.Last)

def Sell(k, balance):
    global leverage, ratio, position, minQty, maxQty
    exchange.SetCurrency(symbols[k])
    exchange.SetPrecision(2, precision[k])
    ticker = _C(exchange.GetTicker)
    amount = _N(ratio * leverage * balance / ticker.Last, precision[k])
    if amount >=  minQty[k]:
        exchange.SetDirection("sell")
        while amount > maxQty:
            Log("下单量大于最大下单量：需要拆单")
            exchange.Sell(-1, maxQty)
            amount = amount - maxQty
        exchange.Sell(-1, amount)
        position = _C(exchange.GetPosition)  
        balance = balance - position["Margin"]
    else:
        Log("下单失败：小于最小下单量", "余额：", balance, "最新成交价：", ticker.Last)

def CloseSell(): 
    global position, maxQty
    exchange.SetDirection("closesell")
    while position[0]["Amount"] > maxQty:
        exchange.Buy(-1, maxQty)
        position = _C(exchange.GetPosition)
    exchange.Buy(-1, position[0]["Amount"])
    position = _C(exchange.GetPosition)

def CloseBuy():
    global position, maxQty
    exchange.SetDirection("closebuy")
    while position[0]["Amount"] > maxQty:
        exchange.Sell(-1, maxQty)
        position = _C(exchange.GetPosition)
    exchange.Sell(-1, position[0]["Amount"])
    position = _C(exchange.GetPosition)

def Strategy(k, OPEN, balance):
    global symbols, position
    exchange.SetCurrency(symbols[k])
    position = _C(exchange.GetPosition)
    if len(position) == 0: # 无仓位
        if (OPEN[k][-1] >= OPEN[k][-1-num_Klines]): # 多头
            Log(symbols[k], ": 下单，做多")
            Buy(k, balance[k])
        elif (OPEN[k][-1] < OPEN[k][-1-num_Klines]): # 空头
            Log(symbols[k], ": 下单，做空")
            Sell(k, balance[k])
    elif len(position) == 1:
        if (OPEN[k][-2] < OPEN[k][-2-num_Klines]) and (OPEN[k][-1] >= OPEN[k][-1-num_Klines]): # 空翻多
            Log(symbols[k], ": 空翻多")
            position = _C(exchange.GetPosition)
            balance[k] = balance[k] + position["Profit"]
            LogProfit(position["Profit"])
            CloseSell() # 平空仓
            Buy(k, balance[k]) # 开多仓
        elif (OPEN[k][-2] >= OPEN[k][-2-num_Klines]) and (OPEN[k][-1] < OPEN[k][-1-num_Klines]): # 多翻空
            Log(symbols[k], ": 多翻空")
            position = _C(exchange.GetPosition)
            balance[k] = balance[k] + position["Profit"]
            LogProfit(position["Profit"])
            CloseBuy() # 平多仓
            Sell(k, balance[k]) # 开空仓
        else:
            if position[0]["Type"] == 0: # 多仓
                Log(symbols[k], ": 继续持有多单")
            elif position[0]["Type"] == 1: # 空仓
                Log(symbols[k], ": 继续持有空单")

def main():
    global symbols, crypto_ratio, leverage, balance, period, num_Klines
    if len(crypto_ratio) != len(symbols):
        Log("占比错误")
    elif sum(crypto_ratio) < 0.9999999999:
        Log("占比的和不等于1")
    else:
        exchange.SetContractType("swap")
        exchange.SetMarginLevel(leverage)
        Log("程序启动")
        for k in range(len(symbols)):
            exchange.SetCurrency(symbols[k])
            position = _C(exchange.GetPosition)
            if len(position) != 0:
                Log(symbols[k], ": 清除原有仓位")
                if position[0]["Type"] == 0: # 多仓
                    CloseBuy()
                elif position[0]["Type"] == 1: # 空仓
                    CloseSell()
        account = _C(exchange.GetAccount)
        initialBalance = float(account["Balance"])
        balance = []
        for k in range(len(symbols)):
            balance.append(initialBalance*crypto_ratio[k])
        Log(balance)
        try:
            while True:
                if period < 60: # 周期小于1h
                    if int(_D()[14:16]) % period != 0:
                        Sleep(1000) # 未到整点 继续休眠
                    else:
                        OPEN = OpenPrice()
                        for k in range(len(symbols)):
                            Strategy(k, OPEN, balance)
                        Sleep(60*1000) # 休眠1min
                elif period == 60:
                    if int(_D()[14:16]) != "00":
                        Sleep(1000) # 未到整点 继续休眠
                    else:
                        OPEN = OpenPrice()
                        for k in range(len(symbols)):
                            Strategy(k, OPEN, balance)
                        Sleep(60*1000) # 休眠1min
                else: # 周期大于1h
                    if int(_D()[11:13]) % (period/60) != 0:
                        Sleep(60*1000)
                    else:
                        OPEN = OpenPrice()
                        for k in range(len(symbols)):
                            Strategy(k, OPEN, balance)
                        Sleep(60*60*1000) # 休眠1h
        except:
            Log("程序已停止")