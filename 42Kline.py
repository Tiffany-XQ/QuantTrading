'''backtest
start: 2022-06-09 10:30:00
end: 2022-06-18 09:15:00
period: 15m
exchanges: [{"eid":"Futures_Binance","currency":"BTC_USDT"}]
'''

import time

leverage = 5
ratio = 0.6
account = None
position = None
minQty = 0.00001
maxQty = 348.86797766
period = 5
num_Klines = 42

def OpenPrice():
    Sleep(6000) # 休眠6s等待k线更新
    records = _C(exchange.GetRecords, period*60)
    OPEN = []
    for i in range(len(records)):
        OPEN.append(float(records[i]["Open"]))
    return OPEN

def Buy():
    global leverage, ratio, account, position, minQty, maxQty
    ticker = _C(exchange.GetTicker)
    if _N(ratio * leverage * account.Balance / ticker.Last,3) >= minQty:
        exchange.SetDirection("buy")
        while ratio * leverage * account.Balance / ticker.Last > maxQty:
            Log("下单量大于最大下单量：需要拆单")
            exchange.Buy(-1, maxQty)
            account = _C(exchange.GetAccount)
            position = _C(exchange.GetPosition)
            ticker = _C(exchange.GetTicker)
        exchange.Buy(-1, _N(ratio * leverage * account.Balance/ticker.Last, 3))
        account = _C(exchange.GetAccount)
        position = _C(exchange.GetPosition)
    else:
        Log("下单失败：小于最小下单量", "余额：", account.Balance, "最新成交价：", ticker.Last)

def Sell():
    global leverage, ratio, account, position, minQty, maxQty
    ticker = _C(exchange.GetTicker)
    if _N(ratio * leverage * account.Balance / ticker.Last,3) >=  minQty:
        exchange.SetDirection("sell")
        while ratio * leverage * account.Balance / ticker.Last > maxQty:
            Log("下单量大于最大下单量：需要拆单")
            exchange.Sell(-1, maxQty)
            account = _C(exchange.GetAccount)
            position = _C(exchange.GetPosition)
            ticker = _C(exchange.GetTicker)
        exchange.Sell(-1, _N(0.5 * leverage * account.Balance/ticker.Last, 3))
        account = _C(exchange.GetAccount)
        position = _C(exchange.GetPosition)  
    else:
        Log("下单失败：小于最小下单量", "余额：", account.Balance, "最新成交价：", ticker.Last)

def CloseSell(): 
    global account, position, maxQty
    exchange.SetDirection("closesell")
    while position[0]["Amount"] > maxQty:
        exchange.Buy(-1, maxQty)
        account = _C(exchange.GetAccount)
        position = _C(exchange.GetPosition)
    exchange.Buy(-1, position[0]["Amount"])
    account = _C(exchange.GetAccount)
    position = _C(exchange.GetPosition)

def CloseBuy():
    global account, position, maxQty
    exchange.SetDirection("closebuy")
    while position[0]["Amount"] > maxQty:
        exchange.Sell(-1, maxQty)
        account = _C(exchange.GetAccount)
        position = _C(exchange.GetPosition)
    exchange.Sell(-1, position[0]["Amount"])
    account = _C(exchange.GetAccount)
    position = _C(exchange.GetPosition)

def main():
    global leverage, account, position, period, num_Klines
    exchange.SetContractType("swap")
    exchange.SetMarginLevel(leverage)
    exchange.SetPrecision(2, 3)
    Log("程序启动")
    account = _C(exchange.GetAccount)
    position = _C(exchange.GetPosition)
    if len(position) != 0:
        Log("清除账户原有仓位")
        if position[0]["Type"] == 0: # 多仓
            CloseBuy()
        elif position[0]["Type"] == 1: # 空仓
            CloseSell()
    initialBalance = float(account["Balance"])
    try:
        while True:
            if int(_D()[14:16]) % period != 0:
                Sleep(1000) # 未到整点 继续休眠
            else:
                OPEN = OpenPrice()
                # Log({"-44":OPEN[-44], "-43":OPEN[-43], "-2":OPEN[-2], "-1":OPEN[-1]})
                account = _C(exchange.GetAccount)
                position = _C(exchange.GetPosition)
                if len(position) == 0: # 无仓位（初始）
                    if (OPEN[-2] < OPEN[-2-num_Klines]) and (OPEN[-1] >= OPEN[-1-num_Klines]): # 空翻多
                        Log("下单，做多")
                        Buy()
                    elif (OPEN[-2] >= OPEN[-2-num_Klines]) and (OPEN[-1] < OPEN[-1-num_Klines]): # 多翻空
                        Log("下单，做空")
                        Sell()
                    elif (OPEN[-2] >= OPEN[-2-num_Klines]) and (OPEN[-1] >= OPEN[-1-num_Klines]): # 多头
                        Log("下单，做多")
                        Buy()
                    elif (OPEN[-2] < OPEN[-2-num_Klines]) and (OPEN[-1] < OPEN[-1-num_Klines]): # 空头
                        Log("下单，做空")
                        Sell()
                elif len(position) == 1:
                    if (OPEN[-2] < OPEN[-2-num_Klines]) and (OPEN[-1] >= OPEN[-1-num_Klines]): # 空翻多
                        Log("空翻多")
                        CloseSell() # 平空仓
                        endingBalance = float(account["Balance"])
                        LogProfit(endingBalance-initialBalance)
                        Buy() # 开多仓
                    elif (OPEN[-2] >= OPEN[-2-num_Klines]) and (OPEN[-1] < OPEN[-1-num_Klines]): # 多翻空
                        Log("多翻空")
                        CloseBuy() # 平多仓
                        endingBalance = float(account["Balance"])
                        LogProfit(endingBalance-initialBalance)
                        Sell() # 开空仓
                    else:
                        if position[0]["Type"] == 0: # 多仓
                            Log("继续持有多单")
                        elif position[0]["Type"] == 1: # 空仓
                            Log("继续持有空单")
                # 状态信息
                account = _C(exchange.GetAccount)
                position = _C(exchange.GetPosition)
                Sleep(60*1000) # 休眠1min      
    except:
        Log("程序已停止")