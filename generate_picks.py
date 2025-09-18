import os
import sqlite3
import google.generativeai as genai
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
GOOGLE_CSE_KEY = os.getenv("GOOGLE_CSE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set up Gemini API configuration
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

DATABASE_NAME = "picks.db"

def get_fixtures_from_db():
    """Fetches a single upcoming NFL fixture with betting odds from the database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                id,
                home_team,
                away_team,
                moneyline_home_odds,
                moneyline_away_odds,
                spread_points,
                spread_home_odds,
                spread_away_odds,
                total_points,
                total_over_odds,
                total_under_odds
            FROM nfl_fixtures
            LIMIT 1
        ''')
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def save_pick_to_db(game_id, market, pick, confidence, rationale, pick_odds):
    """Saves a generated pick into the nfl_picks table, avoiding duplicates."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Check if a pick for this market and game already exists
        cursor.execute('''
            SELECT COUNT(*) FROM nfl_picks
            WHERE game_id = ? AND market = ?
        ''', (game_id, market))
        if cursor.fetchone()[0] > 0:
            print(f"Pick for {game_id} ({market}) already exists. Skipping.")
            return

        cursor.execute('''
            INSERT INTO nfl_picks (game_id, market, pick, confidence_level, rationale, pick_odds)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (game_id, market, pick, confidence, rationale, pick_odds))
        conn.commit()
        print(f"Successfully saved pick for {game_id} ({market}).")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def generate_and_save_picks():
    """Main function to generate and save a pick for a single upcoming fixture."""
    fixture = get_fixtures_from_db()
    
    if not fixture:
        print("No fixtures found. Please run `import_data.py` first.")
        return

    print("Generating a single pick with Gemini...")
    
    (game_id, home_team, away_team,
     moneyline_home, moneyline_away,
     spread_points, spread_home, spread_away,
     total_points, total_over, total_under) = fixture

    prompt = f"""
        You are an expert sports betting analyst. Your task is to provide a single, confident pick for an NFL game.
        
        Game: {away_team} @ {home_team}
        
        Current Betting Odds:
        - Moneyline: {home_team} ({moneyline_home}) / {away_team} ({moneyline_away})
        - Spread: {home_team} {spread_points} ({spread_home}) / {away_team} {-spread_points} ({spread_away})
        - Total: Over {total_points} ({total_over}) / Under {total_points} ({total_under})

        Analyze the matchup and provide your top betting pick.
        
        Your response must be a single block of text formatted as follows:
        
        Market: [Moneyline, Spread, or Total]
        Pick: [Your specific pick, e.g., 'Houston Texans -2.5' or 'Over 45.5']
        Confidence: [High, Medium, or Low]
        Rationale: [A brief, two-sentence explanation of why you made this pick, citing key factors like matchups, form, or injuries.]
    """
    
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            lines = response.text.strip().split('\n')
            data = {line.split(': ')[0].strip().lower(): line.split(': ')[1].strip() for line in lines if ': ' in line}

            market = data.get('market')
            pick = data.get('pick')
            confidence = data.get('confidence')
            rationale = data.get('rationale')
            
            # Extract the specific odds for the pick
            pick_odds = None
            if market.lower() == 'moneyline':
                if pick.lower().startswith(home_team.lower()):
                    pick_odds = moneyline_home
                else:
                    pick_odds = moneyline_away
            elif market.lower() == 'spread':
                if pick.lower().startswith(home_team.lower()):
                    pick_odds = spread_home
                else:
                    pick_odds = spread_away
            elif market.lower() == 'total':
                if 'over' in pick.lower():
                    pick_odds = total_over
                else:
                    pick_odds = total_under
            
            if market and pick and confidence and rationale and pick_odds:
                save_pick_to_db(game_id, market, pick, confidence, rationale, pick_odds)
            else:
                print(f"Failed to parse response for game {game_id}. Response: {response.text}")
        else:
            print(f"No valid response from Gemini for game {game_id}.")

    except Exception as e:
        print(f"An error occurred while generating pick for {game_id}: {e}")

if __name__ == "__main__":
    generate_and_save_picks()