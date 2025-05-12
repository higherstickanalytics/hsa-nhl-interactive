import streamlit as st
import pandas as pd

# Title of the app
st.title("Hockey Data Viewer")

# Load skater data
skaters_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
skaters_df = pd.read_csv(skaters_path, parse_dates=['Date'], dayfirst=False)

# Load goalie data
goalies_path = 'data/hockey_data/combined_goalies_hockey_game_logs.csv'
goalies_df = pd.read_csv(goalies_path, parse_dates=['Date'], dayfirst=False)

# Load NHL schedule
schedule_path = 'data/NHL_Schedule.csv'
schedule_df = pd.read_csv(schedule_path, parse_dates=['Date'], dayfirst=False)

# Display first 5 rows of each
st.subheader("First 5 Rows of Skaters Data")
st.dataframe(skaters_df.head())

st.subheader("First 5 Rows of Goalies Data")
st.dataframe(goalies_df.head())

st.subheader("First 5 Rows of NHL Schedule")
st.dataframe(schedule_df.head())
