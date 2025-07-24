import os, json, csv, datetime, random, math
import pandas as pd

# --- Player Class ---
class Player:
    """
    Represents a chess player in the tournament.
    """
    def __init__(self, id: int, name_surname: str, elo: int):
        """
        Initializes a Player object.

        Args:
            id (int): Unique player ID.
            name_surname (str): Player's full name.
            elo (int): Player's ELO rating.
        """
        if not isinstance(id, int) or id < 0: # ID 0 used for BYE_OPPONENT dummy player
            raise ValueError("Player ID must be a non-negative integer.")
        if not isinstance(name_surname, str) or not name_surname.strip():
            raise ValueError("Player name cannot be empty.")
        if not isinstance(elo, int) or elo < 0:
            print(f"Warning: ELO for {name_surname} is invalid ({elo}). Setting to 100.")
            elo = 100

        self.id = id
        self.name_surname = name_surname.strip()
        self.elo = elo
        self.points = 0.0
        # Initialize mutable attributes as separate empty lists
        self.past_colors = []       # List of colors played (e.g., 'white', 'black', 'bye', 'half bye')
        self.past_matches = []      # List of Match IDs played (per-round IDs)
        self.past_opponents = []    # List of Player IDs of past opponents
        self.had_regular_bye = False # True if player has already received a regular 1-point bye
        self.has_bye_this_round = False # True if player receives ANY type of bye in the current round
        self.is_present = True      # True by default, can be set to False for absence
        self.color_balance_counter = 0 # +1 for white, -1 for black. Resets on bye.

    def add_points(self, n: float) -> None:
        """Adds n points to the player's score."""
        if not isinstance(n, (int, float)):
            raise TypeError("Points to add must be a number.")
        self.points = math.fsum([self.points, n])

    def player_and_elo(self) -> str:
        """Returns a string with player ID, name, and ELO."""
        return f"ID: {self.id} | {self.name_surname} ({self.elo} elo)"

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the player."""
        return f"{self.name_surname} ({self.points:.1f} points)"

    def __repr__(self) -> str:
        """Returns a string for unambiguous representation (e.g., in lists)."""
        return f"<{self.name_surname} - {self.points} pts>"
    
    def to_dict(self) -> dict:
        """
        Converts Player object to a dictionary for CSV serialization.
        Lists are converted to JSON strings to store correctly in CSV fields.
        """
        return {
            "id": self.id,
            "name_surname": self.name_surname,
            "elo": self.elo,
            "points": self.points,
            "past_colors": json.dumps(self.past_colors), # Store as JSON string
            "past_matches": json.dumps(self.past_matches), # Store as JSON string
            "past_opponents": json.dumps(self.past_opponents), # Store as JSON string
            "had_regular_bye": str(self.had_regular_bye), # Convert boolean to string "True"/"False"
            "has_bye_this_round": str(self.has_bye_this_round),
            "is_present": str(self.is_present),
            "color_balance_counter": self.color_balance_counter
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """
        Args:
            data: dict - dictionary of Player ojbject attributes (e.g., read from CSV row).
        JSON strings are parsed back into lists, and string booleans to actual booleans.
        """
        player = cls(
            id=int(data["id"]),
            name_surname=data["name_surname"],
            elo=int(data["elo"])
        )
        player.points = float(data["points"])
        player.past_colors = json.loads(data.get("past_colors", "[]"))
        player.past_matches = json.loads(data.get("past_matches", "[]"))
        player.past_opponents = json.loads(data.get("past_opponents", "[]"))
        player.had_regular_bye = data.get("had_regular_bye", "false").lower() == "true" 
        player.has_bye_this_round =data.get("has_bye_this_round", "false").lower() == 'true'
        player.is_present = data.get("is_present", "true").lower() == 'true'
        player.color_balance_counter = int(data.get("color_balance_counter", 0))
        return player


# --- Match Class ---
class Match:
    """
    Represents a single chess match between two players.
    """
    def __init__(self, match_id: int, player_white: Player, player_black: Player | None, round_number: int):
        """
        Initializes a Match object.

        Args:
            match_id (int): Unique match ID within a round.
            player_white (Player): The player with white pieces (or the player receiving a bye).
            player_black (Player | None): The player with black pieces, or None if it's a bye.
            round_number (int): The round number this match belongs to.
        """
        if not isinstance(player_white, Player):
            raise TypeError("Player white must be a Player object.")
        if player_black is not None and not isinstance(player_black, Player):
            raise TypeError("Player black must be a Player object or None.")
        if player_black is not None and player_white.id == player_black.id and player_white.id != 0:
            raise ValueError("A player cannot play against themselves.")
        if not isinstance(round_number, int) or round_number <= 0:
            raise ValueError("Round number must be a positive integer.")
        
        self.match_id = match_id # This is the per-round match ID
        self.player_white = player_white
        self.player_black = player_black if player_black is not None else Player(0, "BYE_OPPONENT", 0) # Use dummy for bye
        self.round_number = round_number
        self.result = " - " # Default empty result for active matches
        self.is_bye_match = False
        self.is_half_bye_match = False

        if player_black is None:
            self.is_bye_match = True # Marks it as a bye (either regular or half)
            self.result = "bye" # Default result for bye matches

    def set_result(self, result: str) -> None:
        """
        Sets the result of the match.

        Args:
            result (str): The match result ("1-0", "0-1", "0.5-0.5", "bye", "half bye").
        
        Raises:
            ValueError: If the result format is invalid.
        """
        valid_results = {"1-0", "0-1", "0.5-0.5", "bye", "half bye"}
        if result not in valid_results:
            raise ValueError(f"Invalid result format. Must be one of: {', '.join(valid_results)}")
        
        if self.is_bye_match and result not in ["bye", "half bye"]:
            print(f"Warning: Match ID {self.match_id} (R{self.round_number}) is a bye match. Result cannot be changed to '{result}'.")
            return

        # If result already set and trying to change it to something different
        if self.result != " - " and result != self.result: 
             print(f"Warning: Result for Match ID {self.match_id} (R{self.round_number}) already entered as '{self.result}'. Cannot change to '{result}'.")
             return

        self.result = result

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the match."""
        if self.is_bye_match:
            bye_type = "BYE" if self.result == "bye" else "HALF BYE"
            return f"Match ID {self.match_id} (R{self.round_number}): {self.player_white.name_surname} ({bye_type}) - Result: {self.result}"
        else:
            return (f"Match ID {self.match_id} (R{self.round_number}): {self.player_white.name_surname} (W) vs "
                    f"{self.player_black.name_surname} (B) - Result: {self.result}")

    def to_dict(self) -> dict:
        """
        Converts Match object to a dictionary for CSV serialization.
        Stores player IDs instead of full player objects.
        """
        return {
            "match_id": self.match_id,
            "round_number": self.round_number,
            "player_white_id": self.player_white.id,
            "player_black_id": self.player_black.id, # Even for dummy BYE_OPPONENT
            "result": self.result,
            "is_bye_match": str(self.is_bye_match),
            "is_half_bye_match": str(self.is_half_bye_match)
        }

    @classmethod
    def from_dict(cls, data: dict, players_by_id: dict) -> 'Match':
        """
        Reconstructs a Match object from a dictionary (e.g., read from CSV row).
        Requires a dictionary of Player objects (by ID) to link players.
        """
        white_id = int(data["player_white_id"])
        black_id = int(data["player_black_id"])
        
        player_white = players_by_id.get(white_id)
        player_black = players_by_id.get(black_id) 

        is_bye = data.get("is_bye_match", 'False').lower() == 'true'
        is_half_bye = data.get("is_half_bye_match", 'False').lower() == 'true'

        if not player_white:
            raise ValueError(f"Could not find white player for match ID {data['match_id']}. ID: {white_id}")
        
        # If it's a bye match and the black player is our dummy, recreate it if not found
        if is_bye and black_id == 0 and not player_black:
            player_black = Player(0, "BYE_OPPONENT", 0)
        elif not player_black and not is_bye: # If not a bye, black player must exist
             raise ValueError(f"Could not find black player for match ID {data['match_id']}. ID: {black_id}")

        match = cls(int(data["match_id"]), player_white, player_black, int(data["round_number"]))
        match.result = data["result"]
        match.is_bye_match = is_bye
        match.is_half_bye_match = is_half_bye
        return match


