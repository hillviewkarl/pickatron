import requests
import sqlite3
import os
from dotenv import load_dotenv
from sports_config import SPORTS

# This line loads the environment variables from your .env file
load_dotenv() 

# Get your API key from the environment variable named "ODDS_API_KEY"
API_KEY = os.getenv("ODDS_API_KEY")

def _build_odds_url(sport_key: str, regions: str, markets: list[str]) -> str:
    markets_param = ",".join(markets)
    return f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions={regions}&markets={markets_param}"

DATABASE_NAME = "picks.db"

def _extract_best_prices(bookmakers, home_team, away_team):
    """Extracts best available odds across bookmakers for moneyline, spread, and totals."""
    moneyline_home = None
    moneyline_away = None
    spread_points = None
    spread_home = None
    spread_away = None
    total_points = None
    total_over = None
    total_under = None

    if not bookmakers:
        return (moneyline_home, moneyline_away, spread_points, spread_home, spread_away, total_points, total_over, total_under)

    for bm in bookmakers:
        markets = bm.get('markets', [])
        for market in markets:
            key = market.get('key')
            outcomes = market.get('outcomes', [])
            if key == 'h2h':
                # Moneyline
                for o in outcomes:
                    if o.get('name') == home_team:
                        price = o.get('price')
                        if price is not None:
                            moneyline_home = price if moneyline_home is None else max(moneyline_home, price)
                    elif o.get('name') == away_team:
                        price = o.get('price')
                        if price is not None:
                            moneyline_away = price if moneyline_away is None else max(moneyline_away, price)
            elif key == 'spreads':
                # Spreads (assume same point for both outcomes within a market snapshot)
                # Choose the line with highest absolute price or first valid
                best_price_sum = None
                candidate_points = None
                candidate_home = None
                candidate_away = None
                for o in outcomes:
                    if o.get('name') == home_team:
                        candidate_home = o.get('price')
                        candidate_points = o.get('point')
                    elif o.get('name') == away_team:
                        candidate_away = o.get('price')
                        # keep existing candidate_points if already from home
                    # When both sides seen, evaluate
                    if candidate_home is not None and candidate_away is not None and candidate_points is not None:
                        score = abs(candidate_home) + abs(candidate_away)
                        if best_price_sum is None or score > best_price_sum:
                            best_price_sum = score
                            spread_points = candidate_points
                            spread_home = candidate_home
                            spread_away = candidate_away
                        candidate_points = None
                        candidate_home = None
                        candidate_away = None
            elif key == 'totals':
                # Totals (Over/Under)
                candidate_total = None
                over = None
                under = None
                for o in outcomes:
                    if o.get('name') == 'Over':
                        over = o.get('price')
                        candidate_total = o.get('point')
                    elif o.get('name') == 'Under':
                        under = o.get('price')
                        candidate_total = o.get('point') if candidate_total is None else candidate_total
                    if over is not None and under is not None and candidate_total is not None:
                        # Prefer highest combined price
                        if total_points is None or (abs(over) + abs(under)) > (abs(total_over or 0) + abs(total_under or 0)):
                            total_points = candidate_total
                            total_over = over
                            total_under = under

    return (moneyline_home, moneyline_away, spread_points, spread_home, spread_away, total_points, total_over, total_under)

def _extract_epl_odds(bookmakers, home_team, away_team):
    """Extract best available odds for EPL: 3-way result, totals (goals), BTTS."""
    home_win = None
    draw = None
    away_win = None
    total_goals = None
    over_odds = None
    under_odds = None
    btts_yes = None
    btts_no = None

    if not bookmakers:
        return (home_win, draw, away_win, total_goals, over_odds, under_odds, btts_yes, btts_no)

    for bm in bookmakers:
        for market in bm.get('markets', []):
            key = market.get('key')
            outcomes = market.get('outcomes', [])
            if key in ('h2h_3_way', 'h2h'):  # some books may use h2h for 3-way
                for o in outcomes:
                    name = (o.get('name') or '').lower()
                    price = o.get('price')
                    if price is None:
                        continue
                    if name == (home_team or '').lower():
                        home_win = price if home_win is None else max(home_win, price)
                    elif name == (away_team or '').lower():
                        away_win = price if away_win is None else max(away_win, price)
                    elif name == 'draw':
                        draw = price if draw is None else max(draw, price)
            elif key == 'totals':
                cand_total = None
                cand_over = None
                cand_under = None
                for o in outcomes:
                    if o.get('name') == 'Over':
                        cand_over = o.get('price')
                        cand_total = o.get('point')
                    elif o.get('name') == 'Under':
                        cand_under = o.get('price')
                        cand_total = o.get('point') if cand_total is None else cand_total
                    if cand_over is not None and cand_under is not None and cand_total is not None:
                        if total_goals is None or (abs(cand_over) + abs(cand_under)) > (abs(over_odds or 0) + abs(under_odds or 0)):
                            total_goals = cand_total
                            over_odds = cand_over
                            under_odds = cand_under
            elif key == 'btts':
                for o in outcomes:
                    name = (o.get('name') or '').lower()
                    price = o.get('price')
                    if name == 'yes' and price is not None:
                        btts_yes = price if btts_yes is None else max(btts_yes, price)
                    elif name == 'no' and price is not None:
                        btts_no = price if btts_no is None else max(btts_no, price)

    return (home_win, draw, away_win, total_goals, over_odds, under_odds, btts_yes, btts_no)

