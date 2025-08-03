# Chess Tournament

A robust and feature-rich Python-based console application designed to manage Swiss-style chess tournaments. It automates complex pairing generation, handles various bye scenarios, balances colors, and maintains comprehensive tournament standings and history.

## Features

* **Player Management:**

    * Add new players with unique IDs, names, and ELO ratings.

    * Names are automatically encoded to a maximum length of 20 characters (truncating and adding "..." if longer, or using initials for first names).

    * Players can be marked as present or absent for specific rounds.

    * Player data is persisted to and loaded from CSV files.

* **Pairing Systems:**

    * **Random Pairing:** Simple randomized pairings, typically used for the first round.
    * **Pairing by ELO rating:** Simple  pairings based on ELO, typically used for the first round.

    * [**Dutch System**](https://www.wikiwand.com/en/articles/Swiss-system_tournament#Dutch_system) (implemented in `DutchTournament`)

    >### Fast Acknowledgement
    >The core pairing algorithm and concepts for this Chess Tournament were inspired by and adapted from the excellent video on Swiss Tournament Pairing Algorithms by Nice Micro in his [video](https://youtu.be/ijU8kL4hgIg?si=H0vN8dk4TArI67-b) on YouTube.
    Thank You, [@nicemicro](https://github.com/nicemicro/) ❤️

    * **Optimized Pairing Algorithm:** All complex pairing systems utilize a recursive "minimum badness" algorithm. This algorithm:

        * Calculates a badness matrix considering rematches, ELO differences, and system-specific penalties.

        * Employs aggressive pruning to efficiently search for the best possible pairing.

        * Can be configured with a `MATCH_ACCECPTABLE_BADNESS_LIMIT` to find a "good enough" pairing faster for larger tournaments, or set to `0.0` to always find the mathematically optimal pairing.

    ### Algorithmic Complexity (Big O Notation)

    * **Badness Matrix Calculation (`_calculate_badness_matrix`):**
        The time complexity for generating the badness matrix is **O(N^2 * R)**, where `N` is the number of players and `R` is the number of rounds played. This is because it iterates through all possible pairs of players (`N^2`) and for each pair, it might check their `past_opponents` list (which can grow up to `R` in length). In practice, as `R` is typically small and constant, this often behaves closer to **O(N^2)**.

    * **Pairing Algorithm (`_find_best_pairing_recursive`):**
        This algorithm performs a combinatorial search for the optimal pairing. In the theoretical worst-case, the number of possible pairings grows factorially, leading to a complexity of approximately **O(N! * N)**. However, the implementation uses aggressive **pruning** (alpha-beta pruning concept) and a `MATCH_ACCECPTABLE_BADNESS_LIMIT` heuristic. This significantly reduces the actual number of combinations explored, making it practically feasible for tournaments with up to **18-24 players**. For larger tournaments, different heuristic-based approaches would be required to achieve polynomial time complexity, but without guaranteeing absolute optimality.
    > Because of that in `DutchTournament` it used only for last players to avoid some bugs.

* **Sophisticated Bye Handling:**

    * **Regular Bye (1.0 point):** Awarded once to the lowest-point player who hasn't received a regular bye before.

    * **Half Bye (0.5 points):** Awarded to players who are marked as absent for a round, or as a fallback if no player is eligible for a regular bye.

* **Fair Color Balancing:**

    * Intelligent assignment of White/Black pieces based on a `color_balance_counter` that tracks past color assignments:+1 if white, -1 if black.
    * Prioritizes players who have a preference for a certain color (e.g., played more White, now prefers Black).

    * Further tie-breaking rules consider the fewer points and lower ELO.

* **Tournament State Persistence:**

    * Automatically saves and loads all tournament data (players, matches, metadata) to/from CSV files, allowing tournaments to be resumed.

* **Console User Interface:** An interactive command-line interface provides a guided experience for tournament management.

* **Detailed Logging:** Provides real-time updates, warnings, and logs of tournament events directly in the console.

## Project Structure
    |   ├── export/                     #   Directory for all generated output files
    |   ├── leaderboard/            #   Standings for each round
    │   │   ├── standings1.csv
    │   │   ├── standings1.txt
    │   │   ├── ...
    │   │   └── standingsN.txt
    │   ├── pairings/               #   Pairings for each round
    │   │   ├── final_pairings_round1.txt
    │   │   ├── ...
    │   │   └── final_pairings_roundN.txt
    │   ├── final_standings.csv     #   Final tournament standings in CSV
    │   ├── tournament_matches.csv  # All   match data saved cumulatively
    │   ├── tournament_meta.csv     #   Tournament metadata (current round,    etc.)
    │   └── tournament_players.csv  # All   player data saved cumulatively
    ├── import/                     #   Directory for input files
    │   └── chess_players.csv       #   Example CSV for pre-registered players
    ├── .gitignore                  #   Specifies intentionally untracked  files to ignore
    ├── chess_tournament.py         # Core  logic: Player, Match, PairingManager, Tournament classes
    ├── demonstration.py            #   Automated simulation script for    testing (non-interactive)
    ├── main.py                     #   Interactive console application script
    ├── LICENSE.md                  #   License file
    └── README.md                   # This  file (you are reading it!)

## Getting Started

### Prerequisites

* Python 3.8+

* `pandas` library (for badness matrix calculations)

### Installation

1.  **Clone the repository:**

    ```
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd YOUR_REPOSITORY_NAME

    ```

    *(Replace `YOUR_USERNAME` and `YOUR_REPOSITORY_NAME` with your actual GitHub details)*

2.  **Install dependencies:**

    ```
    pip install pandas

    ```

### How to Run

There are two ways to run the project:

1.  **Interactive Console Application (Recommended for actual use):**

    ```
    python main.py

    ```

    This will start the interactive tournament manager.

2.  **Automated Demonstration (for testing/simulation):**

    ```
    python demonstration.py

    ```

    This script will run a pre-defined 10-round tournament simulation with random results and specific player absences. It's useful for quickly seeing the system in action and generating example output files.

## Usage (Interactive `main.py`)

When you run `main.py`, you will be prompted to:

1.  **Set the number of rounds** for your tournament.

2.  The system will attempt to **load players from `import/chess_players.csv`**.

3.  You can then **add additional players** manually (as defined in the `players` dictionary in `main.py`).

4.  The tournament will proceed round by round, pairing players using the following methods:

    * **Round 1:** Uses **Random Pairing**.

    * **Rounds 2 onwards (up to your specified `num_rounds`):** Use **Dutch System Pairing**.

5.  For each match in a round, you will be prompted to **enter results** interactively:

    * `0` for a Draw (`0.5-0.5`)

    * `1` for White wins (`1-0`)

    * `2` for Black wins (`0-1`)

6.  After each round, standings will be updated and exported to `export/leaderboard/standingsX.csv` and `export/leaderboard/standingsX.txt`.

7.  At the end of the tournament, final standings will be exported to `export/final_standings.csv`, and pairings for each round will be exported to `export/pairings/final_pairings_roundX.txt`.

8.  The full tournament state is saved to CSV files in the `export/` directory, allowing you to manually resume a tournament by loading these files.

### Configuration & Customization

You can fine-tune the pairing algorithm and player behavior by modifying constants in `chess_tournament.py` (specifically within the `PairingManager` class):

* `PairingManager.REMATCH_PENALTY`: Adjust the penalty for players who have faced each other before. A higher value makes rematches less likely.

* `PairingManager.ELO_DIFF_DIVISOR`: Controls how much ELO differences influence badness (higher divisor means less influence).

* `PairingManager.SAME_HALF_PENALTY`: For Dutch system, adjusts the penalty for pairing players from the same score half (top-top or bottom-bottom).

* `PairingManager.MATCH_BADNESS_LIMIT`: A threshold for the badness of a single match. If a potential pair exceeds this, it's considered unacceptable.

* `PairingManager.MATCH_ACCECPTABLE_BADNESS_LIMIT`: A heuristic. If the total badness of a complete pairing falls below this value, the algorithm stops searching and returns that pairing. Set to `0.0` to always find the mathematically optimal pairing.

* `Player.name_surname_encoder`: Controls how player names are truncated for display.

* `Player.from_dict`: Handles robust loading of boolean values (e.g., `"True"`/`"False"` strings from CSV).

## Ideas for the new update
* Creating different child Objects for Tournament: Robin Tournament, Single or More Elimination; pure Dutch Swiss.


## Contributing

Contributions are highly encouraged! If you have ideas for new features, improvements to existing algorithms, or bug fixes, please follow these steps:

1.  Fork the repository.

2.  Create a new branch for your feature or fix:

    ```
    git checkout -b feature/your-feature-name

    ```

3.  Make your changes and ensure tests (or the `demonstration.py` script) pass.

4.  Commit your changes with a clear and concise message:

    ```
    git commit -m 'feat: Add new feature X'

    ```

    or

    ```
    git commit -m 'fix: Resolve bug Y'

    ```

5.  Push your branch to your forked repository:

    ```
    git push origin feature/your-feature-name

    ```

6.  Open a Pull Request to the `main` branch of the original repository.

## License

>This project is licensed under the MIT License. See the `LICENSE.md` file for details.