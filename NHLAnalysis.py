import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load data
data_path = 'data/hockey_data/nhl_player_game_logs_2024_2025.csv'
try:
    df = pd.read_csv(data_path, parse_dates=['gameDate'], dayfirst=False)
except FileNotFoundError:
    st.error(f"Could not find the file: {data_path}. Please ensure the file is in the correct directory ('data/hockey_data/') and the path is correct.")
    st.stop()

# Clean the gameDate column to handle NaT values
df['gameDate'] = pd.to_datetime(df['gameDate'], errors='coerce')
df = df.dropna(subset=['gameDate'])  # Remove rows where gameDate is NaT

# Split into skaters and goalies based on position
skaters_df = df[df['position'].isin(['C', 'LW', 'RW', 'D'])]  # Centers, Left/Right Wings, Defensemen
goalies_df = df[df['position'] == 'G']  # Goalies

# App Title
st.title("Hockey Data Viewer with Pie and Time-Series Charts")
st.write("Data from NHL API")

# Sidebar: select position
position = st.sidebar.radio("Select Player Position", ['Skater', 'Goalie'])

if position == 'Skater':
    df = skaters_df
    stats = ['goals', 'assists', 'points', 'shots', 'plusMinus']
    stat_names = ['Goals', 'Assists', 'Points', 'Shots', 'Plus/Minus']
else:
    df = goalies_df
    df["Saves"] = round(df["savePctg"] * df["shotsAgainst"])
    stats = ['shotsAgainst', 'goalsAgainst', 'Saves']
    stat_names = ['Shots Against', 'Goals Against', 'Saves']

# Sidebar: player and stat selection
# Check if full_name column exists and has data
if 'full_name' not in df.columns:
    st.error("The 'full_name' column is missing from the dataset. Please check your CSV file.")
    st.stop()

player_list = df['full_name'].dropna().unique().tolist()
if not player_list:
    st.error("No players found in the 'full_name' column. Please ensure the column contains valid player names.")
    st.stop()

selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))
selected_stat_display = st.sidebar.selectbox("Select a statistic:", stat_names)
selected_stat = stats[stat_names.index(selected_stat_display)]

# Sidebar: date filter
# Ensure min_date and max_date are valid
if not df['gameDate'].empty:
    min_date = df['gameDate'].min()
    max_date = df['gameDate'].max()
else:
    # Fallback dates if the DataFrame is empty or all dates are invalid
    min_date = pd.to_datetime("2024-10-01")  # Start of 2024-2025 NHL season
    max_date = pd.to_datetime("2025-05-27")  # Current date: May 27, 2025

# Convert to datetime.date for st.date_input
min_date = min_date.to_pydatetime().date() if pd.notna(min_date) else pd.to_datetime("2024-10-01").date()
max_date = max_date.to_pydatetime().date() if pd.notna(max_date) else pd.to_datetime("2025-05-27").date()

start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date))

# Filter data
df = df[(df['gameDate'] >= start_date) & (df['gameDate'] <= end_date)]
player_df = df[df['full_name'] == selected_player]
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce')
player_df = player_df.dropna(subset=[selected_stat])

# Histogram threshold
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
        sizes, labels=labels, autopct='%1.1f%%', start modaangle=140,
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
