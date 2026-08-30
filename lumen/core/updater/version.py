"""
Version comparison utilities for the updater subsystem.
"""

from __future__ import annotations

import re


def compare_versions(a: str, b: str) -> int:
    """
    Compare two version strings.
    Returns -1 if a < b, 0 if equal, 1 if a > b.
    Handles MAJOR.MINOR.PATCH gracefully.
    Stripping leading 'v' or 'V' and ignoring non-numeric suffixes.
    """
    a = a.lstrip('vV')
    b = b.lstrip('vV')
    
    parts_a = []
    for p in a.split('.'):
        m = re.match(r'^(\d+)', p)
        parts_a.append(int(m.group(1)) if m else 0)
        
    parts_b = []
    for p in b.split('.'):
        m = re.match(r'^(\d+)', p)
        parts_b.append(int(m.group(1)) if m else 0)
        
    # Pad to equal length
    length = max(len(parts_a), len(parts_b))
    parts_a.extend([0] * (length - len(parts_a)))
    parts_b.extend([0] * (length - len(parts_b)))
    
    for pa, pb in zip(parts_a, parts_b):
        if pa < pb:
            return -1
        elif pa > pb:
            return 1
            
    return 0
