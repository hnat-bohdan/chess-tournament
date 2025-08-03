from dutch_tournament import *
import os
from typing import List, Tuple

PREDEFINED_PLAYERS: dict[str, int] = {
        # NAME : ELO
        "Alice": 500,
        "Bob": 400,
        "Charlie": 600,
        "Diana": 900,
        "Noah": 1000, }

# --- File Paths --- (Keep these at the top)
REGISTERED_PLAYERS_CSV = "import/chess_players.csv"
PLAYERS_CSV = "export/tournament_players.csv"
MATCHES_CSV = "export/tournament_matches.csv"
META_CSV = "export/tournament_meta.csv"
STANDINGS_CSV = "export/standings.csv" # Not directly used for export, but good to keep consistent

# --- Helper Functions for Console UI ---
def clear_screen():
    # Clears the terminal screen for better UX
    os.system('cls' if os.name == 'nt' else 'clear')

def pause_and_continue():
    input("\nPress Enter to continue...")

def get_int_input(prompt, min_val=None, max_val=None):
    """Safely gets integer input from the user with optional min/max validation."""
    while True:
        try:
            value = int(input(prompt))
            if (min_val is not None and value < min_val) or \
               (max_val is not None and value > max_val):
                print("Invalid input. Please enter a value within the specified range.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_string_input(prompt, valid_options: list = None) -> str:
    """Safely gets string input from the user with optional validation."""
    while True:
        value = input(prompt).strip().lower()
        if valid_options and value not in valid_options:
            print(f"Invalid input. Please enter one of the following: {', '.join(valid_options)}")
        else:
            return value

def display_main_menu():
    clear_screen()
    print(TournamentUtils.long_line())
    print(f"{TournamentUtils.now()} | Chess Tournament Manager Menu")
    print(TournamentUtils.long_line())
    print("1. Start New Tournament")
    print("2. Load Existing Tournament")
    print("3. Manage Players")
    print("4. Start Next Round")
    print("5. Enter Match Results")
    print("6. View Standings")
    print("7. View Pairings (Current/Past Rounds)")
    print("8. Export Data")
    print("9. Exit")
    print(TournamentUtils.long_line())

def display_player_management_menu():
    clear_screen()
    print(TournamentUtils.long_line())
    print(f"{TournamentUtils.now()} | Player Management Menu")
    print(TournamentUtils.long_line())
    print("1. Add New Player")
    print("2. Toggle Player Presence (for next round)")
    print("3. Remove Player (if no matches played)")
    print("4. View All Players")
    print("5. Back to Main Menu")
    print(TournamentUtils.long_line())

def display_export_menu():
    clear_screen()
    print(TournamentUtils.long_line())
    print(f"{TournamentUtils.now()} | Export Data Menu")
    print(TournamentUtils.long_line())
    print("1. Export Current Standings (CSV)")
    print("2. Export Current Standings (TXT)")
    print("3. Export Pairings for a Round (TXT)")
    print("4. Save Full Tournament State")
    print("5. Back to Main Menu")
    print(TournamentUtils.long_line())

def toggle_player_presence(tournament: Tournament):
    """
    Allows the user to change the 'is_present' status of players for the next round.
    """
    while True:
        clear_screen()
        print(f"\n--- {TournamentUtils.now()} | Change Player Presence ---")
        print("Current players and their presence status:")
        print(f"{'ID':<4} {'Name':<20} {'ELO':<6} {'Present':<8}")
        print("-" * 40)
        for player in tournament.player_manager.get_all_players():
            print(f"{player.id:<4} {player.name_surname:<20} {player.elo:<6} {'Yes' if player.is_present else 'No':<8}")

        choice = get_string_input("\nEnter player ID to toggle presence, or 'q' to finish: ", ['q'] + [str(p.id) for p in tournament.player_manager.get_all_players()])
        if choice == 'q':
            break
        
        player_id = int(choice)
        player_to_toggle = tournament.player_manager.get_player_by_id(player_id)
        if player_to_toggle:
            player_to_toggle.is_present = not player_to_toggle.is_present
            print(f"Presence for Player ID {player_id} ({player_to_toggle.name_surname}) toggled to {'Present' if player_to_toggle.is_present else 'Absent'}.")
        else:
            print(f"Error: Player with ID {player_id} not found.")

        pause_and_continue()


def handle_manual_pairing(tournament: Tournament) -> Tuple[List[tuple[int, int]], List[Player]]:
    """
    Allows the user to manually pair players before the automatic pairing system runs.
    Returns the list of players that were NOT manually paired.
    """
    unpaired_players = tournament.player_manager.get_active_players()
    match_players_ids: List[tuple[int, int]] = []

    while True:
        clear_screen()
        print(f"\n--- {TournamentUtils.now()} | Manual Pairing ---")
        if len(unpaired_players) < 2:
            print("Not enough players left to manually pair. Exiting manual pairing.")
            break

        print("Current unpaired players:")
        print(f"{'ID':<4} {'Name':<20} {'ELO':<6} {'Points':<8}")
        print("-" * 40)
        for player in sorted(unpaired_players, key=lambda p: (-p.points, -p.elo)):
            print(f"{player.id:<4} {player.name_surname:<20} {player.elo:<6} {player.points:<8.1f}")
        
        choice = get_string_input("\nDo you want to manually pair a match? (y/n): ", ['y', 'n'])
        if choice == 'n':
            break

        while True:
            try:
                p1_id = get_int_input("Enter ID of Player 1: ")
                p2_id = get_int_input("Enter ID of Player 2: ")

                player1 = tournament.player_manager.get_player_by_id(p1_id)
                player2 = tournament.player_manager.get_player_by_id(p2_id)
                
                if player1 not in unpaired_players or player2 not in unpaired_players:
                    print("Error: One or both players are not in the list of unpaired players or are not present. Try again.")
                    continue
                
                if player1.id == player2.id:
                    print("Error: A player cannot play against themselves. Try again.")
                    continue

                if player2.id in player1.past_opponents:
                    print("Warning: These players have already played each other. Do you still want to pair them?")
                    confirm = get_string_input("(y/n): ", ['y', 'n'])
                    if confirm != 'y':
                        continue
                
                
                unpaired_players.remove(player1)
                unpaired_players.remove(player2)
                match_players_ids.append((p1_id, p2_id))
                print(f"Manual pairing created: {player1.name_surname} vs {player2.name_surname}.")
                pause_and_continue()
                break

            except (ValueError, IndexError):
                print("Invalid input. Please enter valid player IDs.")
    
    return (match_players_ids, unpaired_players)


# --- Main Application Logic ---
def main() -> None:
    tournament = None # Initialize tournament object as None
    
    # Main application loop
    while True:
        display_main_menu()
        choice = get_int_input("Enter your choice: ", 1, 9)

        if choice == 1: # Start New Tournament
            num_rounds = get_int_input("Enter the total number of rounds for the tournament: ", min_val=1)
            tournament = DutchTournament(num_rounds)
            
            load_from_csv_choice = input("Load players from 'import/chess_players.csv'? (y/n): ").lower()
            if load_from_csv_choice == 'y':
                tournament.load_players_from_csv(REGISTERED_PLAYERS_CSV)

            
            
            add_initial_players_choice = input(f"Add predefined players {[x for x in PREDEFINED_PLAYERS.keys()]} ? (y/n): ").lower()
            if add_initial_players_choice == 'y':
                for name, elo in PREDEFINED_PLAYERS.items():
                    tournament.add_player(name, elo)
            
            tournament.print_standings()
            pause_and_continue()

        elif choice == 2: # Load Existing Tournament
            if tournament is None:
                tournament = DutchTournament()
            try:
                tournament.load_tournament_state(players_filepath=PLAYERS_CSV, matches_filepath=MATCHES_CSV, meta_filepath=META_CSV)
                print(f"{TournamentUtils.now()} | Tournament loaded successfully.")
                tournament.print_standings()
            except Exception as e:
                print(f"{TournamentUtils.now()} | Error loading tournament: {e}")
            pause_and_continue()

        elif choice == 3: # Manage Players
            if tournament is None:
                print(f"{TournamentUtils.now()} | Please start or load a tournament first.")
                pause_and_continue()
                continue
            
            while True:
                display_player_management_menu()
                player_choice = get_int_input("Enter your choice: ", 1, 5)

                if player_choice == 1: # Add New Player
                    name = input("Enter player name: ")
                    elo = get_int_input("Enter player ELO: ", min_val=0)
                    tournament.add_player(name, elo)
                    pause_and_continue()
                elif player_choice == 2: # Toggle Player Presence (Now a dedicated function)
                    toggle_player_presence(tournament)
                elif player_choice == 3: # Remove Player
                    tournament.display_manager.print_standings(tournament.current_round, tournament.num_rounds, top=len(tournament.players))
                    player_id = get_int_input("Enter ID of player to remove: ", min_val=1)
                    player_to_remove = tournament.player_manager.get_player_by_id(player_id)
                    if player_to_remove:
                        if player_to_remove.past_matches:
                            print(f"{TournamentUtils.now()} | Cannot remove {player_to_remove.name_surname}. They have already played matches. Please mark them as absent instead.")
                        else:
                            confirm = input(f"Are you sure you want to remove {player_to_remove.name_surname}? (y/n): ").lower()
                            if confirm == 'y':
                                tournament.player_manager.players = [p for p in tournament.player_manager.get_all_players() if p.id != player_id]
                                tournament.player_manager.update_next_player_id()
                                print(f"{TournamentUtils.now()} | Player {player_to_remove.name_surname} removed.")
                            else:
                                print(f"{TournamentUtils.now()} | Player removal cancelled.")
                    else:
                        print(f"{TournamentUtils.now()} | Player with ID {player_id} not found.")
                    pause_and_continue()
                elif player_choice == 4: # View All Players
                    tournament.display_manager.print_standings(tournament.current_round, tournament.num_rounds, top=len(tournament.players))
                    pause_and_continue()
                elif player_choice == 5: # Back
                    break

        elif choice == 4: # Start Next Round
            if tournament is None:
                print(f"{TournamentUtils.now()} | Please start or load a tournament first.")
                pause_and_continue()
                continue
            
            if tournament.current_round >= tournament.num_rounds:
                print(f"{TournamentUtils.now()} | Tournament has reached its maximum rounds ({tournament.num_rounds}). No more rounds can be started.")
                pause_and_continue()
                continue

            # --- NEW PRE-PAIRING LOGIC ---
            # Step 1: Handle player presence
            if get_string_input("Do you want to change the presence of any players for this round? (y/n): ", ['y', 'n']) == 'y':
                toggle_player_presence(tournament)

            # Step 2: Handle manual pairings
            unpaired_players = []
            if get_string_input("Do you want to manually pair any matches for this round? (y/n): ", ['y', 'n']) == 'y':
                desidered_pairs, unpaired_players = handle_manual_pairing(tournament)
            else:
                desidered_pairs = []
                unpaired_players = tournament.player_manager.get_active_players()
            
            # Step 3: Select and run the automatic pairing for remaining players
            print("\nSelect Pairing System for remaining players:")
            print("1. Random")
            print("2. By elo")
            print("3. Dutch")
            pairing_choice = get_int_input("Enter pairing system choice: ", 1, 3)
            
            pairing_system = ""
            if pairing_choice == 1:
                pairing_system = "random"
            elif pairing_choice == 2:
                pairing_system = "by elo"
            elif pairing_choice == 3:
                pairing_system = "dutch"

            # Call pair_round with the correct pairing system and the list of unpaired players
            tournament.pair_round(pairing_system, desired_pairs=desidered_pairs)
            tournament.print_pairings()
            
            print(f"{TournamentUtils.now()} | Round {tournament.current_round} pairings created. You can now enter results (option 5).")
            pause_and_continue()


        elif choice == 5: # Enter Match Results
            if tournament is None or not tournament.current_matches:
                print(f"{TournamentUtils.now()} | No matches to enter results for. Start a round first.")
                pause_and_continue()
                continue
            
            print(f"\n{TournamentUtils.now()} | Entering Results for Round {tournament.current_round}...")
            matches_for_results = tournament.current_matches
            results_options_map = {0: "0.5-0.5", 1: "1-0", 2: "0-1"}
            
            for match in matches_for_results:
                if not match.is_bye_match and not match.is_half_bye_match and match.result == " - ": # Only prompt for active, un-entered matches
                    print(match)
            
            enter_more = "y"
            while enter_more == "y":
                match_id: int = get_int_input("Choose ID for non-bye match you want to enter the result: ", min_val=1, max_val=matches_for_results[-1].match_id)
                print("Result Options: 0 (Draw), 1 (White wins), 2 (Black wins)")
                result_input = get_int_input("Enter result: ", 0, 2)
                tournament.enter_result(match_id, results_options_map[result_input], tournament.current_round)
                enter_more = get_string_input("Would you like to continue? [y/n]: ", ["y", "n"])
            
            confirm_end_round = input("Results entered for this round. End round now? (y/n): ").lower()
            if confirm_end_round == 'y':
                tournament.end_round()
                print(f"{TournamentUtils.now()} | Round {tournament.current_round} ended. Standings updated.")
                tournament.print_standings()
            else:
                print(f"{TournamentUtils.now()} | Round not ended. You can enter more results or end it later.")
            pause_and_continue()

        elif choice == 6: # View Standings
            if tournament is None:
                print(f"{TournamentUtils.now()} | Please start or load a tournament first.")
                pause_and_continue()
                continue
            
            tournament.print_standings()
            pause_and_continue()

        elif choice == 7: # View Pairings
            if tournament is None:
                print(f"{TournamentUtils.now()} | Please start or load a tournament first.")
                pause_and_continue()
                continue
            
            view_current = input("View pairings for current round (c) or a specific round (s)? (c/s): ").lower()
            if view_current == 'c':
                tournament.print_pairings(tournament.current_round)
            elif view_current == 's':
                round_num_to_view = get_int_input(f"Enter round number to view (1-{tournament.current_round}): ", 1, tournament.current_round)
                tournament.print_pairings(round_num_to_view)
            else:
                print("Invalid choice.")
            pause_and_continue()

        elif choice == 8: # Export Data
            if tournament is None:
                print(f"{TournamentUtils.now()} | Please start or load a tournament first.")
                pause_and_continue()
                continue
            
            while True:
                display_export_menu()
                export_choice = get_int_input("Enter your choice: ", 1, 5)

                if export_choice == 1: # Export Standings CSV
                    filepath = input(f"Enter filepath for standings CSV (default: {STANDINGS_CSV}): ") or STANDINGS_CSV
                    tournament.export_standings_to_csv(filepath)
                    pause_and_continue()
                elif export_choice == 2: # Export Standings TXT
                    filepath = input(f"Enter filepath for standings TXT (default: export/leaderboard/standings_round{tournament.current_round}.txt): ") or f"export/leaderboard/standings_round{tournament.current_round}.txt"
                    tournament.export_standings_to_txt(filepath)
                    pause_and_continue()
                elif export_choice == 3: # Export Pairings TXT
                    round_num_export = get_int_input(f"Enter round number for pairings export (1-{tournament.current_round}): ", 1, tournament.current_round)
                    filepath = input(f"Enter filepath for pairings TXT (default: export/pairings/round_{round_num_export}_pairings.txt): ") or f"export/pairings/round_{round_num_export}_pairings.txt"
                    tournament.export_pairings_to_txt(filepath, round_num_export)
                    pause_and_continue()
                elif export_choice == 4: # Save Full Tournament State
                    confirm_save = input("Are you sure you want to save the current tournament state? This will overwrite previous save files. (y/n): ").lower()
                    if confirm_save == 'y':
                        tournament.save_tournament_state(PLAYERS_CSV, MATCHES_CSV, META_CSV)
                    else:
                        print(f"{TournamentUtils.now()} | Save cancelled.")
                    pause_and_continue()
                elif export_choice == 5: # Back
                    break
    
        elif choice == 9: # Exit
            confirm_exit = input("Are you sure you want to exit? (y/n): ").lower()
            if confirm_exit == 'y':
                print(f"{TournamentUtils.now()} | Exiting Chess Tournament Manager. Goodbye!")
                break
            else:
                print(f"{TournamentUtils.now()} | Exit cancelled. Returning to main menu.")
                pause_and_continue()

if __name__ == "__main__":
    main()