from typing import List, Dict, Tuple, Optional, Set
import random
from collections import defaultdict
from chess_tournament import *


class ScoreGroup:
    """Represents a group of players with the same score."""
    
    def __init__(self, score: float, players: List[Player]):
        self.score = score
        self.players = players.copy()
        self.unpaired_players = players.copy()
        
    def __len__(self) -> int:
        return len(self.unpaired_players)
    
    def __str__(self) -> str:
        return f"Score {self.score}: {len(self.players)} players ({len(self.unpaired_players)} unpaired)"
    
    def __repr__(self) -> str:
        return f"<ScoreGroup {self.score}: {[p.name_surname for p in self.players]}>"
    
    def sort_players(self) -> None:
        """Sort players within the score group by rating (descending), then by color preference."""
        self.players.sort(key=lambda p: (-p.elo, p.color_balance_counter))
        self.unpaired_players.sort(key=lambda p: (-p.elo, p.color_balance_counter))
    
    def remove_player(self, player: Player) -> None:
        """Remove a player from the unpaired list."""
        # Ensure player is in the list before trying to remove to prevent ValueError
        if player in self.unpaired_players:
            self.unpaired_players.remove(player)
    
    def get_top_half(self) -> List[Player]:
        """Get the top half of unpaired players."""
        mid = len(self.unpaired_players) // 2
        return self.unpaired_players[:mid]
    
    def get_bottom_half(self) -> List[Player]:
        """Get the bottom half of unpaired players."""
        mid = len(self.unpaired_players) // 2
        return self.unpaired_players[mid:]
    
    def can_pair_internally(self) -> bool:
        """Check if this score group has enough players to pair internally."""
        return len(self.unpaired_players) >= 2


class DutchPairingEngine:
    """Specialized pairing engine for Dutch tournament system with proper score groups."""
    
    def __init__(self, player_manager: PlayerManager):
        self.player_manager = player_manager
        self.matrix_engine = PairingEngine(player_manager)
        self.score_groups: List[ScoreGroup] = []
        
    
    def create_score_groups(self, players: List[List[Player]]) -> None:
        """Create score groups from a list of players and assign it to the object."""
        players.sort(key=lambda p: p.points, reverse=True)
        score_dict = defaultdict(list)
        for player in players:
            score_dict[player.points].append(player)

        self.score_groups = []
        for score, players_list in score_dict.items():
            score_group = ScoreGroup(score, players_list)
            self.score_groups.append(score_group)
        return
    
    def _find_opponent_in_candidates(self, player: Player, candidates: List[Player]) -> Optional[Player]:
        """
        Helper to find the best opponent for a player from a list of candidates.
        Prioritizes non-rematches, then color balance, then ELO.
        """
        # 1. Prioritize non-rematch opponents
        non_rematch_candidates = [p for p in candidates if p.id not in player.past_opponents]


        
        if non_rematch_candidates:
            # If no opposite color, take any non-rematch (prefer similar rating)
            non_rematch_candidates.sort(key=lambda p: (player.color_balance_counter * p.color_balance_counter >= 0, abs(p.elo - player.elo)))
            return non_rematch_candidates[0]
        
        # 2. Fallback: If no non-rematch opponents, consider rematches
        """rematch_candidates = [p for p in candidates if p.id in player.past_opponents]
        if rematch_candidates:
            print(f"{TournamentUtils.now()} | Warning: For {player.name_surname}, considering rematch.")
            # Prefer opposite color balance among rematch candidates
            opposite_color_rematches = [p for p in rematch_candidates 
                                        if p.color_balance_counter * player.color_balance_counter <= 0]
            if opposite_color_rematches:
                opposite_color_rematches.sort(key=lambda p: abs(p.elo - player.elo))
                return opposite_color_rematches[0]
            
            # If no opposite color, take any rematch (prefer similar rating)
            rematch_candidates.sort(key=lambda p: abs(p.elo - player.elo))
            return rematch_candidates[0]"""
            
        return None # No valid opponent found, even with rematch
    
    def pair_within_score_group(self, score_group: ScoreGroup) -> List[Tuple[Player, Player]]:
        """Pair players within a single score group using Dutch system rules."""
        pairs = []
        
        # Make a copy of unpaired players to iterate over, as the original list will be modified
        unpaired_players = score_group.unpaired_players
        
        for player1 in unpaired_players:
            if player1 not in score_group.unpaired_players: # Skip if already paired in this loop
                continue

            # Candidates are all other unpaired players in the group
            candidates = [p for p in score_group.unpaired_players if p != player1]
            if not candidates:
                continue # No one left to pair with in this group

            opponent = self._find_opponent_in_candidates(player1, candidates)
            
            if opponent:
                pairs.append((player1, opponent))
                score_group.remove_player(player1)
                score_group.remove_player(opponent)
                print(f"{TournamentUtils.now()} | Paired within score group {score_group.score}: {player1.name_surname} vs {opponent.name_surname}")
            else:
                print(f"{TournamentUtils.now()} | Could not pair {player1.name_surname} within score group {score_group.score}. Will attempt cross-group pairing.")
        
        return pairs

    def assign_colors_to_pair(self, p1: Player, p2: Player) -> Tuple[Player, Player]:
        """Assign colors based on color balance preference, points, and rating."""
        # Rule 1: Color Preference (color_balance_counter)
        # Prefer the player who has played more with black (lower counter) to get white
        if p1.color_balance_counter < p2.color_balance_counter:
            return p1, p2  # p1 gets white (needs white more)
        if p2.color_balance_counter < p1.color_balance_counter:
            return p2, p1  # p2 gets white (needs white more)

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


