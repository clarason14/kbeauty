# utils/idgen.py
def make_id(n: int, prefix="TT") -> str:
    return f"{prefix}{n:04d}"
