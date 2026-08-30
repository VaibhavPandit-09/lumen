"""
High-performance fuzzy matching and acronym recognition engine.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


def get_acronym(text: str) -> str:
    """Extracts acronym characters from a phrase (first letter of each word and uppercase letters)."""
    words = re.findall(r"[a-zA-Z0-9]+", text)
    acronym_chars = []
    for word in words:
        if word:
            acronym_chars.append(word[0].lower())
            # Also include camelCase inner capitals
            for ch in word[1:]:
                if ch.isupper():
                    acronym_chars.append(ch.lower())
    return "".join(acronym_chars)


def fuzzy_match(query: str, target: str) -> Tuple[bool, float]:
    """
    Computes a match score between query and target string.
    Returns (matched: bool, score: float). Higher score indicates better match.
    """
    if not query:
        return True, 1.0

    if not target:
        return False, 0.0

    q = query.strip()
    t = target.strip()
    q_lower = q.lower()
    t_lower = t.lower()

    # 1. Exact match
    if q_lower == t_lower:
        score = 1000.0
        if q == t:
            score += 50.0  # Exact case bonus
        return True, score

    # 2. Exact prefix match
    if t_lower.startswith(q_lower):
        # Shorter targets get a higher density score
        length_ratio = len(q_lower) / len(t_lower)
        score = 800.0 + (length_ratio * 100.0)
        return True, score

    # 3. Word boundary prefix match (e.g. "term" in "Super Terminal")
    words = re.split(r"[\s\-_/.]+", t_lower)
    for idx, word in enumerate(words):
        if word.startswith(q_lower):
            word_penalty = idx * 10.0
            length_ratio = len(q_lower) / len(word)
            score = 650.0 - word_penalty + (length_ratio * 50.0)
            return True, max(score, 500.0)

    # 4. Acronym match (e.g. "ksp" -> "KSystemLog", "ff" -> "Firefox", "gc" -> "Google Chrome")
    acronym = get_acronym(t)
    if q_lower == acronym:
        return True, 600.0
    if acronym.startswith(q_lower):
        return True, 550.0 + (len(q_lower) / len(acronym)) * 40.0

    # 5. Fuzzy Subsequence matching
    # Checks if all characters in query appear in order in target
    q_len = len(q_lower)
    t_len = len(t_lower)

    if q_len > t_len:
        return False, 0.0

    q_idx = 0
    t_idx = 0
    matches: List[int] = []
    consecutive_count = 0
    score = 0.0

    while q_idx < q_len and t_idx < t_len:
        qc = q_lower[q_idx]
        tc = t_lower[t_idx]

        if qc == tc:
            matches.append(t_idx)

            # Match character bonus
            char_score = 10.0

            # Start of string bonus
            if t_idx == 0:
                char_score += 25.0
            # Word boundary bonus (after space, hyphen, underscore, dot, slash)
            elif t_idx > 0 and t[t_idx - 1] in " -_/.":
                char_score += 20.0
            # CamelCase boundary bonus
            elif target[t_idx].isupper() and target[t_idx - 1].islower():
                char_score += 15.0

            # Consecutive match bonus
            if consecutive_count > 0:
                char_score += consecutive_count * 12.0
            consecutive_count += 1

            # Exact case match bonus
            if q[q_idx] == target[t_idx]:
                char_score += 2.0

            score += char_score
            q_idx += 1
        else:
            consecutive_count = 0

        t_idx += 1

    # Check if all query characters were found
    if q_idx == q_len:
        # Distance and gap penalty: penalize span length
        span = matches[-1] - matches[0] + 1
        gap_penalty = (span - q_len) * 3.0
        # Length penalty: prefer compact matches
        length_penalty = (t_len - q_len) * 0.5

        final_score = max(0.0, score - gap_penalty - length_penalty)
        return True, final_score

    return False, 0.0


def score_item(
    query: str,
    title: str,
    subtitle: str = "",
    keywords: Optional[List[str]] = None,
    category: str = "",
) -> Tuple[bool, float]:
    """
    Computes a composite relevance score for an item against a search query.
    Weights: Title (1.0), Keywords (0.8), Subtitle (0.5), Category (0.3).
    """
    if not query:
        return True, 1.0

    best_score = 0.0
    has_match = False

    # 1. Title match (Highest weight)
    matched_title, title_score = fuzzy_match(query, title)
    if matched_title:
        has_match = True
        best_score = max(best_score, title_score * 1.0)

    # 2. Keywords match
    if keywords:
        for kw in keywords:
            if not kw:
                continue
            matched_kw, kw_score = fuzzy_match(query, kw)
            if matched_kw:
                has_match = True
                best_score = max(best_score, kw_score * 0.8)

    # 3. Subtitle / Description match
    if subtitle:
        matched_sub, sub_score = fuzzy_match(query, subtitle)
        if matched_sub:
            has_match = True
            best_score = max(best_score, sub_score * 0.5)

    # 4. Category match
    if category:
        matched_cat, cat_score = fuzzy_match(query, category)
        if matched_cat:
            has_match = True
            best_score = max(best_score, cat_score * 0.3)

    return has_match, best_score
