import os
#print("Current working directory:", os.getcwd())
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

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
class tournament_schedule(db.Model):
    tournament_name = db.Column(db.String(200), nullable = False)
    number_of_teams = db.Column(db.Integer, nullable = False)
    team_id = db.Column(db.Integer, primary_key = True)
    team_name = db.Column(db.String(200), nullable = False)
    start_date = db.Column(db.DateTime, default = datetime.utcnow)

    def __repr__(self):
        return '<Team %r>' % self.team_id
@app.route('/', methods = ['POST', 'GET'])

def index():
    if request.method == 'POST':
        schedule_content = request.form['team_name']
        new_team = tournament_schedule(tournament_name='Some Tournament', number_of_teams=1, team_name = schedule_content)

        try:
            db.session.add(new_team)
            db.session.commit()
            return redirect('/')

        except Exception as e:
            # Print or log the error for debugging purposes
            print(f"Error: {e}")
            return f'OOPs! There was an issue adding your task {e}'
    else:
        get_teams = tournament_schedule.query.order_by(tournament_schedule.start_date).all()
        return render_template('index.html', get_teams = get_teams)

if __name__ == "__main__":
    app.run(debug = True)

# Create tables
with app.app_context():
    db.create_all()