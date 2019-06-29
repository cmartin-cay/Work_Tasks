import pandas as pd
import numpy as np
from datetime import date
from tkinter.filedialog import askopenfilename
from tkinter import Tk

DEV = False
if DEV:
    div_file, trade_file = ("Citco Divs.xlsx", "MSCO.csv")
else:
    div_file, trade_file = (
        askopenfilename(title="Open the Citco Dividends File"),
        askopenfilename(title="Open the MSCO trade file"),
    )
ME_DATE = date(2019, 6, 30)
cashflow = []
error_log = []


def make_dicts():
    # Read the data and convert Ex-Date to a date format, then add a new Column
    divs = pd.read_excel(div_file, usecols=[0, 1, 2, 3, 4, 9, 11, 19])
    divs["New_Quantity"] = divs["Position"]
    div_ident = set(divs["SEDOL"].tolist())

    # Import Trades and adjust for Dates
    trades = pd.read_csv(
        trade_file, usecols=[13, 16, 20, 21, 22, 23, 26, 43], parse_dates=[3, 4, 5]
    )

    # Filter the trade list to only have trades which currently have accrued dividends
    trades = trades[trades["Quantity"] != 0]
    trades = trades[trades["Value Date"] <= ME_DATE]
    trades = trades[(trades["SEDOL"].isin(div_ident))]

    divs_dictionary = list(divs.T.to_dict().values())
    trades_dictionary = trades.T.to_dict().values()
    return trades_dictionary, divs_dictionary


def pay_div(trade, div, temp_cash):
    """
    Pays the dividend, and reduces the ending quantity by the notional
    Conditions:
    (1) The trade and the dividend must be the same security
    (2) The trade start date (origination date) must be before the dividend date
    (3) The dividend date must be before the trade ending date i.e. no dividend if it didn't exist yet
    """
    if (
        trade["SEDOL"] == div["SEDOL"]
        and trade["Start Date"] < div["Ex Date"]
        and div["Ex Date"] <= trade["End Date"]
    ):
        # Increase the amount of cash as the trade hits each relevant dividend
        try:
            reduce_div(trade, div)
        except ValueError:
            error_log.append(trade)
            print(error_log)
        else:
            temp_cash.append(trade["Quantity"] * -div["Amount"])


def reduce_div(trade, div):
    """Reduce the dividend by the trade quantity notional"""
    # We shouldn't ever change quantity from neg to pos or pos to neg
    # Raising the value error allows us to put it in a try block and use
    # basic logging to identify errors
    if abs(trade["Quantity"]) > abs(div["New_Quantity"]):
        raise ValueError("A trade tried to make a dividend negative")
    else:
        div["New_Quantity"] += int(trade["Quantity"])


def run_divs(trades, divs):
    for trade in trades:
        temp_cash = []
        # Create a cash 'bucket' for each unwind trade
        # Iterate through each accrued dividend
        for div in divs:
            pay_div(trade, div, temp_cash)
        # Only add to the cashflows if there has been a dividend created by the trade
        if temp_cash:
            cashflow.append(
                [
                    trade["Stock description"],
                    trade["Value Date"],
                    trade["Swap Settlement Currency"],
                    div["Fund"],
                    sum(temp_cash),
                ]
            )


def main():
    trades_dictionary, divs_dictionary = make_dicts()
    run_divs(trades_dictionary, divs_dictionary)
    cash_entries = pd.DataFrame(cashflow)
    # Perform some Pandas grouping magic to get the correct layout
    cash_entries = cash_entries.groupby([3, 0, 1, 2])[4].sum().reset_index()
    cash_entries["Account"] = 11504
    cash_entries[0] = cash_entries[0] + " Swap div"

    # Create the accruals side - reverse the cash direction and choose the correct anum
    accrual_entries = cash_entries.copy()
    accrual_entries[4] *= -1
    accrual_entries["Account"] = np.where(accrual_entries[4] > 0, 50502, 42003)

    # Combine the cash and accrual entries to make a valid debit and credit list
    system_entries = cash_entries.append(accrual_entries, ignore_index=True)
    system_entries.columns = ["Fund", "Description", "Date", "CCY", "Amount", "Anum"]

    # Create a new dataframe showing the changes to the accrued dividends
    remaining_divs = pd.DataFrame(divs_dictionary)
    remaining_divs = remaining_divs[
        [
            "Fund",
            "Tid",
            "Security",
            "Position",
            "Amount",
            "Div Ccy",
            "Ex Date",
            "SEDOL",
            "New_Quantity",
        ]
    ]
    remaining_divs.sort_values(
        ["Security", "Ex Date"], ascending=[True, True], inplace=True
    )

    # Write the accounting entries and the news dividends to an Excel file
    writer = pd.ExcelWriter("output.xlsx")
    system_entries.to_excel(writer, "Loader", index=False)
    remaining_divs.to_excel(writer, "End Divs", index=False)
    writer.save()


if __name__ == "__main__":
    main()

# TODO Error checking for when Div Quantity changes sign - Done
# TODO Don't allow divs to hit when New Quantity is zero - Done
# TODO Don't allow trades dated(settling?) before Ex-Date to make a dividend - Done
# TODO Cashflow output needs to be per Value Date, not per Trade - Done
# TODO Function to verify if a trade genuinely hits a dividend - Done
# TODO Completely empty cashflow gives KeyError - unlikely to be a serious problem
# TODO Cashflow and output with more details - Done
# TODO Outputs - Done
