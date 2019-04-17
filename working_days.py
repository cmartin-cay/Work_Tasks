from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
import pandas as pd
from datetime import date

# Create the holiday calendar. In this case dates will be entered by hand, no rules will be used
class CaymanHolidays(AbstractHolidayCalendar):
    rules = [Holiday("MadeUpHoliday", month=4, day=8)]

chosen_day = pd.Timestamp('2019-04-05')
print(chosen_day.day_name())
chosen_day = chosen_day + pd.offsets.CDay(7, calendar=CaymanHolidays())
print(chosen_day.day_name())

# Creates an instance of the business day calendar excluding weekends and Cayman holidays
chols = pd.offsets.CustomBusinessDay(calendar=CaymanHolidays())
start_date = date(year=2019, month=4, day=1)
def working_days(start, end, holiday_cal):
    return len(pd.date_range(start=start, end=end, freq=holiday_cal))

print(working_days(start_date, "20190419", chols))