import sqlite3
from flask import Flask, render_template

app = Flask(__name__)
DATABASE_NAME = "picks.db"

def get_db_connection():
    """Connects to the database and returns the connection."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

@app.route('/')
def index():
    """Fetches and displays the analysis report on the main page."""
    conn = get_db_connection()
    picks_data = conn.execute('''
        SELECT
            p.id,
            f.commence_time,
            f.home_team,
            f.away_team,
            p.market,
            p.pick,
            p.pick_odds,
            p.confidence_level,
            p.result
        FROM nfl_picks AS p
        JOIN nfl_fixtures AS f ON p.game_id = f.id
        ORDER BY f.commence_time ASC
    ''').fetchall()
    conn.close()

    # We'll use a simple dictionary to hold data for the template
    report_data = {
        'picks': picks_data
    }

    # Render the HTML template, passing the data to it
    return render_template('report.html', report=report_data)

if __name__ == '__main__':
    app.run(debug=True)