# --- PairingManager Class ---

### Fast Acknowledgement
"""
    The core pairing algorithm and concepts for this Chess Tournament were inspired by and adapted from the excellent video on Swiss Tournament Pairing Algorithms by Nice Micro in his video(https://youtu.be/ijU8kL4hgIg?si=H0vN8dk4TArI67-b) on YouTube.
    Thank You, @nicemicro(https://github.com/nicemicro/) ❤️
"""
class PairingManager:
    """
    Manages the complex pairing algorithms, including badness matrix calculation
    and recursive search for optimal pairings.
    """
    # --- Constants for badness calculation and limits ---
    # Penalty for a single rematch. 
    REMATCH_PENALTY: int = 1000 

    # For quadratic penalty (e.g., if played twice, 4x penalty):
    # REMATCH_PENALTY_QUADRATIC_FACTOR = 100.0 # Use this if you want quadratic penalty
    # badness_matrix.loc[p1.id, p2.id] += self.REMATCH_PENALTY_QUADRATIC_FACTOR * (rematch_count ** 2)

    ELO_DIFF_DIVISOR: float = 500.0
    # POSITION_FINE_TUNE_DIVISOR = 1000.0 # Tiny influence from index difference (if you want)

    # Penalty for dutch system if players are from the same half of the sorted list
    SAME_HALF_PENALTY: float = 3.0 # Moderate penalty to encourage top-vs-bottom pairing

    #MATCH_BADNESS_LIMIT is a heuristic for speed.
    #If total badness of a complete pairing falls below this, the search stops early.
    #If you don't want to skip any matches, set this to float("inf")
    MATCH_BADNESS_LIMIT: float = 10.0
    
    # MATCH_ACCECPTABLE_BADNESS_LIMIT is a heuristic for speed.
    # If total badness of a complete pairing falls below this, the search stops early.
    # If you want to ALWAYS find the absolute mathematically best pairing, set this to 0.0.
    MATCH_ACCECPTABLE_BADNESS_LIMIT:float = 0.0

    def __init__(self, tournament_ref):
        self.tournament = tournament_ref # Reference to the Tournament instance

    def _calculate_badness_matrix(self, players_list: list[Player], current_round_num: int, pairing_system: str) -> pd.DataFrame:
        """
        Calculates a badness matrix (Pandas DataFrame) for pairing.
        Higher values mean worse pairings. Optimized for symmetry.
        Also updates the penalties if you want
        """
        player_ids = [p.id for p in players_list]
        badness_matrix = pd.DataFrame(float("inf"), index=player_ids[:-1], columns=player_ids)

        for i, p1 in enumerate(players_list[:-1]):
            for j, p2 in enumerate(players_list):
                if i >= j: # Only calculate for upper triangle (or diagonal for Infinity penalty)
                    if i == j:
                        badness_matrix.loc[p1.id, p2.id] = float("inf") # Cannot pair with self
                    continue # Skip redundant calculations for lower triangle

                current_pair_badness: float = 0.0

                # 1. Rematch penalty
                if p2.id in p1.past_opponents:
                    current_pair_badness += self.REMATCH_PENALTY
                    # If you want quadratic penalty, uncomment the line below and the constant above:
                    # rematch_count = p1.past_opponents.count(p2.id)
                    # current_pair_badness += self.REMATCH_PENALTY_QUADRATIC_FACTOR * (rematch_count ** 2)

                # 2. Points difference (squared) (not used for now)
                """points_diff = abs(p1.points - p2.points)
                current_pair_badness += (points_diff ** 2)"""

                # 3. ELO difference (divided by 400)
                elo_diff = abs(p1.elo - p2.elo)
                current_pair_badness += (elo_diff / self.ELO_DIFF_DIVISOR)
                
                # 4. dutch System Specific Penalty: Same Half Pairing
                if pairing_system == "dutch":
                    half_size = len(players_list) // 2
                    # Check if both players are in the top half or both in the bottom half
                    if (i < half_size and j < half_size) or (i >= half_size and j >= half_size):
                        current_pair_badness += self.SAME_HALF_PENALTY

                badness_matrix.loc[p1.id, p2.id] = current_pair_badness
                
        return badness_matrix

    def _find_best_pairing_recursive(self, players_remaining: list[Player], badness_matrix: pd.DataFrame, 
                                     current_best_total_badness: float, current_pairing_attempt: list[tuple[Player, Player]]) -> tuple[list[tuple[Player, Player]], float] | None:
        """
        Recursively finds the best pairing (lowest total badness) for a list of players.
        
        Args:
            players_remaining (list[Player]): List of players yet to be paired in this sub-problem.
            badness_matrix (pd.DataFrame): Pre-calculated badness scores between all players.
            current_best_total_badness (float): The current best total badness found so far; used to prune branches.
            current_pairing_attempt (list): The list of pairs already made in this recursive branch (for context/debugging).

        Returns:
            tuple[list[tuple[Player, Player]], float] | None: A tuple containing the list of
            (player1, player2) pairs and their total badness score, or None if no valid pairing
            below the limit is found.
        """
        # Base Case: If no players remaining, we found a complete pairing.
        if not players_remaining:
            return ([], 0.0)

        # Base Case: If only two players remain, they must be paired.
        if len(players_remaining) == 2:
            p1 = players_remaining[0]
            p2 = players_remaining[1]
            badness = badness_matrix.loc[p1.id, p2.id]

            # Prune if this pairing is already worse than current best or exceeds single match limit
            if badness >= current_best_total_badness or badness > self.MATCH_BADNESS_LIMIT:
                return None
            
            return ([(p1, p2)], badness)

        # Recursive Step: More than two players
        best_overall_pairing = None
        min_overall_badness = float("inf")

        first_player = players_remaining[0]

        # Iterate through all other players to find a partner for the first player
        for i in range(1, len(players_remaining)):
            current_partner = players_remaining[i]
            pair_badness = badness_matrix.loc[first_player.id, current_partner.id]
            if pair_badness == float("inf"):
                continue
            
            # Pruning: If this single pair's badness already exceeds the best known total
            # or exceeds the single match badness limit, skip.
            if pair_badness >= current_best_total_badness or pair_badness > self.MATCH_BADNESS_LIMIT:
                continue

            # Create a new list for the recursive call, excluding the current pair
            remaining_players_for_recursion = players_remaining[1:i] + players_remaining[i+1:]
            
            # Recursive call to find the best pairing for the rest of the players
            recursive_result = self._find_best_pairing_recursive(
                remaining_players_for_recursion, 
                badness_matrix, 
                current_best_total_badness - pair_badness, # Adjust limit for recursive call
                current_pairing_attempt + [(first_player, current_partner)] 
            )

            if recursive_result:
                recursive_pairing, recursive_badness = recursive_result
                total_badness_for_combo = pair_badness + recursive_badness
                
                if total_badness_for_combo < min_overall_badness:
                    min_overall_badness = total_badness_for_combo
                    best_overall_pairing = [(first_player, current_partner)] + recursive_pairing
                    current_best_total_badness = min_overall_badness # Update limit for further pruning
                    
                    # Heuristic: If a "good enough" pairing is found, return early for speed
                    if self.MATCH_ACCECPTABLE_BADNESS_LIMIT is not None and min_overall_badness < self.MATCH_ACCECPTABLE_BADNESS_LIMIT:
                        return (best_overall_pairing, min_overall_badness)
            
        if best_overall_pairing is None and min_overall_badness == float("inf"):
            return None # No valid pairing found
        
        return (best_overall_pairing, min_overall_badness)

    def find_optimal_pairing(self, players_to_pair: list[Player], current_round_num: int, pairing_system: str) -> tuple[list[tuple[Player, Player]], float] | None:
        """
        Public method to initiate the optimal pairing search for a round.
        
        Args:
            players_to_pair (list[Player]): The list of players to pair for the current round.
            current_round_num (int): The current round number.
            pairing_system (str): The type of pairing system ("dutch" or "monrad") to influence badness.

        Returns:
            tuple[list[tuple[Player, Player]], float] | None: The best pairing found and its total badness,
            or None if no valid pairing can be found within limits.
        """
        if not players_to_pair:
            return ([], 0.0)
        if len(players_to_pair) % 2 != 0:
            raise ValueError("Player list for optimal pairing must be even after bye assignment.")

        # Recalculate badness matrix for the current set of players and round
        self.badness_matrix = self._calculate_badness_matrix(players_to_pair, current_round_num, pairing_system)
        
        # Calculate dynamic ROUND_BADNESS_LIMIT
        round_badness_limit = len(players_to_pair) * self.tournament.num_rounds * 2 

        # Initial call to recursive function
        result = self._find_best_pairing_recursive(
            players_to_pair, 
            self.badness_matrix, 
            round_badness_limit, # Use the dynamic limit for initial pruning
            []
        )
        
        if result and result[1] <= round_badness_limit:
            return result
        else:
            # print(f"Warning: No optimal pairing found within ROUND_BADNESS_LIMIT ({round_badness_limit:.2f}).")
            return None


