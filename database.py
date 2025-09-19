import sqlite3

DATABASE_NAME = "picks.db"

def create_database():
    """Ensures the SQLite database file exists."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def create_fixtures_table():
    """Creates the nfl_fixtures table if it doesn't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfl_fixtures (
                id TEXT PRIMARY KEY,
                commence_time TEXT,
                home_team TEXT,
                away_team TEXT,
                moneyline_home_odds REAL,
                moneyline_away_odds REAL,
                spread_points REAL,
                spread_home_odds REAL,
                spread_away_odds REAL,
                total_points REAL,
                total_over_odds REAL,
                total_under_odds REAL
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def create_picks_table():
    """Creates the nfl_picks table if it doesn't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfl_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                market TEXT,
                pick TEXT,
                odds REAL,
                confidence_level TEXT,
                rationale TEXT,
                FOREIGN KEY (game_id) REFERENCES nfl_fixtures(id)
            )
        ''')
        conn.commit()
        # In case table existed without 'odds' column, attempt to add it
        try:
            cursor.execute("ALTER TABLE nfl_picks ADD COLUMN odds REAL")
            conn.commit()
        except sqlite3.Error:
            # Likely already exists; ignore
            pass
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def create_epl_fixtures_table():
    """Creates the epl_fixtures table for EPL odds."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS epl_fixtures (
                id TEXT PRIMARY KEY,
                commence_time TEXT,
                home_team TEXT,
                away_team TEXT,
                -- 3-way moneyline
                home_win_odds REAL,
                draw_odds REAL,
                away_win_odds REAL,
                -- totals (goals)
                total_goals REAL,
                over_odds REAL,
                under_odds REAL,
                -- BTTS
                btts_yes_odds REAL,
                btts_no_odds REAL
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
def view_nfl_fixtures():
    """Reads and prints the contents of the nfl_fixtures table."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Select only the columns needed for this view
        cursor.execute("SELECT id, commence_time, home_team, away_team FROM nfl_fixtures ORDER BY commence_time")
        
        fixtures = cursor.fetchall()
        
        if not fixtures:
            print("No NFL fixtures found in the database.")
            return

        print("--- Upcoming NFL Fixtures ---")
        for fixture in fixtures:
            # The order now matches the SELECT statement
            game_id, commence_time, home_team, away_team = fixture
            print(f"Game ID: {game_id}")
            print(f"  Starts: {commence_time}")
            print(f"  Matchup: {away_team} @ {home_team}")
            print("-" * 25)
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
    create_fixtures_table()
    create_picks_table()
    create_epl_fixtures_table()
    view_nfl_fixtures()
