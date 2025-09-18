import sqlite3

DATABASE_NAME = "picks.db"

def view_picks():
    """Reads and displays all records from the nfl_picks table."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT game_id, market, pick, confidence_level, rationale FROM nfl_picks')
        
        records = cursor.fetchall()
        
        if records:
            print("\n--- Generated Picks ---")
            for record in records:
                game_id, market, pick, confidence, rationale = record
                print(f"Game ID: {game_id}")
                print(f"Market: {market}")
                print(f"Pick: {pick}")
                print(f"Confidence: {confidence}")
                print(f"Rationale: {rationale}\n")
        else:
            print("\nNo picks found in the database. Please run `generate_picks.py` first.")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_picks()