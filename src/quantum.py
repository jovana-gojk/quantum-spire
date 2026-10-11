# NOTE: 'backend' is pre-created as a global variable

from qiskit import QuantumCircuit
from qiskit.providers.jobstatus import JobStatus
from qiskit.quantum_info import Statevector
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
        elif name == "ccx":
            circuit.ccx(gate[1], gate[2], gate[3])
        else:
            raise ValueError(f"Unknown gate: {name}")

    circuit.measure(range(n_qubits), range(n_qubits))
    return circuit


def get_exact_probabilities(circuit):
    unitary_circuit = circuit.remove_final_measurements(inplace=False)
    statevector = Statevector.from_instruction(unitary_circuit)
    return statevector.probabilities_dict()


BELL_OUTCOMES = {
    "phi_plus": {"00", "11"},
    "phi_minus": {"00", "11"},
    "psi_plus": {"01", "10"},
    "psi_minus": {"01", "10"},
}


def check_bell(circuit, gimmick, backend=None, max_shots=100):
    expected = BELL_OUTCOMES.get(gimmick)
    observed = set()

    for i in range(max_shots):
        counts, probabilities = run_circuit(circuit, shots=1, backend=backend)
        outcome = next(iter(counts))

        if outcome not in expected:
            return False

        observed.add(outcome)

        if observed == expected:
            return True

    return False


def check_ghz(circuit, backend=None, max_shots=100):
    expected = {"000", "111"}
    observed = set()

    for i in range(max_shots):
        counts, probabilities = run_circuit(circuit, shots=1, backend=backend)
        outcome = next(iter(counts))

        # Check the three relevant qubits.
        outcome = outcome[-3:]

        if outcome not in expected:
            return False

        observed.add(outcome)

        if observed == expected:
            return True

    return False


def check_deutsch_jozsa(circuit, backend=None):
    counts, probabilities = run_circuit(circuit, shots=1, backend=backend)
    outcome = next(iter(counts))

    # A zero in the first input register indicates a constant function.
    return outcome[-1] == "0"

def evaluate_shield(circuit, shield_type, gimmick=None, state_shield=None, backend=None):
    if shield_type == None:
        counts, probabilities = run_circuit(circuit, shots=1, backend=backend)
        outcome = next(iter(counts))
        return outcome.endswith(state_shield)

    if shield_type == "bell":
        return check_bell(circuit, gimmick, backend)

    if shield_type == "ghz":
        return check_ghz(circuit, backend)

    if shield_type == "deutsch":
        return check_deutsch_jozsa(circuit, backend)

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
