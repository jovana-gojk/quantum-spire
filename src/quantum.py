# NOTE: 'backend' is pre-created as a global variable

from qiskit import QuantumCircuit
from qiskit.providers.jobstatus import JobStatus
import time

def build_circuit(n_qubits, gates):
    circuit = QuantumCircuit(n_qubits, n_qubits)

    for gate in gates:
        name = gate[0].lower()

        if name == "h":
            circuit.h(gate[1])
        elif name == "x":
            circuit.x(gate[1])
        elif name == "y":
            circuit.y(gate[1])
        elif name == "z":
            circuit.z(gate[1])
        elif name == "cx":
            circuit.cx(gate[1], gate[2])
        elif name == "cz":
            circuit.cz(gate[1], gate[2])
        else:
            raise ValueError(f"Unknown gate: {name}")

    circuit.measure(range(n_qubits), range(n_qubits))
    return circuit

def run_circuit(circuit, shots=1, backend=None):
    job = backend.run(circuit, shots=shots)

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
