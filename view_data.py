import sqlite3

DATABASE_NAME = "picks.db"

def view_fixtures():
    """Reads and prints the contents of the nfl_fixtures table with odds if available."""
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
                moneyline_home_odds,
                moneyline_away_odds,
                spread_points,
                spread_home_odds,
                spread_away_odds,
                total_points,
                total_over_odds,
                total_under_odds
            FROM nfl_fixtures
            ORDER BY commence_time
        ''')

        rows = cursor.fetchall()

        if not rows:
            print("No data found in nfl_fixtures. Run import_data.py first.")
            return

        print("--- NFL Fixtures ---")
        for row in rows:
            (
                game_id,
                commence_time,
                away_team,
                home_team,
                ml_home,
                ml_away,
                spread_pts,
                spread_home,
                spread_away,
                total_pts,
                over_odds,
                under_odds,
            ) = row

            def fmt(value):
                return "N/A" if value is None else f"{value}"

            print(f"Game ID: {game_id}")
            print(f"  Starts: {fmt(commence_time)}")
            print(f"  Matchup: {fmt(away_team)} @ {fmt(home_team)}")
            print(f"  Moneyline: {fmt(home_team)} ({fmt(ml_home)}) / {fmt(away_team)} ({fmt(ml_away)})")
            home_spread = fmt(spread_pts)
            away_spread = fmt(-spread_pts) if spread_pts is not None else "N/A"
            print(f"  Spread: {fmt(home_team)} {home_spread} ({fmt(spread_home)}) / {fmt(away_team)} {away_spread} ({fmt(spread_away)})")
            print(f"  Total: Over {fmt(total_pts)} ({fmt(over_odds)}) / Under {fmt(total_pts)} ({fmt(under_odds)})")
            print("-" * 25)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_fixtures()


