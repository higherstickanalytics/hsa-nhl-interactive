import streamlit as st
import pandas as pd

# Title of the app
st.title("Hockey Skaters Data Viewer")

# Load the data using pandas
data_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
skaters_df = pd.read_csv(data_path, parse_dates=['Date'], date_parser=lambda x: pd.to_datetime(x, format='%m/%d/%y'))

# Display the first 5 rows
st.subheader("First 5 Rows of Skaters Data")
st.dataframe(skaters_df.head())
