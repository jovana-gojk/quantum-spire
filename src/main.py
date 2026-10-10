from quantum import build_circuit, run_circuit
from game import Game, GateCard, AttackCard, SkillCard

def get_backend():
    # Use Qollab's backend if available, otherwise use local Aer
    qollab_backend = globals().get("backend")

    if qollab_backend is not None:
        print("Using Qollab-provided backend")
        return qollab_backend

    from qiskit_aer import AerSimulator
    print("Using local Qiskit Aer simulator")
    return AerSimulator()


def main(shots: int = 1):
    backend = get_backend()
    game = Game(backend=backend)
    game.start_floor()
    game.start_turn()

    game.play_card(GateCard("Pauli-X", 1, "x"))
    game.play_card(AttackCard("Attack", 1, damage=6))
    game.play_card(SkillCard("Shield", 1, block=5))

    print("Active gates:", game.active_gates)
    print("Pending damage:", game.pending_damage)

    game.end_turn()
    """gates = [
        ("x", 0),
    ]
    circuit = build_circuit(n_qubits=1, gates=gates)

    print(circuit.draw(output="text"))

    counts, probabilities = run_circuit(circuit, shots, backend)

    print("\nCounts:", counts)
    print("Probabilities:")

    for outcome, probability in sorted(probabilities.items()):
        print(f"{outcome}: {probability:.1%}")"""



# Run on my own computer
if __name__ == "__main__" and "backend" not in globals():
    main()
