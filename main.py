if __name__ == "__main__":
    # --- SIMULATION ---
    import timeit, random
    from chess_tournament import *
    CSV_FILE = "input_data/chess_players.csv"
    ###
    START = timeit.timeit()

    tournament = Tournament(num_rounds=5)
    #Loading players from CSV
    tournament.load_players_from_csv(CSV_FILE)
    #Adding Players via add_player function
    tournament.add_player("Nodirbek Abdusattorov", 2700)
    tournament.add_player("Ding Liren", 2770)
    tournament.add_player("Ian Nepomniachtchi", 2790)
    tournament.add_player("Gukesh D", 2760)
    tournament.add_player("Arjun Erigaisi", 2710)

    def valid_results():
        return random.choice(["0.5 - 0.5", "1 - 0", "0 - 1"])

    n = int( len(tournament.players) / 2)

    tournament.pair_first_round()
    tournament.save_pairing2txt("export/pairings_round1.txt")
    for i in range(1, n + 1):
        tournament.set_match_result(i, valid_results())
    tournament.save_matches2txt("export/matches.txt", False)
    tournament.save_standings2txt("export/standings1.txt")
    tournament.end_round()

    for j in range(4):
        tournament.pair_next_round()
        tournament.save_pairing2txt(f"export/pairings_round{j+2}.txt")
        for i in range(1, n + 1):
            tournament.set_match_result(i, valid_results())
        tournament.save_standings2txt(f"export/standings{j+2}.txt")
        tournament.save_matches2txt(f"export/matches{j+2}.txt", True)
        tournament.end_round()

    tournament.save_players2csv("export/players.csv")
    END = timeit.timeit()

    print(f" Executed in {END - START} seconds")