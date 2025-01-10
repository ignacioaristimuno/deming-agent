from logging import Logger, Formatter, StreamHandler
from logging import getLogger
from logging import DEBUG


def custom_logger(logger_name: str) -> Logger:
    """
    Create and configure a logger with a specified name.

    This function initializes a logger with the given name, sets its logging level
    to DEBUG, and configures a StreamHandler with a specific format for log messages.
    If the logger does not already have handlers, a new StreamHandler is added.
    The logger's propagation is disabled to prevent logs from being passed to ancestor loggers.

    Args:
        logger_name (str): The name to assign to the logger.

    Returns:
        Logger: A configured logger instance with the specified name.
    """

    logger = getLogger(f"{logger_name} - ")
    logger.setLevel(DEBUG)
    if not logger.hasHandlers():
        console_handler = StreamHandler()
        console_handler.setLevel(DEBUG)
        formatter = Formatter(
            "%(asctime)s - %(name)s%(levelname)s: %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S%p",
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    logger.propagate = False
    return logger
