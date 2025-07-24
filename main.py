from chess_tournament import *

if __name__ == "__main__":
    # --- File Paths ---
    # You can edit them as you want
    REGISTERED_PLAYERS_CSV = "import/chess_players.csv"
    PLAYERS_CSV = "export/tournament_players.csv"
    MATCHES_CSV = "export/tournament_matches.csv"
    META_CSV = "export/tournament_meta.csv"
    STANDINGS_CSV = "export/standings.csv"

    # Clean up any previous test files for a clean run
    for f in [PLAYERS_CSV, MATCHES_CSV, META_CSV, STANDINGS_CSV]:
        if os.path.exists(f):
            os.remove(f)
            print(f"Cleaned up {f}")

    # --- Setup Tournament with 21 Players ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | Setting up Tournament...\nHow many rounds would you like to have?")
    num_rounds=int(input())
    tournament = Tournament(num_rounds)

    tournament.load_players_from_csv(REGISTERED_PLAYERS_CSV)

    # You can add players here
    players: dict[str, int] = {
        #Name : ELO
        "Alice": 400,
        "Bob": 400,
        "Charlie": 400,
        "Diana": 400,
        "Noah": 400,
    }
    for name, elo in players.items():
        tournament.add_player(name, elo)

    tournament.print_standings()

    #helper function
    def enter_results(round_num: int, tournament: Tournament) -> None:
        print(f"\n{Tournament().now()} | Entering Results for Round {round_num}...")
        for match in tournament.current_matches:
            if not match.is_bye_match:
                result: int = None # Don't enter results for bye/half-bye matches
                results_options = {0: "0.5-0.5", 1: "1-0", 2: "0-1"}
                print(f"Match {match.match_id}: {match.player_white} vs {match.player_black}")
                print(f"Options: {results_options}")
                while result not in [0, 1, 2]:
                    result = int(input("Enter valid result of the match: "))
                tournament.enter_result(match.match_id, results_options[result], match.round_number)


    # ---  Round 1: Random Pairing ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | ROUND 1: RANDOM PAIRING")
    tournament.pair_round("random")
    tournament.print_pairings()
    enter_results(1, tournament)
    tournament.end_round()
    tournament.export_standings_to_csv(f"export/leaderboard/standings1.csv")
    tournament.export_standings_to_txt(f"export/leaderboard/standings1.txt")

    if num_rounds >= 2:
        # --- Round 2: Monrad System ---
        for round_num in range(2, 3): 
            print(f"\n{Tournament().long_line()}")
            print(f"{Tournament().now()} | ROUND {round_num}: MONRAD SYSTEM PAIRING")
            
            # Example: Mark Bob as absent in Round 2 for half bye test
            if round_num == 2:
                absent_player_r2 = tournament.get_player_by_name("Bob")
                if absent_player_r2 is not None:
                    absent_player_r2.is_present = False
                    print(f"{Tournament().now()} | Player {absent_player_r2.name_surname} is marked as absent for this round.")

            tournament.pair_round("monrad")
            tournament.print_pairings()
            enter_results(round_num, tournament)
            tournament.end_round()
            tournament.export_standings_to_csv(f"export/leaderboard/standings{round_num}.csv")
            tournament.export_standings_to_txt(f"export/leaderboard/standings{round_num}.txt")


    bob_player = tournament.get_player_by_name("Bob")
    if bob_player is not None:
        bob_player.is_present = True
        bob_player.has_bye_this_round = False

    # --- Other rounds: Dutch System ---
    if num_rounds >= 3:
        for round_num in range(3, num_rounds + 1):
            print(f"\n{Tournament().long_line()}")
            print(f"{Tournament().now()} | ROUND {round_num}: Dutch SYSTEM PAIRING")
            tournament.pair_round("dutch")
            tournament.print_pairings()
            enter_results(round_num, tournament)
            tournament.end_round()
            tournament.export_standings_to_csv(f"export/leaderboard/standings{round_num}.csv")
            tournament.export_standings_to_txt(f"export/leaderboard/standings{round_num}.txt")
    

    # --- Final Standings and Export ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | TOURNAMENT ENDED. FINAL STANDINGS:")

    tournament.export_standings_to_csv("export/final_standings.csv")

    # --- Test Save/Load ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | Testing Tournament State Save/Load...")
    tournament.save_tournament_state(PLAYERS_CSV, MATCHES_CSV, META_CSV)

    for round in range(tournament.num_rounds):
        tournament.export_pairings_to_txt(f"export/pairings/final_pairings_round{round+1}.txt", round+1)

"""    # --- Final Cleanup --- (if you want)
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | Cleaning up generated files...")
    for f in [PLAYERS_CSV, MATCHES_CSV, META_CSV, STANDINGS_CSV, PAIRINGS_TXT, "final_standings.csv", "final_pairings_round6.txt"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"Cleaned up {f}")
    print(f"{Tournament().now()} | Cleanup complete.")"""