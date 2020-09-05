import pandas as pd
from pandas import DataFrame as df

filename = r'filtr.xlsx'

export = pd.read_excel(filename)

symbol = []
symbol = list(df['Symbol'])
print(symbol)