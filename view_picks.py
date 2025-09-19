import sqlite3

DATABASE_NAME = "picks.db"

def view_picks():
    """Reads and prints the contents of the nfl_picks table with matchup info."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                p.id,
                p.game_id,
                f.away_team,
                f.home_team,
                p.market,
                p.pick,
                p.odds,
                p.confidence_level,
                p.rationale
            FROM nfl_picks p
            LEFT JOIN nfl_fixtures f ON p.game_id = f.id
            ORDER BY p.id DESC
        ''')

        rows = cursor.fetchall()

        if not rows:
            print("No picks found. Run generate_picks.py first.")
            return

        print("--- Generated NFL Picks ---")
        for row in rows:
            pick_id, game_id, away_team, home_team, market, pick, odds, confidence, rationale = row
            matchup = f"{away_team} @ {home_team}" if away_team and home_team else "(matchup unavailable)"
            print(f"Pick ID: {pick_id}")
            print(f"  Game: {game_id}  {matchup}")
            print(f"  Market: {market}")
            print(f"  Pick: {pick}")
            if odds is not None:
                print(f"  Odds: {odds}")
            print(f"  Confidence: {confidence}")
            print(f"  Rationale: {rationale}")
            print("-" * 25)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_picks()


