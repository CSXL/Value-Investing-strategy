import pandas as pd
from iexfinance.stocks import Stock 
import requests 
import numpy as np
import math
class ValueInvesting:
  def __init__(self,stock_df,sk,pk):
    self.stocks = pd.read_csv(stock_df)
    self.Ticker = self.stocks['Ticker']
    self.features_1=[]
    self.key = sk 
    self.pk = pk
    self.Ticker = list(self.Ticker)
    self.QVS_dataframe_cols = 0
    self.cloud_API = 0
    self.features = []
    self.symbol_string = 0
  def get_price_data(self,stock_ticker):
    self.data = []
    for i in stock_ticker:
      try:
        stock_data = Stock(str(i),output_format='pandas',token=self.key).get_quote()
        self.data.append(stock_data['change']+stock_data['previousClose'])
        print(i)
      except:
        print('Unfound stock')
  def Process1(self):
    self.QVS_dataframe_cols = [
                      'symbols',
                      'price',
                      'Number of shares to buy',
                      'price-to-earning ratio',
                      'price-to-earning ratio percentile',
                      "price-to-book-value ratio",
                      'price-to-book-value ratio percentile',
                      'price-to-sales ratio',
                      'price-to-sales ratio percentile',
                      'ev-to-EBITDA ratio',
                      'ev-to-EBITDA ratio percentile',
                      'ev-to-gross profit ratio',
                      'ev-to-gross profit ratio percentile',
                      'Multiples score'
]
    self.QVS_dataframe = pd.DataFrame(columns=self.QVS_dataframe_cols)
    self.cloud_API = self.pk

  def chunk(self,lst,n):
    for i in range(0,len(lst),n):
      yield lst[i:i+n]
  def Process2(self):  
    symbol_group = list(self.chunk(self.Ticker,502))
    self.symbol_string = []
    for i in range(0,len(symbol_group)):
      self.symbol_string.append(','.join(symbol_group[i]))

    print(self.symbol_string[0])

  def book_and_sales_multiples(self):
    stock_list = []
    price_to_book_array =[]
    price_to_sales_array =[]
    price_to_earning_array = []
    for stock in 	self.symbol_string[0].split(","):
      try:

        data = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stock)+'&token='+str(self.key)).json()
        price_to_sales = data[stock]['advanced-stats']['priceToSales']
        price_to_book = data[stock]['advanced-stats']['priceToBook']
        price_to_earning = data[stock]['quote']['peRatio']
        price_to_book_array.append(price_to_book)
        price_to_sales_array.append(price_to_sales)
        stock_list.append(stock)
        price_to_earning_array.append(price_to_earning)
        print(stock)
        print(price_to_book,price_to_sales,price_to_earning)
      except:
        print('Unfound stock')
        price_to_book_array.append(0)
        price_to_sales_array.append(0) 
        stock_list.append(stock)
        price_to_earning_array.append(0)
    return stock_list,price_to_book_array,price_to_sales_array,price_to_earning_array




  def Process3(self):
    stocks,book_ratio,sales_ratio,earning_ratio = self.book_and_sales_multiples()
    self.QVS_dataframe['symbols'] = stocks
    self.QVS_dataframe['price-to-earning ratio'] = earning_ratio
    self.QVS_dataframe['price-to-book-value ratio'] = book_ratio
    self.QVS_dataframe['price-to-sales ratio']=sales_ratio
    for values in range(0,len(self.QVS_dataframe['ev-to-gross profit ratio']),1):
      try:
        stocks = self.QVS_dataframe['symbols'][values]
        data = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stocks)+'&token='+str(self.key)).json()
        self.QVS_dataframe.loc[values,'ev-to-gross profit ratio'] = (data[stocks]['advanced-stats']['enterpriseValue']/data[stocks]['advanced-stats']['grossProfit'])
        print(stocks)
      except:
        print('Unfound data')
        self.QVS_dataframe.loc[values,'ev-to-gross profit ratio'] = 0 

