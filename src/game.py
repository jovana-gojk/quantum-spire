import random
import os
import copy
from quantum import build_circuit, check_bell, check_deutsch_jozsa, check_ghz, get_exact_probabilities, run_circuit


# Game constants
STARTING_HEALTH = 30
STARTING_ENERGY = 3
STARTING_QUBITS = 1
STARTING_BLOCK = 0

MAX_QUBITS = 4

STARTING_FLOOR = 1
EVENT_FLOORS = {
    3: "Spin Lab",
    7: "Superconducting Lab",
    9: "Photonics Lab",
}

FLOORS = {
    # Floor 1: Basic one-qubit shields
    1: [
        {"name": "The Bitwarden", "health": 20, "state_shield": "1", "damage": 5},
        {"name": "Basis Zero", "health": 16, "state_shield": "0", "damage": 4},
        {"name": "Flip-Flops", "health": 24, "state_shield": "1", "damage": 5},
    ],

    # Floor 2: Stronger one-qubit shields
    2: [
        {"name": "Schrodinger's Cat", "health": 26, "state_shield": "0", "damage": 6},
        {"name": "Heisenberg's Uncertainty", "health": 22, "state_shield": "1", "damage": 7},
        {"name": "Spin Up", "health": 30, "state_shield": "0", "damage": 6},
    ],

    # Floor 4: Introduce two-qubit shields and Bell states
    4: [
        {"name": "The Ground State", "health": 34, "state_shield": "00", "damage": 7},
        {"name": "Decoherer", "health": 30, "state_shield": "10", "damage": 8},
        {"name": "Alice and Bob", "health": 40, "state_shield": None, "damage": 7, "shield_type": "bell", "gimmick": "phi_plus"},
    ],

    # Floor 5: More two-qubit shields and a different Bell state
    5: [
        {"name": "The Pauli Exclusion", "health": 44, "state_shield": "11", "damage": 8},
        {"name": "Bell's Inequality", "health": 38, "state_shield": None, "damage": 9, "shield_type": "bell", "gimmick": "phi_minus"},
        {"name": "Interferess", "health": 35, "state_shield": "00", "damage": 10},
    ],

    # Floor 6: Final two-qubit encounters before the upgrade
    6: [
        {"name": "The Singlet", "health": 48, "state_shield": None, "damage": 9, "shield_type": "bell", "gimmick": "psi_plus"},
        {"name": "Broken Circuit", "health": 44, "state_shield": "10", "damage": 10},
        {"name": "The Phasebound", "health": 54, "state_shield": None, "damage": 9, "shield_type": "bell", "gimmick": "psi_minus"},
    ],

    # Floor 8: Three-qubit shields
    8: [
        {"name": "True Null", "health": 65, "state_shield": "000", "damage": 11},
        {"name": "Intro Class", "health": 72, "state_shield": "101", "damage": 12},
        {"name": "Dense Matrix", "health": 60, "state_shield": "110", "damage": 13},
    ],

    # Floor 10: Bosses with distinct quantum challenges
    10: [
        {"name": "Toffoli Tyrant", "health": 100, "state_shield": "111", "damage": 14, "shield_type": "toffoli"},
        {"name": "The Oracle", "health": 110, "state_shield": None, "damage": 16, "shield_type": "deutsch"},
        {"name": "Green Horned Zebra", "health": 125, "state_shield": None, "damage": 15, "shield_type": "ghz"},
    ],
}

def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")

class Card:
    def __init__(self, name, energy_cost):
        self.name = name
        self.energy_cost = energy_cost

class GateCard(Card):
    def __init__(self, name, energy_cost, gate):
        # Inherit from Card class
        super().__init__(name, energy_cost)
        self.gate = gate

class SkillCard(Card):
    def __init__(self, name, energy_cost, block=0, healing=0):
        # Inherit from Card class
        super().__init__(name, energy_cost)
        self.block = block
        self.healing = healing

class AttackCard(Card):
    def __init__(self, name, energy_cost, damage):
        # Inherit from Card class
        super().__init__(name, energy_cost)
        self.damage = damage

