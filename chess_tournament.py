import os, json, csv, datetime, random, math
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union
from collections import *


# --- Player Class ---
class Player:
    """Represents a chess player in the tournament."""
    def __init__(self, id: int, name_surname: str, elo: int):
        if not isinstance(id, int) or id < 0:
            raise ValueError("Player ID must be a non-negative integer.")
        if not isinstance(name_surname, str) or not name_surname.strip():
            raise ValueError("Player name cannot be empty.")
        if not isinstance(elo, int) or elo < 0:
            print(f"Warning: ELO for {name_surname} is invalid ({elo}). Setting to 100.")
            elo = 100

        self.id = id
        self.name_surname = self._name_surname_encoder(name_surname.strip())
        self.elo = self._elo_encoder(elo)
        self.points = 0.0
        self.bonus_points = 0.0
        self.past_colors: list[str] = []
        self.past_matches: list[int] = []
        self.past_opponents: list[int] = []
        self.had_regular_bye = False
        self.has_bye_this_round = False
        self.is_present = True
        self.color_balance_counter = 0
        self.past_results: list[str] = []

    @staticmethod
    def _name_surname_encoder(name_surname: str) -> str:
        """Encode name to fit within length limits (20 characters).
        Args:
            name_surname (str): Player name.
        Returns:
            str: Encoded name.
        """
        length_limit: int = 20
        if name_surname is None or name_surname.strip() == "":
            return "BYE_OPPONENT"
        if len(name_surname) < length_limit:
            return name_surname
        
        name_surname_list = name_surname.split()
        for i in range(len(name_surname_list) - 1):
            name_surname_list[i] = name_surname_list[i][0] + ". "
        name_surname = "".join(name_surname_list)
        
        if len(name_surname) < length_limit:
            return name_surname
        
        return (name_surname[:length_limit - 3] + "...")

    @staticmethod
    def _elo_encoder(elo_input: int | float | None | str) -> int:
        """Encode ELO to valid integer format.
        Args:
            elo_input: Player ELO (even in sentence)
        Returns:
            int: Encoded ELO, 100 if couldn't encode.
        """
        try:
            return int(elo_input)
        except (ValueError, TypeError):
            if isinstance(elo_input, str):
                for item in elo_input.split():
                    if item.isdigit():
                        return int(item)
            print(f"{TournamentUtils.now()} | Warning: Invalid ELO format '{elo_input}'. Defaulting to 100.")
            return 100

    def add_points(self, n: float) -> None:
        if not isinstance(n, (int, float)):
            raise TypeError("Points to add must be a number.")
        self.points = math.fsum([self.points, n])

    def add_bonus_points(self, n: float) -> None:   
        if not isinstance(n, (int, float)):
            raise TypeError("Points to add must be a number.")
        self.bonus_points = math.fsum([self.points, n])

    def player_and_elo(self) -> str:
        return f"ID: {self.id :<3} | {self.name_surname :<20} ({self.elo :<4} elo)"

    def __str__(self) -> str:
        return f"{self.name_surname} ({self.points:.1f} points)"

    def __repr__(self) -> str:
        return f"<{self.name_surname} - {self.points} pts>"
    
    def to_dict(self) -> dict:
        """Returns a dictionary representation of the current Player object."""
        return {
            "id": self.id,
            "name_surname": self.name_surname,
            "elo": self.elo,
            "points": self.points,
            "past_colors": json.dumps(self.past_colors),
            "past_matches": json.dumps(self.past_matches),
            "past_opponents": json.dumps(self.past_opponents),
            "had_regular_bye": str(self.had_regular_bye),
            "has_bye_this_round": str(self.has_bye_this_round),
            "is_present": str(self.is_present),
            "color_balance_counter": self.color_balance_counter,
            "past_results": json.dumps(self.past_results)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """ Create a Player object from a dictionary representation. (Usually used for loading from a JSON file)
        Args:
            data (dict): Dictionary representation of the Player object.
        Returns:
            Player: Player object created from the dictionary representation.
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
        player.has_bye_this_round = data.get("has_bye_this_round", "false").lower() == 'true'
        player.is_present = data.get("is_present", "true").lower() == 'true'
        player.color_balance_counter = int(data.get("color_balance_counter", 0))
        player.past_results = json.loads(data.get("past_results", "[]"))
        return player


# --- Match Class ---
class Match:
    """Represents a single chess match between two players."""
    def __init__(self, match_id: int, player_white: Player, player_black: Optional[Player], round_number: int):
        if not isinstance(player_white, Player):
            raise TypeError("Player white must be a Player object.")
        if player_black is not None and not isinstance(player_black, Player):
            raise TypeError("Player black must be a Player object or None.")
        if player_black is not None and player_white.id == player_black.id and player_white.id != 0:
            raise ValueError("A player cannot play against themselves.")
        if not isinstance(round_number, int) or round_number <= 0:
            raise ValueError("Round number must be a positive integer.")
        
        self.match_id = match_id
        self.player_white = player_white
        self.player_black = player_black if player_black is not None else Player(0, "BYE_OPPONENT", 0)
        self.round_number = round_number
        self.result = " - "
        self.is_bye_match = False
        self.is_half_bye_match = False

        if player_black is None:
            self.is_bye_match = True
            self.result = "bye"

    def set_result(self, result: str) -> None:
        """Set the result of the match.
        Args:
            result (str): Result of the match. Must be one of: "1-0", "0-1", "0.5-0.5", "bye", "half bye".
        Raises:
            ValueError: If the result is not valid.
        """
        valid_results = {"1-0", "0-1", "0.5-0.5", "bye", "half bye"}
        if result not in valid_results:
            raise ValueError(f"Invalid result format. Must be one of: {', '.join(valid_results)}")
        
        if self.is_bye_match and result not in ["bye", "half bye"]:
            print(f"Warning: Match ID {self.match_id} (R{self.round_number}) is a bye match. Result cannot be changed to '{result}'.")
            return

        if self.result != " - " and result != self.result: 
             print(f"Warning: Result for Match ID {self.match_id} (R{self.round_number}) already entered as '{self.result}'. Now result is changed to '{result}'.")
        self.result = result

    def __str__(self) -> str:
        if self.is_bye_match:
            bye_type = "BYE" if self.result == "bye" else "HALF BYE"
            return f"Match ID {self.match_id :<2} (R{self.round_number :<2}): {self.player_white.name_surname} ({bye_type}) - Result: {self.result}"
        else:
            return (f"Match ID {self.match_id :<2} (R{self.round_number :<2}): {self.player_white.name_surname} (W) vs "
                    f"{self.player_black.name_surname} (B) - Result: {self.result}")

    def __repr__(self):
        return f"<R{self.round_number} ID{self.match_id} | {self.player_white.name_surname} {self.result} {self.player_black.name_surname}>"
        
    def to_dict(self) -> dict:
        """Return dictionary rappresentation of the current match."""
        return {
            "match_id": self.match_id,
            "round_number": self.round_number,
            "player_white_id": self.player_white.id,
            "player_black_id": self.player_black.id,
            "result": self.result,
            "is_bye_match": str(self.is_bye_match),
            "is_half_bye_match": str(self.is_half_bye_match)
        }

    @classmethod
    def from_dict(cls, data: dict, players_by_id: dict) -> 'Match':
        """Create a Match object from a dictionary representation.
        Args:
            data (dict): Dictionary containing the match data.
            players_by_id (dict): Dictionary mapping player IDs to Player objects.
        Returns:
            Match: The created Match object.
        Raises:
            ValueError: If the player IDs in the data are not found in the players_by_id dictionary.
        """
        white_id = int(data["player_white_id"])
        black_id = int(data["player_black_id"])
        
        player_white = players_by_id.get(white_id)
        player_black = players_by_id.get(black_id) 

        is_bye = data.get("is_bye_match", 'False').lower() == 'true'
        is_half_bye = data.get("is_half_bye_match", 'False').lower() == 'true'

        if not player_white:
            raise ValueError(f"Could not find white player for match ID {data['match_id']}. ID: {white_id}")
        
        if is_bye and black_id == 0 and not player_black:
            player_black = Player(0, "BYE_OPPONENT", 0)
        elif not player_black and not is_bye:
             raise ValueError(f"Could not find black player for match ID {data['match_id']}. ID: {black_id}")

        match = cls(int(data["match_id"]), player_white, player_black, int(data["round_number"]))
        match.result = data["result"]
        match.is_bye_match = is_bye
        match.is_half_bye_match = is_half_bye
        return match


# --- Utility Functions ---
class TournamentUtils:
    """Utility functions for tournament management."""
    
    @staticmethod
    def now() -> str:
        return datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")

    @staticmethod
    def long_line() -> str:
        return "--- " * 20


# --- Player Manager ---
class PlayerManager:
    """Manages all player-related operations."""
    
    def __init__(self):
        self.players: List[Player] = []
        self.next_player_id = 1

    def add_player(self, name_surname: str, elo: int, id: int = -1) -> None:
        
        """
        Add a new player to the tournament or update an existing player's ELO.

        Args:
            name_surname (str): The name and surname of the player.
            elo (int): The ELO rating of the player.
            id (int, optional): The ID to assign to the player. If not provided or if the ID already exists,
                                a new ID is generated.

        If a player with the same name_surname already exists, their ELO is updated to the provided value.
        Otherwise, a new Player object is created and added to the list of players.
        """
        if id == -1 or self.get_player_by_id(id):
            id_to_use = self.next_player_id
        else:
            id_to_use = id
        
        existing_player = self.get_player_by_name(name_surname)
        if existing_player:
            print(f"{TournamentUtils.now()} | Player '{name_surname}' already exists. Updating ELO from {existing_player.elo} to {elo}.")
            existing_player.elo = elo
        else:
            p = Player(id_to_use, name_surname, elo)
            self.players.append(p)
            self.update_next_player_id()
            print(f"{TournamentUtils.now()} | Player added: {p.player_and_elo()}")

    def get_player_by_name(self, name_surname: str) -> Optional[Player]:
        """
        Arg:
        Returns the player with the given name_surname, or None if not found."""
        name_surname = Player._name_surname_encoder(name_surname).lower()
        for player in self.players:
            if player.name_surname.lower() == name_surname and player.id != 0:
                return player
        return None
    
    def toggle_player_presence(self, player_id: int) -> str:
        player = self.get_player_by_id(player_id)
        player.is_present = not player.is_present
        if player.is_present:
            return f"{TournamentUtils.now()} | Player {player.name_surname} is present now."
        else:
            return f"{TournamentUtils.now()} | Player {player.name_surname} is absent now."

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Rerutns the player with the given ID, or None if not found."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def get_all_players(self) -> List[Player]:
        return self.players.copy()

    def get_active_players(self) -> List[Player]:
        return [p for p in self.players if p.id != 0 and p.is_present] # Filter by is_present

    def update_next_player_id(self) -> None:
        if self.players:
            valid_player_ids = [p.id for p in self.players if p.id != 0]
            if valid_player_ids:
                self.next_player_id = max(valid_player_ids) + 1
            else:
                self.next_player_id = 1
        else:
            self.next_player_id = 1

    def update_standings(self) -> None:
        self.players.sort(key=lambda p: (p.points, -p.color_balance_counter, p.elo), reverse=True)

    def get_final_standings(self, top: Optional[int] = None)-> list[Player]:
        if top is None:
            top = len(self.players)
        
        top -= 1

        final_standings: list[Player] = []

        scoregroups: dict[float, List[Player]] = defaultdict(list)
        #creating scoregroups
        for player in self.players:
            if player.points < self.players[top].points:
                break
            scoregroups[player.points].append(player)

        for scoregruop in scoregroups.values():
            if len(scoregruop) == 1:
                final_standings.append(scoregruop[0])
                continue
            #if there are more players in the scoregroup
            players_and_avarage_opponent: dict[Player, float] = {
                #Player object: the avarage opponents points
            }
            for player in scoregruop:
                opponents_points: list[float] = []
                for i, match_result in enumerate(player.past_results):
                    match(match_result):
                        case "B" | "HB":
                            # skip bye matches
                            continue
                        case "L":
                            # don't give points for losses
                            opponents_points.append(0.0)
                            # but we give some points for elo in any case (tie-breaker)
                            opponents_points.append(self.get_player_by_id(player.past_opponents[i]).elo / 10000)
                            continue
                        case "W":
                            opponent = self.get_player_by_id(player.past_opponents[i])
                            # Prioritize Head-to-Head matches
                            if opponent in scoregruop:
                                opponents_points.append(opponent.points ** 2)
                            else:
                                opponents_points.append(opponent.points)

                            opponents_points.append(opponent.elo / 10000)
                            continue
                        case "D":
                            opponents_points.append(self.get_player_by_id(player.past_opponents[i]).points / 2)
                            opponents_points.append(self.get_player_by_id(player.past_opponents[i]).elo / 10000)
                            continue
                        case _:
                            pass
                players_and_avarage_opponent[player] = (math.fsum(opponents_points) * 2) / len(opponents_points) 

            #Sort the scoregroup by the sum of the opponents' points (descending), 
            players_and_avarage_opponent: list[tuple[Player, float]] = sorted(
                players_and_avarage_opponent.items(),
                key=lambda x: x[1],
                reverse=True)
            
            final_standings.extend([x[0] for x in players_and_avarage_opponent])
        
        if len(final_standings) < len(self.players):
            final_standings.extend(self.players[len(final_standings):])

        return final_standings


# --- Pairing Engine ---
class PairingEngine:
    """Handles all pairing logic and algorithms."""
    
    # --- Constants for badness calculation and limits ---
    # Penalty for a single rematch. 
    REMATCH_PENALTY: float = 1000.0

    # For quadratic penalty (e.g., if played twice, 4x penalty):
    # REMATCH_PENALTY_QUADRATIC_FACTOR = 100.0 # Use this if you want quadratic penalty
    # badness_matrix.loc[p1.id, p2.id] += self.REMATCH_PENALTY_QUADRATIC_FACTOR * (rematch_count ** 2)

    ELO_DIFF_DIVISOR: float = 500.0
    # POSITION_FINE_TUNE_DIVISOR = 1000.0 # Tiny influence from index difference (if you want)

    #MATCH_BADNESS_LIMIT is a heuristic for speed.
    #If total badness of a complete pairing falls below this, the search stops early.
    #If you don't want to skip any matches, set this to float("inf")
    MATCH_BADNESS_LIMIT: float = 10.0
    
    # MATCH_ACCECPTABLE_BADNESS_LIMIT is a heuristic for speed.
    # If total badness of a complete pairing falls below this, the search stops early.
    # If you want to ALWAYS find the absolute mathematically best pairing, set this to 0.0.
    MATCH_ACCEPTABLE_BADNESS_LIMIT:float = 3.0

    def __init__(self, player_manager: PlayerManager):
        self.player_manager = player_manager

    def _calculate_badness_matrix(self, players_list: List[Player], pairing_system: str) -> pd.DataFrame:
        
        """
        Creates a badness matrix for the given players, using a combination of penalties
        for rematches, point differences, and ELO differences.
        The matrix is symmetric, but it generates only the upper triangle.
        
        Args:
            players_list: List of Player objects to calculate the matrix for.
        
        Return:
            A symmetric Pandas DataFrame with the badness of each possible pair.
        """
        player_ids = [p.id for p in players_list]
        # Initialize with inf, then fill.
        badness_matrix = pd.DataFrame(float("inf"), index=player_ids[:-1], columns=player_ids)

        for i, p1 in enumerate(players_list[:-1]):
            for j, p2 in enumerate(players_list):
                if i >= j: # Only calculate for the upper triangle and then mirror
                    continue # Skip redundant calculations for lower triangle and diagonal

                current_pair_badness: float = 0.0

                # 1. Rematch penalty
                if p2.id in p1.past_opponents:
                    current_pair_badness += self.REMATCH_PENALTY
                    # If you want quadratic penalty, uncomment the line below and the constant above:
                    # rematch_count = p1.past_opponents.count(p2.id)
                    # current_pair_badness += self.REMATCH_PENALTY_QUADRATIC_FACTOR * (rematch_count ** 2)

                # 2. Points difference (squared)
                current_pair_badness += (p1.points - p2.points) ** 2

                # 3. ELO difference (divided by 500)
                elo_diff = abs(p1.elo - p2.elo)
                current_pair_badness += (elo_diff / self.ELO_DIFF_DIVISOR)

                # Assign to both symmetrical cells
                badness_matrix.loc[p1.id, p2.id] = current_pair_badness
                #badness_matrix.loc[p2.id, p1.id] = current_pair_badness # Mirror the value
                
        return badness_matrix

    def _find_best_pairing_recursive(self, players_remaining: List[Player], badness_matrix: pd.DataFrame, 
                                     current_best_total_badness: float, current_pairing_attempt: List[Tuple[Player, Player]]) -> Optional[Tuple[List[Tuple[Player, Player]], float]]:
        """
        Recursively searches for the best possible pairing of players by minimizing the total
        "badness" of all pairs.
        
        This function is a recursive helper for `find_best_pairing` and should not be called directly.
        It takes the current best total badness and the current pairing attempt as parameters to
        prune the search space.
        
        Args:
            players_remaining: List of Player objects that still need to be paired.
            badness_matrix: Pandas DataFrame with the badness of each possible pair.
            current_best_total_badness: The best total badness found so far.
            current_pairing_attempt: List of pairs that have been tried so far.
        
        Returns:
            A tuple containing the best pairing found and its total badness, or None if no valid
            pairing was found.
        """
        if not players_remaining:
            return ([], 0.0)

        if len(players_remaining) == 2:
            p1 = players_remaining[0]
            p2 = players_remaining[1]
            badness = badness_matrix.loc[p1.id, p2.id]

            if badness >= current_best_total_badness or badness > self.MATCH_BADNESS_LIMIT:
                return None
            
            return ([(p1, p2)], badness)

        best_overall_pairing = None
        min_overall_badness = float("inf")
        first_player = players_remaining[0]

        for i in range(1, len(players_remaining)):
            current_partner = players_remaining[i]
            pair_badness = badness_matrix.loc[first_player.id, current_partner.id]
            
            # This check is important: if a pair is impossible (inf), skip it.
            if pair_badness == float("inf"):
                continue
            
            # Pruning: If this single pair's badness already exceeds the best known total
            # or exceeds the single match badness limit, skip.
            if pair_badness >= current_best_total_badness or pair_badness > self.MATCH_BADNESS_LIMIT:
                continue

            remaining_players_for_recursion = players_remaining[1:i] + players_remaining[i+1:]
            
            recursive_result = self._find_best_pairing_recursive(
                remaining_players_for_recursion, 
                badness_matrix, 
                current_best_total_badness - pair_badness,
                current_pairing_attempt + [(first_player, current_partner)] 
            )

            if recursive_result:
                recursive_pairing, recursive_badness = recursive_result
                total_badness_for_combo = pair_badness + recursive_badness
                
                if total_badness_for_combo < min_overall_badness:
                    min_overall_badness = total_badness_for_combo
                    best_overall_pairing = [(first_player, current_partner)] + recursive_pairing
                    current_best_total_badness = min_overall_badness
                    
                    if self.MATCH_ACCEPTABLE_BADNESS_LIMIT is not None and min_overall_badness < self.MATCH_ACCEPTABLE_BADNESS_LIMIT:
                        return (best_overall_pairing, min_overall_badness)
            
        if best_overall_pairing is None and min_overall_badness == float("inf"):
            return None
        
        return (best_overall_pairing, min_overall_badness)

    def find_optimal_pairing(self, players_to_pair: List[Player]) -> Optional[Tuple[List[Tuple[Player, Player]], float]]:
        if not players_to_pair:
            return ([], 0.0)
        if len(players_to_pair) % 2 != 0:
            raise ValueError("Player list for optimal pairing must be even after bye assignment.")

        self.badness_matrix = self._calculate_badness_matrix(players_to_pair, "dutch")
        round_badness_limit = len(players_to_pair) * 4 # Adjusted limit to be more generous

        result = self._find_best_pairing_recursive(
            players_to_pair, 
            self.badness_matrix, 
            round_badness_limit,
            []
        )
        
        if result and result[1] <= round_badness_limit:
            return result
        else:
            print(f"{TournamentUtils.now()} | Warning: No optimal pairing found within ROUND_BADNESS_LIMIT ({round_badness_limit:.2f}).")
            return None

    def assign_colors_to_pair(self, p1: Player, p2: Player) -> Tuple[Player, Player]:
        """Assign colors based on color balance preference, points, and rating."""
        # Rule 1: Color Preference (color_balance_counter)
        # Prefer the player who has played more with black (lower counter) to get white
        if p1.color_balance_counter < p2.color_balance_counter:
            return p1, p2  # p1 gets white
        if p2.color_balance_counter < p1.color_balance_counter:
            return p2, p1  # p2 gets white

        # Rule 2: Player with fewer points gets White
        if p1.points < p2.points:
            return p1, p2
        if p2.points < p1.points:
            return p2, p1

        # Rule 3: Player with lower ELO gets White (final tie-breaker)
        if p1.elo <= p2.elo: # If ELO is equal, p1 gets white (stable tie-break)
            return p1, p2
        else:
            return p2, p1


# --- Match Manager ---
class MatchManager:
    """Manages matches and round scheduling."""
    
    def __init__(self, player_manager: PlayerManager, pairing_engine: 'PairingEngine'): # Forward reference for PairingEngine
        self.player_manager = player_manager
        self.pairing_engine = pairing_engine
        self.rounds_matches: Dict[int, List[Match]] = {}
        self.next_match_id_in_round = 1

    def get_match_by_round_and_id(self, round_number: int, match_id: int) -> Optional[Match]:
        for match in self.rounds_matches.get(round_number, []):
            if match.round_number == round_number and match.match_id == match_id:
                return match
        return None
    
    def create_match(self, player_white: Player, player_black: Optional[Player], round_number: int, is_half_bye: bool = False) -> Match:
        match = Match(self.next_match_id_in_round, player_white, player_black, round_number)
        self.next_match_id_in_round += 1
        
        if match.is_bye_match:
            match.is_half_bye_match = is_half_bye
            player_white.past_colors.append("half bye" if is_half_bye else "bye")
            if is_half_bye:
                match.result = "half bye"
                player_white.has_bye_this_round = True # Mark for current round
            else:
                player_white.had_regular_bye = True # Mark as had regular bye
                player_white.has_bye_this_round = True # Mark for current round
            player_white.past_matches.append(match.match_id)
            player_white.past_opponents.append(0)
        else:
            player_white.past_opponents.append(player_black.id)
            player_black.past_opponents.append(player_white.id)
            player_white.past_colors.append("white")
            player_black.past_colors.append("black")
            player_white.past_matches.append(match.match_id)
            player_black.past_matches.append(match.match_id)

        self.rounds_matches.setdefault(round_number, []).append(match)
        print(f"{TournamentUtils.now()} | Added match: {match}")
        return match

    def get_eligible_bye_player(self, players_pool: List[Player]) -> Optional[Player]:
        eligible_for_regular_bye = [p for p in players_pool if not p.had_regular_bye]
        if not eligible_for_regular_bye:
            return None

        eligible_for_regular_bye.sort(key=lambda p: (p.points, p.elo))
        lowest_point = eligible_for_regular_bye[0].points
        tied_players = [p for p in eligible_for_regular_bye if p.points == lowest_point]
        
        return random.choice(tied_players)

    def handle_bye_assignment(self, players_pool: List[Player], round_number: int) -> Tuple[Optional[Player], List[Player]]:
        bye_player = None
        players_for_pairing = list(players_pool)

        # Handle absent players first (they always get a half-bye)
        absent_players = [p for p in players_for_pairing if not p.is_present]
        for p in absent_players:
            if p.id != 0 and not p.has_bye_this_round: # Ensure not already assigned a bye
                p.add_points(0.5)
                p.has_bye_this_round = True
                self.create_match(p, None, round_number, is_half_bye=True)
                print(f"{TournamentUtils.now()} | Player {p.name_surname} is absent and receives a HALF BYE (0.5 pt) in Round {round_number}.")
        
        # Remove absent players from the pool for pairing
        players_for_pairing = [p for p in players_for_pairing if p.is_present]

        if len(players_for_pairing) % 2 != 0: # Odd number of players remaining, so a bye is needed
            potential_regular_bye_player = self.get_eligible_bye_player(players_for_pairing)

            if potential_regular_bye_player:
                bye_player = potential_regular_bye_player
                bye_player.add_points(1.0)
                # had_regular_bye and has_bye_this_round are set in create_match
                self.create_match(bye_player, None, round_number) # This creates a regular bye match
                players_for_pairing.remove(bye_player)
                print(f"{TournamentUtils.now()} | Player {bye_player.name_surname} receives a REGULAR BYE (1.0 pt) in Round {round_number}.")
            else:
                # Fallback to Half Bye if no one eligible for Regular Bye
                players_for_pairing.sort(key=lambda p: (p.points, p.elo))
                half_bye_player = players_for_pairing.pop(0) # Take the lowest-rated player
                
                half_bye_player.add_points(0.5)
                # has_bye_this_round is set in create_match
                bye_player = half_bye_player # This is our bye player for this round
                self.create_match(bye_player, None, round_number, is_half_bye=True)
                print(f"{TournamentUtils.now()} | Player {half_bye_player.name_surname} receives a HALF BYE (0.5 pt) in Round {round_number} (no eligible regular bye player).")
        
        return bye_player, players_for_pairing

    def get_matches_for_round(self, round_number: int) -> List[Match]:
        return self.rounds_matches.get(round_number, [])

    def reset_match_id_counter(self) -> None:
        self.next_match_id_in_round = 1


# --- Result Tracker ---
class ResultTracker:
    """Manages match results and scoring."""
    
    def __init__(self, match_manager: MatchManager, player_manager: PlayerManager):
        self.match_manager = match_manager
        self.player_manager = player_manager

    def enter_result(self, match_id: int, result: str, round_num: int) -> None:
        matches_in_round = self.match_manager.get_matches_for_round(round_num)
        if not matches_in_round:
            print(f"{TournamentUtils.now()} | Error: No matches found for Round {round_num}.")
            return

        match_found = None
        for match in matches_in_round:
            if match.match_id == match_id:
                match_found = match
                break
        
        if not match_found:
            print(f"{TournamentUtils.now()} | Error: Match ID {match_id} not found in Round {round_num}.")
            return

        if match_found.is_bye_match:
            print(f"{TournamentUtils.now()} | Match ID {match_id} (R{round_num}) is a bye match. Points for {match_found.player_white.name_surname} already awarded.")
            return
            
        try:
            match_found.set_result(result)
        except ValueError as e:
            print(f"{TournamentUtils.now()} | Error setting result for Match ID {match_id} (R{round_num}): {e}")
            return
    
        print(f"{TournamentUtils.now()} | Match ID {match_id} (R{round_num}) result set to {result}.")

    def update_players_results(self, matches: List[Match]) -> None:
        for m in matches:
            match(m.result.lower()):
                case "1-0":
                    m.player_white.add_points(1.0)
                    m.player_white.past_results.append("W")
                    m.player_black.past_results.append("L")
                    m.player_black.color_balance_counter -= 1
                    m.player_white.color_balance_counter += 1
                case "0-1":
                    m.player_black.add_points(1.0)
                    m.player_white.past_results.append("L")
                    m.player_black.past_results.append("W")
                    m.player_black.color_balance_counter -= 1
                    m.player_white.color_balance_counter += 1
                case "0.5-0.5":
                    m.player_black.add_points(0.5)
                    m.player_white.add_points(0.5)
                    m.player_white.past_results.append("D")
                    m.player_black.past_results.append("D")
                    m.player_black.color_balance_counter -= 1
                    m.player_white.color_balance_counter += 1
                case "bye":
                    #points are already added in handle_bye_assignment
                    m.player_white.past_results.append("B")
                case "half bye":
                    m.player_white.past_results.append("HB")
                case _:
                    try:
                        m.player_white.past_results.append(m.result)
                        m.player_black.past_results.append(m.result)
                    except:
                        print(f"{TournamentUtils.now()} | Error: Unrecognized result '{m.result}'. No points awarded.")
            

# --- File Manager ---
class FileManager:
    """Handles all file I/O operations."""
    
    def __init__(self, player_manager: PlayerManager, match_manager: MatchManager):
        self.player_manager = player_manager
        self.match_manager = match_manager

    def save_players_to_csv(self, filepath: str = "players.csv") -> None:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

        with open(filepath, "w", newline='') as file:
            fieldnames = ["id", "name_surname", "elo", "points", "past_colors", 
                          "past_matches", "past_opponents", "had_regular_bye", "has_bye_this_round", "is_present", "color_balance_counter", "past_results"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for player in self.player_manager.get_all_players():
                if player.id == 0 and player.name_surname == "BYE_OPPONENT":
                    continue
                writer.writerow(player.to_dict())
            print(f"{TournamentUtils.now()} | Players saved to {filepath}!")

    def load_players_from_csv(self, filepath: str = "registered_players.csv", clear_players: bool = True) -> None:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"{TournamentUtils.now()} | No player data file '{filepath}' found or file is empty. Starting with no players.")
            if clear_players:
                self.player_manager.players = []
            return
        
        if clear_players:
            self.player_manager.players = []

        with open(filepath, "r", newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    self.player_manager.players.append(Player.from_dict(row))
                except (ValueError, KeyError, json.JSONDecodeError, TypeError) as e:
                    print(f"{TournamentUtils.now()} | Error loading player from row {row}: {e}. Skipping row.")
        
        self.player_manager.update_next_player_id()
        print(f"{TournamentUtils.now()} | Players loaded from {filepath}!")

    def save_matches_to_csv(self, filepath: str = "matches.csv") -> None:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', newline='') as f:
            fieldnames = ["match_id", "round_number", "player_white_id", "player_black_id", "result", "is_bye_match", "is_half_bye_match"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for round_num in sorted(self.match_manager.rounds_matches.keys()):
                for match in self.match_manager.rounds_matches[round_num]:
                    writer.writerow(match.to_dict())
        print(f"{TournamentUtils.now()} | Matches saved to {filepath}!")

    def load_matches_from_csv(self, filepath: str = "matches.csv") -> None:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"{TournamentUtils.now()} | No match data file '{filepath}' found. No matches loaded.")
            self.match_manager.rounds_matches = {}
            return

        players_by_id = {p.id: p for p in self.player_manager.get_all_players()}
        self.match_manager.rounds_matches = {}
        
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    match = Match.from_dict(row, players_by_id)
                    self.match_manager.rounds_matches.setdefault(match.round_number, []).append(match)
                except (KeyError, ValueError, TypeError) as e:
                    print(f"{TournamentUtils.now()} | Error loading match from row {row}: {e}. Skipping match.")
        print(f"{TournamentUtils.now()} | Matches loaded from {filepath}!")

    def save_tournament_meta(self, current_round: int, num_rounds: int, next_player_id: int, 
                           next_match_id: int, filepath: str = "tournament_meta.csv") -> None:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', newline='') as f:
            fieldnames = ["current_round", "num_rounds", "next_player_id", "next_match_id_in_round_counter"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                "current_round": current_round,
                "num_rounds": num_rounds,
                "next_player_id": next_player_id,
                "next_match_id_in_round_counter": next_match_id
            })
        print(f"{TournamentUtils.now()} | Tournament metadata saved to {filepath}!")

    def load_tournament_meta(self, filepath: str = "tournament_meta.csv") -> Optional[Dict]:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"{TournamentUtils.now()} | No metadata file '{filepath}' found.")
            return None

        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            try:
                meta_data = next(reader)
                return {
                    "current_round": int(meta_data.get("current_round", 0)),
                    "num_rounds": int(meta_data.get("num_rounds", 5)),
                    "next_player_id": int(meta_data.get("next_player_id", 1)),
                    "next_match_id_in_round_counter": int(meta_data.get("next_match_id_in_round_counter", 1))
                }
            except (StopIteration, KeyError, ValueError) as e:
                print(f"{TournamentUtils.now()} | Error loading metadata from {filepath}: {e}.")
                return None


# --- Display Manager ---
class DisplayManager:
    """Handles all display and export operations."""
    
    def __init__(self, player_manager: PlayerManager, match_manager: MatchManager):
        self.player_manager = player_manager
        self.match_manager = match_manager

    def print_players_with_elo(self, bottom: Optional[int] = 1,  top: Optional[int] | None = None) -> None:
        self.player_manager.update_standings()
        print(f"\n--- {TournamentUtils.now()} | All PLayers info ---")
        # Filter out BYE_OPPONENT and then apply 'top' limit
        display_players = [p for p in self.player_manager.players if not (p.id == 0 and p.name_surname == "BYE_OPPONENT")]

        if top is None:
            top = len(display_players)

        for player in display_players:
            if player.id < bottom:
                continue
            if player.id > top:
                break            
            print(player.player_and_elo())
        print("-" * 80)

    def print_standings(self, current_round: int, num_rounds: int, top: Optional[int] = None) -> None:
        self.player_manager.update_standings()
        print(f"\n--- {TournamentUtils.now()} | Current Standings (Round {current_round} / {num_rounds}) ---")
        print(f"{'Rank':<5} {'Player Name':<20} {'ELO':<6} {'Points':<7} {'Bye':<5} {'Present':<7} {'Color Bal.':<10}")
        print("-" * 80)
        rank = 1
        # Filter out BYE_OPPONENT and then apply 'top' limit
        display_players = [p for p in self.player_manager.players if not (p.id == 0 and p.name_surname == "BYE_OPPONENT")]
        
        if top is None:
            top = len(display_players)

        for player in display_players:
            if rank > top:
                break
            bye_status = "No"
            if player.had_regular_bye:
                bye_status = "Reg"
            if player.has_bye_this_round: # This indicates a bye for the current round (could be half or regular)
                bye_status = "Half" if not player.had_regular_bye else "Reg" # Refine if it's a half or regular bye for display
            
            present_status = "Yes" if player.is_present else "No"
            print(f"{rank:<5} {player.name_surname:<20} {player.elo:<6} {player.points:<7.1f} {bye_status:<5} {present_status:<7} {player.color_balance_counter:<10}")
            rank += 1
        print("-" * 80)

    def print_pairings(self, round_number: int) -> None:
        matches_to_print = self.match_manager.get_matches_for_round(round_number)
        if not matches_to_print:
            print(f"{TournamentUtils.now()} | No pairings found for Round {round_number}.")
            return
        
        print(f"\n--- {TournamentUtils.now()} | Pairings for Round {round_number} ---")
        for match in matches_to_print:
            print(match)
        print("-" * 30)

    def export_standings_to_txt(self, current_round: int, num_rounds: int, filepath: str = "standings.txt") -> None:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        self.player_manager.update_standings()

        with open(filepath, "w") as file:
            file.write(f"--- {TournamentUtils.now()} | Current Standings (Round {current_round} / {num_rounds}) ---\n")
            file.write(f"{'Rank':<5} {'Player Name':<25} {'ELO':<6} {'Points':<7} {'Bye':<5} {'Present':<8} {'Color Bal.':<10}\n")
            file.write("-" * 80 + "\n")
            rank = 1
            display_players = [p for p in self.player_manager.players if not (p.id == 0 and p.name_surname == "BYE_OPPONENT")]
            for player in display_players:
                bye_status = "No"
                if player.had_regular_bye:
                    bye_status = "Reg"
                if player.has_bye_this_round:
                    bye_status = "Half" if not player.had_regular_bye else "Reg"
                present_status = "Yes" if player.is_present else "No"
                file.write(f"{rank:<5} {player.name_surname:<25} {player.elo:<6} {player.points:<7.1f} {bye_status:<5} {present_status:<8} {player.color_balance_counter:<10}\n")
                rank += 1
            file.write("-" * 80 + "\n")
        print(f"{TournamentUtils.now()} | Standings exported to {filepath}!")

    def export_standings_to_csv(self, filepath: str = "standings.csv") -> None:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        self.player_manager.update_standings()
        
        with open(filepath, "w", newline='') as file:
            fieldnames = ["Rank", "Player Name", "ELO", "Points", "Had Regular Bye", "Had Half Bye This Round", "Is Present", "Color Balance Counter"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            rank = 1
            display_players = [p for p in self.player_manager.players if not (p.id == 0 and p.name_surname == "BYE_OPPONENT")]
            for player in display_players:
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
        print(f"{TournamentUtils.now()} | Standings exported to {filepath}!")

    def export_pairings_to_txt(self, round_number: int, filepath: str = "pairings.txt") -> None:
        matches_to_export = self.match_manager.get_matches_for_round(round_number)
        if not matches_to_export:
            print(f"{TournamentUtils.now()} | No pairings found for Round {round_number} to export.")
            return

        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, "w") as file:
            file.write(f"--- {TournamentUtils.now()} | Tournament Pairings for Round {round_number} ---\n")
            for match in matches_to_export:
                file.write(str(match) + "\n")
            file.write("-" * 40 + "\n")
        print(f"{TournamentUtils.now()} | Pairings for Round {round_number} exported to {filepath}!")


# --- Tournament (Main Controller) ---
class Tournament:
    """Main controller that coordinates all tournament operations."""
    
    def __init__(self, num_rounds: int = 5):
        if not isinstance(num_rounds, int) or num_rounds <= 0:
            raise ValueError("Number of rounds must be a positive integer.")
        
        self.current_round = 0
        self.num_rounds = num_rounds
        
        # Initialize all managers
        self.player_manager = PlayerManager()
        self.pairing_engine = PairingEngine(self.player_manager)
        self.match_manager = MatchManager(self.player_manager, self.pairing_engine)
        self.result_tracker = ResultTracker(self.match_manager, self.player_manager)
        self.file_manager = FileManager(self.player_manager, self.match_manager)
        self.display_manager = DisplayManager(self.player_manager, self.match_manager)

    # Delegate methods to appropriate managers
    def add_player(self, name_surname: str, elo: int, id: int = -1) -> None:
        self.player_manager.add_player(name_surname, elo, id)

    def get_player_by_name(self, name_surname: str) -> Optional[Player]:
        return self.player_manager.get_player_by_name(name_surname)
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        return self.player_manager.get_player_by_id(player_id)
    
    def toggle_player_presence(self, player_id: int) -> str:
        return self.player_manager.toggle_player_presence(player_id)

    def pair_round_random(self, round_number: int, players_for_pairing: List[Player]) -> List[Match]:
        print(f"\n{TournamentUtils.long_line()}")
        print(f"{TournamentUtils.now()} | Pairing Round {round_number} using RANDOM SYSTEM")
        random.shuffle(players_for_pairing)
        for i in range(0, len(players_for_pairing), 2):
            player1 = players_for_pairing[i]
            player2 = players_for_pairing[i+1]
            self.match_manager.create_match(player1, player2, round_number)
        return self.match_manager.get_matches_for_round(round_number)

    def pair_round_by_elo(self, round_number: int, players_for_pairing: List[Player]) -> List[Match]:
        print(f"\n{TournamentUtils.long_line()}")
        print(f"{TournamentUtils.now()} | Pairing Round {round_number} BY ELO")
        players_for_pairing.sort(key=lambda p: p.elo)
        for i in range(0, len(players_for_pairing), 2):
            player1 = players_for_pairing[i]
            player2 = players_for_pairing[i+1]
            if i % 4 == 0:
                self.match_manager.create_match(player1, player2, round_number)
            else:
                self.match_manager.create_match(player2, player1, round_number)
        return self.match_manager.get_matches_for_round(round_number)

    def pair_round_matrix(self, round_number: int, players_for_pairing: List[Player], matrix_engine: PairingEngine | None = None) -> List[Match]:
        print(f"\n{TournamentUtils.long_line()}")
        print(f"{TournamentUtils.now()} | Pairing Round {round_number} using MATRIX SYSTEM")
        players_for_pairing.sort(key=lambda p: (p.points, p.elo), reverse=True)
        if matrix_engine is None:
            matrix_engine = self.match_manager.pairing_engine

        optimal_pairing_result = matrix_engine.find_optimal_pairing(players_for_pairing)
        
        matches: list[Match] = []
        if optimal_pairing_result:
            optimal_pairing_result = optimal_pairing_result[0]
            for p1, p2 in optimal_pairing_result:
                p1, p2 = matrix_engine.assign_colors_to_pair(p1, p2)
                matches.append(self.match_manager.create_match(p1, p2, round_number))
        
        return matches

    def pair_round(self, pairing_system: str) -> List[Match]:
        if self.current_round >= self.num_rounds:
            print(f"{TournamentUtils.now()} | Tournament has reached its maximum rounds ({self.num_rounds}). Cannot pair new round.")
            return []

        self.current_round += 1
        self.match_manager.reset_match_id_counter()

        print(f"\n{TournamentUtils.long_line()}")
        print(f"{TournamentUtils.now()} | Pairing Round {self.current_round} / {self.num_rounds} using {pairing_system.upper()} system.")

        # Reset has_bye_this_round for all players at the start of a new round
        for p in self.player_manager.get_all_players():
            p.has_bye_this_round = False

        active_players = self.player_manager.get_active_players()
        if len(active_players) < 2:
            print(f"{TournamentUtils.now()} | Not enough active players ({len(active_players)}) to pair a round.")
            return []

        # Handle bye assignment for the round
        bye_player, players_for_pairing = self.match_manager.handle_bye_assignment(active_players, self.current_round)
        
        if len(players_for_pairing) % 2 != 0:
            raise RuntimeError(f"Internal error: Odd number of players ({len(players_for_pairing)}) remaining after bye assignment for pairing.")
        
        if not players_for_pairing:
            print(f"{TournamentUtils.now()} | No players left to pair after bye assignment.")
            return self.match_manager.get_matches_for_round(self.current_round)

        # Perform Pairing based on System
        match(pairing_system.lower()):
            case "random":
                return self.pair_round_random(self.current_round, players_for_pairing)
            case "by elo":
                return self.pair_round_by_elo(self.current_round, players_for_pairing)
            case "matrix":
                return self.pair_round_matrix(self.current_round, players_for_pairing)
            # case "ducth" - we don't use no more
            case _:
                raise ValueError(f"Invalid pairing system: {pairing_system}")

    def enter_result(self, match_id: int, result: str, round_num: Optional[int] = None) -> None:
        if round_num is None:
            self.result_tracker.enter_result(match_id, result, self.current_round)
        self.result_tracker.enter_result(match_id, result, round_num)

    def end_round(self) -> None:
        print(f"\n{TournamentUtils.long_line()}")
        print(f"{TournamentUtils.now()} | Ending Round {self.current_round} / {self.num_rounds}")

        self.result_tracker.update_players_results(self.match_manager.get_matches_for_round(self.current_round))
        
        self.player_manager.update_standings()
        print(f"{TournamentUtils.now()} | Round {self.current_round} / {self.num_rounds} ended.")
        print(TournamentUtils.long_line())

    def get_final_standings(self, top: Optional[int] = None)-> list[Player]:
        return self.player_manager.get_final_standings(top)

    def end_tournament(self, top: Optional[int] = None) -> None:
        self.get_final_standings(top)
        print(f"{TournamentUtils.now()} | Tournament ended. Standings exported to 'standings.txt' and 'standings.csv'")
        
    # Display methods
    def print_standings(self, top: Optional[int] = None) -> None: # Changed default top to None
        self.display_manager.print_standings(self.current_round, self.num_rounds, top)

    def print_pairings(self, round_number: Optional[int] = None) -> None:
        if round_number is None:
            round_number = self.current_round
        self.display_manager.print_pairings(round_number)

    # Export methods
    def export_standings_to_txt(self, filepath: str = "standings.txt", final: bool = False) -> None:
        if final:
            self.player_manager.players = self.player_manager.get_final_standings()
        self.display_manager.export_standings_to_txt(self.current_round, self.num_rounds, filepath)

    def export_standings_to_csv(self, filepath: str = "standings.csv", final: bool = False) -> None:
        if final:
            self.player_manager.players = self.player_manager.get_final_standings()
        self.display_manager.export_standings_to_csv(filepath)

    def export_pairings_to_txt(self, filepath: str = "pairings.txt", round_number: Optional[int] = None) -> None:
        if round_number is None:
            round_number = self.current_round
        self.display_manager.export_pairings_to_txt(round_number, filepath)

    # File I/O methods
    def save_players_to_csv(self, filepath: str = "players.csv") -> None:
        self.file_manager.save_players_to_csv(filepath)

    def load_players_from_csv(self, filepath: str = "registered_players.csv", clear_players: bool = True) -> None:
        self.file_manager.load_players_from_csv(filepath, clear_players)

    def save_tournament_state(self, players_filepath: str = "players_state.csv", 
                            matches_filepath: str = "matches.csv", 
                            meta_filepath: str = "tournament_meta.csv") -> None:
        self.player_manager.players = self.player_manager.get_final_standings()
        self.file_manager.save_players_to_csv(players_filepath)
        self.file_manager.save_matches_to_csv(matches_filepath)
        self.file_manager.save_tournament_meta(
            self.current_round, self.num_rounds, 
            self.player_manager.next_player_id, 
            self.match_manager.next_match_id_in_round, 
            meta_filepath
        )

    def load_tournament_state(self, players_filepath: str = "players_state.csv", 
                            matches_filepath: str = "matches.csv", 
                            meta_filepath: str = "tournament_meta.csv") -> None:
        # Load metadata first
        meta_data = self.file_manager.load_tournament_meta(meta_filepath)
        if meta_data:
            self.current_round = meta_data["current_round"]
            self.num_rounds = meta_data["num_rounds"]
            self.player_manager.next_player_id = meta_data["next_player_id"]
            self.match_manager.next_match_id_in_round = meta_data["next_match_id_in_round_counter"]
            print(f"{TournamentUtils.now()} | Metadata loaded!")
        else:
            print(f"{TournamentUtils.now()} | Using default tournament settings.")

        # Load players and matches
        self.file_manager.load_players_from_csv(players_filepath)
        self.file_manager.load_matches_from_csv(matches_filepath)
        print(f"{TournamentUtils.now()} | Tournament state fully loaded!")

    # Utility properties for backward compatibility
    
    @property
    def players(self) -> List[Player]:
        return self.player_manager.get_all_players()

    @property
    def current_matches(self) -> List[Match]:
        # This property should reflect the matches for the current round
        return self.match_manager.get_matches_for_round(self.current_round)

    @property
    def rounds_matches(self) -> Dict[int, List[Match]]:
        return self.match_manager.rounds_matches