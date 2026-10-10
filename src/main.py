# NOTE: 'backend' is pre-created as a global variable

from qiskit import QuantumCircuit
from qiskit.providers.jobstatus import JobStatus
import time

def get_backend():
    # Use Qollab's backend if available, otherwise use local Aer

    qollab_backend = globals().get("backend")

    if qollab_backend is not None:
        print("Using Qollab-provided backend")
        return qollab_backend

    from qiskit_aer import AerSimulator

    print("Using local Qiskit Aer simulator")
    return AerSimulator()

def build_circuit(n_qubits, gates):
    circuit = QuantumCircuit(n_qubits, n_qubits)

    for gate in gates:
        name = gate[0].lower()

        if name == "h":
            circuit.h(gate[1])
        elif name == "x":
            circuit.x(gate[1])
        elif name == "z":
            circuit.z(gate[1])
        elif name == "cx":
            circuit.cx(gate[1], gate[2])
        else:
            raise ValueError(f"Unknown gate: {name}")

    circuit.measure(range(n_qubits), range(n_qubits))
    return circuit

def run_circuit(circuit, shots=1):
    execution_backend = get_backend()
    job = execution_backend.run(circuit, shots=shots)

    while True:
        status = job.status()
        if status == JobStatus.DONE:
            break

        if status == JobStatus.ERROR:
            raise RuntimeError(
                f"Circuit execution failed: {job.result()}"
            )
        time.sleep(2)

    counts = job.result().get_counts()
    total = sum(counts.values())

    probabilities = {
        bitstring: count / total
        for bitstring, count in counts.items()
    }

    return counts, probabilities


def main(shots: int = 1):
    gates = [
        ("x", 0),
    ]
    circuit = build_circuit(n_qubits=1, gates=gates)

    print(circuit.draw(output="text"))

    counts, probabilities = run_circuit(circuit, shots)

    print("\nCounts:", counts)
    print("Probabilities:")

    for outcome, probability in sorted(probabilities.items()):
        print(f"{outcome}: {probability:.1%}")


# Run on my own computer
if __name__ == "__main__" and "backend" not in globals():
    main()
