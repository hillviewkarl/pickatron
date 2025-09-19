SPORTS = {
    "American Football": {
        "regions": "us",
        "markets": ["h2h", "spreads", "totals"],
        "leagues": [
            {"name": "NFL", "sport_key": "americanfootball_nfl", "table": "nfl_fixtures"},
        ],
        "fields": [
            "id", "commence_time", "home_team", "away_team",
            "moneyline_home_odds", "moneyline_away_odds",
            "spread_points", "spread_home_odds", "spread_away_odds",
            "total_points", "total_over_odds", "total_under_odds",
        ],
    },
    "Soccer": {
        "regions": "uk,eu,us",
        "markets": ["h2h", "totals", "btts"],
        "leagues": [
            {"name": "EPL", "sport_key": "soccer_epl", "table": "epl_fixtures"},
            # Add more leagues here later
        ],
        "fields": [
            "id", "commence_time", "home_team", "away_team",
            # 3-way moneyline
            "home_win_odds", "draw_odds", "away_win_odds",
            # total goals
            "total_goals", "over_odds", "under_odds",
            # BTTS
            "btts_yes_odds", "btts_no_odds",
        ],
    },
}


