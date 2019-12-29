from sqlalchemy import Column, String, Integer, Boolean, create_engine, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import date
import pandas as pd


Base = declarative_base()

class CostEntry(Base):
    __tablename__ = "costentry"
    id =Column(Integer, primary_key=True)
    fund_name = Column(String, nullable=False)
    series_name = Column(String, nullable=False)
    SSS_ID = Column(String, nullable=False)
    month = Column(Date)
    opening_equity = Column(Float)
    subs = Column(Float)
    reds = Column(Float)
    switch_in = Column(Float)
    switch_out = Column(Float)
    sub_red_cost = Column(Float)
    switch_cost = Column(Float)
    closing_cost = Column(Float)
    dividend = Column(Float)

if __name__ == "__main__":
    engine = create_engine("sqlite:///llec_divs.db")
    Base.metadata.create_all(engine)