# %%
from numpy import dtype
import pandas as pd
# %%
#data read
df = pd.read_csv('./souce/GBPUSD202102.csv')
df.tail(2)
# %%
#data read
usecols = ['time','open_bid','high_bid','low_bid','close_bid','open_ask','high_ask','low_ask','close_ask']
df = pd.read_csv('./souce/GBPUSD202102.csv',usecols=usecols,index_col='time',parse_dates=True)
df.head()
# renameColumes = ['OpenBid','HighBid','LowBid','ClobseBid','OpenAsk','HighAsk','LowAsk','CloseAsk']
# df.columns = renameColumes
# df.columns
# %%
