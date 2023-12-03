from flask import Flask, render_template, request
from datetime import datetime, timedelta
from math import log2

app = Flask(__name__)

def generate_single_elimination_schedule(num_teams, start_date, end_date):
    if num_teams < 2 or not (num_teams & (num_teams - 1) == 0):
        print("Number of teams must be a power of 2 and greater than or equal to 2.")
        return

    # Validate constraints
    num_rounds = int(log2(num_teams))
    expected_duration = timedelta(days=num_rounds)
    actual_duration = end_date - start_date

    if end_date < start_date:
        print("Error: The end date cannot be earlier than the start date.")
        return

    if expected_duration > actual_duration:
        days_missing = (expected_duration - actual_duration).days
        print(f"The provided range of dates may not be enough for this tournament. Please extend your end date by {days_missing} days.")
        return

    # Calculate the time difference between start and end dates
    time_diff = end_date - start_date

    # Initialize teams
    teams = [f"Team {i}" for i in range(1, num_teams + 1)]

    # Generate schedule for each round
    schedule_data = []
    for round_number in range(1, num_rounds + 1):
        print(f"\nRound {round_number} Schedule:")

        # Calculate the date for the current round
        round_date = start_date + timedelta(days=int((round_number - 1) / num_rounds * time_diff.days))

        # Generate matches for the current round
        matches_in_round = num_teams // (2 ** round_number)
        winners = []

        for match_number in range(1, matches_in_round + 1):
            team1_index = (match_number - 1) * 2
            team2_index = (match_number - 1) * 2 + 1

            team1 = teams[team1_index]
            team2 = teams[team2_index]

            print(f"Match {match_number} on {round_date}: {team1} vs {team2}")

            # Simulate the match and get the winner
            winner = f"Winner {match_number}"
            winners.append(winner)

        # If the number of winners is odd, append the last team as a "Bye"
        if len(winners) % 2 != 0:
            bye_team = teams[-1]
            print(f"Bye on {round_date}: {bye_team}")
            winners.append(bye_team)

        # Append match data to the current round's schedule
        round_schedule = []
        for match_number in range(1, matches_in_round + 1):
            team1_index = (match_number - 1) * 2
            team2_index = (match_number - 1) * 2 + 1

            team1 = teams[team1_index]
            team2 = teams[team2_index]

            round_schedule.append({
                'match_number': match_number,
                'round_date': round_date,
                'team1': team1,
                'team2': team2
            })

        # If the number of winners is odd, append the bye match data
        if len(winners) % 2 != 0:
            round_schedule.append({
                'match_number': 'Bye',
                'round_date': round_date,
                'team1': bye_team,
                'team2': None
            })

        schedule_data.append({'round_number': round_number, 'matches': round_schedule})
        teams = winners

    return schedule_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            num_teams = int(request.form['num_teams'])
            start_date_str = request.form['start_date']
            end_date_str = request.form['end_date']

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            schedule_data = generate_single_elimination_schedule(num_teams, start_date, end_date)
            return render_template('schedule.html', schedule_data=schedule_data)
        except ValueError:
            error_message = "Invalid input. Please enter valid integers and dates."
            return render_template('schedule.html', error_message=error_message)

    return render_template('schedule.html')

if __name__ == '__main__':
    app.run(debug=True)
