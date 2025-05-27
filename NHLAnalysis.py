import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load combined game logs CSV
csv_path = 'nhl_player_game_logs_2024_2025.csv'
df = pd.read_csv(csv_path)

# Parse date and rename columns if needed
df['gameDate'] = pd.to_datetime(df['gameDate'], errors='coerce')
df = df.rename(columns={'full_name': 'playerName'})  # match app expectations

# Separate skaters and goalies
df['position'] = df['position'].fillna('')  # avoid NaNs
skaters_df = df[~df['position'].str.upper().isin(['G', 'GOALIE'])]
goalies_df = df[df['position'].str.upper().isin(['G', 'GOALIE'])]

# App Title
st.title("NHL 2024–25 Player Game Log Viewer")
st.write("Data includes Regular Season and Playoff games")

# Sidebar: Position select
position = st.sidebar.radio("Select Player Position", ['Skater', 'Goalie'])

if position == 'Skater':
    df = skaters_df
    stats = ['goals', 'assists', 'points', 'shots', 'plusMinus']
    stat_names = ['Goals', 'Assists', 'Points', 'Shots', 'Plus/Minus']
else:
    df = goalies_df
    df['Saves'] = round(df.get('savePctg', 0) * df.get('shotsAgainst', 0))
    stats = ['shotsAgainst', 'goalsAgainst', 'Saves']
    stat_names = ['Shots Against', 'Goals Against', 'Saves']

# Sidebar: Player + Stat select
player_list = df['playerName'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))
selected_stat_display = st.sidebar.selectbox("Select a statistic:", stat_names)
selected_stat = stats[stat_names.index(selected_stat_display)]

# Sidebar: Date filtering
df = df[df['playerName'] == selected_player]
min_date = df['gameDate'].min()
max_date = df['gameDate'].max()
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))
df = df[(df['gameDate'] >= start_date) & (df['gameDate'] <= end_date)]

# Numeric conversion
df[selected_stat] = pd.to_numeric(df[selected_stat], errors='coerce')
df = df.dropna(subset=[selected_stat])

# Plotting if data is present
if not df.empty:
    threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(df[selected_stat].max()), value=float(df[selected_stat].median()), step=0.5)

    # Pie Chart
    st.subheader(f"{selected_stat_display} Distribution for {selected_player}")
    stat_counts = df[selected_stat].value_counts().sort_index()
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
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 10})
    ax1.axis('equal')
    ax1.set_title(f"{selected_stat_display} Value Distribution")
    st.pyplot(fig1)

    # Breakdown Table
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
            'Count': [color_categories['green'], color_categories['red'], color_categories['gray']],
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
    bars = ax2.bar(df['gameDate'], df[selected_stat], color='gray', edgecolor='black')

    count_above = 0
    for bar, val in zip(bars, df[selected_stat]):
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

    st.write(f"Games at or above threshold: {count_above}/{len(df)} ({count_above / len(df):.2%})")
else:
    st.warning("No data available for the selected player and date range.")
