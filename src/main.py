import random

import pandas as pd
from datetime import datetime, timedelta
from random import randint

import tkinter as tk
from tkinter import *
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from utils import parse_report

import sys
sys.path.append("../../DBMaintain/src")
from BaseDB import BaseDB

sys.path.append("../../backTrader/src")
from util import get_target_dict, get_prev_minimum_date


def load_log():
    global loglist
    if check_var.get() == 1:
        file_path = filedialog.askopenfilename()
        if file_path:
            log = open(file_path, 'r')
            loglist = log.readlines()
            log.close()
    else:
        messagebox.showerror("muti-stock viewer message box", "unable to load log from file, please click Import Log first !")

def load_target():
    global target, all_target
    if target_var.get() == "top10":
        dir_path = filedialog.askdirectory()
        target, all_target = get_target_dict(dir_path)

    else:
        messagebox.showerror("muti-stock viewer message box", "unable to load target from file, please click top10 first !")

def increment_date():
    date = date_entry.get_date() + timedelta(days=1)
    date_entry.set_date(date)
    update_stock_options()
    update_figures()

def decrement_date():
    date = date_entry.get_date() - timedelta(days=1)
    date_entry.set_date(date)
    update_stock_options()
    update_figures()

def scale_date():
    day = days_spinbox.get()
    start_date = date_entry.get_date() - timedelta(days=day)
    end_date = date_entry.get_date() + timedelta(days=day)
    print(start_date)
    print(end_date)


def update_stock_options(*args):
    global target, all_target, available_stocks
    if len(stock_listbox.curselection()):
        return
    date = date_entry.get_date()

    if target_var.get() == "input":
        available_stocks = (target_entries["input"].get()).split()
    elif target_var.get() == "top10":
        target_date = get_prev_minimum_date(target, date)
        available_stocks = [item+"R1" for item in target[target_date]]

    stock_listbox.delete(0, 'end')
    for stock in available_stocks:
        stock_listbox.insert('end', stock)



def update_figures(*args):
    global available_stocks, loglist
    df_dict = dict()
    # available_stocks = []

    if len(stock_listbox.curselection()):
        selected_stock_ids = [stock_listbox.get(i) for i in stock_listbox.curselection()]
    else:
        selected_stock_ids = available_stocks

    # stock_list = ["CDFR1", "DXFR1", "GHFR1", "GNFR1", "DKFR1", "GXFR1", "CHFR1", "NDFR1", "LQFR1", "JZFR1", "PEFR1"]
    # selected_stock_ids = random.sample(stock_list, 10)
    print(selected_stock_ids)

    plt.close('all')
    for widget in charts_frame.winfo_children():
        widget.destroy()
    for widget in profit_frame.winfo_children():
        widget.destroy()

    day = days_spinbox.get()
    cur_date = date_entry.get_date()
    start_date = date_entry.get_date() - timedelta(days=day)
    end_date = date_entry.get_date() + timedelta(days=day)
    print(f"current date: {cur_date} | start_date: {start_date} | end_date: {end_date}")

    report_dict = dict()
    if check_var.get() == 1 and loglist:
        report_dict = parse_report(loglist, str(cur_date))


    selected_period = interval_var.get()
    selected_number = interval_entries[selected_period].get()
    total = 0
    for idx, item in enumerate(selected_stock_ids):
        df = db.readKbarsFromDB(contractName=item, start = start_date, end = end_date)
        if len(df) == 0: continue
        df = get_resampled_df(df)
        df_dict[item] = df

        row = idx // 4
        col = idx % 4

        lf = tk.LabelFrame(charts_frame, text=f"Stock: {item}")
        lf.grid(row=row, column=col, sticky="nsew")

        apv = mpf.make_addplot(df['Volume'], panel=1, color='g', secondary_y='auto', ylabel='Volume', type='bar')
        mystyle = mpf.make_mpf_style(base_mpf_style='binance', rc={'xtick.labelsize':8})
        # fig, axes = mpf.plot(df, type='line', style=mystyle, addplot=apv, returnfig=True, figscale=0.55)

        PLOT_TYPE = 'line' if len(df) >= 500 else 'candle'
        fig, axes = mpf.plot(df, type=PLOT_TYPE, style=mystyle, addplot=apv, returnfig=True, figscale=0.55)

        if item in report_dict:
            profit = float(report_dict[item]['profit'])
            color = "green" if profit >=0 else "red"
            fig.text(0.05, 0.9, f"profit: {report_dict[item]['profit']}", fontsize=16, color=color)
            total += float(report_dict[item]['profit'])
            # fig.text(0.05, 0.8, f"profit: {report_dict[item]['profit']}\n"
            #                    f"entry: {report_dict[item]['entry_price']}\n"
            #                    f"exit: {report_dict[item]['exit_price']}", fontsize=16, color=color)
            # entry = f"entry_date: {report_dict[item]['entry_date']}, entry_price: {report_dict[item]['entry_price']}"
            # exit = f"exit_date: {report_dict[item]['exit_date']}, exit_price: {report_dict[item]['exit_price']}"
            # axes[0].annotate({entry}, xy=(0, float(report_dict[item]['entry_price'])), textcoords='axes fraction', xytext=(0,0),
            #                  arrowprops=dict(facecolor='green', arrowstyle="->"), fontsize=16, horizontalalignment='right', verticalalignment='top')
            # axes[0].annotate({exit}, xy=(len(df), float(report_dict[item]['exit_price'])), textcoords='axes fraction', xytext=(1, 1),
            #                  arrowprops=dict(facecolor='red', arrowstyle="->"), fontsize=16, horizontalalignment='right', verticalalignment='top')




        canvas = FigureCanvasTkAgg(fig, master=lf)
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        canvas.draw()
    color = "green" if total >=0 else "red"
    pf = tk.Label(profit_frame, text=f"Total profit: {total}", fg=color).pack()

