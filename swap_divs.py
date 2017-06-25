import pandas as pd
from datetime import datetime, date
from pprint import pprint
from collections import defaultdict

ME_DATE = date(2017, 6, 30)

# Read the data and convert Ex-Date to a date format, then add a new Column
divs = pd.read_csv('Citco Divs.csv', usecols=[0, 1, 2, 3, 4, 9, 11, 19], parse_dates=[6])
divs['New_Quantity'] = divs['Position']
div_ident = set(divs["SEDOL"].tolist())

# Import Trades and adjust for Dates
trades = pd.read_csv('MSCO.csv', usecols=[13, 16, 20, 21, 22, 23, 26, 43], parse_dates=[3, 4, 5])

# Filter the trade list to only have trades which currently have accrued dividends
trades = trades[trades["Quantity"] != 0]
trades = trades[trades['Value Date'] <= ME_DATE]
trades = trades[(trades["SEDOL"].isin(div_ident))]

divs_dictionary = list(divs.T.to_dict().values())
trades_dictionary = trades.T.to_dict().values()

cashflow = []
error_log = []


def pay_div(trade, div, temp_cash):
    """
    Pays the dividend, and reduces the ending quantity by the notional
    Conditions:
    (1) The trade and the dividend must be the same security
    (2) The trade start date (origination date) must be before the dividend date
    (3) The dividend date must be before the trade ending date i.e. no dividend if it didn't exist yet
    """
    if trade["SEDOL"] == div["SEDOL"] and trade["Start Date"] <= div["Ex Date"] and div["Ex Date"] <= trade["End Date"]:
        # Increase the amount of cash as the trade hits each relevant dividend
        # div["New_Quantity"] -= trade['Quantity']
        try:
            reduce_div(trade, div)
        except ValueError:
            error_log.append(trade)
        else:
            temp_cash.append(trade['Quantity'] * -div['Amount'])


def reduce_div(trade, div):
    """Reduce the dividend by the trade quantity notional"""
    # We shouldn't ever change quantity from neg to pos or pos to neg
    # Raising the value error allows us to put it in a try block and use
    # basic logging to identify errors
    if trade['Quantity'] > div['New_Quantity']:
        raise ValueError("A trade tried to make a dividend negative")
    else:
        div['New_Quantity'] += int(trade['Quantity'])


def run_divs(trades, divs):
    for trade in trades:
        temp_cash = []
        # Create a cash 'bucket' for each unwind trade
        # Iterate through each accrued dividend
        for div in divs:
            pay_div(trade, div, temp_cash)
        # Only add to the cashflows if there has been a dividend created by the trade
        if temp_cash:
            cashflow.append([trade['Stock description'], trade['Value Date'], sum(temp_cash)])


if __name__ == '__main__':
    run_divs(trades_dictionary, divs_dictionary)
    # pprint(divs_dictionary)
    cf = pd.DataFrame(cashflow)
    print()
    cf = cf.groupby([0, 1]).sum().reset_index()
    print(cf)
    writer = pd.ExcelWriter('output.xlsx')
    cf.to_excel(writer, 'Sheet1', index=False)
    d = pd.DataFrame(divs_dictionary)
    print(d.dtypes)
    d = d[["Fund", "Tid", "Security", "Position", "Amount", "Div Ccy", "Ex Date", "SEDOL", "New_Quantity"]]
    d.sort_values(["Security", "Ex Date"], ascending=[True, True], inplace=True)
    d.to_excel(writer, "End Divs", index=False)
    writer.save()

    # TODO Error checking for when Div Quantity changes sign - Done
    # TODO Don't allow divs to hit when New Quantity is zero - Done
    # TODO Don't allow trades dated(settling?) before Ex-Date to make a dividend - Done but needs test data
    # TODO Cashflow output needs to be per Value Date, not per Trade - Done
    # TODO Function to verify if a trade genuinely hits a dividend - Done
    # TODO Cashflow with more details
    # TODO Outputs
