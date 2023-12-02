import os
#print("Current working directory:", os.getcwd())
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta
from flask_migrate import Migrate
from math import log2
from sqlalchemy.orm import joinedload
import random
#import pdb; pdb.set_trace()

app = Flask(__name__)

# Get the absolute path to the directory of the current script (app.py)
current_directory = os.path.abspath(os.path.dirname(__file__))

# Specify the absolute path to the database file in the same directory as app.py
db_file_path = os.path.join(current_directory, 'schedule.db')

#app configuration
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#initializing the database
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

#create a model/database
# Tournament model
class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_name = db.Column(db.String(200), nullable=False)
    number_of_teams = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    teams = db.relationship('Team', backref='tournament', lazy=True)

# Team model
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(200), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)

    def __repr__(self):
        return '<Team %r>' % self.id
    
# Match model
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    winner_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    match_date = db.Column(db.Date)
    bye_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    
#define the relationsships in the match model
    team1 = db.relationship('Team', foreign_keys=[team1_id], backref='team1_match', lazy=True)
    team2 = db.relationship('Team', foreign_keys=[team2_id], backref='team2_match', lazy=True)
    winner = db.relationship('Team', foreign_keys=[winner_id], backref='winner_match', lazy=True)
    bye_team = db.relationship('Team', foreign_keys=[bye_team_id], backref='bye_match', lazy=True)
#create schedule

#create tournament
@app.route('/', methods = ['POST', 'GET'])

def index():
    
    get_tournament = Tournament.query.order_by(Tournament.id).all()
    print("get_tournament:", get_tournament)  # line for debugging
    get_team = Team.query.order_by(Team.id).all()
    # Fetch a specific tournament, for example, the first one
    tournament = get_tournament[0] if get_tournament else None
    #select_tournament = Tournament.query.order_by(Tournament.id).all()

    #1
    return render_template('index.html', get_tournament=get_tournament, get_team=get_team, tournament=tournament)
    #return render_template('index.html', get_tournament=get_tournament, get_team=get_team, select_tournament=select_tournament)

    #method 2
    # Render the initial page with the forms
    return render_template('index.html')

#create tournament / process form 1
@app.route('/process_form1', methods=['POST'])
def process_form1():
    if request.method == 'POST':
        print("Received form data:", request.form)
        tournament_name = request.form['tournament_name']
        number_of_teams = int(request.form['number_of_teams'])      

        # Remove the time portion from the date strings
        #start_date_str = request.form['start_date'].split()[0]
        #end_date_str = request.form['end_date'].split()[0]

        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'],'%Y-%m-%d')

        # Print the received date strings
        print("Received start_date string:", start_date)
        print("Received end_date string:", end_date)

        # Print the converted datetime objects
        print("Converted start_date:", start_date)
        print("Converted end_date:", end_date)

        # Validate number_of_teams based on the series
        n = 100
        valid_team_counts = [2 * 2**(i-1) for i in range(1, n+1)]

        if number_of_teams not in valid_team_counts:
            return f"For the single elimination, the number of teams must be one of the following: {valid_team_counts}. Please choose a valid number."
        
        # Validation: Check if end_date is greater than start_date
        if end_date < start_date:
            return "End date must be ahead of start date or the same. Please correct the dates."

        add_tournament = Tournament(
            tournament_name=tournament_name, 
            number_of_teams=number_of_teams, 
            start_date=start_date, 
            end_date=end_date
        )

        try:
            db.session.add(add_tournament)
            db.session.commit()

             # Automatically add team names to the 'teams' table for this tournament
            tournament_id = add_tournament.id
            for i in range(1, number_of_teams + 1):
                team_name = f"Team {i}"
                add_team = Team(
                    team_name=team_name,
                    tournament_id=tournament_id
                )
                db.session.add(add_team)

            #create schedule

            create_single_elimination_schedule(tournament_id, number_of_teams)

            db.session.commit()
            return redirect('/')

        except Exception as e:
            # Print or log the error for debugging purposes
            print(f"Error: {e}")
            return f'OOPs! There was an issue adding your task in form 1 {e}'
    else:
        get_tournament = Tournament.query.order_by(Tournament.start_date).all()
        print("Number of tournaments:", len(get_tournament))  # line for debugging
        for tournament in get_tournament:
            print(tournament.id, tournament.tournament_name, tournament.number_of_teams, tournament.start_date, tournament.end_date)
        return render_template('index.html', get_tournament=get_tournament)
    
