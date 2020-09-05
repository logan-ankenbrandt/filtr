import models
import yfinance
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Stock, Expiration, Strike
from operator import truediv, add
import sqlite3
import pandas as pd
import numpy as np

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

class StockRequest(BaseModel):
    symbol: str

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.get("/")
def home(request: Request, percent_profit = None, price_to_execute = None, in_the_money = None, db: Session = Depends(get_db)):
    """
    show all stocks in the database and button to add more
    button next to each stock to delete from database
    filters to filter this list of stocks
    button next to each to add a note or save for later
    """

    strike = db.query(Strike)

    if percent_profit:
        strike = strike.filter(Strike.percent_profit > percent_profit)

    if price_to_execute:
        strike = strike.filter(Strike.price_to_execute < price_to_execute)
    
    if in_the_money:
        strike = strike.filter(Strike.in_the_money == in_the_money)
    
    strike = strike.all()

    return templates.TemplateResponse("home.html", {
        "request": request, 
        "strike": strike, 
        "percent_profit": percent_profit,
        "price_to_execute": price_to_execute,
        "in_the_money": in_the_money
    })

def fetch_stock_data(symbol: str):
    db = SessionLocal()
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()

    yahoo_data = yfinance.Ticker(stock.symbol)
    exp_list = list(yahoo_data.options)
    strike = {}
    contract = {}
    price = {}
    profit = {}
    in_the_money = {}

    for i in exp_list:
        opt = yahoo_data.option_chain(i) 
        strike[i] = opt.calls['strike'] 
        strike_value = strike.values()
        strike_list = list(strike_value) 
        strike_price = [element * 100 for element in strike_list] 
        contract[i] = opt.calls['ask'] 
        contract_value = contract.values()
        contract_list = list(contract_value) 
        contract_price = [element * 10 for element in contract_list] 
        price = yahoo_data.info['previousClose'] 
        price_total = price * 100
        price_to_execute = list(map(add, strike_price, contract_price)) 
        profit = [element - price_total for element in price_to_execute]
        profit_large = profit * 100
        percent_profit = list(map(truediv, profit_large, price_to_execute))
        in_the_money[i] = opt.calls['inTheMoney']
        itm_value = in_the_money.values()
        itm_list = list(itm_value)
    
    stock.price = price_total
    exps = []
    for date in exp_list:
        exps.append(Expiration(symbol=stock.symbol, exp_list=date))
    
    df = pd.DataFrame(strike_price)
    strike_listee = df.values.tolist()
    strike_final = [[x for x in y if not np.isnan(x)] for y in strike_listee]
    c_df = pd.DataFrame(contract_price)
    contract_listee = c_df.values.tolist()
    contract_final = [[x for x in y if not np.isnan(x)] for y in contract_listee]
    p2e_df = pd.DataFrame(price_to_execute)
    p2e_listee = p2e_df.values.tolist()
    p2e_final = [[x for x in y if not np.isnan(x)] for y in p2e_listee]
    p_profit_df = pd.DataFrame(percent_profit)
    p_profit_listee = p_profit_df.values.tolist()
    p_profit_final = [[x for x in y if not np.isnan(x)] for y in p_profit_listee]
    itm_df = pd.DataFrame(itm_list)
    itm_listee = itm_df.values.tolist()
    itm_final = [[x for x in y if not np.isnan(x)] for y in itm_listee]
    strk = []
    for strike_group, contract_group, p2e_group, p_profit_group, itm_group, date in zip(strike_final, contract_final, p2e_final, p_profit_final, itm_final, exp_list):
        for strikes, contracts, p2es, p_profits, itms in zip(strike_group, contract_group, p2e_group, p_profit_group, itm_group):
            strk.append(Strike(symbol=stock.symbol, exp_list=date, strike_price=strikes, contract_price=contracts, price_to_execute=p2es, percent_profit=p_profits, in_the_money=itms))
  
    instances = [stock]
    instances.extend(exps)
    instances.extend(strk)

    db.add_all(instances)
    db.commit() 

@app.post("/stock")
async def create_stock(stock_request: StockRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    created a stock and stores it in the database
    """
    stock = Stock()

    stock.symbol = stock_request.symbol

    db.add(stock)
    db.commit()

    background_tasks.add_task(fetch_stock_data, stock.symbol)

    return {
        "code": "success",
        "message": "stock created"
    }
