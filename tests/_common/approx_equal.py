def approx_eq(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol
