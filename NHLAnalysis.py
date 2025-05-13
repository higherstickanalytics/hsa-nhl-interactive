import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---------- CACHED DATA LOAD ----------
@st.cache_data
def load_data(path, date_column=None, date_format=None):
    df = pd.read_csv(path)
    if date_column and date_format:
        df[date_column] = pd.to_datetime(df[date_column], format=date_format, errors='coerce')
    return df

# ---------- PLOTTING ----------
def plot_histogram(data, threshold, title, x_label):
    fig, ax = plt.subplots(figsize=(10, 6))
    n, bins, patches = ax.hist(data, bins=20, edgecolor='black')
    total = sum(n)
    proportions = n / total if total else [0] * len(n)

    for patch, left, right in zip(patches, bins[:-1], bins[1:]):
        mean = (left + right) / 2
        patch.set_facecolor('green' if mean > threshold else 'red' if mean < threshold else 'grey')

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel('Frequency')
    st.pyplot(fig)

    st.text(f"Proportions for {x_label}:\n" + "\n".join(
        [f"{round((l + r) / 2)}: {p:.2%}" for p, l, r in zip(proportions, bins[:-1], bins[1:]) if p > 0]
    ))

def plot_time_series(df, date_col, stat_col, threshold, player):
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(df[date_col], df[stat_col], color='grey', edgecolor='black')

    count = 0
    for bar, value in zip(bars, df[stat_col]):
        if value >= threshold:
            bar.set_color('green')
            count += 1
        else:
            bar.set_color('red')

    total = len(df)
    ax.axhline(y=threshold, color='blue', linestyle='--', label=f'Threshold: {threshold}')
    ax.set_title(f'{stat_col} Over Time for {player}')
    ax.set_xlabel('Date')
    ax.set_ylabel(stat_col)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    st.text(f"{count}/{total} games at or above threshold: {count / total:.2%}")

# ---------- DATA LOADING ----------
skaters_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
goalies_path = 'data/hockey_data/combined_goalies_hockey_game_logs.csv'
schedule_path = 'data/NHL_Schedule.csv'

skaters_df = load_data(skaters_path, 'Date', '%m/%d/%y')
goalies_df = load_data(goalies_path, 'Date', '%m/%d/%y')
schedule_df = load_data(schedule_path, 'DATE', '%m/%d/%Y')

# ---------- UI ----------
st.title("NHL Player Stats Viewer")
st.write("All data from [Hockey Reference](https://www.hockey-reference.com/).")

# Sidebar filters
st.sidebar.title("Filters")
position = st.sidebar.radio("Player Type:", ['Skater', 'Goalie'])

if position == 'Skater':
    df = skaters_df
    stat_options = ['G.1', 'SOG', 'A', 'PTS', 'BLK']
    stat_labels = ['Goals', 'Shots on Goal', 'Assists', 'Points', 'Blocked Shots']
else:
    df = goalies_df
    stat_options = ['SV', 'GA', 'SA']
    stat_labels = ['Saves', 'Goals Against', 'Shots Against']

player_list = df['Player'].dropna().unique()
selected_player = st.sidebar.selectbox("Select Player", sorted(player_list))

min_date = df['Date'].min()
max_date = df['Date'].max()
start = st.sidebar.text_input("Start Date (MM/DD/YYYY):", min_date.strftime('%m/%d/%Y'))
end = st.sidebar.text_input("End Date (MM/DD/YYYY):", max_date.strftime('%m/%d/%Y'))

try:
    start_dt = pd.to_datetime(start, format='%m/%d/%Y')
    end_dt = pd.to_datetime(end, format='%m/%d/%Y')
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
except:
    st.sidebar.error("Please enter dates in MM/DD/YYYY format.")
    start_dt, end_dt = min_date, max_date

filtered_df = df[(df['Date'] >= start_dt) & (df['Date'] <= end_dt)]
filtered_df = filtered_df[filtered_df['Player'] == selected_player]

# Select stat
selected_label = st.sidebar.selectbox("Select Stat", stat_labels)
stat_col = stat_options[stat_labels.index(selected_label)]

# Convert and filter stat values
filtered_df[stat_col] = pd.to_numeric(filtered_df[stat_col], errors='coerce')
stat_data = filtered_df[['Date', stat_col]].dropna()

if stat_data.empty:
    st.warning("No data available for selected player and date range.")
else:
    threshold = st.number_input(f"Set threshold for {selected_label}", min_value=0.0,
                                max_value=float(stat_data[stat_col].max()), 
                                value=float(stat_data[stat_col].median()), step=0.5)

    # Visualization selection
    view = st.sidebar.radio("Visualization Type:", ['Histogram', 'Time Series'])

    st.subheader(f"{selected_label} for {selected_player}")

    if view == 'Histogram':
        plot_histogram(stat_data[stat_col], threshold, f"{selected_label} Distribution", selected_label)
    else:
        plot_time_series(stat_data, 'Date', stat_col, threshold, selected_player)
