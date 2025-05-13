import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load data
skaters_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
goalies_path = 'data/hockey_data/combined_goalies_hockey_game_logs.csv'
schedule_path = 'data/NHL_Schedule.csv'

skaters_df = pd.read_csv(skaters_path, parse_dates=['Date'], dayfirst=False)
goalies_df = pd.read_csv(goalies_path, parse_dates=['Date'], dayfirst=False)

# App Title
st.title("Hockey Data Viewer with Histograms")
st.write("Data from [Hockey Reference](https://www.hockey-reference.com/)")

# Sidebar: select position
position = st.sidebar.radio("Select Player Position", ['Skater', 'Goalie'])

if position == 'Skater':
    df = skaters_df
    stats = ['G.1', 'SOG', 'A', 'PTS', 'BLK']
    stat_names = ['Goals', 'Shots on Goal', 'Assists', 'Points', 'Blocked Shots']
else:
    df = goalies_df
    stats = ['SV', 'GA', 'SA']
    stat_names = ['Saves', 'Goals Against', 'Shots Against']

# Sidebar: player and stat selection
player_list = df['Player'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))
selected_stat_display = st.sidebar.selectbox("Select a statistic:", stat_names)
selected_stat = stats[stat_names.index(selected_stat_display)]

# Sidebar: date filter
min_date = df['Date'].min()
max_date = df['Date'].max()

start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))

# Filter data
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
player_df = df[df['Player'] == selected_player]
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce').dropna()

# Histogram threshold
max_val = player_df[selected_stat].max()
default_thresh = player_df[selected_stat].median()
threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(max_val), value=float(default_thresh), step=0.5)

# Distribution Histogram
st.subheader(f"{selected_stat_display} Distribution for {selected_player}")
fig1, ax1 = plt.subplots()
n, bins, patches = ax1.hist(player_df[selected_stat], bins=20, edgecolor='black')

for patch, left, right in zip(patches, bins[:-1], bins[1:]):
    center = (left + right) / 2
    if center > threshold:
        patch.set_facecolor('green')
    elif center < threshold:
        patch.set_facecolor('red')
    else:
        patch.set_facecolor('gray')

ax1.set_title(f"{selected_stat_display} Distribution")
ax1.set_xlabel(selected_stat_display)
ax1.set_ylabel("Frequency")
st.pyplot(fig1)

# Time-Series Histogram
st.subheader(f"{selected_stat_display} Over Time for {selected_player}")
fig2, ax2 = plt.subplots(figsize=(12, 6))
data = player_df[['Date', selected_stat]].dropna()
bars = ax2.bar(data['Date'], data[selected_stat], color='gray', edgecolor='black')

count_above = 0
for bar, val in zip(bars, data[selected_stat]):
    if val > threshold:
        bar.set_color('green')
        count_above += 1
    elif val < threshold:
        bar.set_color('red')
    else:
        bar.set_color('gray')
        count_above += 1

ax2.axhline(y=threshold, color='blue', linestyle='--', linewidth=2, label=f'Threshold: {threshold}')
ax2.set_xlabel("Date")
ax2.set_ylabel(selected_stat_display)
ax2.set_title(f"{selected_stat_display} Over Time")
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax2.legend()
st.pyplot(fig2)

# Proportion summary
total_games = len(data)
if total_games > 0:
    st.write(f"Games at or above threshold: {count_above}/{total_games} ({count_above / total_games:.2%})")
else:
    st.write("No data available in selected date range.")
