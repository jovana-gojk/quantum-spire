# Quantum Spire

A terminal deckbuilder roguelike inspired by *Slay the Spire*, where combat is fought with real quantum circuits. Play cards to build a circuit, measure it, and break each enemy's **quantum state shield** before you can hurt it.

This project is under the Quantum Playground theme: an interactive game that teaches quantum mechanics with a roguelike spin. It teaches circuit construction in a creative way, letting the player learn how gates interact with each other and how to entangle qubits. Boss floors also teach specific quantum circuit problems.

Developed by Jovana Gojkovic. MIT licensed.

## Requirements

- Python 3
- `qiskit` and `qiskit-aer` (see `requirements.txt`)

```bash
git clone https://github.com/jovana-gojk/quantum-spire
cd quantum-spire
pip install -r requirements.txt
```

## Running

```bash
python src/main.py
```

This is an **interactive terminal game**. It reads your choices from the keyboard with `input()`, so it must be run in a normal terminal. It uses the local `AerSimulator` from `qiskit-aer` to run your circuits.

If the game is run somewhere with no keyboard input (for example a platform that runs scripts without a terminal), `input()` fails and the game stops with an error. A separate autoplay version, which has a bot play when input is unavailable, was made for Qollab.

## Controls

- **Title screen:** `1` to start, `2` to quit.
- **Your turn:** type the number of a card in your hand to play it, or press Enter to end your turn.
- **Gate cards:** if you have more than one qubit, you are asked which qubit(s) to use. Press Enter at a qubit prompt to cancel the card.
- **Rewards:** type the number of the card you want to add to your deck.

## How it works

You climb ten floors. Floors 1, 2, 4, 5, 6, 8 and 10 are fights. Floors 3, 7 and 9 are lab events.

### Your turn

- You start with 30 HP, 3 energy per turn, and 1 qubit (maximum 4).
- You draw 4 cards each turn from your deck.
- **Gate cards** add a quantum gate to your circuit. The circuit carries over from turn to turn within a floor and resets on the next floor.
- **Attack cards** queue damage. **Skill cards** give block or healing.
- At the end of your turn your circuit is measured, and the result is checked against the enemy's shield.

### Quantum state shields

While an enemy's shield is up, your queued damage is blocked. Break the shield by getting the right measurement result:

| Shield | How to break it |
| --- | --- |
| Basis state (e.g. `1`, `00`, `101`) | Measure the required state |
| Bell state | Produce both outcomes of the required Bell pair, and no other outcomes |
| Deutsch-Jozsa (The Oracle) | Pass the Deutsch-Jozsa check |
| GHZ (Green Horned Zebra) | Produce both `000` and `111` and nothing else |
| Toffoli (Toffoli Tyrant) | Play a Toffoli gate and measure `111` |

Once a shield is broken, damage goes through. Gates in your circuit then also have passive effects each turn:

| Gate | Passive |
| --- | --- |
| Hadamard | +3 block |
| Pauli-X | 3 damage |
| Pauli-Y | heal 2 HP |
| Pauli-Z | 3 damage |
| CNOT | 6 damage |
| CZ | 6 damage |
| Toffoli | 12 damage |

Enemies alternate between attacking and resting. Block resets at the start of each turn.

### Cards

Starting deck: 2 Hadamard, 2 Pauli-X, 1 Shield, 2 Attack.

Other cards you can earn: Pauli-Y, Pauli-Z, CNOT, CZ, Toffoli, Heal, Little Strike.

### Lab events (floors 3, 7, 9)

Each lab heals you for 10 HP and lets you add cards. Floors 3 and 7 also give you a qubit (up to 4).

- **Floor 3, Spin Lab:** gain a qubit, heal, receive a CNOT card, then choose one more card.
- **Floor 7, Superconducting Lab:** gain a qubit, heal, receive a Toffoli card, then choose one more card.
- **Floor 9, Photonics Lab:** heal and choose two cards (no qubit).

## Project layout

```
src/main.py      entry point
src/game.py      game loop, cards, enemies, floors
src/quantum.py   circuit building and shield checks (Qiskit)
```