CARD_POOL = [
    # Gate cards
    GateCard("Hadamard", 1, "h"),
    GateCard("Pauli-X", 1, "x"),
    GateCard("Pauli-Z", 1, "z"),
    GateCard("Pauli-Y", 1, "y"),
    GateCard("CNOT", 1, "cx"),
    GateCard("CZ", 1, "cz"),
    GateCard("Toffoli", 1, "ccx"),
    # Skill cards
    SkillCard("Shield", 1, block=5),
    SkillCard("Heal", 2, healing=6),
    # Attack cards
    AttackCard("Attack", 1, damage=6),
    AttackCard("Little Strike", 0, damage=3)
]

STARTING_DECK = [
    GateCard("Hadamard", 1, "h"),
    GateCard("Hadamard", 1, "h"),
    GateCard("Pauli-X", 1, "x"),
    GateCard("Pauli-X", 1, "x"),
    SkillCard("Shield", 1, block=5),
    AttackCard("Attack", 1, damage=6),
    AttackCard("Attack", 1, damage=6)
]

class Player:
    def __init__(self):
        # Player standing
        self.health = STARTING_HEALTH
        self.max_health = STARTING_HEALTH
        self.block = STARTING_BLOCK
        self.energy = STARTING_ENERGY
        self.max_energy = STARTING_ENERGY
        self.qubits = STARTING_QUBITS

        self.deck = STARTING_DECK.copy()

    def health_change(self, hp_points):
        # Take damage or healing
        self.health += hp_points

        # Keep health within max
        self.health = min(self.health, self.max_health)
        self.health = max(self.health, 0)

    def play_cards(self, energy_cost):
        # Spend energy to play cards
        if energy_cost > self.energy:
            return False
        
        self.energy -= energy_cost
        return True

    def get_block(self, block):
        # Get amount of block listed by cards
        self.block += block

class Enemy:
    def __init__(self, name, health, state_shield, damage, shield_type=None, gimmick=None):
        self.name = name
        self.health = health
        self.max_health = health
        self.state_shield = state_shield
        self.shield_type = shield_type
        self.gimmick = gimmick
        self.shield_status = self.shield_type is not None or self.state_shield is not None
        self.damage = damage
        self.is_attacking = True

    def take_damage(self, amount):
        if not self.shield_status:
            self.health = max(0, self.health - amount)

    def do_damage(self, player):
        blocked = min(player.block, self.damage)
        player.block -= blocked

        over_damage = self.damage - blocked
        player.health = max(0, player.health - over_damage)
        return over_damage
    
    def next_phase(self):
        self.is_attacking = not self.is_attacking

