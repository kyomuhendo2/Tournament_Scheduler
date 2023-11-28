import os
print("Current working directory:", os.getcwd())
from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
#create a model/database
class tournament_schedule(db.Model):
    team_id = db.Column(db.Integer, primary_key = True)
    team_name = db.Column(db.String(200), nullable = False)
    start_date = db.Column(db.DateTime, default = datetime.utcnow)

    def __repr__(self):
        return '<Team %r>' % self.team_id
@app.route('/')

def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug = True)

# Create tables
with app.app_context():
    db.create_all()