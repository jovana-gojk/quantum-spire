from game import Game

def get_backend():
    # Use Qollab's backend if available, otherwise use local Aer
    qollab_backend = globals().get("backend")

    if qollab_backend is not None:
        return qollab_backend

    from qiskit_aer import AerSimulator
    return AerSimulator()


def main():
    backend = get_backend()
    game = Game(backend=backend)
    game.run()

# Run on my own computer
if __name__ == "__main__" and "backend" not in globals():
    main()