# Create a single-elimination schedule
def create_single_elimination_schedule(tournament_id, number_of_teams):
    # Calculate the number of rounds needed
    num_rounds = int(log2(number_of_teams))

     # Handle odd number of teams
    if number_of_teams % 2 == 1:
        bye_team = Team.query.filter_by(tournament_id=tournament_id, team_name='Bye').first()
        if not bye_team:
            bye_team = Team(team_name='Bye', tournament_id=tournament_id)
            db.session.add(bye_team)
            db.session.commit()

        # Add the bye team to the list of teams
        teams = Team.query.filter_by(tournament_id=tournament_id).order_by(Team.id).all()
        teams.append(bye_team)
    else:
        # If even number of teams, get teams directly from the database
        teams = Team.query.filter_by(tournament_id=tournament_id).order_by(Team.id).all()

        #teams = Team.query.filter_by(tournament_id=tournament_id).order_by(Team.id).all()

    # Generate random dates for each round within the start date and end date limits
    start_date = Tournament.query.filter_by(id=tournament_id).first().start_date
    end_date = Tournament.query.filter_by(id=tournament_id).first().end_date

    # Create matches for each round
    for round_number in range(1, num_rounds + 1):
        matches_in_round = 2**(num_rounds - round_number)

        for match_in_round in range(1, matches_in_round + 1):
            match = Match(
                tournament_id=tournament_id,
                round_number=round_number,
            )
            
        round_start_date = (
        start_date
        if round_number == 1
        else start_date + timedelta(days = (end_date - start_date).days * random.random())
        )

        for match_in_round in range(1, matches_in_round + 1):
            match = Match(
                tournament_id=tournament_id,
                round_number=round_number,
            )
             # Assign teams to the match based on the round and match_in_round
            team1_index = (match_in_round - 1) * 2
            team2_index = (match_in_round - 1) * 2 + 1

            if team1_index < len(teams):
                match.team1_id = teams[team1_index].id
            if team2_index < len(teams):
                match.team2_id = teams[team2_index].id

            # Handle bye team for odd number of teams
            if number_of_teams % 2 == 1 and team2_index >= len(teams):
                match.bye_team_id = teams[-1].id

            """existing_match = (
                Match.query.filter_by(tournament_id=tournament_id, round_number=round_number - 1)
                .filter((Match.team1_id == match.team1_id) & (Match.team2_id == match.team2_id))
                .first()
            )

            if existing_match:
                # If the match already exists in a previous round, skip this match
                print(f"Match between {teams[team1_index].team_name} and {teams[team2_index].team_name} already exists in round {round_number - 1}. Skipping this match.")
                continue"""
            
	        # Assign a random date within the start date and end date limits for the current round
            #match_date = round_start_date + (end_date - round_start_date) * random.random()
            #match.match_date = match_date

            round_start_date = start_date + timedelta(days=(end_date - start_date).days * random.random())
            match_date = round_start_date + timedelta(days=(end_date - round_start_date).days * random.random())
            match.match_date = match_date

            db.session.add(match)

    db.session.commit()

# New route for generating schedule
@app.route('/generate_schedule/<tournament_id>', methods=['GET', 'POST'])
def generate_schedule(tournament_id):
    #select_tournament = Tournament.query.get_or_404(id)
    tournament = Tournament.query.get_or_404(tournament_id)
    try:
        if request.method == 'POST':
            print(f"Received form data: {request.form}")
            # Assuming 'tournament_name' is part of the form data
            tournament_info = request.form.get('tournament_id')
            tournament_id, number_of_teams = map(int, tournament_info.split('|'))
            print(f"Tournament ID: {tournament_id}")
            print(f"Number of Teams: {number_of_teams}")
            
            if tournament_id and number_of_teams:
                #select_tournament.tournament_name = tournament_name
                # Schedule generation logic here
                tournament_id = int(tournament_id)
                number_of_teams = int(number_of_teams)
                create_single_elimination_schedule(tournament_id, number_of_teams)

                # Redirect to the page that displays the generated schedule
                return redirect(url_for('display_schedule', tournament_id=tournament_id))
            else:
                #raise ValueError("Form data does not contain 'tournament_id'")
                return render_template('error.html', error_message="Invalid request method")
    except Exception as e:
        print(f"Error: {e}")
        return render_template('generate_schedule.html', tournament_id=tournament_id, tournament = tournament, error_message=str(e))

    # Default return statement (you can modify this)
    return render_template('generate_schedule.html', tournament_id=tournament_id,error_message="Invalid request method")

