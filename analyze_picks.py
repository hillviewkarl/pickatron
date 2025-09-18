import sqlite3

DATABASE_NAME = "picks.db"

def display_pick_report():
    """Displays a report of all generated picks, including specific odds."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Updated SELECT statement to pull pick_odds directly from nfl_picks
        cursor.execute('''
            SELECT
                p.id,
                f.commence_time,
                f.home_team,
                f.away_team,
                p.market,
                p.pick,
                p.pick_odds,
                p.confidence_level,
                p.result
            FROM nfl_picks AS p
            JOIN nfl_fixtures AS f
            ON p.game_id = f.id
            ORDER BY f.commence_time ASC
        ''')
        
        picks_data = cursor.fetchall()
        
        if not picks_data:
            print("No picks found in the database. Run `generate_picks.py` first!")
            return None

        print("\n--- Pickatron NFL Analysis Report ---")
        print("-------------------------------------")
        
        for pick in picks_data:
            (pick_id, commence_time, home_team, away_team, market, pick_text, 
             pick_odds, confidence, result) = pick
            
            result_display = result if result else "PENDING"
            
            print(f"[{pick_id}] Game: {away_team} @ {home_team}")
            print(f"    Date: {commence_time}")
            print(f"    Market: {market.capitalize()}")
            print(f"    Pick: {pick_text}")
            print(f"    Odds: {pick_odds}")
            print(f"    Confidence: {confidence}")
            print(f"    Result: {result_display}")
            print("-" * 25)
            
        return picks_data
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_pick_result(pick_id, result):
    """Updates the result for a specific pick in the database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE nfl_picks
            SET result = ?
            WHERE id = ?
        ''', (result, pick_id))
        conn.commit()
        print(f"Result for Pick ID {pick_id} updated to {result}.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def calculate_roi():
    """Calculates and prints the total ROI based on all settled picks."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        stake = 100

        # Now we pull the odds directly from the picks table
        cursor.execute('''
            SELECT
                p.result,
                p.pick_odds
            FROM nfl_picks AS p
            WHERE p.result IS NOT NULL AND p.result != 'PUSH'
        ''')
        picks = cursor.fetchall()

        if not picks:
            print("\nNo completed picks to calculate ROI yet.")
            return

        total_profit = 0
        total_staked = 0

        for result, pick_odds in picks:
            total_staked += stake
            if result == "WIN":
                profit = (pick_odds - 1) * stake
                total_profit += profit

        if total_staked > 0:
            roi = (total_profit / total_staked) * 100
            print(f"\n--- Performance Metrics ---")
            print(f"Total Bets: {len(picks)}")
            print(f"Total Staked: ${total_staked:,.2f}")
            print(f"Total Profit: ${total_profit:,.2f}")
            print(f"**Return on Investment (ROI): {roi:.2f}%**")
        else:
            print("\nCannot calculate ROI. Total staked is zero.")

    except sqlite3.Error as e:
        print(f"Database error during ROI calculation: {e}")
    finally:
        if conn:
            conn.close()

def main_menu():
    """Presents a menu to the user for interacting with the report."""
    while True:
        picks_data = display_pick_report()
        if not picks_data:
            break

        calculate_roi()

        print("\nOptions:")
        print("1. Enter results for a pick")
        print("2. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            try:
                pick_id = int(input("Enter the Pick ID to update: "))
                result = input("Enter result (WIN, LOSS, PUSH): ").strip().upper()
                if result in ["WIN", "LOSS", "PUSH"]:
                    update_pick_result(pick_id, result)
                else:
                    print("Invalid result. Please use WIN, LOSS, or PUSH.")
            except ValueError:
                print("Invalid ID. Please enter a number.")
        elif choice == '2':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()