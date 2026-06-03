"""Compat shim — o objeto db real vive em src.config.database."""
from src.config.database import db  # noqa: F401
