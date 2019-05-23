import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from financial_models import Entries, Base
from datetime import datetime

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

def get_or_create_instrument(session, fund_name, date, anum):
    entry = session.query(Entries).filter_by(fund_name=fund_name, date=date, anum=anum).first()
    if entry:
        entry.value=1000
        print(entry)
        session.commit()
        return entry
    else:
        print("New")
        entry = Entries(fund_name=fund_name, date=date, anum=anum)
        entry.value =777.77
        session.add(entry)
        session.commit()
        return entry

date = datetime(2019, 3, 31)
# df = pd.read_csv("entries.csv", parse_dates=['date'])
#
# df.to_sql("entries", con=engine, if_exists="append", index=False)
session = make_session()
print(get_or_create_instrument(session=session, fund_name="Fund 1", date=date, anum=10000))


