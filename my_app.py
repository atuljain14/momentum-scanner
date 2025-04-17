import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import numpy as np


session = requests.sessions.Session()
session.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
session.get('https://www.nseindia.com', timeout=10)
url = "https://www.nseindia.com/api/equity-stockIndices?index="


col1, col2 = st.columns([1, 3])
with col1:
    st.subheader("Configuration",divider="gray")

    # Options for the dropdown
    options = ["NIFTY 50", "NIFTY NEXT 50", "NIFTY MICROCAP 250"]

    # Create the dropdown menu
    selected_index = st.selectbox("Select an index:", options)

    short_timeframe = st.select_slider(
        "Select a short term momentum weightage",
        options=[
            "0","10",
            "20",
            "30",
            "40",
            "50", "60", "70", "80", "90", "100"
        ], value="20"
    )

    med_timeframe = st.select_slider(
        "Select a medium term momentum weightage",
        options=[
            "0","10",
            "20",
            "30",
            "40",
            "50", "60", "70", "80", "90", "100"
        ],value="20"
    )

    long_timeframe = st.select_slider(
        "Select a long term momentum weightage",
        options=[
            "0","10",
            "20",
            "30",
            "40",
            "50", "60", "70", "80", "90", "100"
        ],value="60"
    )

    total_weight = int(short_timeframe) + int(long_timeframe) + int(med_timeframe)
    date = st.date_input("Select a date")

    is_run = st.button(label="Run Scan")

@st.cache_data
def fetch_index_data_from_nse(symbol):
  df=pd.DataFrame()
  res=session.get(url + symbol, timeout=10)
  if res.status_code == 200:
      res_json = res.json()
      if 'data' in res_json:
        df = pd.DataFrame(pd.json_normalize(res_json['data']))
  else:
    st.error("Error in fetching index data from NSE.. Please try again")
  df.rename(columns={'symbol': 'Symbol', 'lastPrice': 'Close'},inplace=True)
  df.Symbol = df.Symbol.apply(lambda x: x + '.NS')
  df_clean  = pd.DataFrame(df[1:][['Symbol', 'Close']])
  return df_clean 

def reformat_data(data):
  df = pd.DataFrame(data['Close'].reset_index())
  data_dict = {}

  for symbol in df.columns:
    ## Skip Date Column
    if symbol == 'Date':
      continue
    new_df = pd.DataFrame(df[['Date', symbol]].rename(columns={symbol:'Close'}))
    if(new_df['Close'].count()>246):
      print("dalala")
      data_dict[symbol] = new_df  
  return data_dict


@st.cache_data
def fetch_data_from_yahoo(df):
  symbols = []
  for symbol in df.Symbol:
    symbols.append(symbol)
  data = yf.download(symbols, interval='1d', period='1y', multi_level_index=False)
  #st.dataframe(data)
  formated_data = reformat_data(data)

  return formated_data

def compute_daily_returns(stock_df):
   stock_df['1D Returns'] = stock_df.Close.pct_change()

def compute_std_dev(stock_df):
   return stock_df['1D Returns'].std() * np.sqrt(252)
   

def compute_weekly_returns_and_mom_score(stock_df, std_dev):
   stock_df['1W Returns'] = stock_df.Close.pct_change(periods=5)
   stock_df['1W MoM Score'] = stock_df['1W Returns']/std_dev

def compute_monthly_returns_and_mom_score(stock_df, std_dev):
   stock_df['1M Returns'] = stock_df.Close.pct_change(periods=20)
   stock_df['1M MoM Score'] = stock_df['1M Returns']/std_dev   

def compute_3monthly_returns_and_mom_score(stock_df, std_dev):
   stock_df['3M Returns'] = stock_df.Close.pct_change(periods=60)
   stock_df['3M MoM Score'] = stock_df['3M Returns']/std_dev   

def compute_weekly_z_score(stock_df, mean, sd):
   stock_df['1W Z-Score'] = (stock_df['1W MoM Score'] - mean)/sd

def compute_monthly_z_score(stock_df, mean, sd):
   stock_df['1M Z-Score'] = (stock_df['1M MoM Score'] - mean)/sd

def compute_3monthly_z_score(stock_df, mean, sd):
   stock_df['3M Z-Score'] = (stock_df['3M MoM Score'] - mean)/sd

def compute_wzscore(stock_df):
   stock_df['WZ-Score'] = (int(short_timeframe)/100) * stock_df['1W Z-Score'] + (int(med_timeframe)/100) * stock_df['1M Z-Score'] + (int(long_timeframe)/100) * stock_df['3M Z-Score']
   normalized_score = []
   for score in stock_df['WZ-Score']:
    if score >= 0:
      normalized_score.append(1 + score) # Use score instead of the whole column
    else:
      normalized_score.append(1 / (1 - score)) # Use score instead of the whole column
   stock_df['Normalized Z Score'] = normalized_score



def start():
    index_df = fetch_index_data_from_nse(selected_index)
    all_data = fetch_data_from_yahoo(index_df)
    for stock_df in all_data.values():
       compute_daily_returns(stock_df)
       std_dev = compute_std_dev(stock_df)
       compute_weekly_returns_and_mom_score(stock_df, std_dev)       
       compute_monthly_returns_and_mom_score(stock_df, std_dev)
       compute_3monthly_returns_and_mom_score(stock_df, std_dev)
    
    week_mom_ratios = []
    m1_mom_ratios = []
    m3_mom_ratios = []
    for stock_df in all_data.values():
      week_mom_ratios.append(stock_df.iloc[-1]['1W MoM Score'])
      m1_mom_ratios.append(stock_df.iloc[-1]['1M MoM Score'])
      m3_mom_ratios.append(stock_df.iloc[-1]['3M MoM Score'])
    
    print(np.isnan(week_mom_ratios))

    weekly_mom_ratio_mean = np.mean(week_mom_ratios)
    m1_mom_ratio_mean = np.mean(m1_mom_ratios)
    m3_mom_ratio_mean = np.mean(m3_mom_ratios)

    weekly_mom_ratio_std = np.std(week_mom_ratios)
    m1_mom_ratio_std = np.std(m1_mom_ratios)
    m3_mom_ratio_std = np.std(m3_mom_ratios)

    print(weekly_mom_ratio_mean)
    print(m1_mom_ratio_mean)

    for stock_df in all_data.values():
      compute_weekly_z_score(stock_df, weekly_mom_ratio_mean,weekly_mom_ratio_std)
      compute_monthly_z_score(stock_df, m1_mom_ratio_mean,m1_mom_ratio_std)
      compute_3monthly_z_score(stock_df, m3_mom_ratio_mean, m3_mom_ratio_std)
      compute_wzscore(stock_df)
      
    final_list = []

    final_df = pd.DataFrame(columns=['Stock', 'Score'])
    for key, value in all_data.items():
      last_z_score = value.iloc[-1]['Normalized Z Score']
      final_list.append({"Stock": key, "Score": last_z_score})

    st.dataframe(pd.DataFrame(final_list).sort_values(by='Score', ascending=False).head(10)) 
    #st.dataframe(all_data['AARTIDRUGS.NS'])


with col2:
    if(is_run):
        if(total_weight!=100):
            st.error("The total weight of momentum should be 100 across short, medium and long term")
        else:
            print("button pressed.. Calculation will be done.")
            start()
            #st.write(selected_index + " " + short_timeframe + " " + med_timeframe + " " + long_timeframe + " ")
    else:
        print("button not pressed")

