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

def save_pick_to_db(game_id, market, pick, confidence, rationale, odds):
    """Saves a generated pick into the nfl_picks table, avoiding duplicates."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Check if a pick for this market and game already exists
        cursor.execute('''
            SELECT id, odds FROM nfl_picks
            WHERE game_id = ? AND market = ?
        ''', (game_id, market))
        existing = cursor.fetchone()
        if existing:
            pick_id, existing_odds = existing
            if existing_odds is None and odds is not None:
                cursor.execute('UPDATE nfl_picks SET pick = ?, odds = ?, confidence_level = ?, rationale = ? WHERE id = ?', (pick, odds, confidence, rationale, pick_id))
                conn.commit()
                print(f"Updated existing pick with odds for {game_id} ({market}).")
            else:
                print(f"Pick for {game_id} ({market}) already exists. Skipping.")
            return

        cursor.execute('''
            INSERT INTO nfl_picks (game_id, market, pick, odds, confidence_level, rationale)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (game_id, market, pick, odds, confidence, rationale))
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

    # Safely format odds that might be missing (None)
    def fmt(value):
        return "N/A" if value is None else f"{value}"

    home_spread_points = fmt(spread_points)
    away_spread_points = fmt(-spread_points) if spread_points is not None else "N/A"

    prompt = f"""
        You are an expert sports betting analyst. Your task is to provide a single, confident pick for an NFL game.
        
        Game: {away_team} @ {home_team}
        
        Current Betting Odds:
        - Moneyline: {home_team} ({fmt(moneyline_home)}) / {away_team} ({fmt(moneyline_away)})
        - Spread: {home_team} {home_spread_points} ({fmt(spread_home)}) / {away_team} {away_spread_points} ({fmt(spread_away)})
        - Total: Over {fmt(total_points)} ({fmt(total_over)}) / Under {fmt(total_points)} ({fmt(total_under)})

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
            
            # Determine odds for chosen outcome
            chosen_odds = None
            if market and pick:
                market_lower = market.lower()
                pick_lower = pick.lower()
                home_lower = (home_team or '').lower()
                away_lower = (away_team or '').lower()

                if market_lower == 'moneyline':
                    if home_lower and home_lower in pick_lower:
                        chosen_odds = moneyline_home
                    elif away_lower and away_lower in pick_lower:
                        chosen_odds = moneyline_away
                elif market_lower == 'spread':
                    # If pick mentions home team, use home spread odds; if away team, use away spread odds
                    if home_lower and home_lower in pick_lower:
                        chosen_odds = spread_home
                    elif away_lower and away_lower in pick_lower:
                        chosen_odds = spread_away
                elif market_lower == 'total' or market_lower == 'totals':
                    if 'over' in pick_lower:
                        chosen_odds = total_over
                    elif 'under' in pick_lower:
                        chosen_odds = total_under
            
            if market and pick and confidence and rationale:
                save_pick_to_db(game_id, market, pick, confidence, rationale, chosen_odds)
            else:
                print(f"Failed to parse response for game {game_id}. Response: {response.text}")
        else:
            print(f"No valid response from Gemini for game {game_id}.")

    except Exception as e:
        print(f"An error occurred while generating pick for {game_id}: {e}")

if __name__ == "__main__":
    generate_and_save_picks()