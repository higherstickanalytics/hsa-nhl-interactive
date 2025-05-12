import streamlit as st
import pandas as pd

# Paths to the files
skaters_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
goalies_path = 'data/hockey_data/combined_goalies_hockey_game_logs.csv'
schedule_path = 'data/NHL_Schedule.csv'

# Load the data
skaters_df = pd.read_csv(skaters_path)
goalies_df = pd.read_csv(goalies_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['DATE'], dayfirst=False)

# Title of the app
st.title("Hockey Data Viewer")

# Display the first 5 rows of each dataset
st.subheader("First 5 Rows of Skaters Data")
st.dataframe(skaters_df.head())

st.subheader("First 5 Rows of Goalies Data")
st.dataframe(goalies_df.head())

st.subheader("First 5 Rows of NHL Schedule Data")
st.dataframe(schedule_df.head())
