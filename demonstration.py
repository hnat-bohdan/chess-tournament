from chess_tournament import *
import timeit

# --- DEMONSTRATION & SIMULATION ---
if __name__ == "__main__":
    start = timeit.default_timer()
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
    print(f"{Tournament().now()} | Setting up Tournament with 19 Players (best performance for biggest number of players)")
    tournament = Tournament(num_rounds=6)

    tournament.load_players_from_csv(REGISTERED_PLAYERS_CSV)

    # Generate 14
    player_names = [
        "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry","Ivy",
        "Jack","Karen", "Liam", "Mia", "Noah",]
    for i, name in enumerate(player_names):
        elo = 400 + 50 *random.randint(0, 32) # Random ELO between 400 and 2000
        tournament.add_player(name, elo)

    tournament.print_standings()

    # --- Simulate Round 1: Random Pairing ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | SIMULATING ROUND 1: RANDOM PAIRING")

    tournament.pair_round("random")
    tournament.print_pairings()

    # Simulate random results for current matches
    print(f"\n{Tournament().now()} | Entering Random Results for Round 1...")
    for match in tournament.current_matches:
        if not match.is_bye_match: # Don't enter results for bye/half-bye matches
            results_options = ["1-0", "0-1", "0.5-0.5"]
            random_result = random.choice(results_options)
            tournament.enter_result(match.match_id, random_result, match.round_number)

    tournament.end_round()



    # --- Simulate Rounds 2-4: Monrad System ---
    for round_num in range(2, 5): # Rounds 2, 3, 4
        print(f"\n{Tournament().long_line()}")
        print(f"{Tournament().now()} | SIMULATING ROUND {round_num}: MONRAD SYSTEM PAIRING")
        
        # Example: Mark Jack as absent in Round 3 for half bye test
        if round_num == 3:
            absent_player_r3 = tournament.get_player_by_name("Jack")
            if absent_player_r3:
                absent_player_r3.is_present = False
                print(f"{Tournament().now()} | Player {absent_player_r3.name_surname} is marked as absent for this round.")
        else: # Ensure Jack is present if not round 3
            jack_player = tournament.get_player_by_name("Jack")
            if jack_player:
                jack_player.is_present = True

        tournament.pair_round("monrad")
        tournament.print_pairings()

        print(f"\n{Tournament().now()} | Entering Random Results for Round {round_num}...")
        for match in tournament.current_matches:
            if not match.is_bye_match:
                results_options = ["1-0", "0-1", "0.5-0.5"]
                random_result = random.choice(results_options)
                tournament.enter_result(match.match_id, random_result, match.round_number)
        
        tournament.end_round()

    # --- Simulate Rounds 5-6: Dutch System ---
    for round_num in range(5, 7): # Rounds 5, 6
        print(f"\n{Tournament().long_line()}")
        print(f"{Tournament().now()} | SIMULATING ROUND {round_num}: DUTCH SYSTEM PAIRING")

        # Example: Mark Karen as absent in Round 5
        if round_num == 5:
            absent_player_r5 = tournament.get_player_by_name("Karen")
            if absent_player_r5:
                absent_player_r5.is_present = False
                print(f"{Tournament().now()} | Player {absent_player_r5.name_surname} is marked as absent for this round.")
        else:
            karen_player = tournament.get_player_by_name("Karen")
            if karen_player:
                karen_player.is_present = True

        tournament.pair_round("dutch")
        tournament.print_pairings()

        print(f"\n{Tournament().now()} | Entering Random Results for Round {round_num}...")
        for match in tournament.current_matches:
            if not match.is_bye_match:
                results_options = ["1-0", "0-1", "0.5-0.5"]
                random_result = random.choice(results_options)
                tournament.enter_result(match.match_id, random_result, match.round_number)
        
        tournament.end_round()
    

    # --- Final Standings and Export ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | TOURNAMENT ENDED. FINAL STANDINGS:")

    tournament.export_standings_to_csv("export/final_standings.csv")

    # --- Test Save/Load ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | Testing Tournament State Save/Load...")
    tournament.save_tournament_state(PLAYERS_CSV, MATCHES_CSV, META_CSV)

    loaded_tournament = Tournament()
    loaded_tournament.load_tournament_state(PLAYERS_CSV, MATCHES_CSV, META_CSV)

    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | Loaded Tournament State Verification:")
    print(f"Loaded Current Round: {loaded_tournament.current_round}")
    loaded_tournament.print_standings()
    loaded_tournament.print_pairings(loaded_tournament.current_round)

    # Verify a player's history and color balance after load
    sample_player = loaded_tournament.get_player_by_name("Alice")
    if sample_player:
        print(f"\n{Tournament().now()} | Alice after load: Points={sample_player.points}, Had Regular Bye={sample_player.had_regular_bye}, Past Colors={sample_player.past_colors}, Past Opponents={sample_player.past_opponents}, Color Balance={sample_player.color_balance_counter}")
    
    # Verify a match from a specific round
    if 1 in loaded_tournament.rounds_matches and len(loaded_tournament.rounds_matches[1]) > 0:
        sample_match_r1 = loaded_tournament.rounds_matches[1][0]
        print(f"\n{Tournament().now()} | Sample loaded match R1 ID {sample_match_r1.match_id}: {sample_match_r1}")
        assert isinstance(sample_match_r1.player_white, Player)
        assert isinstance(sample_match_r1.player_black, Player) or sample_match_r1.player_black.id == 0
        print(f"{Tournament().now()} | Loaded match players are correctly reconstructed Player objects. (Assertion check)")
    else:
        print(f"{Tournament().now()} | No matches found to verify player object reconstruction.")

    for round in range(tournament.num_rounds):
        tournament.export_pairings_to_txt(f"export/pairings/final_pairings_round{round+1}.txt", round+1)

    end = timeit.default_timer()
    print(f"\n{Tournament().now()} | Total Execution Time: {end - start}")

"""    # --- Final Cleanup ---
    print(f"\n{Tournament().long_line()}")
    print(f"{Tournament().now()} | Cleaning up generated files...")
    for f in [PLAYERS_CSV, MATCHES_CSV, META_CSV, STANDINGS_CSV, PAIRINGS_TXT, "final_standings.csv", "final_pairings_round6.txt"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"Cleaned up {f}")
    print(f"{Tournament().now()} | Cleanup complete.")"""
