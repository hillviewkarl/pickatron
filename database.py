import sqlite3

DATABASE_NAME = "picks.db"

def create_database():
    """Creates the SQLite database file and tables if they don't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        print(f"Database created: {DATABASE_NAME}")
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def create_fixtures_table():
    """Creates the nfl_fixtures table to store game data and odds."""
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
        print("Table 'nfl_fixtures' created successfully.")
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def create_picks_table():
    """Creates the nfl_picks table to store generated picks."""
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
                confidence_level TEXT,
                rationale TEXT,
                result TEXT,
                pick_odds REAL,
                FOREIGN KEY (game_id) REFERENCES nfl_fixtures(id)
            )
        ''')
        conn.commit()
        print("Table 'nfl_picks' created successfully.")
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
    create_fixtures_table()
    create_picks_table()