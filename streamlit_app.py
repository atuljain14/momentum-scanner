import streamlit as st
import pandas as pd
import yfinance as yf
import requests


session = requests.sessions.Session()
session.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
session.get('https://www.nseindia.com', timeout=10)
url = "https://www.nseindia.com/api/equity-stockIndices?index="

@st.cache_data
def fetch_data_from_nse(symbol):
  df=[]
  res=session.get(url + symbol, timeout=10)
  if res.status_code == 200:
      res_json = res.json()
      if 'data' in res_json:
        df = pd.json_normalize(res_json['data'])
  else:
    print('error')
  print('fir se aa gya')
  return df

@st.cache_data
def fetch_data_from_yahoo(df):
  symbols = []
  for symbol in df.Symbol:
    symbols.append(symbol)
  data = yf.download(symbols, interval='1d', period='1y')

  return data

@st.cache_data
def reformat_data(data):
  df = pd.DataFrame(data['Close'].reset_index())
  data_dict = {}

  for symbol in df.columns:
    ## Skip Date Column
    if symbol == 'Date':
      continue
    new_df = pd.DataFrame(df[['Date', symbol]].rename(columns={symbol:'Close'}))
    data_dict[symbol] = new_df
    print('eeeeeeeeeeeeopaopwodpwodpwedopewope')    
  return data_dict

# Title for the app
st.title("Select Index")

# Options for the dropdown
options = ["NIFTY 50", "NIFTY NEXT 50", "NIFTY MICROCAP 250"]

# Create the dropdown menu
selected_option = st.selectbox("Select a index:", options)
index = selected_option

short_timeframe = st.select_slider(
    "Select a short term momentum percentage",
    options=[
        "10",
        "25",
        "50",
        "75",
        "100",
    ],
)

med_timeframe = st.select_slider(
    "Select a medium term momentum percentage",
    options=[
        "10",
        "25",
        "50",
        "75",
        "100",
    ],
)

long_timeframe = st.select_slider(
    "Select a long term momentum percentage",
    options=[
        "10",
        "25",
        "50",
        "75",
        "100",
    ],
)

if(int(short_timeframe) + int(med_timeframe) + int(long_timeframe) != 100):
  st.error("Sum should be 100")

#index = "NIFTY 50"
index_data = fetch_data_from_nse(index)
df = pd.DataFrame(index_data)
df = df.rename(columns={'symbol': 'Symbol', 'lastPrice': 'Close'})
df.Symbol = df.Symbol.apply(lambda x: x + '.NS')
df_clean  = pd.DataFrame(df[1:][['Symbol', 'Close']])

data = fetch_data_from_yahoo(df_clean)

all_data = reformat_data(data)
from scipy import stats
import numpy as np
for df in all_data.values():
  
  df['Daily Returns'] = df.Close.pct_change()
  std_dev = df['Daily Returns'].std() * np.sqrt(252)

  df['Weekly Returns'] = df.Close.pct_change(periods=5)
  df['Weekly MoM Score'] = df['Weekly Returns']/std_dev
  week_mean = df['Weekly MoM Score'].mean()
  df['Weekly Z-Score'] = (df["Weekly MoM Score"] - week_mean) / std_dev
  #df['Weekly Z-Score'] = stats.zscore(df['Weekly Returns'],nan_policy='omit')
  df['Monthly Returns'] = df.Close.pct_change(periods=20)
  df['Monthly MoM Score'] = df['Monthly Returns']/std_dev
  mon_mean = df['Monthly MoM Score'].mean()
  df['Monthly Z-Score'] = (df["Monthly MoM Score"] - mon_mean) / std_dev
  
  
  df['3M Returns'] = df.Close.pct_change(periods=60)
  df['3M MoM Score'] = df['3M Returns']/std_dev

  m3_mean = df['3M MoM Score'].mean()
  df['3M Z-Score'] = (df["3M MoM Score"] - m3_mean) / std_dev

  df['6M Returns'] = df.Close.pct_change(periods=120)
  df['6M MoM Score'] = df['6M Returns']/std_dev

  m6_mean = df['6M MoM Score'].mean()
  df['6M Z-Score'] = (df["6M MoM Score"] - m6_mean) / std_dev

  df['12M Returns'] = df.Close.pct_change(periods=240)
  df['12M MoM Score'] = df['12M Returns']/std_dev

  m12_mean = df['12M MoM Score'].mean()
  df['12M Z-Score'] = (df["12M MoM Score"] - m12_mean) / std_dev

  df['W Z-Score'] = 0.5*df['Monthly Z-Score'] + 0.5 * df['3M Z-Score']

  # Iterate over the 'Weighted Z Score' column
  normalized_z_score = []
  for score in df['W Z-Score']:
    if score >= 0:
      normalized_z_score.append(1 + score) # Use score instead of the whole column
    else:
      normalized_z_score.append(1 / (1 - score)) # Use score instead of the whole column
  df['Normalized Z Score'] = normalized_z_score

final_list = []

final_df = pd.DataFrame(columns=['Stock', 'Score'])
for key, value in all_data.items():
  
  #final_df['Stock'] = key
  #final_df['Score'] = value.iloc[-1]['Normalized Z Score']
  last_z_score = value.iloc[-1]['Normalized Z Score']
  final_list.append({"Stock": key, "Score": last_z_score})



st.dataframe(pd.DataFrame(final_list)) 
st.dataframe(all_data['EICHERMOT.NS'])

#st.dataframe(all_data['RELIANCE.NS'])
#st.dataframe(all_data['INFY.NS'])
#st.dataframe(yf.tickers('INFY.NS', interval='1d', period='1y'))
st.button("Rerun")