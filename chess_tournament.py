import os, csv, datetime
from math import fsum

class Player:
    def __init__(self, id:int, name_surname: str, elo:int):
        self.id = id
        self.name_surname = name_surname
        self.elo = elo
        if not isinstance(self.elo, int):
            self.elo = 100
        self.points = 0.0
        self.past_matches = []
        self.past_opponents: list = []
        self.past_colors = []
        self.is_present = False
        self.had_bye = False
        
        
    def add_points(self, n):
        self.points = fsum([self.points, n])

    def player_and_elo(self):
        return f"ID: {self.id} | {self.name_surname} ({self.elo} elo)"

    def __str__(self):
        return f"{self.name_surname} ({self.points} points)"

class Match():
    def __init__(self, player_white:Player, player_black: Player = None, id: int = 1):
        self.round = 1
        self.id = id
        self.white = player_white
        self.result = "bye" if player_black == None else " - "
        self.black = " " if player_black == None else player_black
        self.bye = True if self.result == "bye" else False

    def set_result(self, result: str):
        if self.bye:
            print("Cannot enter result for bye match")
            return None
        valid_results = ("0.5 - 0.5", "1 - 0", "0 - 1")
        if result in valid_results:
            self.result = result
            print(f"Result changed! {self}")
        else:
            print(f"'{result}' - invalid input")

    def __str__(self):
        return f"Round {self.round} ID: {self.id} | {self.white} {self.result} {self.black}"

