from tkinter import Tk
from tkinter import StringVar
from tkinter import DoubleVar
from tkinter import messagebox
from tkinter import END
import tkinter as tk
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
import threading


class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        if reqId != -1:
            print("Error: ", reqId, " ", errorCode, " ", errorString)

    def nextValidId(self, nextorderId):
        global orderId
        orderId = nextorderId

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print("OrderStatus. Id:", orderId, ", Status:", status, ", Filled:",
              filled, ", Remaining:", remaining, ", LastFillPrice:", lastFillPrice)


class OrderInfo:
    @staticmethod
    def BracketOrder(parentOrderId: int, action: str, quantity: int,
                     limitPrice: float, takeProfitLimitPrice: float,
                     stopLossPrice: float):

        parent = Order()
        parent.orderId = parentOrderId
        parent.action = action
        parent.orderType = "STP LMT"
        parent.totalQuantity = input.share_size
        parent.lmtPrice = input.entry
        parent.auxPrice = input.entry
        parent.transmit = False

        takeProfit = Order()
        takeProfit.orderId = parent.orderId + 1
        takeProfit.action = "SELL" if action == "BUY" else "BUY"
        takeProfit.orderType = "LMT"
        takeProfit.totalQuantity = input.share_size
        takeProfit.lmtPrice = input.target
        takeProfit.parentId = parentOrderId
        takeProfit.transmit = False

        stopLoss = Order()
        stopLoss.orderId = parent.orderId + 2
        stopLoss.action = "SELL" if action == "BUY" else "BUY"
        stopLoss.orderType = "STP"
        stopLoss.totalQuantity = input.share_size
        stopLoss.auxPrice = input.stop
        stopLoss.parentId = parentOrderId
        stopLoss.transmit = True

        bracketOrder = [parent, takeProfit, stopLoss]
        return bracketOrder


def contractCreate():
    contract = Contract()
    contract.symbol = input.ticker
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.primaryExchange = "ISLAND"
    return contract


def clear(*args):
    ticker_entry.delete(0, END)
    entry_entry.delete(0, END)
    stop_entry.delete(0, END)


def input(*args):
    global orderId
    input.ticker = ticker_input.get().upper()  # ticker

    input.entry = round(float(entry_input.get()), 2)  # entry
    print("ENTRY: ", input.entry)

    input.stop = round(float(stop_input.get()), 2)  # stop
    print("STOP: ", input.stop)

    input.stop_points = abs(round(input.entry - input.stop, 2))  # stop points
    print("STOP POINTS: ", input.stop_points)

    # limit_size is 10% the size of the stop
    input.limit_size = round(abs(input.stop_points / 10), 2)
    print("LIMIT SIZE: ", input.limit_size)

    input.stop_size = round(input.stop_points + input.limit_size, 2)
    print("STOP SIZE: ", input.stop_size)

    input.target_points = round(input.stop_points * 2, 2)  # target points
    print("TARGET POINTS: ", input.target_points)

    input.share_size = abs((int)(risk / input.stop_points))  # share size
    if input.share_size == 0:
        input.share_size = 1
    print("SHARE SIZE: ", input.share_size)

    if input.entry - input.stop > 0:
        input.order_type = "BUY"
        input.position = "LONG"

        input.target = round(input.entry + input.target_points, 2)  # target
        print("TARGET: ", input.target)

        input.entry_stop_limit = round(input.entry + input.limit_size, 2)
        print("ENTRY STOP LIMIT: ", input.entry_stop_limit)

    elif input.entry - input.stop < 0:
        input.order_type = "SELL"
        input.position = "SHORT"

        input.target = round(input.entry - input.target_points, 2)  # target
        print("TARGET: ", input.target)

        input.entry_limit = round(input.entry - input.limit_size, 2)
        print("ENTRY LIMIT: ", input.entry_limit)

    # make sure risk does not exceed $10
    if input.share_size * input.stop_points <= 10:
        contractObject = contractCreate()
        bracket = OrderInfo.BracketOrder(
            orderId, input.order_type, input.share_size, input.entry, input.target, input.stop)
        for order in bracket:
            app.placeOrder(order.orderId, contractObject, order)
        orderId += 3

        confirm()

    else:
        tk.messagebox.showerror(
            "Order Failed", "Risk too high.")


