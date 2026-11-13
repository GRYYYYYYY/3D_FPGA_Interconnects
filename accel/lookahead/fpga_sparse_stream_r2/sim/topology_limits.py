"""Current implemented harness/central-tag limits, not a scaling prediction."""
def validate_many_topology(lanes, ports):
    if lanes < 2 or lanes > 32 or lanes & (lanes - 1):
        raise ValueError('implemented many-tile lanes must be a power of two in 2..32; 64 needs wider host masks and central client IDs/grants')
    if ports < 1 or ports > 32 or ports & (ports - 1):
        raise ValueError('implemented many-tile physical ports must be a power of two in 1..32')