class Tournament():
    def __init__(self, num_rounds: int = 5):
        self.CURRENT_ROUND = 1
        self.players: list = []
        self.LAST_ROUND = num_rounds
        self.NEXT_ID = 0
        self.NEXT_MATCH_ID = 1
        self.current_matches = []
        self.past_matches = []

    def save_players2csv(self, filepath: str = "players.csv") -> None:
        self.check_file_exsistence(filepath)

        with open(filepath, "w") as file:
            keys = ["id","name_surname","elo","points","past_matches","past_opponents", "past_colors",  "is_present", "had_bye"]
            csv.writer(file).writerow(keys)
            for player in self.players:
                d = player.__dict__.values()
                csv.writer(file).writerow(d)
                print(f"{self.now()} | Player {player} saved to {filepath}!")

    def add_player(self, name_surname:str = "", elo:int = 200, id: int = "int id") -> None:
        #test
        if id == "int id":
            id = id = self.NEXT_ID 
        else: 
            try:
                id = int(id)
            except:
                id = self.NEXT_ID

        elo = self.elo_encoder(elo)

        p = Player(id, name_surname, elo)
        if self.avoid_name_duplicates(p): #function gives True if there is no player and we can add him; Otherwise it changes the player's info
            self.players.append(p)
            self.NEXT_ID += 1
        print(f"Player added! {p.player_and_elo()}")

    def get_player_by_id(self, player_id: int) -> Player | None:
        """Returns a player object by ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def load_players_from_csv(self, filepath: str) -> None:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} - path doesn't exist")
        
        with open(filepath, "r") as file:
            reader = csv.reader(file)
            next(reader)
            for player in reader:
                if player[1]:
                    #avoids id duplicates
                    if self.get_player_by_id(int(player[0])) == None:
                        self.add_player(id=int(player[0]), name_surname=player[1], elo=player[2])
                    else:
                        self.add_player(name_surname=player[1], elo=player[2])
                    
        self.update_players_ID()

    def print_standings(self):
        print(f"--- {self.now()} | Standings | Round {self.CURRENT_ROUND} / {self.LAST_ROUND} ---")
        for i, player in enumerate(self.players):
            print(i + 1 , player)
        print(self.long_line())

    def update_standings(self) -> None:
        self.players.sort(key=lambda p: p.points, reverse=True)
        print(f"{self.now()} |Standings sorted by points!")

    def add_match(self, white: Player, black: Player, round: int = 1) -> None:
        if black != None and white != None:
            white.past_opponents.append(black.id)
            black.past_opponents.append(white.id)
        m = Match(white, black, self.NEXT_MATCH_ID)
        m.round = round
        self.NEXT_MATCH_ID += 1
        self.current_matches.append(m)
        print(f"{m} added")

    def set_match_result(self, match_id: int, result: str = ("0.5 - 0.5", "1 - 0", "0 - 1", "bye")) -> None:
        for match in self.current_matches:
            if match.id == int(match_id):
                match.set_result(result)

    def pair_first_round(self, desidered_pairs_for_ids: list = [[]]) -> None:
        self.players.sort(key=lambda x: x.elo, reverse=True)
        print(f"{self.now()} |Standing sorted by elo!")
        print(f"--- Round {self.CURRENT_ROUND} / {self.LAST_ROUND} pairs ---")
        players = list(self.players)
        for pair in desidered_pairs_for_ids:
            if pair != []:
                white_id, black_id = pair
                white = self.get_player_by_id(white_id)
                black = self.get_player_by_id(black_id)
                self.add_match(white, black)
                i = 0
                while i < range(len(players)):
                    if players[i].id in pair:
                        players.pop(i)
                        continue
                    i += 1
        #bye match
        if len(players) % 2:
            self.players[-1].had_bye = True
            self.add_match(players[-1], None)
            players.pop()

        remained_matches = int(len(players) / 2)

        for id in range(remained_matches):
            self.add_match(players[id*2], players[id*2+1])
        
        print(self.long_line())

    def end_round(self) -> None:
        for chess_match in self.current_matches:
            match(chess_match.result):
                case "bye":
                    chess_match.white.add_points(0.5)
                    chess_match.white.past_opponents.append("bye")
                    chess_match.white.past_matches.append("bye")
                case "0.5 - 0.5":
                    chess_match.white.add_points(0.5)
                    chess_match.black.add_points(0.5)
                    chess_match.white.past_matches.append("draw")    
                    chess_match.black.past_matches.append("draw")
                case " - ":
                    chess_match.white.add_points(0.5)
                    chess_match.black.add_points(0.5)
                    chess_match.white.past_matches.append("draw")    
                    chess_match.black.past_matches.append("draw")
                case "1 - 0":
                    chess_match.white.add_points(1)
                    chess_match.white.past_matches.append("win")    
                    chess_match.black.past_matches.append("lose")
                case "0 - 1":
                    chess_match.black.add_points(1)
                    chess_match.white.past_matches.append("lose")    
                    chess_match.black.past_matches.append("win")

        self.update_standings()
        self.print_standings()

        self.update_standings
        self.NEXT_MATCH_ID = 1
        self.past_matches.append(list(self.current_matches))
        self.current_matches = []
        print(f"--- {self.now()} | Round {self.CURRENT_ROUND} / {self.LAST_ROUND} ended ---")
        print(self.long_line())

    def show_mathes(self) -> None:
        print("--- {self.now()} |Current matches ---")
        for match in self.current_matches:
            print(match)
        print(self.long_line())

    def pair_next_round(self) -> None:
        self.CURRENT_ROUND += 1
        print(f"--- {self.now()} | Round {self.CURRENT_ROUND} / {self.LAST_ROUND} pairs---")
        players = list(self.players)
        self.NEXT_MATCH_ID = 1
        #bye match
        if len(players) % 2:
            j = 1
            while j < len(players):
            #while j < self.CURRENT_ROUND:
                if not players[-j].had_bye:
                    self.players[-j].had_bye = True
                    self.add_match(players[-j], None, self.CURRENT_ROUND)
                    players.pop(-j)
                    j = len(players)
                j += 1

        remained_matches = int(len(players) / 2)
        for i in range(remained_matches):
            white = players[0]
            j = 1
            while j < len(players):
                black = players[j]
                if not (white.id in black.past_opponents):
                    self.add_match(white, black, self.CURRENT_ROUND)
                    players.pop(j)
                    j = len(players)
                    players.pop(0)
                j += 1

        if players != []:
            for player in players:
                self.add_match(player, None, self.CURRENT_ROUND)
        print(self.long_line())

    def save_matches2txt(self, filepath: str = "matches.txt", clear_past_matches: bool = True) -> None:
        self.check_file_exsistence(filepath)
        with open(filepath, "w") as file:
            file.write(self.now() + "\n")
            file.write(f"--- Past matches ---\n")
            for matches in self.past_matches:
                for match in matches:
                    file.write(f"{match}\n")
            file.write(f"--- Current matches ---\n")
            for match in self.current_matches:
                file.write(f"{match}\n")
        if clear_past_matches:
            self.past_matches = []
            print(f"Past matches cleared")
        print(f"{self.now()} |Matches saved to {filepath}")
    
    def save_standings2txt(self, filepath: str = "standings.txt"):
        self.check_file_exsistence(filepath)
        with open(filepath, "w") as file:
            file.write(f"--- {self.now()} | Standings for Round {self.CURRENT_ROUND} / {self.LAST_ROUND} ---\n")
            for place, player in enumerate(self.players):
                file.write(f" {place + 1}. {player}\n")
        print(f"{self.now()} |Standings saved to {filepath}")

    def save_pairing2txt(self, filepath: str = "pairings.txt"):
        """
        Saves current pairings to a TXT file.

        Args:
            filepath (str): The path to the file where pairings will be saved.
        """
        # Create directory if it doesn't exist
        self.check_file_exsistence(filepath)

        # Open file for writing
        with open(filepath, "w") as file:
            file.write(f"--- {self.now()} | Current Pairings for Round {self.CURRENT_ROUND} / {self.LAST_ROUND} ---\n")
            # Write each match in the current matches to the file
            for match in self.current_matches:
                file.write(f"{match}\n")
        
        print(f"{self.now()} |Pairings saved to {filepath}")

# Some functions I use in other functions :)
    def now(self):
        return datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")
    def long_line(self):
        return "--- " * 10
    def update_players_ID(self) -> None:
        self.NEXT_ID = self.players[-1].id + 1
        print(f"ID updated, next id: {self.NEXT_ID}")

    def elo_encoder(self, elo) -> int:
        try:
            return int(elo)
        except:
            pass
        if (isinstance(elo, str)):
            elo_array = elo.split()
            for item in elo_array:
                if item.isdigit():
                   return int(item)
        return 100

    def avoid_name_duplicates(self, player_test: Player) -> bool:
        for i in range(len(self.players)):
            if (player_test.name_surname.lower() == self.players[i].name_surname.lower()):
                print(f"{self.players[i].player_and_elo()} -> {player_test.player_and_elo()} ")
                self.players[i].elo = player_test.elo
                return False
        return True
    
    def check_file_exsistence(self, filepath: str = "players.csv") -> None:
        if not os.path.exists(filepath):
            with open(filepath, "a"):
                print(f"{filepath} created")