# Route to display the generated schedule
@app.route('/display_schedule/<int:tournament_id>')
def display_schedule(tournament_id):
    # Retrieve the tournament and schedule information
    tournament = Tournament.query.get_or_404(tournament_id)

    # Query the schedule with joined loading of related teams
    schedule = (
        db.session.query(Match)
        .options(joinedload(Match.team1), joinedload(Match.team2), joinedload(Match.winner))
        .filter(Match.tournament_id == tournament_id)
        .filter(Match.team1 != None, Match.team2 != None)
        .all()
    # Filter out matches with None teams
    )

    teams = Team.query.filter_by(tournament_id=tournament_id).order_by(Team.id).all()

    # Print schedule in the terminal and store data for rendering
    match_data = []

    # Print schedule in the terminal
    print(f"\nSchedule for Tournament '{tournament.tournament_name}':")
    print("Schedule before loop:", schedule)
    for match in schedule:
        match_date = match.match_date.strftime('%Y-%m-%d') if match.match_date else 'Not determined yet'
        team1_name = match.team1.team_name if match.team1 else 'Not determined yet'
        team2_name = match.team2.team_name if match.team2 else 'Not determined yet'
        winner_name = match.winner.team_name if match.winner else 'Not determined yet'        

        print(f"Date: {match_date}, Round {match.round_number}: {team1_name} vs {team2_name}, Winner: {winner_name}")
        match_data.append({
            'round_number': match.round_number,
            'team1_name': team1_name,
            'team2_name': team2_name,
            'winner_name': winner_name,
            'match_date': match_date,
        })
    return render_template('generate_schedule.html', tournament=tournament, schedule=schedule, teams=teams)

#create teams
@app.route('/process_form2', methods=['POST'])
def process_form2():
    if request.method == 'POST':
        team_name = request.form['team_name']
        tournament_id = request.form['tournament_id']

        add_team = Team( 
            team_name = team_name,            
            tournament_id = tournament_id
        )
        try:
            db.session.add(add_team)
            db.session.commit()
            return redirect('/')

        except Exception as e:
            # Print or log the error for debugging purposes
            print(f"Error: {e}")
            return f'OOPs! There was an issue adding your task in form 2 {e}'
    else:
        get_team = Team.query.order_by(Team.id).all()
        get_tournament = Tournament.query.order_by(Tournament.start_date).all()
        print("get_tournament:", get_tournament)
        return render_template(
            'index.html', 
            get_team=get_team, 
            get_tournament=get_tournament
        )
    
#delete
@app.route('/delete_tournament/<int:id>')
def delete_tournament(id):
    tournament_to_delete = Tournament.query.get_or_404(id)

    try:
        db.session.delete(tournament_to_delete)
        db.session.commit()
        return redirect('/')
    except Exception as e:
         # Print or log the error for debugging purposes
        print(f"Error: {e}")
        return f'OOPs! There was an issue updating your task {e}'
    

@app.route('/clear_matches/<int:tournament_id>', methods=['GET', 'POST'])
def clear_matches(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    if request.method == 'POST':
        try:
            # Delete all matches for the specified tournament
            Match.query.filter_by(tournament_id=tournament_id).delete()
            db.session.commit()
            return redirect(url_for('display_schedule', tournament_id=tournament_id))
        except Exception as e:
            # Handle the exception (log, display an error message, etc.)
            print(f"Error: {e}")
            return render_template('error.html', error_message="Error clearing matches.")
    else:
        # Render the confirmation page
        return render_template('clear_matches.html', tournament=tournament)

@app.route('/delete_team/<int:id>')
def delete_team(id):
    team_to_delete = Team.query.get_or_404(id)

    try:
        db.session.delete(team_to_delete)
        db.session.commit()
        return redirect('/')
    except Exception as e:
         # Print or log the error for debugging purposes
        print(f"Error: {e}")
        return f'OOPs! There was an issue updating your task {e}'

#update
@app.route('/update_tournament/<int:id>', methods = ['GET', 'POST'])

def update_tournament_fun(id):
    update_tournament = Tournament.query.get_or_404(id)
    if request.method == 'POST':
        print(f"Received form data: {request.form}")
        update_tournament.tournament_name = request.form['tournament_name']

        try:
            db.session.commit()
            print(f"Team updated successfully: {update_tournament}")
            return redirect('/')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('updatetournament.html', update_tournament=update_tournament)
    

@app.route('/update_team/<int:id>', methods = ['GET', 'POST'])

def update_team_fun(id):
    update_team = Team.query.get_or_404(id)
    if request.method == 'POST':
        print(f"Received form data: {request.form}")
        update_team.team_name = request.form['team_name']

        try:
            db.session.commit()
            print(f"Team updated successfully: {update_team}")
            return redirect('/')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('updateteam.html', update_team=update_team)

if __name__ == "__main__":
    app.run(debug = True)

# Create tables
    with app.app_context():
        db.create_all()