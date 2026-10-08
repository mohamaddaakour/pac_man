from maze_adapter import _convert_cells

def main() -> None:
    """Entry point for pac-man game."""
    print(_convert_cells([[13, 7, 15]], 3, 1))


if __name__ == "__main__":
    main()