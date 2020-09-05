from sqlalchemy import ARRAY, Boolean, Column, ForeignKey, Numeric, Integer, String, Date, Float
from sqlalchemy.orm import relationship, backref

from database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    price = Column(Float)

class Expiration(Base):
    __tablename__ = "expirations"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, ForeignKey(Stock.symbol), index=True)
    exp_list = Column(String)

class Strike(Base):
    __tablename__ = "strikes"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, ForeignKey(Stock.symbol), index=True)
    exp_list = Column(String, ForeignKey(Expiration.exp_list))
    strike_price = Column(Float)
    contract_price = Column(Float)
    price_to_execute = Column(Float)
    percent_profit = Column(Float)
    in_the_money = Column(Boolean)




    





