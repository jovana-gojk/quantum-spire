from game import Game

def get_backend():
    # Use Qollab's backend if available, otherwise use local Aer
    qollab_backend = globals().get("backend")

    if qollab_backend is not None:
        print("Using Qollab-provided backend")
        return qollab_backend

    from qiskit_aer import AerSimulator
    print("Using local Qiskit Aer simulator")
    return AerSimulator()


def main():
    backend = get_backend()
    game = Game(backend=backend)
    game.start_floor()
    while game.enemy.health > 0 and game.player.health > 0:
        game.start_turn()
        game.play_hand()
        game.end_turn()

# Run on my own computer
if __name__ == "__main__" and "backend" not in globals():
    main()
