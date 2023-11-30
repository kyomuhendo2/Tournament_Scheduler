import os
#print("Current working directory:", os.getcwd())
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from math import log2
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
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
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
#create schedule

#create tournament
@app.route('/', methods = ['POST', 'GET'])

def index():
    
    get_tournament = Tournament.query.order_by(Tournament.id).all()
    print("get_tournament:", get_tournament)  # line for debugging
    get_team = Team.query.order_by(Team.id).all()
    #select_tournament = Tournament.query.order_by(Tournament.id).all()
    return render_template('index.html', get_tournament=get_tournament, get_team=get_team)
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
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'],'%Y-%m-%d')

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

    teams = Team.query.filter_by(tournament_id=tournament_id).order_by(Team.id).all()

    # Create matches for each round
    for round_number in range(1, num_rounds + 1):
        matches_in_round = 2**(num_rounds - round_number)

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

            db.session.add(match)

    db.session.commit()

# New route for generating schedule
@app.route('/generate_schedule', methods=['GET', 'POST'])
def generate_schedule():
    #select_tournament = Tournament.query.get_or_404(id)
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
        return render_template('generate_schedule.html', error_message=str(e))

    # Default return statement (you can modify this)
    return render_template('generate_schedule.html', error_message="Invalid request method")
# Route to display the generated schedule
@app.route('/display_schedule/<int:tournament_id>')
def display_schedule(tournament_id):
    # Retrieve the tournament and schedule information
    tournament = Tournament.query.get_or_404(tournament_id)
    schedule = Match.query.filter_by(tournament_id=tournament_id).all()
    teams = Team.query.filter_by(tournament_id=tournament_id).order_by(Team.id).all()
    

# Print schedule in the terminal
    print(f"\nSchedule for Tournament '{tournament.tournament_name}':")
    for match in schedule:
        team1_name = Team.query.get(match.team1_id).team_name if match.team1_id else 'Not determined yet'
        team2_name = Team.query.get(match.team2_id).team_name if match.team2_id else 'Not determined yet'
        winner_name = Team.query.get(match.winner_id).team_name if match.winner_id else 'Not determined yet'
        print(f"Round {match.round_number}: {team1_name} vs {team2_name}, Winner: {winner_name}")

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