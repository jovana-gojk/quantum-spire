import random
import os
from quantum import build_circuit, run_circuit

# Game constants
STARTING_HEALTH = 30
STARTING_ENERGY = 3
STARTING_QUBITS = 1
STARTING_BLOCK = 0

MAX_QUBITS = 4
DEFAULT_SHOTS = 1024

STARTING_FLOOR = 1
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

    def deal_damage(damage, target):
        # Check if they have shield
        if True:
            return False
        else:
            target.health -= damage
            return True

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


class Game:
    def __init__(self, backend):
        self.backend = backend
        # Game state beginning
        self.floor = STARTING_FLOOR

        # Init the player in the game
        self.player = Player()

        self.turn = 0
        self.active_gates = []
        self.pending_damage = 0
        self.draw_pile = self.player.deck.copy()
        random.shuffle(self.draw_pile)
        self.discard_pile = []
        self.hand = []
        self.circuit_preview = None
        self.circuit_probabilities = {}

    def start_floor(self):
        if self.floor == 1:
            self.enemy = Enemy(name="Guard", health=20, state_shield="1", damage=5)

        print(f"Floor {self.floor} started!")
        print(f"Enemy: {self.enemy.name}")
        print(f"Enemy health: {self.enemy.health}, State shield: {self.enemy.state_shield}")

    def resolve_circuit(self):
        circuit = build_circuit(n_qubits=self.player.qubits, gates=self.active_gates)

        counts, probabilities = run_circuit(circuit, shots=1, backend=self.backend)
        outcome = next(iter(counts))

        print("Measurement:", outcome)

        if outcome[-1] == self.enemy.state_shield:
            self.enemy.shield_status = False

    def draw_hand(self):
        self.hand = []
        # Draw 4 cards
        while len(self.hand) < 4:
            if not self.draw_pile:
                if not self.discard_pile:
                    break
                self.draw_pile = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.draw_pile)
            self.hand.append(self.draw_pile.pop())

    def show_hand(self):
        print("Hand:")
        if not self.hand:
            print("(empty)")
            return

        for index, card in enumerate(self.hand, start=1):
            print(f"{index}. {card.name} (Energy: {card.energy_cost})")

    def show_status(self):
        print(f"Player HP:  {self.player.health}/{self.player.max_health}       Block:      {self.player.block}")
        print(f"Energy:     {self.player.energy}/{self.player.max_energy}")
        print(f"Enemy:      {self.enemy.name}")
        print(f"Enemy HP:   {self.enemy.health}/{self.enemy.max_health}")

        shield = "ACTIVE" if self.enemy.shield_status else "BROKEN"
        print(f"Shield:     {shield} (requires |{self.enemy.state_shield}⟩)")

    def start_turn(self):
        if self.enemy.health <= 0 or self.player.health <= 0:
            print("Combat has ended!")
            return

        self.turn += 1
        self.player.energy = self.player.max_energy
        self.player.block = 0
        self.active_gates = []
        self.pending_damage = 0

        print(f"---- Turn {self.turn} ----")
        self.show_status()
        self.draw_hand()
        self.show_hand()

    def update_circuit_preview(self):
        self.circuit_preview = build_circuit(n_qubits=self.player.qubits, gates=self.active_gates)
        counts, self.circuit_probabilities = run_circuit(self.circuit_preview, shots=DEFAULT_SHOTS, backend=self.backend)

    def show_circuit(self):
        print("Circuit:")
        if self.circuit_preview is None:
            print("(no circuit)")
            return

        print(self.circuit_preview.draw(output="text"))
        print("Measurement probabilities:")
        for state, probability in sorted(self.circuit_probabilities.items()):
            print(f" {state}: {probability:.1%}")

    def gameplay_turn(self):
        if self.enemy.health <= 0 or self.player.health <= 0:
            print("Combat has ended!")
            return

        self.start_turn()
        self.update_circuit_preview()
        self.play_hand()

        self.discard_pile.extend(self.hand)
        self.hand.clear()

    def play_hand(self):
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
            if self.play_card(card):
                self.discard_pile.append(self.hand.pop(hand_index))
                if isinstance(card, GateCard):
                    self.update_circuit_preview()
        self.display_game()

    def play_card(self, card, qubit=0, control=0, target=1):
        if card.energy_cost > self.player.energy:
            print("Not enough energy")
            return False

        # Invalid gate card placement
        if isinstance(card, GateCard):
            if card.gate in ("cx", "cz"):
                if (control == target or 
                    control < 0 or target < 0 or 
                    control >= self.player.qubits or 
                    target >= self.player.qubits):
                    print("Invalid qubit targets")
                    return False
                
            elif qubit < 0 or qubit >= self.player.qubits:
                print("Unavailable qubit")
                return False

        if not self.player.play_cards(card.energy_cost):
            return False

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
        clear_terminal()

        print("-" * 50)
        print("QUANTUM SPIRE")
        print("-" * 50)

        print(f"Floor: {self.floor}         Turn: {self.turn}\n")

        self.show_status()
        self.show_circuit()
        self.show_hand()


    def end_turn(self):
        self.resolve_circuit()
        
        if self.enemy.shield_status == False and self.player.health > 0:
            self.enemy.take_damage(self.pending_damage)
            print(f"Shield broken! Dealt {self.pending_damage} damage.")
        else:
            print("The shield blocked the attack!")

        self.pending_damage = 0

        if self.enemy.health > 0:
            self.enemy.do_damage(self.player)
            print(f"Player health: {self.player.health}")
            print(f"Player block: {self.player.block}")
        else:
            print("Enemy defeated!")

        if self.player.health <= 0:
            print("You have been defeated!")

        self.discard_pile.extend(self.hand)
        self.hand.clear()
