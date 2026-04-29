### converts the raw MLB Stats API data into a nicer game info for the schedule endpoint
### will return a list of objects, one for each requested team ID
def parse_schedule_data(raw_data: dict, team_ids: list) -> list:

    results = {str(team_id): {} for team_id in team_ids} # starter dict

    dates = raw_data.get("dates", [])
    if not dates:
        return [{"team": tid, "gameInfo": info} for tid, info in results.items()] # return empty object if no games

    games = dates[0].get("games", [])

    for game in games:

        away_team = game.get("teams", {}).get("away", {}).get("team", {})
        home_team = game.get("teams", {}).get("home", {}).get("team", {})
        
        away_id = str(away_team.get("id"))
        home_id = str(home_team.get("id"))

        for tracked_id in [away_id, home_id]:

            ## only run if a Marlins affiliate we care about
            if tracked_id in results:

                ## determine who our team is and who the opponent is
                if tracked_id == away_id:
                    our_team_name = away_team.get("name")
                    opponent_name = home_team.get("name")
                else:
                    our_team_name = home_team.get("name")
                    opponent_name = away_team.get("name")

                status_code = game.get("status", {}).get("statusCode")
                game_state = "Not Started"

                print("status code is here: ", status_code)
                
                ## temporary but I think these codes map to:
                ## S = Scheduled, P = Pre-Game, F = Final, I = In Progress, O = Game Over (but not officially final)
                if status_code in ["F", "O"]:
                    game_state = "Completed"
                elif status_code in ["I", "M", "MA"]: # M & MA = Manager challenge
                    game_state = "In Progress"

                game_info = {
                    "teamName": our_team_name,
                    "level": game.get("gameType"), # returns integer.  needs to find map and convert maybe?
                    "opponent": opponent_name,
                    "opponentParentClub": "need to do this still", 
                    "state": game_state,
                    "venue": game.get("venue", {}).get("name")
                }

                ## add in state-dependent data
                if game_state == "Not Started":
                    game_info["gameTime"] = game.get("gameDate")
                    game_info["probablePitchers"] = "N/A" # look into this, maybe in base payload?
                    
                elif game_state == "Completed":
                    ## get final score for completed games
                    away_score = game.get("teams", {}).get("away", {}).get("score", 0)
                    home_score = game.get("teams", {}).get("home", {}).get("score", 0)
                    
                    if tracked_id == away_id:
                        game_info["finalScore"] = f"{our_team_name} {away_score} - {opponent_name} {home_score}"
                    else:
                        game_info["finalScore"] = f"{our_team_name} {home_score} - {opponent_name} {away_score}"
                        
                    # pitching decisions??  come back to

                elif game_state == "In Progress":
                    away_score = game.get("teams", {}).get("away", {}).get("score", 0)
                    home_score = game.get("teams", {}).get("home", {}).get("score", 0)
                    game_info["currentScore"] = f"{away_score} - {home_score}"
                    # might need more inputs to get things like current inning or outs....come back to

                results[tracked_id] = game_info

    ## format into final list of objects
    final_output = [{"team": tid, "gameInfo": info} for tid, info in results.items()]

    return final_output
