import random
import os
import copy
import time
from quantum import build_circuit, get_exact_probabilities, run_circuit

# Game constants
STARTING_HEALTH = 30
STARTING_ENERGY = 3
STARTING_QUBITS = 1
STARTING_BLOCK = 0

MAX_QUBITS = 4

STARTING_FLOOR = 1
EVENT_FLOORS = {
    3: "Campfire",
    7: "Quantum Smithy",
    9: "Card Archive",
}
FLOORS = {
    # Floor 1: One-qubit shields
    1: [
        {"name": "Guard", "health": 20, "state_shield": "1", "damage": 5},
        {"name": "Lost Qubit", "health": 16, "state_shield": "0", "damage": 4},
        {"name": "Twin Initiates", "health": 24, "state_shield": "1", "damage": 5},
    ],

    # Floor 2: Stronger one-qubit enemies
    2: [
        {"name": "Wraith", "health": 26, "state_shield": "0", "damage": 6},
        {"name": "Phase Thief", "health": 22, "state_shield": "1", "damage": 7},
        {"name": "Entangled Pair", "health": 30, "state_shield": "0", "damage": 6},
    ],

    # Floor 4: Two-qubit shields
    4: [
        {"name": "Watcher", "health": 34, "state_shield": "00", "damage": 7},
        {"name": "Glitch", "health": 30, "state_shield": "10", "damage": 8},
        {"name": "Twin Sentinels", "health": 40, "state_shield": "11", "damage": 7},
    ],

    # Floor 5: Two-qubit shields
    5: [
        {"name": "Iron Golem", "health": 44, "state_shield": "11", "damage": 8},
        {"name": "Phase Knight", "health": 38, "state_shield": "01", "damage": 9},
        {"name": "Probability Witch", "health": 35, "state_shield": "00", "damage": 10},
    ],

    # Floor 6: Final two-qubit encounter before the upgrade
    6: [
        {"name": "Void Stalker", "health": 48, "state_shield": "00", "damage": 9},
        {"name": "Broken Circuit", "health": 44, "state_shield": "10", "damage": 10},
        {"name": "Gatekeeper", "health": 54, "state_shield": "11", "damage": 9},
    ],

    # Floor 8: Three-qubit shields
    8: [
        {"name": "Crystal Titan", "health": 65, "state_shield": "000", "damage": 11},
        {"name": "Void Twins", "health": 72, "state_shield": "101", "damage": 12},
        {"name": "Circuit Devourer", "health": 60, "state_shield": "110", "damage": 13},
    ],

    # Floor 10: Bosses
    10: [
        {"name": "Quantum Warden", "health": 100, "state_shield": "111", "damage": 14},
        {"name": "Architect of Chaos", "health": 110, "state_shield": "010", "damage": 16},
        {"name": "Entanglement King", "health": 125, "state_shield": "101", "damage": 15},
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
    def __init__(self, name, health, state_shield, damage):
        self.name = name
        self.health = health
        self.max_health = health
        self.state_shield = state_shield
        self.shield_status = True
        self.damage = damage

    def take_damage(self, amount):
        if self.shield_status == False:
            self.health = max(0, self.health - amount)

    def do_damage(self, player):
        blocked = min(player.block, self.damage)
        player.block -= blocked

        over_damage = self.damage - blocked
        player.health = max(0, player.health - over_damage)
        return over_damage

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

    def grant_floor_rewards(self):
        # Add qubit on event floor
        if self.player.qubits < MAX_QUBITS:
            self.player.qubits += 1
            print(f"Gained a qubit. You now have {self.player.qubits}.")
        else:
            print(f"Already at the maximum of {MAX_QUBITS} qubits.")

        # Heal on event floor
        self.player.health_change(10)
        print(f"Recovered 10 health. HP: {self.player.health}/{self.player.max_health}")

        # Add a card to your deck
        print("Choose a card to add to your deck:")
        for index, card in enumerate(CARD_POOL, start=1):
            print(f"{index}. {card.name} (Energy: {card.energy_cost})")

        while True:
            choice = input(f"Choose a card (1-{len(CARD_POOL)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(CARD_POOL):
                selected_card = copy.deepcopy(CARD_POOL[int(choice) - 1])
                self.player.deck.append(selected_card)
                self.draw_pile.append(copy.deepcopy(selected_card))
                print(f"Added {selected_card.name} to your deck.")
                break
            print(f"Choose a number from 1 to {len(CARD_POOL)}.")

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

        # Remove the state shield if circuit outcome is correct
        shield_length = len(self.enemy.state_shield)
        if outcome[-shield_length:] == self.enemy.state_shield and self.enemy.shield_status:
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
        print(f"Enemy HP:   {self.enemy.health}/{self.enemy.max_health}     Incoming Damage:   {self.enemy.damage}")

        shield = "ACTIVE" if self.enemy.shield_status else "BROKEN"
        print(f"Quantum State Shield:   {shield} (requires |{self.enemy.state_shield}⟩)")
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
                print(f"Choose a number from 1 to {len(self.hand)}.")
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
            if card.gate in ("cx", "cz"):
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

        print("-" * 50)
        print("QUANTUM SPIRE")
        print("-" * 50)

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
            over_damage = self.enemy.do_damage(self.player)

            if blocked >= 0:
                print(f"You blocked {self.enemy.damage} damage.")

            print(f"The enemy dealt {over_damage} damage to you.")
        else:
            print("Enemy defeated!")

        # If you lose
        if self.player.health <= 0:
            print("You have been defeated!")

        input("\nPress Enter to continue...")
        self.discard_pile.extend(self.hand)
        self.hand.clear()
