#!/usr/bin/env python3
"""Temporary RED scaffold; implementation is added in the paired GREEN commit."""
from __future__ import annotations

class Reject(Exception):
    def __init__(self, code: str):
        self.code = code

def check_heading(text: str) -> None:
    # Deliberately incomplete: the contract test must expose the stale heading.
    return None