class Game:
    def __init__(self, backend):
        self.backend = backend
        # Game state beginning
        self.floor = STARTING_FLOOR

        # Init the player in the game
        self.player = Player()

        # Turn counter
        self.turn = 0
        # Retain circuits over turns
        self.active_gates = []
        # Keep damage until end of turn
        self.pending_damage = 0

        # Deck stuff
        self.draw_pile = self.player.deck.copy()
        random.shuffle(self.draw_pile)
        self.discard_pile = []
        self.hand = []

        # Display stuff
        self.circuit_preview = None
        self.circuit_probabilities = {}

    def start_floor(self):
        # Reset for new floor
        self.active_gates = []
        self.circuit_preview = None
        self.circuit_probabilities = {}
        self.turn = 0
        print(f"Floor {self.floor} started!")

        # Get floor data if its event floor
        if self.floor in EVENT_FLOORS:
            self.enemy = None
            print(f"{EVENT_FLOORS[self.floor]}: gain a qubit, recover health, and add a card.")
            self.grant_floor_rewards()
            return False

        # Find enemy data and face against it
        enemy_data = random.choice(FLOORS[self.floor])
        self.enemy = Enemy(**enemy_data)
        return True

    def add_card(self, card):
        new_card = copy.deepcopy(card)
        self.player.deck.append(new_card)
        self.draw_pile.append(copy.deepcopy(new_card))
        random.shuffle(self.draw_pile)
        print(f"Added {new_card.name} to your deck.")

    def choose_card_reward(self, exclude=None):
        # Cards that can never appear as reward choices
        excluded_cards = [
            "Shield",
            "Attack",
            "Pauli-X",
            "Hadamard",
        ]

        # Add any floor-specific exclusions
        if exclude:
            excluded_cards.extend(exclude)

        cards = [card for card in CARD_POOL if card.name not in excluded_cards]
        # Choose 3 different options
        options = random.sample(cards, min(3, len(cards)))

        print("\nChoose a card to add to your deck:")
        for index, card in enumerate(options, start=1):
            print(f"{index}. {card.name} (Energy: {card.energy_cost})")

        while True:
            choice = input(f"Choose a card (1-{len(options)}): ").strip()

            if choice.isdigit() and 1 <= int(choice) <= len(options):
                selected_card = options[int(choice) - 1]
                self.add_card(selected_card)
                return

            print(f"Choose a number from 1 to {len(options)}.")

    def grant_floor_rewards(self):
        clear_terminal()
        print(f"Welcome to floor {self.floor}, the {EVENT_FLOORS[self.floor]}!")
        # Add qubit on event floor
        if self.player.qubits < MAX_QUBITS and self.floor != 9:
            self.player.qubits += 1
            print(f"Gained a qubit. You now have {self.player.qubits}.")

        # Heal on event floor
        self.player.health_change(10)
        print(f"Recovered 10 health. HP: {self.player.health}/{self.player.max_health}")

        # Add a card to your deck
        if self.floor == 3:
            cnot_card = next(card for card in CARD_POOL if card.name == "CNOT")
            self.add_card(cnot_card)

        elif self.floor == 7:
            toffoli_card = next(card for card in CARD_POOL if card.name == "Toffoli")
            self.add_card(toffoli_card)

        # Choose how many cards to receive
        if self.floor == 9:
            number_of_choices = 2
        else:
            number_of_choices = 1

        # Floor 3: Toffoli cannot appear as a choice
        excluded_cards = ["Toffoli"] if self.floor == 3 else []

        for i in range(number_of_choices):
            self.choose_card_reward(exclude=excluded_cards)

    def run(self):
        # Run the main gameplay loop for the floors
        final_floor = max((*FLOORS.keys(), *EVENT_FLOORS.keys()))
        while self.floor <= final_floor and self.player.health > 0:
            combat_floor = self.start_floor()
            # Run the turn logic for within each floor
            if combat_floor:
                while self.enemy.health > 0 and self.player.health > 0:
                    self.gameplay_turn()
            if self.player.health > 0:
                self.floor += 1

        # When you beat the final floor
        if self.player.health > 0:
            print("You conquered Quantum Spire!")
        else:
            print("Run ended.")

    def resolve_circuit(self):
        # Resolve the circuit for combat
        circuit = build_circuit(n_qubits=self.player.qubits, gates=self.active_gates)
        counts, probabilities = run_circuit(circuit, shots=1, backend=self.backend)
        outcome = next(iter(counts))
        print(f"Measurement: |{outcome}⟩")

        shield_type = self.enemy.shield_type
        if not self.enemy.shield_status:
            return False
        if shield_type == "bell":
            broken = check_bell(circuit, self.enemy.gimmick, backend=self.backend, max_shots=100)
            print(f"Bell-state check: {'passed' if broken else 'failed'}.")

        elif shield_type == "ghz":  
            broken = check_ghz(circuit, backend=self.backend, max_shots=100)
            print(f"GHZ-state check: {'passed' if broken else 'failed'}.")

        elif shield_type == "deutsch":            
            broken = check_deutsch_jozsa(circuit, backend=self.backend)
            print(f"Deutsch-Jozsa check: {'passed' if broken else 'failed'}.")

        elif shield_type == "toffoli":
            toffoli_check = any(gate[0] == "ccx" for gate in self.active_gates)
            broken = toffoli_check and self.enemy.state_shield is not None and outcome.endswith(self.enemy.state_shield)
            print(f"Toffoli check: {'passed' if broken else 'failed'}.")

        else:
            broken = outcome.endswith(self.enemy.state_shield)

        if broken and self.enemy.shield_status:
            self.enemy.shield_status = False
            print("Quantum state shield broken!")
            return True
        return False

    def apply_gate_passives(self):
        # Gates have passive effects so they have use after you break the state shield
        for gate in self.active_gates:
            name = gate[0]
            if name == "h":
                self.player.get_block(3)
                print("Hadamard passive: gained 3 block.")
            elif name == "x":
                self.pending_damage += 3
                print("Pauli-X passive: dealt 3 damage.")
            elif name == "y":
                self.player.health_change(2)
                print("Pauli-Y passive: recovered 2 health.")
            elif name == "z":
                self.pending_damage += 3
                print("Pauli-Z passive: dealt 3 damage.")
            elif name == "cx":
                self.pending_damage += 6
                print("CNOT passive: dealt 6 damage.")
            elif name == "cz":
                self.pending_damage += 6
                print("CZ passive: dealt 6 damage.")
            elif name == "cxx":
                self.pending_damage += 6
                print("Toffoli passive: dealt 12 damage.")

    def draw_hand(self):
        self.hand = []
        # Draw 4 cards
        while len(self.hand) < 4:
            if not self.draw_pile:
                if not self.discard_pile:
                    break

                # Only reshuffle when the draw pile is empty
                self.draw_pile = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.draw_pile)
            self.hand.append(self.draw_pile.pop())

    def show_hand(self):
        # Displays the cards you drew in your hand
        print("\nHand:")
        if not self.hand:
            print("(empty)")
            return

        for index, card in enumerate(self.hand, start=1):
            print(f"{index}. {card.name} (Energy: {card.energy_cost})")
        print(f"Energy:     {self.player.energy}/{self.player.max_energy}")

    def show_status(self):
        # Display current state of the player and enemy after playing a card
        print(f"Player HP:  {self.player.health}/{self.player.max_health}       Block:  {self.player.block}")
        print(f"\nEnemy:    {self.enemy.name}")

        if self.enemy.is_attacking:
            phase = f"Attack for {self.enemy.damage} damage"
        else:
            phase = f"Rest"
        print(f"Enemy HP:   {self.enemy.health}/{self.enemy.max_health}     Enemy intent:   {phase}")
        shield = "ACTIVE" if self.enemy.shield_status else "BROKEN"

        if self.enemy.shield_type == "bell":
            bell_outcomes = {
                "phi_plus": "|00⟩ and |11⟩",
                "phi_minus": "|00⟩ and |11⟩",
                "psi_plus": "|01⟩ and |10⟩",
                "psi_minus": "|01⟩ and |10⟩",
            }
            outcomes = bell_outcomes.get(self.enemy.gimmick)
            objective = f"produce both {outcomes}, with no other outcomes"

        elif self.enemy.shield_type == "ghz":
            objective = "produce both |000⟩ and |111⟩ outcomes on qubits 0, 1, and 2 without any other outcomes"

        elif self.enemy.shield_type == "deutsch":
            objective = "pass the Deutsch-Jozsa check by measuring |0⟩ on qubit 0"

        elif self.enemy.shield_type == "toffoli":
            objective = "play a Toffoli gate and measure the target state"

        else:
            objective = f"requires |{self.enemy.state_shield}⟩"

        print(f"Quantum State Shield:   {shield} ({objective})")
        print(f"\nPending damage on enemy:    {self.pending_damage}")

    def start_turn(self):
        if self.enemy.health <= 0 or self.player.health <= 0:
            print("Combat has ended!")
            return

        # Set up turns on a floor
        self.turn += 1
        self.player.energy = self.player.max_energy
        self.player.block = 0
        self.pending_damage = 0

        print(f"---- Turn {self.turn} ----")
        self.show_status()
        self.draw_hand()
        self.show_hand()

    def update_circuit_preview(self):
        # Get the circuit and probabilities for player
        self.circuit_preview = build_circuit(n_qubits=self.player.qubits, gates=self.active_gates)
        self.circuit_probabilities = get_exact_probabilities(self.circuit_preview)

    def show_circuit(self):
        # Display the circuit and probabilities for the player to preview before playing whatever cards
        print("\nCircuit:")
        if self.circuit_preview is None:
            print("(no circuit)")
            return

        print(self.circuit_preview.draw(output="text"))
        print("Measurement probabilities:")
        for state, probability in sorted(self.circuit_probabilities.items()):
            print(f" {state}: {probability:.1%}")

    def gameplay_turn(self):
        # Run everything that needs to happen in a turn
        if self.enemy.health <= 0 or self.player.health <= 0:
            print("Combat has ended!")
            return

        self.start_turn()
        self.update_circuit_preview()
        self.play_hand()
        self.end_turn()

    def choose_qubit(self, label):
        # Chooses specific qubit you want to put the gate on
        while True:
            if self.player.qubits == 1:
                return 0
            choice = input(f"{label} qubit (0-{self.player.qubits - 1}, or Enter to cancel): ").strip()
            if not choice:
                return None
            if choice.isdigit() and 0 <= int(choice) < self.player.qubits:
                return int(choice)
            print(f"Enter a qubit number from 0 to {self.player.qubits - 1}, or press Enter to cancel.")

    def choose_gate_qubits(self, card):
        # For the gate you play choose which qubit(s) you are putting it on
        if card.gate == "ccx":
            print(f"Available qubits: 0 to {self.player.qubits - 1}")
            control = self.choose_qubit("First control")
            if control is None:
                return None

            while True:
                second_control = self.choose_qubit("Second control")
                if second_control is None:
                    return None
                if second_control != control:
                    break
                print("The control qubits must be different.")

            while True:
                target = self.choose_qubit("Target")
                if target is None:
                    return None
                if target != control and target != second_control:
                    return control, second_control, target
                print("The target must be different from both control qubits.")

        if card.gate in ("cx", "cz"):
            if self.player.qubits < 2:
                print(f"{card.name} requires at least 2 qubits.")
                return None

            print(f"Available qubits: 0 to {self.player.qubits - 1}")
            control = self.choose_qubit("Control")
            if control is None:
                return None

            while True:
                target = self.choose_qubit("Target")
                if target is None:
                    return None
                if target != control:
                    return 0, control, target
                print("Control and target must be different qubits.")
        print(f"Available qubits: 0 to {self.player.qubits - 1}")
        qubit = self.choose_qubit("Qubit")
        if qubit is None:
            return None
        return qubit, 0, 1

    def play_hand(self):
        # Handles playing the cards from you hand
        while self.hand:
            self.display_game()
            choice = input("Choose a card to play (1-4), or press Enter to end your turn: ").strip()
            if not choice:
                break
            if not choice.isdigit() or not 1 <= int(choice) <= len(self.hand):
                input(f"Choose a number from 1 to {len(self.hand)}. Press Enter to continue...")
                continue

            hand_index = int(choice) - 1
            card = self.hand[hand_index]
            if card.energy_cost > self.player.energy:
                self.play_card(card)
                continue

            placement = None
            if isinstance(card, GateCard):
                placement = self.choose_gate_qubits(card)
                if placement is None:
                    continue

            if placement is None:
                played = self.play_card(card)
            else:
                qubit, control, target = placement
                played = self.play_card(
                    card,
                    qubit=qubit,
                    control=control,
                    target=target,
                )

            if played:
                self.discard_pile.append(self.hand.pop(hand_index))
                if isinstance(card, GateCard):
                    self.update_circuit_preview()
                input("\nCard played. Press Enter to continue...")
        self.display_game()

    def play_card(self, card, qubit=0, control=0, target=1):
        # Handles playing cards
        if card.energy_cost > self.player.energy:
            input("\nNot enough energy. Press Enter to continue...")
            return False

        if not self.player.play_cards(card.energy_cost):
            return False
        print(f"\nPlayed {card.name}.")

        # Valid gate card placements
        if isinstance(card, GateCard):
            if card.gate == "ccx":
                self.active_gates.append((card.gate, qubit, control, target))
                print(f"Added Toffoli gate: qubits {qubit} and {control} control qubit {target}.")
            elif card.gate in ("cx", "cz"):
                self.active_gates.append((card.gate, control, target))
                print(f"Added {card.gate.upper()} gate: "
                f"qubit {control} -> qubit {target}.")
            else:
                self.active_gates.append((card.gate, qubit))
                print(f"Added {card.gate.upper()} gate to qubit {qubit}.")
        
        # Attack cards
        elif isinstance(card, AttackCard):
            self.pending_damage += card.damage
            print(f"Queued {card.damage} damage")

        # Skill cards
        elif isinstance(card, SkillCard):
            if card.block != 0:
                self.player.get_block(card.block)
                print(f"Gained {card.block} block")

            if card.healing != 0:
                self.player.health_change(card.healing)
                print(f"Recovered {card.healing} health")
        
        print(f"Energy remaining: {self.player.energy}")
        return True

    def display_game(self):
        # Display top of the screen with title, turn and floor
        clear_terminal()
        print("""
┏━┓╻ ╻┏━┓┏┓╻╺┳╸╻ ╻┏┳┓   ┏━┓┏━┓╻┏━┓┏━╸
┃┓┃┃ ┃┣━┫┃┗┫ ┃ ┃ ┃┃┃┃   ┗━┓┣━┛┃┣┳┛┣╸ 
┗┻┛┗━┛╹ ╹╹ ╹ ╹ ┗━┛╹ ╹   ┗━┛╹  ╹╹┗╸┗━╸
""")
        print(f"Floor: {self.floor}         Turn: {self.turn}\n")

        # Show other aspects of the game
        self.show_status()
        self.show_circuit()
        self.show_hand()


    def end_turn(self):
        # End the turn
        print()
        # Do gate passives if the shield was broken before this turn
        if self.enemy.shield_status == False:
            self.apply_gate_passives()

        # Resolve circuit - see what output the circuit you made has and check if it breaks the shield
        self.resolve_circuit()
        print()
        if self.enemy.shield_status:
            if self.pending_damage > 0:
                print("The quantum state shield blocked the attack!")
            elif self.enemy.state_shield is None:
                print(f"Complete the {self.enemy.shield_type} shield check to break the shield.")
            else:
                print(f"Measure |{self.enemy.state_shield}⟩ to break the state shield.")
        elif self.player.health > 0:
            self.enemy.take_damage(self.pending_damage)
            print(f"You dealt {self.pending_damage} damage.")

        # Reset the pending damage once dealt
        self.pending_damage = 0

        # Update block interaction with message in terminal
        if self.enemy.health > 0:
            blocked = self.player.block - self.enemy.damage
            if self.enemy.is_attacking:
                over_damage = self.enemy.do_damage(self.player)
                print(f"The enemy dealt {over_damage} damage to you.")
            else:
                print("Enemy rests this turn. You take no damage.")
            self.enemy.next_phase()
            if blocked >= 0:
                print(f"You blocked {self.enemy.damage} damage.")


        else:
            print("Enemy defeated!")

        # If you lose
        if self.player.health <= 0:
            print("You have been defeated!")

        input("\nPress Enter to continue...")
        self.discard_pile.extend(self.hand)
        self.hand.clear()

    def show_title_screen(self):
        clear_terminal()

        print(r"""
█████  █    █ ████  ██████ █████ █    █ █████████      ██████ █████ █  █████  ██████
█   █  █    █ █   █ █    █   █   █    █ █   █   █      █      █   █ █  █   █  █     
██  █  ██   █ █████ ██   █   ██  ██   █ ██  █   █      ██████ █████ ██ ██████ ███   
██  █  ██   █ ██  █ ██   █   ██  ██   █ ██      █          ██ ██    ██ ██   █ ██    
██████ ██████ ██  █ ██   █   ██  ██████ ██      █      ██████ ██    ██ ██   █ ██████
""")

        print("     Ten floors stand between you and the summit.")
        print("     Build quantum circuits, defeat enemies, and upgrade your deck as the challenges grow more complex.\n")
        print("             Inspired by Slay the Spire, and developed by Jovana Gojkovic\n")

        print("  1. Start Game")
        print("  2. Quit")

        while True:
            choice = input("\n  Choose an option: ").strip()

            if choice == "1":
                return True
            elif choice == "2":
                return False
            else:
                print("  Enter 1 or 2.")