#data = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str('AAPL')+'&token='+str("Tsk_dfa0c966233d465bb823aac1c2d58a22"))
#QVS_dataframe['ev-to-EBITDA ratio']
  def Process4(self):
    for values in self.QVS_dataframe.index:
      try:
        stock = self.QVS_dataframe['symbols'][values]
    #QVS_dataframe.loc[values,'ev-to-EBITDA ratio'] = ev_to_ebitda_array_1[values]
        data = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stock)+'&token='+str(self.key)).json()
        self.QVS_dataframe.loc[values,'ev-to-EBITDA ratio'] = float(data[stock]['advanced-stats']['enterpriseValue']/data[stock]['advanced-stats']['EBITDA'])
      except:
        self.QVS_dataframe.loc[values,'ev-to-EBITDA ratio']  = 0
        print('Unfound data')
    self.features = ['price-to-earning ratio','price-to-book-value ratio','price-to-sales ratio','ev-to-EBITDA ratio',"ev-to-gross profit ratio"]
    for feature in self.features:
      self.QVS_dataframe[feature].fillna(0)  
      print(self.QVS_dataframe)

  def Process5(self):
    index = 0
    for data in self.QVS_dataframe['ev-to-EBITDA ratio']:
      try:
        if data == 0:
          stock = self.QVS_dataframe.loc[index,'symbols']
          print(stock)
          batch_api = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stock)+'&token='+str(self.key)).json()
          self.QVS_dataframe.loc[index,'ev-to-EBITDA ratio'] = float(batch_api[stock]['advanced-stats']['enterpriseValue']/batch_api[stock]['advanced-stats']['EBITDA'])
          index +=1
      except:
        print(stock,'Unfound data')

  def fill_holes_for_ev_as_numerator(self,df,feature,jsonkey1,jsonkey2,jsonkey3,jsonkey4):
    while (df.loc[df[feature]==0]):
      for i in df.index:
        stock = df.loc[i,'symbols']
        if(df.loc[i,feature] == 0):
          try:
            batch_api = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stock)+'&token='+str(self.key)).json()
            df.loc[i,feature] = batch_api[stock][jsonkey1][jsonkey2]/batch_api[stock][jsonkey3][jsonkey4]
          except:
            print('could not do process')
    nan_df = (df.loc[df[feature]]==0)
    for i in nan_df.index:
      stock = nan_df.loc[i,'symbols']
      if(nan_df.loc[i,feature] == 0):
        try:
          batch_api = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stock)+'&token='+str(self.key)).json()
          nan_df.loc[i,feature] = batch_api[stock][jsonkey1][jsonkey2]/batch_api[stock][jsonkey3][jsonkey4]
        except:
          print('could not do proces')
    for i in list(nan_df.index):
      df.loc[i,feature] = nan_df.loc[i,feature]
    print(self.QVS_dataframe.columns)
    
  def fill_holes(self,df,feature,jsonkey1,jsonkey2):
    while (df.loc[df[feature]==0]):
      for i in df.index:
        stock = df.loc[i,'symbols']
        if(df.loc[i,feature] == 0):
          try:
            batch_api = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stock)+'&token='+str(self.key)).json()
            df.loc[i,feature] = batch_api[stock][jsonkey1][jsonkey2]
          except:
            print('could not do process')
    nan_df = (df.loc[df[feature]]==0)
    for i in nan_df.index:
      stock = nan_df.loc[i,'symbols']
      if(nan_df.loc[i,feature] == 0):
        try:
          batch_api = requests.get('https://cloud.iexapis.com/stable/stock/market/batch/?types=advanced-stats,stats,quote&symbols='+str(stock)+'&token='+str(self.key)).json()
          nan_df.loc[i,feature] = batch_api[stock][jsonkey1][jsonkey2]
        except:
          print('could not do proces')
    for i in list(nan_df.index):
      df.loc[i,feature] = nan_df.loc[i,feature]
    print(self.QVS_dataframe.columns)

  def Process6(self):
    self.fill_holes(self.QVS_dataframe,'price-to-earning ratio','quote','peRatio')
    self.fill_holes(self.QVS_dataframe,'price-to-book-value ratio','advanced-stats','priceToBook')
    self.fill_holes(self.QVS_dataframe,'price-to-sales ratio','advanced-stats','priceToSales')
    self.fill_holes_for_ev_as_numerator(self.QVS_dataframe,'ev-to-gross profit ratio','advanced-stats','enterpriseValue','advanced-stats','grossProfit')

    self.features_1 = ["price-to-earning ratio","price-to-book-value ratio","price-to-sales ratio","ev-to-EBITDA ratio","ev-to-gross profit ratio"]
    import scipy
    for row in self.QVS_dataframe.index:
      for feature in self.features_1:
        a = self.QVS_dataframe[feature]
        b = self.QVS_dataframe.loc[row,feature]
        print(feature+str('percentile'))
        self.QVS_dataframe.loc[row,feature+str(' percentile')] = scipy.stats.percentileofscore(a,b)


    for row in self.QVS_dataframe.index:
      avgpercentile = []
      for feature in self.features_1:
        avgpercentile.append(self.QVS_dataframe.loc[row,feature+str(' percentile')])
        self.QVS_dataframe.loc[row,'Multiples score'] = float(np.mean(avgpercentile))
    
    print(self.QVS_dataframe)
  def Process7(self):
    QVS_dataframe=QVS_dataframe.loc[self.QVS_dataframe['Multiples score']>np.mean(self.QVS_dataframe['Multiples score'])]

    price_info = list(self.get_price_data(self.Ticker))

    pi = []
    for price in price_info:
      __price__ = price
      __price__ = float(__price__)
      print(__price__)
      pi.append(__price__)

    self.QVS_dataframe['price'] = pi

    portfolio_budget = float(input("How much is your portfolio budget?"))
    portfolio_size = float(portfolio_budget/70)
    portfolio_size
    for i in QVS_dataframe.index:
      self.QVS_dataframe.loc[i,'Number of shares to buy'] = portfolio_size/self.Process3QVS_dataframe.loc[i,'price']

    self.QVS_dataframe = QVS_dataframe.sort_index(by=['Multiples score'],ascending=False,inplace=True)
    print(self.QVS_dataframe)
