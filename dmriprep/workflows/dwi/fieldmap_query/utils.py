def check_opposite(direction: str, target: list, layout) -> bool:
    """
    Checks if the opposite phase is available.

    Parameters
    ----------
    direction : str
        Phase encoding direction.
    opposite_direction : str
        Opposite phase encoding direction.

    Returns
    -------
    bool
        True if opposite phase is available.
    """
    opposite_direction = layout.get_metadata(target).get(
        "PhaseEncodingDirection"
    )
    if not opposite_direction:
        raise ValueError(
            f"{target} does not have PhaseEncodingDirection key in metadata."
        )
    if "-" in direction and opposite_direction == direction.replace("-", ""):
        return True
    elif (
        ("-" not in direction)
        and (direction in opposite_direction)
        and ("-" in opposite_direction)
    ):
        return True
    return False
