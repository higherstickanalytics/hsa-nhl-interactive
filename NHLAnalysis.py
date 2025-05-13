import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load data
skaters_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
goalies_path = 'data/hockey_data/combined_goalies_hockey_game_logs.csv'
schedule_path = 'data/NHL_Schedule.csv'

skaters_df = pd.read_csv(skaters_path, parse_dates=['Date'], dayfirst=False)
goalies_df = pd.read_csv(goalies_path, parse_dates=['Date'], dayfirst=False)

# App Title
st.title("Hockey Data Viewer with Pie Charts")
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

# Threshold input
max_val = player_df[selected_stat].max()
default_thresh = player_df[selected_stat].median()
threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(max_val), value=float(default_thresh), step=0.5)

# Pie chart for player stats
st.subheader(f"{selected_stat_display} Value Distribution for {selected_player}")

# Count the values above, below, and equal to the threshold
above_threshold = player_df[player_df[selected_stat] > threshold]
below_threshold = player_df[player_df[selected_stat] < threshold]
equal_threshold = player_df[player_df[selected_stat] == threshold]

sizes = [len(above_threshold), len(below_threshold), len(equal_threshold)]
labels = [
    f"Green (Above {threshold} {selected_stat_display})",
    f"Red (Below {threshold} {selected_stat_display})",
    f"Gray (Equal to {threshold} {selected_stat_display})"
]
colors = ['green', 'red', 'gray']

# Pie chart creation
fig1, ax1 = plt.subplots()
wedges, texts, autotexts = ax1.pie(
    sizes,
    labels=labels,
    autopct='%1.1f%%',
    startangle=140,
    colors=colors,
    textprops={'fontsize': 10},
    pctdistance=0.85  # Move the percentage outside the pie chart
)

# Adjust label and percentage positions
for text in texts:
    text.set_fontsize(10)
for autotext in autotexts:
    autotext.set_fontsize(10)
    # Get the current position (coordinates)
    x, y = autotext.get_position()
    autotext.set_position((x * 1.1, y * 1.1))  # Move percentages outward

ax1.axis('equal')  # Equal aspect ratio ensures pie chart is drawn as a circle.
ax1.set_title(f"{selected_stat_display} Value Distribution")
st.pyplot(fig1)

# Show percentage table
total_games = len(player_df)
if total_games > 0:
    green_percent = (len(above_threshold) / total_games) * 100
    red_percent = (len(below_threshold) / total_games) * 100
    gray_percent = (len(equal_threshold) / total_games) * 100

    data = {
        'Category': ['Above Threshold', 'Below Threshold', 'Equal to Threshold'],
        'Count': [len(above_threshold), len(below_threshold), len(equal_threshold)],
        'Percentage': [f"{green_percent:.2f}%", f"{red_percent:.2f}%", f"{gray_percent:.2f}%"]
    }
    df_percent = pd.DataFrame(data)
    st.table(df_percent)
else:
    st.write("No data available in selected date range.")
