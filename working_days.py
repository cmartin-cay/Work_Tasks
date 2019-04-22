from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
import pandas as pd
from mymodels import Base, Delivery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from PySide2.QtCore import QDate, Qt
from PySide2.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
    QApplication,
    QDialog,
    QFormLayout,
    QVBoxLayout,
    QDialogButtonBox,
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


def enter_delivery_date(name, cal_date):
    """
    Create an entry in the Delivery database
    :param name: Client Name
    :param cal_date: DateTime
    :return: None
    """
    current_month_start = date(year=cal_date.year, month=cal_date.month, day=1)
    business_days = working_days(
        start=current_month_start, end=cal_date, holiday_cal=chols
    )
    session = make_session()
    entry = Delivery(name=name, calendar_date=cal_date, working_day=business_days)
    session.add(entry)
    session.commit()


class EntryWindow(QDialog):
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
        for client in CLIENT_LIST:
            self.form_layout.addRow(client, DatePicker())
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(self.save_to_db_button_box)
        self.setLayout(main_layout)

    def save_to_db(self):
        num_items = self.form_layout.count()
        for index in range(0, num_items, 2):
            name = self.form_layout.itemAt(index).widget().text()
            cal_date = self.form_layout.itemAt(index+1).widget().date().toPython()
            enter_delivery_date(name=name, cal_date=cal_date)



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

# for client in CLIENT_LIST:
#     date_picker = DatePicker()
#     CLIENT_DICT[client] = date_picker
# print(CLIENT_DICT)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = EntryWindow()
    main_window.show()
    sys.exit(app.exec_())
