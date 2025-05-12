import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.preprocessing import OneHotEncoder

# Load and preprocess data
@st.cache_data
def load_and_preprocess_data(path, date_column, date_format):
    df = pd.read_csv(path)
    df[date_column] = pd.to_datetime(df[date_column], format=date_format, errors='coerce')
    return df

# Prepare models for prediction
@st.cache_data
def prepare_models(df, stats, features):
    encoder = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
    X = encoder.fit_transform(df[features])
    X_df = pd.DataFrame(X, columns=encoder.get_feature_names_out(features))
    models = {stat: sm.OLS(df[stat], X_df).fit() for stat in stats}
    return encoder, models

# Predict player stats
def predict_stats(date, schedule, players, stats, encoder, models, selected_player):
    date = pd.to_datetime(date, format='%m/%d/%Y')
    games_today = schedule[schedule['DATE'].dt.normalize() == date.normalize()]
    if games_today.empty:
        st.warning(f"No games scheduled for {date.strftime('%m/%d/%Y')}")
        return pd.DataFrame()

    predictions = []
    for _, game in games_today.iterrows():
        for team, opponent in [(game['HOME'], game['AWAY']), (game['AWAY'], game['HOME'])]:
            if players[players['Tm'] == team]['Player'].str.contains(selected_player, case=False, na=False).any():
                player_features = pd.DataFrame([{'Opp': opponent, 'Player': selected_player}])

                try:
                    player_encoded = encoder.transform(player_features)
                except Exception as e:
                    st.error(f"Encoding failed: {e}")
                    continue

                player_df = pd.DataFrame(player_encoded, columns=encoder.get_feature_names_out(['Opp', 'Player']))
                expected_columns = list(models.values())[0].model.exog_names
                player_df = player_df.reindex(columns=expected_columns, fill_value=0)

                prediction = {stat: round(models[stat].predict(player_df)[0], 4) for stat in stats}
                predictions.append({
                    'Date': date,
                    'Player': selected_player,
                    'Team': team,
                    'Opponent': opponent,
                    **prediction
                })

    if not predictions:
        st.warning(f"No prediction match found for {selected_player} on {date.strftime('%m/%d/%Y')}.")

    return pd.DataFrame(predictions)

# Plot histogram with threshold coloring
def plot_histogram(data, threshold, title, x_label):
    fig, ax = plt.subplots(figsize=(10, 6))
    n, bins, patches = ax.hist(data, bins=20, edgecolor='black')
    total_count = sum(n)
    proportions = n / total_count

    for patch, left, right in zip(patches, bins[:-1], bins[1:]):
        mean = (left + right) / 2
        color = 'green' if mean > threshold else 'red' if mean < threshold else 'grey'
        patch.set_facecolor(color)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel('Frequency')
    plt.tight_layout()
    st.pyplot(fig)

    proportion_text = f"Proportions for {x_label} (non-zero bins):\n"
    for count, prop, left, right in zip(n, proportions, bins[:-1], bins[1:]):
        if count > 0:
            stat_value = round((left + right) / 2)
            stat_label = f"{stat_value} {x_label}" if stat_value != 1 else f"{stat_value} {x_label[:-1]}"
            proportion_text += f"{stat_label}: {prop:.2%}\n"

    st.text(proportion_text if proportion_text.strip() != f"Proportions for {x_label} (non-zero bins):" else f"No non-zero bins for {x_label}.")

# Load data
skaters_df = load_and_preprocess_data('data/hockey_data/combined_skaters_hockey_game_logs.csv', 'Date', '%m/%d/%y')
goalies_df = load_and_preprocess_data('data/hockey_data/combined_goalies_hockey_game_logs.csv', 'Date', '%m/%d/%y')
nhl_schedule_df = load_and_preprocess_data('data/NHL_Schedule.csv', 'DATE', '%m/%d/%Y')

# Prepare models
encoder_skaters, models_skaters = prepare_models(skaters_df, ['G.1', 'SOG', 'A', 'PTS', 'BLK'], ['Opp', 'Player'])
encoder_goalies, models_goalies = prepare_models(goalies_df, ['SV', 'GA', 'SA'], ['Opp', 'Player'])

# Sidebar UI
st.sidebar.title("NHL Filters & Visualization")
position = st.sidebar.radio("Select Player Position:", ('Skater', 'Goalie'))

if position == 'Skater':
    filtered_df = skaters_df
    stats = ['G.1', 'SOG', 'A', 'PTS', 'BLK']
    stats_display = ['Goals', 'Shots on Goal', 'Assists', 'Points', 'Blocked Shots']
    encoder, models = encoder_skaters, models_skaters
else:
    filtered_df = goalies_df
    stats = ['SV', 'GA', 'SA']
    stats_display = ['Saves', 'Goals Against', 'Shots Against']
    encoder, models = encoder_goalies, models_goalies

# Player and date selection
all_players = filtered_df['Player'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox('Select a player:', all_players)
min_date_str = filtered_df['Date'].min().strftime('%m/%d/%Y')
max_date_str = filtered_df['Date'].max().strftime('%m/%d/%Y')

start_date_str = st.sidebar.text_input('Start Date (MM/DD/YYYY):', min_date_str)
end_date_str = st.sidebar.text_input('End Date (MM/DD/YYYY):', max_date_str)

try:
    start_date = pd.to_datetime(start_date_str, format='%m/%d/%Y')
    end_date = pd.to_datetime(end_date_str, format='%m/%d/%Y')
    if start_date > end_date:
        start_date, end_date = end_date, start_date
        st.sidebar.warning("Start date was after end date. Swapped them.")
except ValueError:
    st.sidebar.error("Please enter valid dates in MM/DD/YYYY format.")
    start_date, end_date = filtered_df['Date'].min(), filtered_df['Date'].max()

filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

# Main app area
st.title("NHL Player Performance Analyzer")

st.write(f"### Stats for {selected_player} from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")
player_stats = filtered_df[filtered_df['Player'] == selected_player]

if not player_stats.empty:
    st.dataframe(player_stats[['Date'] + stats])
    for stat, label in zip(stats, stats_display):
        plot_histogram(player_stats[stat].dropna(), threshold=player_stats[stat].mean(), title=f"{label} Distribution", x_label=label)
else:
    st.warning(f"No data available for {selected_player} in the selected date range.")

# Prediction section
st.header("Predict Player Performance")
prediction_date = st.text_input("Enter date to predict (MM/DD/YYYY):", max_date_str)

if st.button("Predict"):
    predictions_df = predict_stats(prediction_date, nhl_schedule_df, filtered_df, stats, encoder, models, selected_player)
    if not predictions_df.empty:
        st.subheader("Prediction Results")
        st.dataframe(predictions_df)
