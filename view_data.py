import sqlite3

DATABASE_NAME = "picks.db"

def view_nfl_fixtures():
    """Reads and prints the contents of the nfl_fixtures table with odds."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Select all columns from the updated fixtures table
        cursor.execute("SELECT * FROM nfl_fixtures ORDER BY commence_time")
        
        fixtures = cursor.fetchall()
        
        if not fixtures:
            print("No NFL fixtures found in the database.")
            return

        print("--- Upcoming NFL Fixtures with Odds ---")
        print("---------------------------------------")
        
        for fixture in fixtures:
            # Unpack all 12 columns from the updated table
            (game_id, commence_time, home_team, away_team, 
             moneyline_home_odds, moneyline_away_odds, 
             spread_points, spread_home_odds, spread_away_odds, 
             total_points, total_over_odds, total_under_odds) = fixture
            
            print(f"Game ID: {game_id}")
            print(f"  Starts: {commence_time}")
            print(f"  Matchup: {away_team} @ {home_team}")
            
            if moneyline_home_odds is not None:
                print(f"  Moneyline: {home_team} ({moneyline_home_odds}), {away_team} ({moneyline_away_odds})")
            
            if spread_points is not None:
                print(f"  Spread: {home_team} {spread_points} ({spread_home_odds}), {away_team} {-spread_points} ({spread_away_odds})")
                
            if total_points is not None:
                print(f"  Total: Over {total_points} ({total_over_odds}), Under {total_points} ({total_under_odds})")
            
            print("-" * 25)
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_nfl_fixtures()