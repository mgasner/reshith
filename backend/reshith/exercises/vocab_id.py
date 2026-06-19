"""Deterministic vocab IDs for cross-table lookup.

Each (language, lemma) pair maps to a stable UUID5 derived from a fixed
namespace. This lets us seed primary-deck `Card.id` deterministically from
lesson JSON and reference vocabulary in `ExerciseAttempt.vocab_id` without
needing a join through `Card`.
"""

import uuid

# Random project-wide namespace (UUID4). Do not change — IDs derived from it
# are persisted in the database.
NAMESPACE_VOCAB = uuid.UUID("e3b0c442-98fc-1c14-9afb-f4c8996fb924")


def vocab_id(language: str, lemma: str) -> uuid.UUID:
    """Return a deterministic UUID for a (language, lemma) pair."""
    return uuid.uuid5(NAMESPACE_VOCAB, f"{language}|{lemma}")
