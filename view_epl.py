import sqlite3

DATABASE_NAME = "picks.db"

def view_epl_fixtures():
    """Reads and prints the contents of the epl_fixtures table with odds."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id,
                commence_time,
                away_team,
                home_team,
                home_win_odds,
                draw_odds,
                away_win_odds,
                total_goals,
                over_odds,
                under_odds,
                btts_yes_odds,
                btts_no_odds
            FROM epl_fixtures
            ORDER BY commence_time
        ''')

        rows = cursor.fetchall()

        if not rows:
            print("No data found in epl_fixtures. Run import_data.py first.")
            return

        def fmt(value):
            return "N/A" if value is None else f"{value}"

        print("--- EPL Fixtures ---")
        for row in rows:
            (
                match_id,
                commence_time,
                away_team,
                home_team,
                home_win,
                draw,
                away_win,
                total_goals,
                over,
                under,
                btts_yes,
                btts_no,
            ) = row

            print(f"Match ID: {match_id}")
            print(f"  Starts: {fmt(commence_time)}")
            print(f"  Matchup: {fmt(away_team)} @ {fmt(home_team)}")
            print(f"  3-Way: {fmt(home_team)} ({fmt(home_win)}) / Draw ({fmt(draw)}) / {fmt(away_team)} ({fmt(away_win)})")
            print(f"  Total Goals: Over {fmt(total_goals)} ({fmt(over)}) / Under {fmt(total_goals)} ({fmt(under)})")
            print(f"  BTTS: Yes ({fmt(btts_yes)}) / No ({fmt(btts_no)})")
            print("-" * 25)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_epl_fixtures()


