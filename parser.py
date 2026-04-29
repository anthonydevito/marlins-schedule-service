### converts the raw MLB Stats API data into a nicer game info for the schedule endpoint
### will return a list of objects, one for each requested team ID
def parse_schedule_data(raw_data: dict, team_ids: list, parent_club_cache: dict) -> list:

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
                    opponent_id = home_id
                else:
                    our_team_name = home_team.get("name")
                    opponent_name = away_team.get("name")
                    opponent_id = away_id

                opponent_parent = parent_club_cache.get(opponent_id, "Unknown MLB Affiliate") # get parent club from cache

                status_code = game.get("status", {}).get("statusCode")
                game_state = "Not Started"
                
                ## confirm these letter codes
                ## temporary but I think these codes map to:
                ## F = Final, O = Game Over (but not officially final)
                if status_code in ["F", "O"]:
                    game_state = "Completed"
                elif status_code in ["I", "D", "DI"]: # I = In Progress, D = Delayed
                    game_state = "In Progress"


                ## initially had a dynamic cache for these levels
                ## but figured hard-coding would be best if we're only hitting 11 teams
                ## on a larger scale application, dynamically caching on startup would be the best option here
                team_id_to_level = {
                    "146": "MLB", # Miami Marlins
                    "564": "Triple-A", # Jacksonville Jumbo Shrimp
                    "4124": "Double-A", # Pensacola Blue Wahoos
                    "554": "High-A", # Beloit Sky Carp
                    "479": "Single-A", # Jupiter Hammerheads
                    "467": "Rookie", # FCL Marlins
                    "619": "Rookie", # DSL Marlins
                    "2127": "Rookie", # DSL Miami
                    "385": "Minor League Baseball", # Marlins Prospects
                    "3276": "Minor League Baseball", # Alternate Site
                    "3277": "Minor League Baseball" # Organization
                }
                
                level_str = team_id_to_level.get(tracked_id, "Unknown Level")

                game_info = {
                    "teamName": our_team_name,
                    "level": level_str,
                    "opponent": opponent_name,
                    "opponentParentClub": opponent_parent,
                    "state": game_state,
                    "venue": game.get("venue", {}).get("name")
                }

                ## add in state-dependent data
                if game_state == "Not Started":
                    game_info["gameTime"] = game.get("gameDate")
                    
                    ## extract starting pitchers
                    away_pitcher = game.get("teams", {}).get("away", {}).get("probablePitcher", {}).get("fullName")
                    home_pitcher = game.get("teams", {}).get("home", {}).get("probablePitcher", {}).get("fullName")

                    if away_pitcher and home_pitcher:
                         game_info["probablePitchers"] = f"{away_pitcher} vs {home_pitcher}"
                    elif away_pitcher:
                         game_info["probablePitchers"] = f"{away_pitcher} (Away) - Home TBD"
                    elif home_pitcher:
                         game_info["probablePitchers"] = f"Away TBD - {home_pitcher} (Home)"
                    else:
                         game_info["probablePitchers"] = "TBD"
                    
                elif game_state == "Completed":
                    ## get final score for completed games
                    away_score = game.get("teams", {}).get("away", {}).get("score", 0)
                    home_score = game.get("teams", {}).get("home", {}).get("score", 0)
                    
                    if tracked_id == away_id:
                        game_info["finalScore"] = f"{our_team_name} {away_score} - {opponent_name} {home_score}"
                    else:
                        game_info["finalScore"] = f"{our_team_name} {home_score} - {opponent_name} {away_score}"
                        
                    decisions = game.get("decisions", {})

                    game_info["winningPitcher"] = decisions.get("winner", {}).get("fullName", "Unknown")
                    game_info["losingPitcher"] = decisions.get("loser", {}).get("fullName", "Unknown")
                    
                    if "save" in decisions:
                        game_info["savePitcher"] = decisions.get("save", {}).get("fullName")

                elif game_state == "In Progress":
                    away_score = game.get("teams", {}).get("away", {}).get("score", 0)
                    home_score = game.get("teams", {}).get("home", {}).get("score", 0)
                    game_info["currentScore"] = f"{away_score} - {home_score}"
                    
                    ## extract linescore
                    linescore = game.get("linescore", {})
                    game_info["inning"] = f"{linescore.get('inningHalf', '')} {linescore.get('currentInningOrdinal', '')}"
                    game_info["outs"] = linescore.get("outs")

                    offense = linescore.get("offense", {})
                    defense = linescore.get("defense", {})

                    game_info["batterUp"] = offense.get("batter", {}).get("fullName", "Unknown")
                    game_info["currentPitcher"] = defense.get("pitcher", {}).get("fullName", "Unknown")

                    runners = []
                    if "first" in offense: runners.append("1B")
                    if "second" in offense: runners.append("2B")
                    if "third" in offense: runners.append("3B")
                    game_info["runnersOnBase"] = ", ".join(runners) if runners else "Bases Empty"

                results[tracked_id] = game_info

    ## format into final list of objects
    final_output = [{"team": tid, "gameInfo": info} for tid, info in results.items()]

    return final_output
