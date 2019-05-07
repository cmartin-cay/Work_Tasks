from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
import pandas as pd
import altair as alt
from mymodels import Base, Delivery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from PySide2.QtCore import QDate, Qt
from PySide2.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
    QApplication,
    QDialog,
    QFormLayout,
    QVBoxLayout,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
)
import sys

CLIENT_LIST = ["Client 1", "Client 2", "Client 3"]
CLIENT_DICT = dict()


# Create the holiday calendar. In this case dates will be entered by hand, no rules will be used
class CaymanHolidays(AbstractHolidayCalendar):
    rules = [
        Holiday("New Years Day", month=1, day=1),
        Holiday("Heroes Day", month=1, day=28),
        Holiday("Ash Wednesday", month=3, day=6),
        Holiday("Good Friday", month=4, day=19),
        Holiday("Easter Monday", month=4, day=22),
        Holiday("Discovery Day", month=5, day=20),
        Holiday("Queens Birthday", month=6, day=10),
        Holiday("Constitution Day", month=7, day=1),
        Holiday("Remembrance Day", month=11, day=11),
        Holiday("Christmas Day", month=12, day=25),
        Holiday("Boxing Day", month=12, day=26),
    ]


# Creates an instance of the business day calendar excluding weekends and Cayman holidays
chols = pd.offsets.CustomBusinessDay(calendar=CaymanHolidays())


def working_days(start, end, holiday_cal):
    return len(pd.date_range(start=start, end=end, freq=holiday_cal))


def make_session():
    """
    Generate a SQL Alchemy session
    :return: SQLAlchemy session
    """
    engine = create_engine("sqlite:///delivery_dates.db")
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


def conflicting_month(year, month, name, session):
    month_start = date(year=year, month=month, day=1)
    if month == 12:
        month_end = month_start.replace(
            year=year + 1, month=(month + 1) % 12
        ) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month + 1) - timedelta(days=1)
    results = (
        session.query(Delivery)
            .filter(
            Delivery.calendar_date >= month_start,
            Delivery.calendar_date <= month_end,
            Delivery.name == name,
            )
            .first()
    )
    if results:
        return True


def enter_delivery_date(name, cal_date):
    """
    Create an entry in the Delivery database
    :param name: Client Name
    :param cal_date: DateTime
    :return: None
    """
    session = make_session()
    current_month_start = date(year=cal_date.year, month=cal_date.month, day=1)
    business_days = working_days(
        start=current_month_start, end=cal_date, holiday_cal=chols
    )
    entry = Delivery(name=name, calendar_date=cal_date, working_day=business_days)
    session.add(entry)
    session.commit()


def enter_delivery_date_list(lst):
    """
    Create multiple entries in the Delivery database from a provided list
    :param lst: List of 2 element tuples with Name and Calender date
    :return: None
    """
    session = make_session()
    for elem in lst:
        name, cal_date = elem
        existing = conflicting_month(
            year=cal_date.year, month=cal_date.month, name=name, session=session
        )
        if existing:
            msg_box = QMessageBox()
            msg_box.setText("Entry Error")
            msg_box.setInformativeText(
                f"The entry for {name} and {cal_date:%B} {cal_date.year} already exists"
            )
            msg_box.exec_()
            # Return statement breaks out of both inner and outer loop. This means an entry will only be made
            # if all entries are valid
            return
        current_month_start = date(year=cal_date.year, month=cal_date.month, day=1)
        business_days = working_days(
            start=current_month_start, end=cal_date, holiday_cal=chols
        )
        entry = Delivery(name=name, calendar_date=cal_date, working_day=business_days)
        session.add(entry)
    session.commit()


def get_delivery_dates(start, end):
    """
    :param start: Start Date in Python date format
    :param end: End Date in Python date format
    :return: SQLAlchemy query
    """
    session = make_session()
    delivery_days = session.query(Delivery).filter(
        Delivery.calendar_date.between(start, end)
    )
    return delivery_days


def delivery_dates_to_pandas(results):
    df = pd.read_sql(
        results.statement, results.session.bind, parse_dates=["calendar_date"]
    ).drop(["id"], axis=1)
    return df


def graph_delivery_dates(df):
    alt.themes.enable("opaque")
    source = df
    shapes = alt.Shape("name:N")

    colors = alt.Color("name:N", legend=alt.Legend(title="Something"))

    line = (
        alt.Chart(source)
        .mark_line()
        .encode(
            x="yearmonth(calendar_date):N",
            y="working_day:Q",
            color=alt.Color("name", legend=None),
        )
    )

    points = line.mark_point(filled=True, size=80, opacity=1).encode(
        color=colors, shape="name"
    )

    alt.layer(line, points).resolve_scale(color="independent", shape="independent").save("chart.png")


# days = get_delivery_dates(date(2018, 1, 1), date(2019, 4, 30))
# df = delivery_dates_to_pandas(days)
# graph_delivery_dates(df=df)


class EntryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Delivery Dates")
        self.save_to_db_button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.save_to_db_button_box.accepted.connect(self.save_to_db)
        self.save_to_db_button_box.rejected.connect(self.close)
        main_layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.form_layout.setHorizontalSpacing(10)
        self.form_layout.setVerticalSpacing(10)
        for client in CLIENT_LIST:
            date_picker = DatePicker()
            CLIENT_DICT[client] = date_picker
            self.form_layout.addRow(client, date_picker)
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(self.save_to_db_button_box)
        self.setLayout(main_layout)

    def save_to_db(self):
        entries = []
        for key, val in CLIENT_DICT.items():
            cal_date = val.date().toPython()
            entries.append((key, cal_date))
        enter_delivery_date_list(entries)

class ChartOutputWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Reporting Period")
        main_layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.start_date = DatePicker()
        self.end_date = DatePicker()
        self.end_date.dateChanged.connect(self.end_date_chosen)
        self.form_layout.addRow("End Date", self.end_date)
        self.form_layout.addRow("Start Date", self.start_date)
        self.get_from_db_button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.get_from_db_button_box.accepted.connect(self.delivery_dates)
        self.get_from_db_button_box.rejected.connect(self.close)
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(self.get_from_db_button_box)
        self.setLayout(main_layout)

    def end_date_chosen(self, date):
        self.start_date.setMaximumDate(date)
        date = date.addMonths(-24)
        date.setDate(date.year(), date.month(), 1)
        self.start_date.setDate(date)

    def delivery_dates(self):
        query = get_delivery_dates(start=self.start_date.date().toPython(), end=self.end_date.date().toPython())
        df = delivery_dates_to_pandas(query)
        print(df)
        graph_delivery_dates(df=df)


class DatePicker(QDateEdit):
    def __init__(self):
        super().__init__()
        self.setDisplayFormat("dd/MM/yy")
        self.setDate(QDate.currentDate())
        self.setCalendarPopup(True)
        self.setCalendarWidget(Calendar())


class Calendar(QCalendarWidget):
    def __init__(self):
        super().__init__()
        self.setGridVisible(True)
        self.setFirstDayOfWeek(Qt.Monday)
        self.setVerticalHeaderFormat(self.NoVerticalHeader)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ChartOutputWindow()
    main_window.show()

    sys.exit(app.exec_())
