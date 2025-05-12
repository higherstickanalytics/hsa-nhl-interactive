import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import threading
import statsmodels.api as sm
from sklearn.preprocessing import OneHotEncoder

# Function to load and preprocess data (without caching)
def load_and_preprocess_data(path, date_column, date_format):
    df = pd.read_csv(path)
    df[date_column] = pd.to_datetime(df[date_column], format=date_format, errors='coerce')
    return df

# Function to prepare models (without caching)
def prepare_models(df, stats, features):
    encoder = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
    X = encoder.fit_transform(df[features])
    X_df = pd.DataFrame(X, columns=encoder.get_feature_names_out(features))
    models = {stat: sm.OLS(df[stat], X_df).fit() for stat in stats}
    return encoder, models

# Prediction function
def predict_stats(date, schedule, players, stats, encoder, models, selected_player):
    date = pd.to_datetime(date, format='%m/%d/%Y')
    games_today = schedule[schedule['DATE'] == date]
    if games_today.empty:
        st.write(f"No games scheduled for {date}")
        return pd.DataFrame()

    predictions = []
    for _, game in games_today.iterrows():
        for team, opponent in [(game['HOME'], game['AWAY']), (game['AWAY'], game['HOME'])]:
            if players[players['Tm'] == team]['Player'].str.contains(selected_player, case=False, na=False).any():
                player_features = pd.DataFrame([{'Opp': opponent, 'Player': selected_player}])
                player_encoded = encoder.transform(player_features)
                player_df = pd.DataFrame(player_encoded, columns=encoder.get_feature_names_out(['Opp', 'Player']))

                if player_df.shape[1] < list(models.values())[0].model.exog.shape[1]:
                    player_df = player_df.reindex(columns=list(models.values())[0].model.exog.columns, fill_value=0)

                prediction = {stat: round(models[stat].predict(player_df)[0], 4) for stat in stats}
                predictions.append({
                    'Date': date,
                    'Player': selected_player,
                    'Team': team,
                    'Opponent': opponent,
                    **prediction
                })

    return pd.DataFrame(predictions)

# Plotting function for histograms
def plot_histogram(data, threshold, title, x_label):
    fig, ax = plt.subplots(figsize=(10, 6))  # Increased figure size for less scrunching
    n, bins, patches = ax.hist(data, bins=20, edgecolor='black')
    total_count = sum(n)  # Total number of data points
    proportions = n / total_count  # Calculate proportion for each bin

    # Color bars based on threshold
    for patch, left, right in zip(patches, bins[:-1], bins[1:]):
        mean = (left + right) / 2
        color = 'green' if mean > threshold else 'red' if mean < threshold else 'grey'
        patch.set_facecolor(color)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel('Frequency')
    plt.tight_layout()  # Adjust layout to prevent clipping
    st.pyplot(fig)

    # Display proportions as text below the histogram, only for non-zero bins
    proportion_text = f"Proportions for {x_label} (non-zero bins):\n"
    for i, (count, prop, left, right) in enumerate(zip(n, proportions, bins[:-1], bins[1:])):
        if count > 0:  # Only include bins with non-zero counts
            # Use the midpoint of the bin, rounded to the nearest integer for discrete stats like goals
            stat_value = round((left + right) / 2)
            stat_label = f"{stat_value} {x_label}" if stat_value != 1 else f"{stat_value} {x_label[:-1]}"  # Handle plural
            proportion_text += f"{stat_label}: {prop:.2%}\n"
    st.text(
        proportion_text if proportion_text != f"Proportions for {x_label} (non-zero bins):\n" else f"No non-zero bins for {x_label}.")

# Paths to the data files
skaters_path = 'data/hockey_data/combined_skaters_hockey_game_logs.csv'
goalies_path = 'data/hockey_data/combined_goalies_hockey_game_logs.csv'
schedule_path = 'data/NHL_Schedule.csv'

# Load data
skaters_df = load_and_preprocess_data(skaters_path, 'Date', '%m/%d/%y')
goalies_df = load_and_preprocess_data(goalies_path, 'Date', '%m/%d/%y')
nhl_schedule_df = load_and_preprocess_data(schedule_path, 'DATE', '%m/%d/%Y')

# Prepare models for both skaters and goalies
encoder_skaters, models_skaters = prepare_models(skaters_df, ['G.1', 'SOG', 'A', 'PTS', 'BLK'], ['Opp', 'Player'])
encoder_goalies, models_goalies = prepare_models(goalies_df, ['SV', 'GA', 'SA'], ['Opp', 'Player'])

# Sidebar for view selection and filters
st.sidebar.title("NHL Filters & Visualization")
position = st.sidebar.radio("Select Player Position:", ('Skater', 'Goalie'))

if position == 'Skater':
    filtered_df, stats, stats_display, encoder, models = skaters_df, ['G.1', 'SOG', 'A', 'PTS', 'BLK'], ['Goals',
                                                                                                         'Shots on Goal',
                                                                                                         'Assists',
                                                                                                         'Points',
                                                                                                         'Blocked Shots'], encoder_skaters, models_skaters
