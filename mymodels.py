from sqlalchemy import Column, String, Integer, create_engine, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

Base = declarative_base()


class Delivery(Base):
    __tablename__ = "delivery"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    calendar_date = Column(Date)
    working_day = Column(Integer)

    def __repr__(self):
        return f"Client {self.name}: delivered on {self.calendar_date}"


if __name__ == '__main__':
    engine = create_engine("sqlite:///delivery_dates.db")
    Base.metadata.create_all(engine)
