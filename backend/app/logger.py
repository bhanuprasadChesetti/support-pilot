import logging
import sys
import os
from typing import Any

class ColoredFormatter(logging.Formatter):
    """Custom formatter adding color coding and clear visual structure for terminal output."""

    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    cyan = "\x1b[36;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"

    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    LEVEL_COLORS = {
        logging.DEBUG: cyan,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, self.grey)
        formatter = logging.Formatter(
            f"{color}%(asctime)s{self.reset} | {color}%(levelname)-8s{self.reset} | "
            f"{self.blue}%(name)s:%(funcName)s:%(lineno)d{self.reset} - {record.getMessage()}",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        if record.exc_info:
            text = formatter.format(record)
            return text
        return formatter.format(record)


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configures root and application loggers with formatted color logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ColoredFormatter())
    # Ensure logs directory exists
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, 'app.log')
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(file_handler)

    root_logger.addHandler(console_handler)

    # Set appropriate levels for third-party loggers to prevent noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("docling").setLevel(logging.WARNING)

    logger = logging.getLogger("app")
    logger.info("Structured logging framework initialized successfully.")
