import re
from collections import defaultdict


def parse_report(loglist, date):
    report_dict = defaultdict(dict)
    for line in loglist:
        if date + "T" in line:
            if "SELL EXECUTED" in line:
                stock_id = re.search("Stock: (.*?),", line).group(1) + "R1"
                entry_price = re.search("Price: (\d+\.\d+)", line).group(1)
                entry_date = re.search("(\d{4}-\d{2}-\d{2}T\d+:\d+:\d+)", line).group(1)
                report_dict[stock_id]["entry_date"] = entry_date
                report_dict[stock_id]["entry_price"] = entry_price

            elif "BUY EXECUTED" in line:
                stock_id = re.search("Stock: (.*?),", line).group(1) + "R1"
                exit_price = re.search("Price: (\d+\.\d+),", line).group(1)
                exit_date = re.search("(\d{4}-\d{2}-\d{2}T\d+:\d+:\d+)", line).group(1)
                report_dict[stock_id]["exit_date"] = exit_date
                report_dict[stock_id]["exit_price"] = exit_price
            elif "OPERATION PROFIT" in line:
                stock_id = re.search("Stock: (.*?),", line).group(1) + "R1"
                profit = re.search("NET (-?\d+\.\d+)", line).group(1)
                report_dict[stock_id]["profit"] = profit





    return report_dict
