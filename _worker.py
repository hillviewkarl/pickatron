import sqlite3
from flask import Flask, render_template
import os
from aiohttp import web
from aioflask import AioFlask

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

# This is the entry point for the Cloudflare Pages Worker
async def handle_request(request):
    """Handles an incoming request and passes it to the Flask app."""
    return await AioFlask(app)(request)

async def handle_static_files(request):
    """Serves static files."""
    filepath = request.path
    if filepath == '/':
        return await handle_request(request)
    
    # Simple check for static files (e.g. from the templates folder)
    # Note: Cloudflare Pages handles static assets automatically, but this
    # is a fallback if needed for more complex routing.
    # For this project, all assets are in the templates folder, so this is not strictly necessary.
    
    return web.HTTPNotFound()

# The entry point for the Cloudflare Worker
async def worker_entrypoint(request, env):
    return await handle_request(request)
