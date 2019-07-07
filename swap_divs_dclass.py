import datetime
from dataclasses import dataclass
from typing import Type, List
from collections import defaultdict
import pandas as pd

from dataclass_csv import DataclassReader, dateformat

ME_DATE = datetime.datetime(2017, 9, 30)
DIV_CASH = []
WHT_CASH = []
DIV_AMOUNT = []


@dataclass
@dateformat("%m/%d/%Y")
class Trade:
    SEDOL: str
    swap_settlement_currency: str
    stock_description: str
    end_date: datetime.datetime
    value_date: datetime.datetime
    quantity: int
    dividend: float
    start_date: datetime.datetime = datetime.datetime.now().strftime("%m/%d/%Y")


@dataclass
@dateformat("%d %b %Y %H:%M")
class Dividend:
    fund: str
    tid: int
    security: str
    start_position: int
    new_position: int
    amount: float
    div_ccy: str
    ex_date: datetime.datetime
    _SEDOL: str

    @property
    def SEDOL(self):
        return self._SEDOL.lstrip("0")

    @property
    def is_offshore(self):
        return True if self.fund in ("BHRO", "BHROR") else False

    # TODO Remember cut off date for WHT
    @property
    def is_WHT(self):
        return (
            True
            if self.is_offshore and self.amount > 0 and self.div_ccy == "USD"
            else False
        )

    @property
    def WHT_rate(self):
        return 0.3 if self.is_WHT else 0

    def valid_div(self, trade: Type[Trade]):
        if (
            self.SEDOL == trade.SEDOL
            and trade.start_date < self.ex_date
            and self.ex_date <= trade.end_date
        ):
            return True
        else:
            return False

    def pay_div(
        self, trade: Type[Trade], temp_div_cash, temp_WHT_cash, temp_div_amount
    ):
        if self.valid_div(trade):
            temp_div_amount.append(trade.quantity * self.amount)
            temp_div_cash.append(trade.quantity * -self.amount * (1 - self.WHT_rate))
            if self.is_WHT:
                temp_WHT_cash.append(trade.quantity * -self.amount * self.WHT_rate)
            self.reduce_div(trade)

    def reduce_div(self, trade: Type[Trade]):
        self.new_position += trade.quantity


def read_divs(file_name):
    div_list = []
    with open(file_name) as divs_csv:
        reader = DataclassReader(divs_csv, Dividend)
        reader.map("Fund").to("fund")
        reader.map("Tid").to("tid")
        reader.map("Security").to("security")
        reader.map("Position").to("start_position")
        reader.map("Position").to("new_position")
        reader.map("Amount").to("amount")
        reader.map("Div Ccy").to("div_ccy")
        reader.map("Ex Date").to("ex_date")
        reader.map("SEDOL").to("_SEDOL")
        for row in reader:
            div_list.append(row)
        return div_list


def read_trades(file_name):
    trade_list = []
    with open(file_name) as trades_csv:
        reader = DataclassReader(trades_csv, Trade)
        reader.map("Swap Settlement Currency").to("swap_settlement_currency")
        reader.map("Stock description").to("stock_description")
        reader.map("Start Date").to("start_date")
        reader.map("End Date").to("end_date")
        reader.map("Value Date").to("value_date")
        reader.map("Quantity").to("quantity")
        reader.map("Dividend").to("dividend")
        for row in reader:
            if row.quantity != 0 and row.value_date <= ME_DATE:
                trade_list.append(row)
        return trade_list


def filter_trades(trades: List[Trade], divs: List[Dividend]) -> List[Trade]:
    """Filter down the trades to include only those with an accrued dividend"""
    # Step 1 - Create a set of valid dividend SEDOLs
    SEDOL_with_div = set(div.SEDOL for div in divs)
    return [trade for trade in trades if trade.SEDOL in SEDOL_with_div]


all_divs = read_divs("Swap Divs.csv")
divs_dict = defaultdict(list)
for div in all_divs:
    divs_dict[div.SEDOL].append(div)
all_trades = read_trades("MSCO BHRI September.csv")
valid_trades = filter_trades(all_trades, all_divs)

trade: Type[Trade]
div: Type[Dividend]
for idx, trade in enumerate(valid_trades):
    temp_div_amount = []
    temp_div_cash = []
    temp_WHT_cash = []
    # for div in all_divs:
    for div in divs_dict[trade.SEDOL]:
        div.pay_div(trade, temp_div_cash, temp_WHT_cash, temp_div_amount)
    # if temp_div_cash:
    #     print(f"Temp Cash Entry {idx} {trade.stock_description} {trade.swap_settlement_currency} {sum(temp_div_cash)}")
    # if temp_WHT_cash:
    #     print(f"Temp WHT Cash Entry {idx} {trade.stock_description} {trade.swap_settlement_currency} {sum(temp_WHT_cash)}")
    # if temp_div_amount:
    #     print(f"Temp Div Amount Entry {idx} {trade.stock_description} {trade.swap_settlement_currency} {sum(temp_div_amount)}")
    if temp_div_cash:
        DIV_CASH.append(
            [
                trade.stock_description,
                trade.value_date,
                trade.swap_settlement_currency,
                div.fund,
                sum(temp_div_cash),
            ]
        )

def create_pnl_entries(cashflow_list, WHT=False):
    pnl_entries = pd.DataFrame(cashflow_list, columns=["Description", "Value Date", "Currency", "Fund", "Amount"])
    # Divs were calculated based on cash, so amount needs to be flipped
    pnl_entries["Amount"] *= -1
    pnl_entries = pnl_entries.groupby(["Fund", "Description", "Value Date", "Currency"]).sum().reset_index()
    pnl_entries["Description"] = pnl_entries["Description"] + " Swap Div"
    # Set the cash entries to be Income by default then change for Expense
    pnl_entries["Account"] = 42003
    pnl_entries.loc[pnl_entries["Amount"] > 0, "Account"] = 52502
    return pnl_entries

def create_cash_entries(df, WHT=False):
    if not WHT:
       cash_entries = df.copy()
       cash_entries["Amount"] *= -1
       cash_entries["Account"] = 11504
       return cash_entries

initial = create_pnl_entries(DIV_CASH)
second = create_cash_entries(initial)
