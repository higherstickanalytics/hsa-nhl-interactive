import streamlit as st
import pandas as pd

# Assuming this function is defined elsewhere and imported correctly
from your_module import load_and_preprocess_data  # Replace with actual module name

# Title of the app
st.title("Hockey Skaters and Goalies Data Viewer")

# Load and preprocess the skaters data
skaters_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
skaters_df = load_and_preprocess_data(skaters_path, 'Date', '%m/%d/%y')

# Load and preprocess the goalies data
goalies_path = 'data/hockey_data/combined_goalies_hockey_game_logs.csv'
goalies_df = load_and_preprocess_data(goalies_path, 'Date', '%m/%d/%y')

# Load and preprocess the NHL schedule
schedule_path = 'data/NHL_Schedule.csv'
schedule_df = load_and_preprocess_data(schedule_path, 'Date', '%m/%d/%y')

# Display first 5 rows of skaters data
st.subheader("First 5 Rows of Skaters Data")
st.dataframe(skaters_df.head())

# Display first 5 rows of goalies data
st.subheader("First 5 Rows of Goalies Data")
st.dataframe(goalies_df.head())

# Display first 5 rows of NHL schedule
st.subheader("First 5 Rows of NHL Schedule")
st.dataframe(schedule_df.head())