class DutchMatchManager(MatchManager):
    """Match manager specifically for Dutch tournament system."""
    
    def __init__(self, player_manager: PlayerManager):
        # Pass a dummy PairingEngine to the base MatchManager __init__
        # The DutchPairingEngine is used directly by DutchMatchManager methods for pairing logic
        super().__init__(player_manager, PairingEngine(player_manager))
        self.old_pairing_engine = PairingEngine(player_manager)
        self.pairing_engine = DutchPairingEngine(player_manager) # Override with Dutch specific engine


class DutchTournament(Tournament):
    """Dutch tournament system with proper score group pairing."""
    
    def __init__(self, num_rounds: int = 5):
        super().__init__(num_rounds)
        
        # Replace the match manager with Dutch-specific one
        self.match_manager = DutchMatchManager(self.player_manager)
        self.result_tracker = ResultTracker(self.match_manager, self.player_manager)
        # Re-initialize file_manager and display_manager with the new match_manager
        self.file_manager = FileManager(self.player_manager, self.match_manager)
        self.display_manager = DisplayManager(self.player_manager, self.match_manager)
        
        print(f"{TournamentUtils.now()} | Dutch Tournament System initialized with {num_rounds} rounds")
    

    def pair_round_dutch(self, round_number: int, players_for_pairing: List[Player] ) -> List[Match]:
        """Pair a round using proper Dutch system with score groups."""
        
        print(f"\n{TournamentUtils.long_line()}")
        print(f"{TournamentUtils.now()} | Pairing Round {round_number} using DUTCH SYSTEM with Score Groups")

        
        # For small amount of players use uneficient old matrix pairing to prevent some bugs
        if len(players_for_pairing) < 10:
            return self.pair_round_matrix(round_number, players_for_pairing, self.match_manager.old_pairing_engine)
        
        # Create score groups from the remaining players
        self.match_manager.pairing_engine.create_score_groups(players_for_pairing)
        score_groups = self.match_manager.pairing_engine.score_groups
        
        print(f"{TournamentUtils.now()} | Created {len(score_groups)} score groups:")
        for group in score_groups:
            print(f"  {group}")
        
        # Phase 1: Pair within score groups
        all_pairs = []
        for i, group in enumerate(score_groups):
            if i > 0:
                group.unpaired_players.extend(score_groups[i-1].unpaired_players)
            if (len(self.players) // 2) - len(all_pairs)  < self.current_round:
                # for last gruop we will use matrix algorithm to prevent some bugs
                if len(group.unpaired_players) < self.current_round * 2 and len(group.unpaired_players) < 15:
                    break
            if group.can_pair_internally():
                pairs = self.match_manager.pairing_engine.pair_within_score_group(group)
                all_pairs.extend(pairs)
        
        # Phase 2: Create matches with proper color assignment (for Dutch system)
        paired_player_ids = set()
        for p1, p2 in all_pairs:
            white_player, black_player = self.match_manager.pairing_engine.assign_colors_to_pair(p1, p2)
            self.match_manager.create_match(white_player, black_player, round_number)
            paired_player_ids.add(p1.id)
            paired_player_ids.add(p2.id)
        
        # Phase 3: Pair unpaired players using matrix algorithm (assigning colors embled)
        unpaired_after_dutch_logic = [p for p in players_for_pairing if p.id not in paired_player_ids and not p.has_bye_this_round]
        if unpaired_after_dutch_logic:
            print(f"{TournamentUtils.now()} | Pairing unpaired players using matrix algorithm")
            if len(unpaired_after_dutch_logic) > 20:
                n = len(unpaired_after_dutch_logic) // 10
                for i in range(n):
                    l = 11 if len(unpaired_after_dutch_logic) < 11 else len(unpaired_after_dutch_logic) 
                    generated_matches: list[Match] = self.pair_round_matrix(round_number, players_for_pairing[:l], self.match_manager.old_pairing_engine)
                    if generated_matches is not None:
                        for match in generated_matches:
                            unpaired_after_dutch_logic.remove(match.player_black)
                            unpaired_after_dutch_logic.remove(match.player_white)
                            paired_player_ids.add(match.player_black.id)
                            paired_player_ids.add(match.player_white.id)
            else:
                generated_matches: list[Match] = self.pair_round_matrix(round_number, unpaired_after_dutch_logic, self.match_manager.old_pairing_engine)
                for match in generated_matches:
                    paired_player_ids.add(match.player_black.id)
                    paired_player_ids.add(match.player_white.id)

        # Phase 4: Create bye matches for unpaired players
        unpaired_after_dutch_logic = [p for p in players_for_pairing if p.id not in paired_player_ids and not p.has_bye_this_round]
    
        for p in unpaired_after_dutch_logic:
            p.add_points(0.5)
            self.match_manager.create_match(p, None, round_number, is_half_bye=True)
        
        print(f"{TournamentUtils.now()} | Dutch pairing complete: {len(self.match_manager.get_matches_for_round(round_number))} matches created")
        return self.match_manager.get_matches_for_round(round_number) # Return matches directly from rounds_matches
    
    def pair_round(self, pairing_system: str = "dutch", desired_pairs: Tuple[int, int] = ()) -> List[Match]:
        if self.current_round >= self.num_rounds:
            print(f"{TournamentUtils.now()} | Tournament has reached its maximum rounds ({self.num_rounds}). Cannot pair new round.")
            return []

        self.current_round += 1
        self.match_manager.reset_match_id_counter()

        # Reset has_bye_this_round for all players at the start of a new round
        for p in self.player_manager.get_all_players():
            p.has_bye_this_round = False

        all_players = self.player_manager.get_all_players()

        if len(all_players) < 2:
            print(f"{TournamentUtils.now()} | Not enough active players ({len(all_players)}) to pair a round.")
            return []

        # Desired pairs
        for white_id, black_id in desired_pairs:
            if black_id == 0:
                white_player = self.player_manager.get_player_by_id(white_id)
                print(f"{TournamentUtils.now()} | Adding desired bye: {white_player}")
                self.match_manager.create_match(white_player, None, self.current_round)
                all_players.remove(white_player)
            else:
                white_player = self.player_manager.get_player_by_id(white_id)
                black_player = self.player_manager.get_player_by_id(black_id)
                print(f"{TournamentUtils.now()} | Adding desired pair: {white_player} vs {black_player}")
                self.match_manager.create_match(white_player, black_player, self.current_round)
                all_players.remove(white_player)
                all_players.remove(black_player)

        # Handle bye assignment for the round
        bye_player, players_for_pairing = self.match_manager.handle_bye_assignment(all_players, self.current_round)
        
        if len(players_for_pairing) % 2 != 0:
            raise RuntimeError(f"Internal error: Odd number of players ({len(players_for_pairing)}) remaining after bye assignment for pairing.")
        
        if not players_for_pairing:
            print(f"{TournamentUtils.now()} | No players left to pair after bye assignment.")
            return self.match_manager.get_matches_for_round(self.current_round)

        created_matches = self.current_matches.copy()
        # Perform Pairing based on System
        match(pairing_system.lower()):
            case "random":
                return created_matches + self.pair_round_random(self.current_round, players_for_pairing) 
            case "by elo":
                return created_matches + self.pair_round_by_elo(self.current_round, players_for_pairing)
            case "dutch":
                return created_matches + self.pair_round_dutch(self.current_round, players_for_pairing)
            case _:
                raise ValueError(f"Invalid pairing system: {pairing_system}")
    
    def print_score_groups(self) -> None:
        """Print current score groups for analysis."""
        all_players = self.player_manager.get_all_players()
        if not all_players:
            print(f"{TournamentUtils.now()} | No active players to display.")
            return
        
        self.match_manager.pairing_engine.create_score_groups(all_players)
        score_groups = self.match_manager.pairing_engine.score_groups
        
        print(f"\n--- {TournamentUtils.now()} | Current Score Groups (Round {self.current_round}) ---")
        for i, group in enumerate(score_groups, 1):
            print(f"\nScore Group {i} - {group.score} points:")
            print(f"{'Rank':<4} {'Player Name':<20} {'ELO':<6} {'Color Bal.':<10}")
            print("-" * 45)
            for j, player in enumerate(group.players, 1):
                print(f"{j:<4} {player.name_surname:<20} {player.elo:<6} {player.color_balance_counter:<10}")
        print("-" * 50)