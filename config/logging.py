from __future__ import annotations

import logging

from colorama import Fore, Style


class VivaceFormatter(logging.Formatter):
    """Custom log message formatter."""

    template = "[{levelname}][{asctime}][{name}][{module}][{lineno}][{process:d}][{thread:d}]|{message}"

    def get_template(self, record: logging.LogRecord) -> str:
        """Get log message template."""
        return self.template

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        """Format log message."""
        log_fmt = self.get_template(record)
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)


class ColoramaFormatter(VivaceFormatter):
    """Add color to log messages based on log level."""

    def get_template(self, record: logging.LogRecord) -> str:
        """Add color to log messages based on log level."""
        config = {
            logging.CRITICAL: Fore.RED,
            logging.ERROR: Fore.MAGENTA,
            logging.WARNING: Fore.YELLOW,
            logging.INFO: Fore.GREEN,
            logging.DEBUG: Fore.WHITE,
        }

        if record.levelno in config:
            # build template
            return f"{config[record.levelno]}{self.template}{Style.RESET_ALL}"
        return super().get_template(record)
