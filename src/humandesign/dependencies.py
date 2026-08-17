"""
Backward-compatible auth dependency.
All logic moved to auth.py — this re-exports verify_token.
"""
from .auth import verify_token, security

__all__ = ["verify_token", "security"]
