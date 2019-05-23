from sqlalchemy import Column, String, Integer, create_engine, Date, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

Base = declarative_base()


class Entries(Base):
    __tablename__ = "entries"
    # __table_args__ = (UniqueConstraint('fund_name', 'date', 'anum', name="entry_check"),)
    # id = Column(Integer, primary_key=True)
    fund_name = Column(String(250), primary_key=True)
    date = Column(Date, primary_key=True)
    anum = Column(Integer, primary_key=True)
    short_category = Column(String(256))
    long_category = Column(String(256))
    value = Column(Float)

    def __repr__(self):
        return f"Client {self.fund_name}, Anum {self.anum}, Value {self.value} "


if __name__ == '__main__':
    engine = create_engine("sqlite:///trial_balance.db")
    Base.metadata.create_all(engine)