def confirm():
    confirmation = Tk()
    confirmation.title("Order Sent!")
    confirmation.geometry("200x300")

    tradeframe = tk.Frame(confirmation)
    tradeframe.grid(column=0, row=0)
    confirmation.columnconfigure(0, weight=1)
    confirmation.rowconfigure(0, weight=1)

    if input.position == "LONG":
        tk.Label(tradeframe, text=input.position,
                 fg="green").grid(column=0, row=0)
    elif input.position == "SHORT":
        tk.Label(tradeframe, text=input.position,
                 fg="red").grid(column=0, row=0)

    tk.Label(tradeframe, text=input.ticker).grid(column=1, row=0)

    tk.Label(tradeframe, text="Entry").grid(column=0, row=1)
    tk.Label(tradeframe, text=input.entry).grid(column=1, row=1)

    tk.Label(tradeframe, text="Stop", fg="red").grid(column=0, row=2)
    tk.Label(tradeframe, text=input.stop).grid(column=1, row=2)

    tk.Label(tradeframe, text="Target", fg="green").grid(column=0, row=3)
    tk.Label(tradeframe, text=input.target).grid(column=1, row=3)

    tk.Label(tradeframe, text="Shares").grid(column=0, row=4)
    tk.Label(tradeframe, text=input.share_size).grid(column=1, row=4)

    tk.Label(tradeframe, text="Risk", fg="red").grid(column=0, row=5)
    tk.Label(tradeframe, text=abs(round(input.stop_points *
             input.share_size, 2))).grid(column=1, row=5)

    tk.Label(tradeframe, text="Reward", fg="green").grid(column=0, row=6)
    tk.Label(tradeframe, text=abs(round(input.target_points *
             input.share_size, 2))).grid(column=1, row=6)

    for child in tradeframe.winfo_children():
        child.grid_configure(padx=5, pady=5)
    confirmation.attributes("-topmost", True)
    confirmation.lift()
    confirmation.mainloop()


risk = 10.00
reward = 20.00

root = Tk()
root.title("Order Placer")
root.geometry("200x300")

mainframe = tk.Frame(root)
mainframe.grid(column=0, row=0)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

ticker_input = StringVar()
ticker_entry = tk.Entry(
    mainframe, width=7, textvariable=ticker_input)

entry_input = DoubleVar()
entry_entry = tk.Entry(
    mainframe, width=7, textvariable=entry_input)

stop_input = DoubleVar()
stop_entry = tk.Entry(mainframe, width=7,
                      textvariable=stop_input)

tk.Label(mainframe, text=reward, fg="green").grid(column=0, row=0)
tk.Label(mainframe, text=risk, fg="red").grid(column=1, row=0)

tk.Label(mainframe, text="Ticker").grid(column=0, row=1)
ticker_entry.grid(column=1, row=1)
ticker_entry.delete(0, END)

tk.Label(mainframe, text="Entry").grid(column=0, row=2)
entry_entry.grid(column=1, row=2)
entry_entry.delete(0, END)

tk.Label(mainframe, text="Stop").grid(column=0, row=3)
stop_entry.grid(column=1, row=3)
stop_entry.delete(0, END)

tk.Button(mainframe, text="Clear",
          command=clear).grid(column=0, row=6)
tk.Button(mainframe, text="Send Order",
          command=input).grid(column=1, row=6)

for child in mainframe.winfo_children():
    child.grid_configure(padx=20, pady=15)

root.bind("<Return>", input)

app = IBApi()
app.connect("127.0.0.1", 7496, 0)  # 7496 = REAL, 7497 = PAPER
ib_thread = threading.Thread(target=app.run, daemon=True)
ib_thread.start()

root.attributes("-topmost", True)
root.mainloop()
