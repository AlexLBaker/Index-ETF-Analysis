import fredapi
import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

# Select indices for the analysis.
tickers = ['^GSPC', '^DJI', '^IXIC', '^RUT', '^SP400', '^SP600', 'SWTSX']
names = ['S&P 500', 'Dow Jones', 'NASDAQ', 'Russell 2000', 'S&P 400', 'S&P 600', 'Schwab Total']

# Set dates for the time period.
start_date = '2005-01-01'
end_date = '2023-01-01'

# Initialize FRED API with private key.
fred = fredapi.Fred(api_key='687db299c439e1b9b04416d1b4eae9c7')

# Fetch risk-free rate and calculate monthly inflation rate.
rf_series = fred.get_series('TB3MS', start_date, end_date) / 12 / 100 
cpi = fred.get_series('CPIAUCSL', start_date, end_date)
inflation_series = cpi.pct_change()

results = []

# use forloop to iterate over tickers.
for name, symbol in zip(names, tickers):

    try:
    # Fetch data from Yahoo Finance.
        print(f"Processing symbol {symbol}...")
        df_index = yf.download(symbol, start=start_date, end=end_date, interval='1mo')

    except Exception as e:
        print(f"An error occurred when processing {symbol}: {e}")
        continue

    # Calculate nominal returns as a growth factor with percent change between elements.
    df_index['return'] = df_index['Adj Close'].pct_change() + 1

    # Calculate real and excess returns.
    df_index['real_return'] = ((1 + df_index['return'])/(1 + inflation_series)) - 1
    df_index['excess_return'] = df_index['return'] - 1 - rf_series

    # Calculate the geometric mean of monthly growth factors.
    geom_mean_nominal = df_index['return'].prod()**(1/df_index['return'].count())
    geom_mean_real = df_index['real_return'].prod()**(1/df_index['real_return'].count())
    geom_mean_excess = geom_mean_real - rf_series.mean()

    # Annualize the returns and convert from growth factor to percentage.
    average_annual_nominal_return = (geom_mean_nominal**12) - 1
    average_annual_real_return = (geom_mean_real**12) - 1
    average_annual_excess_return = average_annual_real_return - rf_series.mean()*12

    # Calculate risk measures adjusted for monthly data.
    std_dev = df_index['excess_return'].std() * np.sqrt(12)
    sharpe_ratio = average_annual_excess_return / std_dev

    results.append({
        'index': name,
        'ticker': symbol,
        'nominal return': average_annual_nominal_return,
        'real return': average_annual_real_return,
        'risk premium': average_annual_excess_return,
        'std. dev.': std_dev,
        'sharpe ratio': sharpe_ratio
    })

# Convert results to a DataFrame.
results_df = pd.DataFrame(results)

# Export to .csv file for reports.
start_year = start_date[:4]
end_year = end_date[:4]
file_name = f"Indices {start_year}-{end_year}.csv"
directory = "/Users/alb/Documents/GitHub/Financial-Models/Reports"
    
# use os.path.join to combine the directory and file name.
full_path = os.path.join(directory, file_name)
results_df.to_csv(full_path, index=False)