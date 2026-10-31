"""
Aegis AI - Structured Logging Utility.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "aegis",
    log_dir: Optional[Path] = None,
    debug: bool = False,
) -> logging.Logger:
    """Configures and returns a thread-safe, structured logger."""
    log_instance = logging.getLogger(name)
    if log_instance.handlers:
        return log_instance

    log_instance.setLevel(logging.DEBUG if debug else logging.INFO)

    log_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(log_format)
    log_instance.addHandler(console_handler)

    # Rotating File Handler
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = log_dir / "aegis.log"
        file_handler = RotatingFileHandler(
            filename=str(file_path),
            maxBytes=10 * 1024 * 1024,  # 10 MB per file
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        log_instance.addHandler(file_handler)

    return log_instance


# Default application logger instance
logger = setup_logger(name="aegis")
