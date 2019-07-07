import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from financial_models import Entries, Base
from datetime import datetime, date

engine = create_engine("sqlite:///trial_balance.db")


def make_session():
    """
    Generate a SQL Alchemy session
    :return: SQLAlchemy session
    """
    engine = create_engine("sqlite:///trial_balance.db")
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


def get_or_create_entry(session, fund_name, date, anum):
    entry = session.query(Entries).filter_by(fund_name=fund_name, date=date, anum=anum).first()
    if entry:
        entry.value = 1000
        print(entry)
        session.commit()
        return entry
    else:
        print("New")
        entry = Entries(fund_name=fund_name, date=date, anum=anum)
        entry.value = 777.77
        session.add(entry)
        session.commit()
        return entry


def get_anums(fund_name):
    """Get a unique list of all the anums used in the fund"""
    pass

def sum_entries(session, fund_name, anum):
    """Sum the total of a specific anum in a specific fund"""
    summed = session.query(func.sum(Entries.value)).filter_by(fund_name=fund_name, anum=anum).scalar()
    print(summed)


date1 = datetime(2019, 3, 31)
date2 = datetime(2019, 4, 30)
# df = pd.read_csv("entries.csv", parse_dates=['date'])
#
# df.to_sql("entries", con=engine, if_exists="append", index=False)
session = make_session()
# print(get_or_create_entry(session=session, fund_name="Fund 2", date=date2, anum=10000))
sum_entries(session, fund_name="Fund 1", anum=10000)
