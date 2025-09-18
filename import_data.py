import requests
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

SPORT_KEY = "americanfootball_nfl"
REGIONS = "us"
MARKETS = "h2h,spreads,totals"
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={MARKETS}"

DATABASE_NAME = "picks.db"

def fetch_and_store_nfl_fixtures():
    """Fetches upcoming NFL fixtures with odds and stores them in the database."""
    if not API_KEY:
        print("Error: ODDS_API_KEY not found. Please check your .env file.")
        return

    conn = None
    try:
        print("Fetching data from The Odds API...")
        response = requests.get(ODDS_API_URL)
        response.raise_for_status()
        
        data = response.json()
        
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        new_fixtures_count = 0
        
        for game in data:
            game_id = game['id']
            commence_time = game['commence_time']
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Initialize odds variables to None
            moneyline_home_odds = None
            moneyline_away_odds = None
            spread_points = None
            spread_home_odds = None
            spread_away_odds = None
            total_points = None
            total_over_odds = None
            total_under_odds = None

            # Find a bookmaker with the odds we need
            if 'bookmakers' in game and game['bookmakers']:
                bookmaker = game['bookmakers'][0] # Use the first bookmaker for simplicity

                # Parse the markets for h2h (moneyline), spreads, and totals
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                moneyline_home_odds = outcome['price']
                            elif outcome['name'] == away_team:
                                moneyline_away_odds = outcome['price']
                    elif market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                spread_points = outcome['point']
                                spread_home_odds = outcome['price']
                            elif outcome['name'] == away_team:
                                spread_away_odds = outcome['price']
                    elif market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            if outcome['name'] == 'Over':
                                total_points = outcome['point']
                                total_over_odds = outcome['price']
                            elif outcome['name'] == 'Under':
                                total_under_odds = outcome['price']

            # Check if the fixture already exists (if it does, we'll skip it)
            cursor.execute("SELECT id FROM nfl_fixtures WHERE id = ?", (game_id,))
            existing_fixture = cursor.fetchone()

            if not existing_fixture:
                # Insert the fixture and odds data into the database
                cursor.execute(
                    "INSERT INTO nfl_fixtures (id, commence_time, home_team, away_team, moneyline_home_odds, moneyline_away_odds, spread_points, spread_home_odds, spread_away_odds, total_points, total_over_odds, total_under_odds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (game_id, commence_time, home_team, away_team, moneyline_home_odds, moneyline_away_odds, spread_points, spread_home_odds, spread_away_odds, total_points, total_over_odds, total_under_odds)
                )
                new_fixtures_count += 1
                
        conn.commit()
        print(f"Successfully added {new_fixtures_count} new fixtures with odds to the database.")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except KeyError as e:
        print(f"Key error in API response: Missing expected key {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fetch_and_store_nfl_fixtures()