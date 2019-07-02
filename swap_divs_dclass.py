from dataclasses import dataclass, field, replace
from dateutil import parser
import datetime
from typing import Type
from dataclass_csv import DataclassReader, dateformat

ME_DATE = datetime.datetime(2017, 9, 30)
div_cashflow = []
WHT_cashflow = []


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

    def pay_div(self, trade: Type[Trade], temp_div_cash, temp_WHT_cash):
        if self.valid_div(trade):
            temp_div_cash.append(trade.quantity * -self.amount * (1 - self.WHT_rate))
            if self.is_WHT:
                temp_WHT_cash.append(trade.quantity * self.amount * self.WHT_rate)
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


all_divs = read_divs("Swap Divs.csv")
all_trades = read_trades("MSCO BHRI September.csv")

trade: Type[Trade]
div: Type[Dividend]
for trade in all_trades:
    temp_div_cash = []
    temp_WHT_cash = []
    for div in all_divs:
        div.pay_div(trade, temp_div_cash, temp_WHT_cash)
    if temp_div_cash:
        print(f"Temp Cash {trade.stock_description} {trade.swap_settlement_currency} {sum(temp_div_cash)}")