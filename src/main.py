from quantum import build_circuit, run_circuit

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
    gates = [
        ("x", 0),
    ]
    circuit = build_circuit(n_qubits=1, gates=gates)

    print(circuit.draw(output="text"))

    counts, probabilities = run_circuit(circuit, shots, backend)

    print("\nCounts:", counts)
    print("Probabilities:")

    for outcome, probability in sorted(probabilities.items()):
        print(f"{outcome}: {probability:.1%}")


# Run on my own computer
if __name__ == "__main__" and "backend" not in globals():
    main()
