import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Load combined data (skaters + goalies)
data_path = 'data/hockey_data/nhl_player_game_logs_2024_2025.csv'
df = pd.read_csv(data_path, parse_dates=['gameDate'], dayfirst=False)

# Identify goalies vs skaters by checking if any goalie-specific stat columns are non-NaN
goalie_cols = ['gamesStarted', 'decision', 'shotsAgainst', 'goalsAgainst', 'savePctg', 'shutouts']
# Create mask for goalie rows (if any goalie stat is not NaN)
goalie_mask = df[goalie_cols].notna().any(axis=1)

goalies_df = df[goalie_mask].copy()
skaters_df = df[~goalie_mask].copy()

# App Title
st.title("Hockey Data Viewer with Pie and Time-Series Charts (2024-2025 Season)")
st.write("Data from [Hockey Reference](https://www.hockey-reference.com/)")

# Sidebar: select position
position = st.sidebar.radio("Select Player Position", ['Skater', 'Goalie'])

if position == 'Skater':
    df = skaters_df
    stats = ['goals', 'assists', 'points', 'shots', 'plusMinus']
    stat_names = ['Goals', 'Assists', 'Points', 'Shots', 'Plus/Minus']
else:
    df = goalies_df
    # Calculate Saves as rounded product of savePctg and shotsAgainst (handle NaNs safely)
    df['Saves'] = (df['savePctg'] * df['shotsAgainst']).round()
    stats = ['shotsAgainst', 'goalsAgainst', 'Saves']
    stat_names = ['Shots Against', 'Goals Against', 'Saves']

# Sidebar: player and stat selection
player_list = df['full_name'].dropna().unique().tolist()  # use 'full_name' column for player name
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))
selected_stat_display = st.sidebar.selectbox("Select a statistic:", stat_names)
selected_stat = stats[stat_names.index(selected_stat_display)]

# Sidebar: date filter
df['gameDate'] = pd.to_datetime(df['gameDate'], errors='coerce')
min_date = df['gameDate'].min()
max_date = df['gameDate'].max()
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))

# Filter data by player and date range
df = df[(df['gameDate'] >= start_date) & (df['gameDate'] <= end_date)]
player_df = df[df['full_name'] == selected_player].copy()
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce')
player_df = player_df.dropna(subset=[selected_stat])

# Histogram threshold and charts
if not player_df.empty:
    max_val = player_df[selected_stat].max()
    default_thresh = player_df[selected_stat].median()
    threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(max_val), value=float(default_thresh), step=0.5)

    # Pie Chart
    st.subheader(f"{selected_stat_display} Distribution for {selected_player}")
    stat_counts = player_df[selected_stat].value_counts().sort_index()
    labels = [f"{int(val)}" if val == int(val) else f"{val:.1f}" for val in stat_counts.index]
    sizes = stat_counts.values

    colors = []
    color_categories = {'green': 0, 'red': 0, 'gray': 0}
    for val, count in zip(stat_counts.index, stat_counts.values):
        if val > threshold:
            colors.append('green')
            color_categories['green'] += count
        elif val < threshold:
            colors.append('red')
            color_categories['red'] += count
        else:
            colors.append('gray')
            color_categories['gray'] += count

    fig1, ax1 = plt.subplots()
    wedges, texts, autotexts = ax1.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=140,
        colors=colors, textprops={'fontsize': 10}
    )
    ax1.axis('equal')
    ax1.set_title(f"{selected_stat_display} Value Distribution")
    st.pyplot(fig1)

    # Pie Chart Breakdown
    total_entries = sum(color_categories.values())
    if total_entries > 0:
        st.markdown("**Pie Chart Color Breakdown:**")
        breakdown_df = pd.DataFrame({
            'Color': ['🟩 Green', '🟥 Red', '⬜ Gray'],
            'Category': [
                f"Above {threshold} {selected_stat_display}",
                f"Below {threshold} {selected_stat_display}",
                f"At {threshold} {selected_stat_display}"
            ],
            'Count': [
                color_categories['green'],
                color_categories['red'],
                color_categories['gray']
            ],
            'Percentage': [
                f"{color_categories['green'] / total_entries:.2%}",
                f"{color_categories['red'] / total_entries:.2%}",
                f"{color_categories['gray'] / total_entries:.2%}"
            ]
        })
        st.table(breakdown_df)
    else:
        st.write("No data available to display pie chart.")

    # Time Series
    st.subheader(f"{selected_stat_display} Over Time for {selected_player}")
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    data = player_df[['gameDate', selected_stat]].dropna()
    bars = ax2.bar(data['gameDate'], data[selected_stat], color='gray', edgecolor='black')

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

    st.write(f"Games at or above threshold: {count_above}/{len(data)} ({count_above / len(data):.2%})")
else:
    st.warning("No data available for the selected player and date range.")