else:
    filtered_df, stats, stats_display, encoder, models = goalies_df, ['SV', 'GA', 'SA'], ['Saves', 'Goals Against',
                                                                                          'Shots Against'], encoder_goalies, models_goalies

all_players = filtered_df['Player'].unique().tolist()
selected_player = st.sidebar.selectbox('Select a player:', all_players, format_func=lambda x: x if x else '')

# Date Input for filtering
start_date_str, max_date_str = filtered_df['Date'].min().strftime('%m/%d/%Y'), filtered_df['Date'].max().strftime('%m/%d/%Y')
start_date = st.sidebar.text_input('Start Date (MM/DD/YYYY):', start_date_str)
end_date = st.sidebar.text_input('End Date (MM/DD/YYYY):', max_date_str)

try:
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
except ValueError:
    st.sidebar.error("Invalid date format. Please use MM/DD/YYYY.")

# Stat Selection
selected_stat_index = st.sidebar.selectbox('Select a statistic for visualization:', stats_display)
selected_stat = stats[stats_display.index(selected_stat_index)]

# Main content area
st.title('NHL Player Stats Visualization')
st.write("Data collected using [Hockey Reference](https://www.hockey-reference.com/).")

filtered_df[selected_stat] = pd.to_numeric(filtered_df[selected_stat], errors='coerce').dropna()
player_data = filtered_df[filtered_df['Player'] == selected_player][selected_stat]

if not player_data.empty:
    max_value, default_value = player_data.max(), player_data.median()
    threshold = st.number_input(f'Set Threshold for {selected_stat_index}:', min_value=0.0,
                                max_value=float(max_value) if pd.notna(max_value) else 1.0,
                                value=float(default_value) if pd.notna(default_value) else 0.0, step=0.5)

    # Visualization Type
    view = st.sidebar.radio("Select Visualization Type:", ('Histograms',))

    if view == 'Histograms':
        st.subheader(f'{selected_stat_index} Distribution Histogram')
        plot_histogram(player_data, threshold, f'{selected_stat_index} Distribution for {selected_player}',
                       selected_stat_index)

        st.subheader(f'{selected_stat_index} Time Series Histogram')
        fig, ax = plt.subplots(figsize=(14, 8))  # Increased figure size for less scrunching
        player_data_time = filtered_df[filtered_df['Player'] == selected_player][['Date', selected_stat]].dropna()
        bars = ax.bar(player_data_time['Date'], player_data_time[selected_stat], color='grey', edgecolor='black')

        # Color bars based on threshold and count games at or above threshold
        at_or_above_count = 0
        total_games = len(player_data_time[selected_stat])
        for bar, stat_value in zip(bars, player_data_time[selected_stat]):
            if stat_value > threshold:
                bar.set_color('green')
                at_or_above_count += 1
            elif stat_value == threshold:
                bar.set_color('grey')
                at_or_above_count += 1
            else:
                bar.set_color('red')

        # Calculate proportion of games at or above threshold
        at_or_above_proportion = at_or_above_count / total_games if total_games > 0 else 0

        ax.axhline(y=threshold, color='blue', linestyle='--', linewidth=2, label=f'Threshold: {threshold}')
        ax.set_title(f'{selected_stat_index} Over Time for {selected_player}')
        ax.set_xlabel('Date')
        ax.set_ylabel(selected_stat_index)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        ax.legend()
        plt.tight_layout()  # Adjust layout to prevent clipping
        st.pyplot(fig)

        # Display proportion of games at or above threshold
        proportion_text = f"Proportion of games with {selected_stat_index} at or above threshold ({threshold}):\n"
        proportion_text += f"{at_or_above_count} out of {total_games} games: {at_or_above_proportion:.2%}"
        st.text(proportion_text)

# Predictions for selected player
prediction_date = st.text_input("Enter Date for Predictions (MM/DD/YYYY):", pd.Timestamp.now().strftime('%m/%d/%Y'))
st.subheader(f"Predictions for {selected_player} on {pd.to_datetime(prediction_date).strftime('%m/%d/%Y')}")

if st.button("Get Predictions"):
    predictions = predict_stats(prediction_date, nhl_schedule_df, filtered_df, stats, encoder, models, selected_player)
    if not predictions.empty:
        new_columns = ['Date', 'Player', 'Team', 'Opponent'] + stats_display
        if position == 'Goalie':
            predictions = predictions.rename(columns={'SV': 'Saves', 'SA': 'Shots Against', 'GA': 'Goals Against'})
            predictions['SV%'] = predictions['Saves'] / predictions['Shots Against']
            predictions['SV%'] = predictions['SV%'].apply(lambda x: round(x, 3) if x != 0 else 0)
            new_columns.append('SV%')

        predictions.columns = new_columns
        predictions['Date'] = predictions['Date'].dt.strftime('%m/%d/%Y')
        predictions.set_index('Date', inplace=True)
        st.dataframe(predictions)
    else:
        st.write(f"No predictions could be made for {selected_player} on {pd.to_datetime(prediction_date).strftime('%m/%d/%Y')}.")
