from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
import pandas as pd
from mymodels import Base, Delivery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from PySide2.QtCore import QDate, Qt
from PySide2.QtWidgets import QCalendarWidget, QDateEdit

# Create the holiday calendar. In this case dates will be entered by hand, no rules will be used
class CaymanHolidays(AbstractHolidayCalendar):
    rules = [Holiday("New Years Day", month=1, day=1),
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
    business_days = working_days(start=current_month_start, end=cal_date, holiday_cal=chols)
    session = make_session()
    entry = Delivery(name=name, calendar_date=cal_date, working_day=business_days)
    session.add(entry)
    session.commit()

