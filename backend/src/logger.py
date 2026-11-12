import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

file_handler = RotatingFileHandler(
    LOG_DIR / "api.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)

formatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré pour écrire dans le fichier."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)

    logger.propagate = False

    return logger