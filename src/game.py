import random


# Game constants
STARTING_HEALTH = 30
STARTING_ENERGY = 3
STARTING_QUBITS = 1
STARTING_BLOCK = 0

MAX_QUBITS = 4
DEFAULT_SHOTS = 1

STARTING_FLOOR = 1

    
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
    def __init__(self, name, energy_cost, block, healing):
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
    "Hadamard",
    "Hadamard",
    "Pauli-X",
    "Pauli-X",
    "Shield",
    "Attack",
    "Attack",
]

class Player:
    def __init__(self):
        # Player standing
        self.health = STARTING_HEALTH
        self.max_health = STARTING_HEALTH
        self.block = STARTING_BLOCK
        self.energy = STARTING_ENERGY
        self.max_energy = STARTING_ENERGY
        self.n_qubits = STARTING_QUBITS

        self.deck = STARTING_DECK

    def health_change(self, hp_points):
        # Take damage or healing
        self.health += hp_points

        # Keep health within max
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


class Game:
    def __init__(self):
        # Game state beginning
        self.floor = STARTING_FLOOR

        # Init the player in the game
        self.player = Player()