"""Local-only chat logging helpers built on top of ``minescript.echo``."""

from __future__ import annotations

import traceback

import minescript


class LogController:
    """Emit logs only to the local player's chat.

    This controller deliberately uses ``minescript.echo`` instead of ``chat`` so
    messages stay private to the local player and never get sent to public chat.
    """

    def __init__(self, *, tag: str = "mc", debug_enabled: bool = False):
        """Create a local chat logger.

        Args:
            tag: Short prefix shown in each log line.
            debug_enabled: Whether ``debug(...)`` messages should be emitted.
        """
        self.tag = str(tag)
        self.debug_enabled = bool(debug_enabled)

    def log(self, *parts, level: str = "INFO"):
        """Emit a log line to the local player's chat only."""
        prefix = f"[{self.tag}:{level}]"
        minescript.echo(prefix, *[str(part) for part in parts])

    def info(self, *parts):
        """Emit an informational message."""
        self.log(*parts, level="INFO")

    def warn(self, *parts):
        """Emit a warning message."""
        self.log(*parts, level="WARN")

    def error(self, *parts):
        """Emit an error message."""
        self.log(*parts, level="ERROR")

    def debug(self, *parts):
        """Emit a debug message when ``debug_enabled`` is true."""
        if self.debug_enabled:
            self.log(*parts, level="DEBUG")

    def exception(self, exc: BaseException, *parts):
        """Emit an error message followed by the exception type and message."""
        if parts:
            self.error(*parts)
        self.error(f"{type(exc).__name__}: {exc}")

    def traceback(self, exc: BaseException, *parts):
        """Emit a short traceback to the local player's chat only."""
        if parts:
            self.error(*parts)
        for line in traceback.format_exception(type(exc), exc, exc.__traceback__):
            for chunk in line.rstrip().splitlines():
                if chunk:
                    self.error(chunk)


__all__ = ["LogController"]