# --- Tournament Class ---
class Tournament:
    """
    Manages a chess tournament, including players, pairings, and results.
    Persists data using CSV files.
    """
    def __init__(self, num_rounds: int = 5):
        """
        Initializes a Tournament.

        Args:
            num_rounds (int): The total number of rounds in the tournament.
        """
        if not isinstance(num_rounds, int) or num_rounds <= 0:
            raise ValueError("Number of rounds must be a positive integer.")
        
        self.current_round = 0 # Starts at 0, first pairing will be round 1
        self.num_rounds = num_rounds
        self.players: list[Player] = [] # List of Player objects
        self.next_player_id = 1 # Tracks the next available player ID
        
        self.current_matches: list[Match] = [] # Matches for the current round
        self.rounds_matches: dict[int, list[Match]] = {} # All matches, organized by round number
        
        self.NEXT_MATCH_ID_IN_ROUND = 1 # Resets each round for match.id
        
        self.pairing_manager = PairingManager(self) # Initialize PairingManager with reference to self

    def now(self) -> str:
        """Returns current datetime formatted as string."""
        return datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")

    def long_line(self) -> str:
        """Returns a decorative line for printing."""
        return "--- " * 20

    def update_next_player_id(self) -> None:
        """Updates next_player_id based on the highest existing player ID."""
        if self.players:
            # Exclude the dummy BYE_OPPONENT (ID 0) from max calculation
            valid_player_ids = [p.id for p in self.players if p.id != 0]
            if valid_player_ids:
                self.next_player_id = max(valid_player_ids) + 1
            else: # Only dummy player or no players
                self.next_player_id = 1
        else:
            self.next_player_id = 1
        print(f"{self.now()} | Player ID tracker updated. Next ID: {self.next_player_id}")

    def name_surname_encoder(self, name_surname: str) -> str:
        """Encodes name and surname to a maximum of 20 characters."""
        lenght_limit: int = 20
        if name_surname is None or name_surname.strip() == "":
            return "BYE_OPPONENT"
        if len(name_surname) < lenght_limit:
            return name_surname
        
        name_surname_list = name_surname.split()
        surname = name_surname_list.pop()
        for name in name_surname_list:
            name = name[0] + ". "
        name_surname = "".join(name_surname_list) + surname
        
        if len(name_surname) < lenght_limit:
            return name_surname
        
        return (name_surname[:lenght_limit - 3] + "...")

    def elo_encoder(self, elo_input) -> int:
        """
        Encodes ELO input to an integer. Handles string input with digits.
        """
        try:
            return int(elo_input)
        except (ValueError, TypeError):
            if isinstance(elo_input, str):
                for item in elo_input.split():
                    if item.isdigit():
                        return int(item)
            print(f"{self.now()} | Warning: Invalid ELO format '{elo_input}'. Defaulting to 100.")
            return 100

    def get_player_by_name(self, name_surname: str) -> Player | None:
        """Returns a player object by name, case-insensitive."""
        for player in self.players:
            if player.name_surname.lower() == name_surname.lower() and player.id != 0: # Exclude dummy BYE_OPPONENT
                return player
        return None
    
    def get_player_by_id(self, player_id: int) -> Player | None:
        """Returns a player object by ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def add_player(self, name_surname: str, elo: int, id: int = -1) -> None:
        """
        Adds a new player to the tournament or updates an existing one if name matches.
        """
        if id == -1: # Use internal ID if not provided
            id_to_use = self.next_player_id
        else:
            id_to_use = id

        name_surname = self.name_surname_encoder(name_surname)
        existing_player = self.get_player_by_name(name_surname)
        if existing_player:
            print(f"{self.now()} | Player '{name_surname}' already exists. Updating ELO from {existing_player.elo} to {elo}.")
            existing_player.elo = self.elo_encoder(elo)
        else:
            p = Player(id_to_use, name_surname, self.elo_encoder(elo))
            self.players.append(p)
            self.update_next_player_id() # Update ID tracker after adding
            print(f"{self.now()} | Player added: {p.player_and_elo()}")

    def save_players_to_csv(self, filepath: str = "players.csv") -> None:
        """
        Saves all players to a CSV file. Overwrites existing file.
        """
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True) 

        with open(filepath, "w", newline='') as file:
            fieldnames = ["id", "name_surname", "elo", "points", "past_colors", 
                          "past_matches", "past_opponents", "had_regular_bye", "has_bye_this_round", "is_present", "color_balance_counter"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for player in self.players:
                if player.id == 0 and player.name_surname == "BYE_OPPONENT": # Do not save dummy BYE_OPPONENT
                    continue
                writer.writerow(player.to_dict())
            print(f"{self.now()} | Players saved to {filepath}!")

    def load_players_from_csv(self, filepath: str = "registered_players.csv", clear_players: bool = True) -> None:
        """
        Loads players from a CSV file.
        Args:
            filepath (str): The path to the CSV file.
            clear_players (bool): If True, clears existing players before loading.
        """
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"{self.now()} | No player data file '{filepath}' found or file is empty. Starting with no players.")
            self.players = []
            return
        
        if clear_players:
            self.players = [] # Clear current players before loading

        with open(filepath, "r", newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    self.players.append(Player.from_dict(row))
                except (ValueError, KeyError, json.JSONDecodeError, TypeError) as e:
                    print(f"{self.now()} | Error loading player from row {row}: {e}. Skipping row.")
        
        self.update_next_player_id()
        print(f"{self.now()} | Players loaded from {filepath}!")

    def update_standings(self) -> None:
        """Sorts players by points and color balance in descending order, then ELO for tie-breaking."""
        self.players.sort(key=lambda p: (p.points, -p.color_balance_counter, p.elo), reverse=True)
        # print(f"{self.now()} | Standings sorted by points and ELO!") # Removed this print for less verbosity

    def _assign_colors_to_pair(self, p1: Player, p2: Player) -> tuple[Player, Player]:
        """
        Assigns White and Black colors to a pair based on preference, past colors, points, and ELO.
        Returns (white_player, black_player).
        """
        # Rule 1: Strong Color Preference
        if p2.color_balance_counter <= -2 or p1.color_balance_counter >= 2: # p2 wants white or p1 prefer black
            return p2, p1
        if p1.color_balance_counter <= -2 or p2.color_balance_counter >= 2: # vice versa
            return p1, p2

        # Rule 2: Player who played more Black games gets White
        black_games_p1 = p1.past_colors.count("black")
        black_games_p2 = p2.past_colors.count("black")
        if black_games_p1 > black_games_p2:
            return p1, p2
        if black_games_p2 > black_games_p1:
            return p2, p1

        # Rule 3: Player with fewer points gets White
        if p1.points < p2.points:
            return p1, p2
        if p2.points < p1.points:
            return p2, p1

        # Rule 4: Player with lower ELO gets White (final tie-breaker)
        if p1.elo <= p2.elo:
            return p1, p2
        else:
            return p2, p1

    def _add_match_to_tournament(self, player_white: Player, player_black: Player | None = None, is_half_bye: bool = False) -> Match:
        """Helper to create and add a match, updating player history."""
        match = Match(self.NEXT_MATCH_ID_IN_ROUND, player_white, player_black, self.current_round)
        self.NEXT_MATCH_ID_IN_ROUND += 1
        
        if match.is_bye_match: # It's a bye, either regular or half
            match.is_half_bye_match = is_half_bye # Mark if it's explicitly a half bye
            player_white.past_colors.append("half bye" if  is_half_bye else "bye")
            match.is_half_bye_match = is_half_bye
            if is_half_bye:
                match.result = "half bye"
                player_white.has_bye_this_round = True
            else:
                player_white.had_regular_bye = True
            player_white.past_matches.append(match.match_id) # Use per-round ID
            player_white.past_opponents.append(0) # 0 for BYE_OPPONENT ID
        else:
            player_white.past_opponents.append(player_black.id)
            player_black.past_opponents.append(player_white.id)
            player_white.past_colors.append("white")
            player_black.past_colors.append("black")
            player_white.past_matches.append(match.match_id) # Use per-round ID
            player_black.past_matches.append(match.match_id)

        self.current_matches.append(match)
        self.rounds_matches.setdefault(self.current_round, []).append(match) # Store in rounds_matches
        print(f"{self.now()} | Added match: {match}")
        return match

    def _get_eligible_bye_player(self, players_pool: list[Player]) -> Player | None:
        """
        Finds the lowest-point player eligible for a REGULAR bye (hasn't had one before).
        If tied, selects randomly.
        """
        eligible_for_regular_bye = [p for p in players_pool if not p.had_regular_bye]
        if not eligible_for_regular_bye:
            return None # No one eligible for a regular bye

        # Sort eligible players by points ascending, then ELO ascending (to make random choice more stable)
        eligible_for_regular_bye.sort(key=lambda p: (p.points, p.elo))
        
        lowest_point = eligible_for_regular_bye[0].points
        tied_players = [p for p in eligible_for_regular_bye if p.points == lowest_point]
        
        return random.choice(tied_players) # Randomly select from those tied on lowest points

    def _handle_bye_assignment(self, players_pool: list[Player]) -> tuple[Player | None, list[Player]]:
        """
        Manages bye assignment (regular or half-bye).
        Returns the bye player (if any) and the updated list of players for pairing.
        """
        bye_player = None
        players_for_pairing = list(players_pool) # Create a copy of active players

        # Handle players marked as absent (is_present = False) - they get a half-bye first
        absent_players = [p for p in players_for_pairing if not p.is_present]
        for p in absent_players:
            if p.id != 0 and not p.has_bye_this_round: # Ensure not already assigned a bye
                p.add_points(0.5)
                p.has_bye_this_round = True
                self._add_match_to_tournament(p, None, is_half_bye=True)
                print(f"{self.now()} | Player {p.name_surname} is absent and receives a HALF BYE (0.5 pt) in Round {self.current_round}.")
        
        # Remove absent players from the pool for pairing
        players_for_pairing = [p for p in players_for_pairing if p.is_present]

        if len(players_for_pairing) % 2 != 0: # Odd number of players remaining, so a bye is needed
            
            # --- Attempt Regular Bye ---
            potential_regular_bye_player = self._get_eligible_bye_player(players_for_pairing)

            if potential_regular_bye_player:
                # If an eligible player for a regular bye is found, assign it
                bye_player = potential_regular_bye_player
                bye_player.add_points(1.0) # 1 point for regular bye
                bye_player.had_regular_bye = True
                self._add_match_to_tournament(bye_player, None, )
                players_for_pairing.remove(bye_player)
                #print(f"{self.now()} | Player {bye_player.name_surname} receives a REGULAR BYE (1.0 pt) in Round {self.current_round}.")
            else:
                # --- Fallback to Half Bye if no one eligible for Regular Bye ---
                # Find the lowest-rated player among remaining players
                players_for_pairing.sort(key=lambda p: (p.points, p.elo))
                half_bye_player = players_for_pairing.pop(0) # Take the lowest-rated player
                
                half_bye_player.add_points(0.5) # 0.5 points for half bye
                half_bye_player.has_bye_this_round = True
                bye_player = half_bye_player # This is our bye player for this round
                self._add_match_to_tournament(bye_player) 
                print(f"{self.now()} | Player {half_bye_player.name_surname} receives a HALF BYE (0.5 pt) in Round {self.current_round} (no eligible regular bye player).")
        
        return bye_player, players_for_pairing

    def pair_round(self, pairing_system: str) -> list[Match]:
        """
        Generates pairings for the current round based on the specified system.
        
        Args:
            pairing_system (str): "random", "by rank",  "dutch", or "monrad".
            
        Returns:
            list[Match]: A list of Match objects for the current round.
        
        Raises:
            ValueError: If an invalid pairing system is specified.
            RuntimeError: If pairing fails and manual intervention is needed.
        """
        if self.current_round >= self.num_rounds:
            print(f"{self.now()} | Tournament has reached its maximum rounds ({self.num_rounds}). Cannot pair new round.")
            return []

        self.current_round += 1
        self.current_matches = [] # Reset matches for the new round
        self.NEXT_MATCH_ID_IN_ROUND = 1 # Reset match ID for the new round
        self.rounds_matches[self.current_round] = [] # Initialize list for this round

        print(f"\n{self.long_line()}")
        print(f"{self.now()} | Pairing Round {self.current_round} / {self.num_rounds} using {pairing_system.upper()} system.")

        # Reset has_bye_this_round for all players at the start of a new round
        for p in self.players:
            p.has_bye_this_round = False # Only relevant for the current round

        # Get players who are present for this round
        active_players = [p for p in self.players if p.id != 0] # Exclude dummy bye opponent
        if len(active_players) < 2:
            print(f"{self.now()} | Not enough active players ({len(active_players)}) to pair a round.")
            return []

        # Handle bye assignment for the round
        bye_player, players_for_pairing = self._handle_bye_assignment(active_players)
        
        if len(players_for_pairing) % 2 != 0: # Should be even after bye handling
            raise RuntimeError(f"Internal error: Odd number of players ({len(players_for_pairing)}) remaining after bye assignment for pairing.")
        
        if not players_for_pairing: # No players left after bye, e.g., 1 player tournament
            print(f"{self.now()} | No players left to pair after bye assignment.")
            return self.current_matches

        # --- Perform Pairing based on System ---
        paired_player_tuples: list[tuple[Player, Player]] = []
        
        if pairing_system == "random":
            random.shuffle(players_for_pairing)
            for i in range(0, len(players_for_pairing), 2):
                paired_player_tuples.append((players_for_pairing[i], players_for_pairing[i+1]))

        elif pairing_system == "by rank":
            players_for_pairing.sort(key=lambda p: (p.points, p.elo), reverse=True)
            for i in range(0, len(players_for_pairing), 2):
                paired_player_tuples.append((players_for_pairing[i], players_for_pairing[i+1]))
            
        elif pairing_system in ["dutch", "monrad"]:
            # Sort players according to the system's rules before passing to optimal pairing
            players_for_pairing.sort(key=lambda p: (p.points, p.elo), reverse=True)

            optimal_pairing_result = self.pairing_manager.find_optimal_pairing(
                players_for_pairing, self.current_round, pairing_system
            )
            
            if optimal_pairing_result:
                paired_player_tuples = optimal_pairing_result[0]
            else:
                print(f"{self.now()} | Failed to find optimal {pairing_system.upper()} pairing. Assigning half-byes to remaining players.")
                for p in players_for_pairing: # Give half-bye to all remaining
                    if not p.has_bye_this_round: # Only if not already handled as absent or regular bye
                        p.add_points(0.5)
                        p.has_bye_this_round = True
                        self._add_match_to_tournament(p, None, is_half_bye=True)
                return self.current_matches # Return matches with half-byes
        else:
            raise ValueError(f"Unknown pairing system: {pairing_system}")

        # --- Create Match Objects and Assign Colors ---
        for p1, p2 in paired_player_tuples:
            white_player, black_player = self._assign_colors_to_pair(p1, p2)
            self._add_match_to_tournament(white_player, black_player)
        
        print(f"{self.now()} | Round {self.current_round} pairings complete.")
        return self.current_matches

    def enter_result(self, match_id: int, result: str, round_num: int | None = None) -> None:
        """
        Enters the result for a given match ID and round number, then updates player scores.
        """
        if round_num is None:
            round_num = self.current_round
        
        matches_in_round = self.rounds_matches.get(round_num)
        if not matches_in_round:
            print(f"{self.now()} | Error: No matches found for Round {round_num}.")
            return

        match_found = None
        for match in matches_in_round:
            if match.match_id == match_id:
                match_found = match
                break
        
        if not match_found:
            print(f"{self.now()} | Error: Match ID {match_id} not found in Round {round_num}.")
            return

        if match_found.is_bye_match: # Cannot enter result for bye match, points already awarded
            print(f"{self.now()} | Match ID {match_id} (R{round_num}) is a bye match. Points for {match_found.player_white.name_surname} already awarded.")
            return

        # Check if result was already entered (if it's not the default " - ")
        if match_found.result != " - ":
            print(f"{self.now()} | Warning: Result for Match ID {match_id} (R{round_num}) already entered as '{match_found.result}'. Skipping.")
            return
            
        try:
            match_found.set_result(result) # Use the setter with validation
        except ValueError as e:
            print(f"{self.now()} | Error setting result for Match ID {match_id} (R{round_num}): {e}")
            return

        # Update player points based on result
        if result == "1-0": # White wins
            match_found.player_white.add_points(1.0)
            match_found.player_black.add_points(0.0)
            print(f"{self.now()} | Result entered: {match_found.player_white.name_surname} wins against {match_found.player_black.name_surname}")
        elif result == "0-1": # Black wins
            match_found.player_white.add_points(0.0)
            match_found.player_black.add_points(1.0)
            print(f"{self.now()} | Result entered: {match_found.player_black.name_surname} wins against {match_found.player_white.name_surname}")
        elif result == "0.5-0.5": # Draw
            match_found.player_white.add_points(0.5)
            match_found.player_black.add_points(0.5)
            print(f"{self.now()} | Result entered: Draw between {match_found.player_white.name_surname} and {match_found.player_black.name_surname}")
        else:
            print(f"{self.now()} | Error: Unrecognized result '{result}'. No points awarded.")

        # After results, standings might need to be re-sorted for the next round
        self.update_standings()

    def end_round(self) -> None:
        """
        Finalizes the current round, updates player points based on results,
        and prepares for the next round.
        """
        print(f"\n{self.long_line()}")
        print(f"{self.now()} | Ending Round {self.current_round} / {self.num_rounds}")

        # Update color balance counters and reset has_bye_this_round
        for p in self.players:
            if p.id == 0: # Skip dummy bye opponent
                continue
            
            else:
                # Update color balance for players who played a match
                # Find the match they played in this round
                player_match = None
                for match in self.rounds_matches.get(self.current_round, []):
                    if match.player_white.id == p.id:
                        player_match = match
                        p.color_balance_counter += 1
                        break
                    elif match.player_black.id == p.id:
                        player_match = match
                        p.color_balance_counter -= 1
                        break
        
        # Clear current matches for the next round
        self.current_matches = []
        # self.NEXT_MATCH_ID_IN_ROUND will be reset at the start of pair_round

        print(f"{self.now()} | Round {self.current_round} / {self.num_rounds} ended.")
        self.print_standings()
        print(self.long_line())

    def print_standings(self, top: int | None = None) -> None:
        """Prints the current tournament standings.
        Args:
            top (int | None, optional): Maximum number of players to display.
            If None -> display all players.
        """
        self.update_standings() # Ensure sorted before printing
        print(f"\n--- {self.now()} | Current Standings (Round {self.current_round} / {self.num_rounds}) ---")
        print(f"{'Rank':<5} {'Player Name':<25} {'ELO':<6} {'Points':<7} {'Bye':<5} {'Present':<8} {'Color Bal.':<10}")
        print("-" * 80)
        rank = 1
        if top is None:
            top = len(self.players)
        for player in self.players:
            if rank > top:
                break
            # Do not display the dummy BYE_OPPONENT in standings
            if player.id == 0 and player.name_surname == "BYE_OPPONENT":
                continue 
            bye_status = "No"
            if player.had_regular_bye:
                bye_status = "Yes"
            if player.has_bye_this_round:
                bye_status = "Half" 
            present_status = "Yes" if player.is_present else "No"
            print(f"{rank:<5} {player.name_surname:<25} {player.elo:<6} {player.points:<7.1f} {bye_status:<5} {present_status:<8} {player.color_balance_counter:<10}")
            rank += 1
        print("-" * 80)

    def print_pairings(self, round_number: int | None = None) -> None:
        """
        Prints pairings for a specific round or the current round.
        """
        if round_number is None:
            round_number = self.current_round
        
        matches_to_print = self.rounds_matches.get(round_number)
        if not matches_to_print:
            print(f"{self.now()} | No pairings found for Round {round_number}.")
            return
        
        print(f"\n--- {self.now()} | Pairings for Round {round_number} ---")
        for match in matches_to_print:
            print(match) # Use the __str__ of Match
        print("-" * 30)

    def export_standings_to_txt(self, filepath: str = "standings.txt") -> None:
        """
        Exports current tournament standings to a plain text file.

        Args:
            filepath (str): The path to the file where standings will be saved.
        """
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        self.update_standings() # Ensure standings are current

        with open(filepath, "w") as file:
            file.write(f"--- {self.now()} | Current Standings (Round {self.current_round} / {self.num_rounds}) ---\n")
            file.write(f"{'Rank':<5} {'Player Name':<25} {'ELO':<6} {'Points':<7} {'Bye':<5} {'Present':<8} {'Color Bal.':<10}\n")
            file.write("-" * 80 + "\n")
            rank = 1
            for player in self.players:
                if player.id == 0 and player.name_surname == "BYE_OPPONENT":
                    continue
                bye_status = "Reg" if player.had_regular_bye else ("Half" if player.has_bye_this_round else "No")
                present_status = "Yes" if player.is_present else "No"
                file.write(f"{rank:<5} {player.name_surname:<25} {player.elo:<6} {player.points:<7.1f} {bye_status:<5} {present_status:<8} {player.color_balance_counter:<10}\n")
                rank += 1
            file.write("-" * 80 + "\n")
        print(f"{self.now()} | Standings exported to {filepath}!")
    def export_standings_to_csv(self, filepath: str = "standings.csv") -> None:
        """Exports current standings to a CSV file."""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        self.update_standings() # Ensure standings are current
        
        with open(filepath, "w", newline='') as file:
            fieldnames = ["Rank", "Player Name", "ELO", "Points", "Had Regular Bye", "Had Half Bye This Round", "Is Present", "Color Balance Counter"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            rank = 1
            for player in self.players:
                if player.id == 0 and player.name_surname == "BYE_OPPONENT": # Do not export dummy BYE_OPPONENT
                    continue
                writer.writerow({
                    "Rank": rank,
                    "Player Name": player.name_surname,
                    "ELO": player.elo,
                    "Points": player.points,
                    "Had Regular Bye": "Yes" if player.had_regular_bye else "No",
                    "Had Half Bye This Round": "Yes" if player.has_bye_this_round else "No",
                    "Is Present": "Yes" if player.is_present else "No",
                    "Color Balance Counter": player.color_balance_counter
                })
                rank += 1
        print(f"{self.now()} | Standings exported to {filepath}!")

    def export_pairings_to_txt(self, filepath: str = "pairings.txt", round_number: int | None = None) -> None:
        """Exports pairings to a TXT file."""
        if round_number is None:
            round_number = self.current_round
        
        matches_to_export = self.rounds_matches.get(round_number)
        if not matches_to_export:
            print(f"{self.now()} | No pairings found for Round {round_number} to export.")
            return

        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, "w") as file:
            file.write(f"--- {self.now()} | Tournament Pairings for Round {round_number} ---\n")
            for match in matches_to_export:
                file.write(str(match) + "\n") # Use __str__ of Match
            file.write("-" * 40 + "\n")
        print(f"{self.now()} | Pairings for Round {round_number} exported to {filepath}!")

    def save_tournament_state(self, players_filepath: str = "players_state.csv", matches_filepath: str = "matches.csv", meta_filepath: str = "tournament_meta.csv") -> None:
        """
        Saves the entire tournament state across multiple CSV files.
        - players.csv: Player details
        - matches.csv: All match details (including round number)
        - tournament_meta.csv: Basic tournament metadata (current_round, num_rounds)
        """
        # Save Players
        self.save_players_to_csv(players_filepath)

        # Save Matches
        os.makedirs(os.path.dirname(matches_filepath) or '.', exist_ok=True)
        with open(matches_filepath, 'w', newline='') as f:
            fieldnames = ["match_id", "round_number", "player_white_id", "player_black_id", "result", "is_bye_match", "is_half_bye_match"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # Iterate through all matches in all rounds
            for round_num in sorted(self.rounds_matches.keys()):
                for match in self.rounds_matches[round_num]:
                    writer.writerow(match.to_dict())
        print(f"{self.now()} | Matches saved to {matches_filepath}!")

        # Save Metadata
        os.makedirs(os.path.dirname(meta_filepath) or '.', exist_ok=True)
        with open(meta_filepath, 'w', newline='') as f:
            fieldnames = ["current_round", "num_rounds", "next_player_id", "next_match_id_in_round_counter"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                "current_round": self.current_round,
                "num_rounds": self.num_rounds,
                "next_player_id": self.next_player_id,
                "next_match_id_in_round_counter": self.NEXT_MATCH_ID_IN_ROUND
            })
        print(f"{self.now()} | Tournament metadata saved to {meta_filepath}!")

    def load_tournament_state(self, players_filepath: str = "players_state.csv", matches_filepath: str = "matches.csv", meta_filepath: str = "tournament_meta.csv") -> None:
        """
        Loads the entire tournament state from multiple CSV files.
        """
        # Load Metadata first
        if os.path.exists(meta_filepath) and os.path.getsize(meta_filepath) > 0:
            with open(meta_filepath, 'r', newline='') as f:
                reader = csv.DictReader(f)
                try:
                    meta_data = next(reader)
                    self.current_round = int(meta_data.get("current_round", 0))
                    self.num_rounds = int(meta_data.get("num_rounds", 5))
                    self.next_player_id = int(meta_data.get("next_player_id", 1))
                    self.NEXT_MATCH_ID_IN_ROUND = int(meta_data.get("next_match_id_in_round_counter", 1))
                    print(f"{self.now()} | Metadata loaded from {meta_filepath}!")
                except (StopIteration, KeyError, ValueError) as e:
                    print(f"{self.now()} | Error loading metadata from {meta_filepath}: {e}. Resetting tournament state.")
                    self.__init__(self.num_rounds)
                    return
        else:
            print(f"{self.now()} | No metadata file '{meta_filepath}' found. Initializing tournament defaults.")
            self.__init__(self.num_rounds)
            return

        # Load Players
        self.load_players_from_csv(players_filepath)
        players_by_id = {p.id: p for p in self.players} # Create lookup for matches

        # Load Matches
        if os.path.exists(matches_filepath) and os.path.getsize(matches_filepath) > 0:
            self.rounds_matches = {} # Clear existing matches before loading
            with open(matches_filepath, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        match = Match.from_dict(row, players_by_id)
                        # Add to rounds_matches based on its round_number
                        self.rounds_matches.setdefault(match.round_number, []).append(match)
                    except (KeyError, ValueError, TypeError) as e:
                        print(f"{self.now()} | Error loading match from row {row}: {e}. Skipping match.")
            print(f"{self.now()} | Matches loaded from {matches_filepath}!")
        else:
            print(f"{self.now()} | No match data file '{matches_filepath}' found. No matches loaded.")
            self.rounds_matches = {}
        
        print(f"{self.now()} | Tournament state fully loaded!")