def get_resampled_df(df):
    import time
    start = time.time()
    selected_interval = interval_var.get()
    selected_number = interval_entries[selected_interval].get()

    if selected_interval == "day":
        period = str(selected_number) + 'D'
    elif selected_interval == "hour":
        period = str(selected_number) + 'H'
    elif selected_interval == "min":
        period = str(selected_number) + 'T'

    print(f"selected_interval: {selected_interval}, Selected_interval_number: {selected_number}, period: {period}")

    df['ts'] = pd.to_datetime(df['ts'])
    df.set_index('ts', inplace=True)

    resampled_df = pd.DataFrame()
    resampled_df['Volume'] = df['Volume'].resample(period).sum()
    resampled_df['High'] = df['High'].resample(period).max()
    resampled_df['Low'] = df['Low'].resample(period).min()
    resampled_df['Open'] = df['Open'].resample(period).first()
    resampled_df['Close'] = df['Close'].resample(period).last()
    resampled_df = resampled_df.dropna()
    # resampled_df = resampled_df[~resampled_df.index.isnull()]
    print(f"time elapsed: {time.time()-start}")
    return resampled_df



root = tk.Tk()
root.title("multi-stock viewer")
root.geometry("1800x1200")

charts_frame = tk.Frame(root)
charts_frame.pack()

profit_frame = tk.Frame(root)
profit_frame.pack()



db_path = "/home/ss900405tw/Desktop/stockPredict/DBMaintain/db/futures_1min_quick.db"
db = BaseDB(db_path)
df = db.readKbarsFromDB(contractName='CDFR1')
# print(df)

# frame of importing log
log_frame = tk.Frame(root)
log_frame.pack(side=tk.LEFT)

# selector for importing log
check_var = tk.IntVar()
check_button = tk.Checkbutton(log_frame, text="Import Report",variable=check_var, onvalue=1, offvalue=0)
check_button.pack()

# load file from path
load_button = tk.Button(log_frame, text="Load File", command=load_log)
load_button.pack()


# frame of importing target
target_frame = tk.Frame(root)
target_frame.pack(side=tk.LEFT)

target_var = tk.StringVar(target_frame)
target_var.set("top10")

target_options = ["top10", "input"]
target_entries = {}

radiobutton = tk.Radiobutton(target_frame, text="top10", variable=target_var, value="top10")
radiobutton.pack()
load_target_button = tk.Button(target_frame, text="Load Dir", command=load_target)
load_target_button.pack()

radiobutton = tk.Radiobutton(target_frame, text="input", variable=target_var, value="input")
radiobutton.pack()
entry = tk.Entry(target_frame)
entry.pack()
target_entries["input"] = entry

update_button = tk.Button(target_frame, text="update stocks", command=update_stock_options)
update_button.pack()





# Select date to display
date = '2022-01-04'
date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidh=2, date_pattern='yyyy-mm-dd')
date_entry.set_date(date)
date_entry.pack(side=tk.LEFT)
# date_entry.bind("<<DateEntrySelected>>", update_stock_options)
date_entry.bind("<<DateEntrySelected>>", update_stock_options)
date_entry.bind("<<DateEntrySelected>>", update_figures, add="+")

# increase/decrease date
increment_button = tk.Button(root, text="+", command=increment_date)
increment_button.pack(side=tk.LEFT)

decrement_button = tk.Button(root, text="-", command=decrement_date)
decrement_button.pack(side=tk.LEFT)

# listbox for user to select stocks
scrollbar = Scrollbar(root)
stock_listbox = tk.Listbox(root, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set)
stock_listbox.pack(side=tk.LEFT)
scrollbar.pack(side=tk.LEFT)
scrollbar.config(command=stock_listbox.yview)

# spinbox for user to select display days
days_var = tk.StringVar(root)
# days_spinbox = tk.Spinbox(root, from_=1, to=365, textvariable=days_var)
days_spinbox = tk.Scale(root, from_=0, to = 30)
days_spinbox.set(2)
days_spinbox.pack(side=tk.LEFT)

# Radiobutton and Entry for user to select time period
interval_var = tk.StringVar(root)
interval_var.set("day")

interval_options = ["min", "hour", "day"]
interval_entries = {}

for option in interval_options:
    radiobutton = tk.Radiobutton(root, text=option, variable=interval_var, value=option)
    radiobutton.pack(side=tk.LEFT)

    entry = tk.Entry(root)
    entry.pack(side=tk.LEFT)
    interval_entries[option] = entry
interval_entries["day"].insert(0,1)

load_button = tk.Button(root, text="update figure", command=update_figures)
load_button.pack(side=tk.LEFT)

# chAAApDDrAis test
root.mainloop()
