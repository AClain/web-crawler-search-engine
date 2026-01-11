def normalize_priority(priority: float) -> float:
    if priority > 1.0:
        priority = 1.0
    elif priority < 0.0:
        priority = 0.0

    return float("{:.1f}".format(priority))