def fetch_and_store_all():
    """Fetches upcoming fixtures for all configured sports/leagues and upserts odds."""
    # Check if the API key was successfully loaded
    if not API_KEY:
        print("Error: ODDS_API_KEY not found. Please check your .env file.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        for sport_name, sport_cfg in SPORTS.items():
            regions = sport_cfg["regions"]
            markets = sport_cfg["markets"]
            leagues = sport_cfg["leagues"]
            print(f"Fetching {sport_name} data...")

            for league in leagues:
                league_name = league["name"]
                sport_key = league["sport_key"]
                table = league["table"]
                url = _build_odds_url(sport_key, regions, markets)
                print(f"  League {league_name}: requesting markets {markets}")
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as http_err:
                    if getattr(http_err.response, 'status_code', None) == 422 and sport_name == "Soccer":
                        reduced_markets = [m for m in markets if m != "btts"]
                        print(f"  422 for {league_name}. Retrying with {reduced_markets}...")
                        response = requests.get(_build_odds_url(sport_key, regions, reduced_markets))
                        response.raise_for_status()
                    else:
                        raise

                data = response.json()
                inserted = 0
                updated = 0

                if sport_name == "American Football":
                    for game in data:
                        game_id = game['id']
                        commence_time = game['commence_time']
                        home_team = game['home_team']
                        away_team = game['away_team']
                        bookmakers = game.get('bookmakers', [])
                        (
                            moneyline_home,
                            moneyline_away,
                            spread_points,
                            spread_home,
                            spread_away,
                            total_points,
                            total_over,
                            total_under,
                        ) = _extract_best_prices(bookmakers, home_team, away_team)

                        cursor.execute(f"SELECT id FROM {table} WHERE id = ?", (game_id,))
                        exists = cursor.fetchone()

                        if not exists:
                            cursor.execute(
                                f"""
                                INSERT INTO {table} (
                                    id, commence_time, home_team, away_team,
                                    moneyline_home_odds, moneyline_away_odds,
                                    spread_points, spread_home_odds, spread_away_odds,
                                    total_points, total_over_odds, total_under_odds
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    game_id, commence_time, home_team, away_team,
                                    moneyline_home, moneyline_away,
                                    spread_points, spread_home, spread_away,
                                    total_points, total_over, total_under,
                                )
                            )
                            inserted += 1
                        else:
                            cursor.execute(
                                f"""
                                UPDATE {table} SET
                                    commence_time = ?,
                                    home_team = ?,
                                    away_team = ?,
                                    moneyline_home_odds = ?,
                                    moneyline_away_odds = ?,
                                    spread_points = ?,
                                    spread_home_odds = ?,
                                    spread_away_odds = ?,
                                    total_points = ?,
                                    total_over_odds = ?,
                                    total_under_odds = ?
                                WHERE id = ?
                                """,
                                (
                                    commence_time,
                                    home_team,
                                    away_team,
                                    moneyline_home,
                                    moneyline_away,
                                    spread_points,
                                    spread_home,
                                    spread_away,
                                    total_points,
                                    total_over,
                                    total_under,
                                    game_id,
                                )
                            )
                            updated += 1

                elif sport_name == "Soccer":
                    for match in data:
                        match_id = match['id']
                        commence_time = match['commence_time']
                        home_team = match['home_team']
                        away_team = match['away_team']
                        bookmakers = match.get('bookmakers', [])

                        (home_win, draw, away_win, total_goals, over_odds, under_odds, btts_yes, btts_no) = _extract_epl_odds(bookmakers, home_team, away_team)

                        cursor.execute(f"SELECT id FROM {table} WHERE id = ?", (match_id,))
                        exists = cursor.fetchone()

                        if not exists:
                            cursor.execute(
                                f"""
                                INSERT INTO {table} (
                                    id, commence_time, home_team, away_team,
                                    home_win_odds, draw_odds, away_win_odds,
                                    total_goals, over_odds, under_odds,
                                    btts_yes_odds, btts_no_odds
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    match_id, commence_time, home_team, away_team,
                                    home_win, draw, away_win,
                                    total_goals, over_odds, under_odds,
                                    btts_yes, btts_no,
                                )
                            )
                            inserted += 1
                        else:
                            cursor.execute(
                                f"""
                                UPDATE {table} SET
                                    commence_time = ?,
                                    home_team = ?,
                                    away_team = ?,
                                    home_win_odds = ?,
                                    draw_odds = ?,
                                    away_win_odds = ?,
                                    total_goals = ?,
                                    over_odds = ?,
                                    under_odds = ?,
                                    btts_yes_odds = ?,
                                    btts_no_odds = ?
                                WHERE id = ?
                                """,
                                (
                                    commence_time, home_team, away_team,
                                    home_win, draw, away_win,
                                    total_goals, over_odds, under_odds,
                                    btts_yes, btts_no,
                                    match_id,
                                )
                            )
                            updated += 1

                conn.commit()
                print(f"  {league_name} upserts complete. Inserted: {inserted}, Updated: {updated}.")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except KeyError as e:
        print(f"Key error in API response: Missing expected key {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fetch_and_store_all()