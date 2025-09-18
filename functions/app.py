import sqlite3
from flask import Flask, render_template
import os

app = Flask(__name__)
# Cloudflare Workers has a temporary file system, so we need to copy the DB
DATABASE_NAME = "picks.db"
if os.path.exists('/data/picks.db'):
    DATABASE_NAME = '/data/picks.db'

def get_db_connection():
    """Connects to the database and returns the connection."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
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
    
    report_data = {
        'picks': picks_data
    }

    return render_template('report.html', report=report_data)

# Cloudflare Pages will serve your app through a main function
def main(request, env, context):
    return app(request, env, context)