# -*- coding: utf-8 -*-
"""In-process scheduler for the long-running dashboard."""

from __future__ import unicode_literals

import logging
import threading
import time

try:
    text_type = unicode  # type: ignore[name-defined]
except NameError:
    text_type = str


MINUTE_SECONDS = 60


class WebScheduler(object):
    """Run one guarded synchronization at a fixed interval."""

    def __init__(self, callback, interval=5, enabled=True, guard=None, logger=None):
        # type: (object, int, bool, object | None, logging.Logger | None) -> None
        self._callback = callback
        self._guard = guard
        self._logger = (logger or logging.getLogger()).getChild("scheduler")
        self._condition = threading.Condition()
        self._clock = getattr(time, "monotonic", time.time)
        self._interval = self._validate_interval(interval)
        self._enabled = bool(enabled)
        self._thread = None
        self._stopping = False
        self._running = False
        self._next_run = None
        self._last_run = None
        self._last_error = None
        self._blocked_reason = None

    @staticmethod
    def _validate_interval(interval):
        # type: (object) -> int
        if isinstance(interval, bool):
            raise ValueError("Web scheduler interval must be a positive integer.")
        try:
            parsed = int(interval)
        except (TypeError, ValueError):
            raise ValueError("Web scheduler interval must be a positive integer.")
        if isinstance(interval, float) and interval != parsed:
            raise ValueError("Web scheduler interval must be a positive integer.")
        if parsed < 1 or parsed > 1440:
            raise ValueError("Web scheduler interval must be between 1 and 1440 minutes.")
        return parsed

    def _schedule_next_locked(self):
        # type: () -> None
        self._next_run = (
            self._clock() + self._interval * MINUTE_SECONDS if self._enabled and self._thread is not None else None
        )

    def start(self):
        # type: () -> None
        """Start the scheduler thread without running an immediate synchronization."""
        with self._condition:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stopping = False
            self._running = False
            self._blocked_reason = None
            self._thread = threading.Thread(target=self._run, name="ddns-web-scheduler")
            self._thread.daemon = True
            self._schedule_next_locked()
            self._thread.start()

    def stop(self):
        # type: () -> None
        """Stop scheduling and wait for an active synchronization to finish."""
        with self._condition:
            thread = self._thread
            if thread is None:
                return
            self._stopping = True
            self._condition.notify_all()
        thread.join()
        with self._condition:
            self._thread = None
            self._running = False
            self._next_run = None
            self._stopping = False

    def configure(self, enabled=None, interval=None):
        # type: (bool | None, int | None) -> dict
        """Update the persistent intent and re-arm the next run."""
        if interval is not None:
            interval = self._validate_interval(interval)
        with self._condition:
            if interval is not None:
                self._interval = interval
            if enabled is not None:
                self._enabled = bool(enabled)
            self._blocked_reason = None
            self._schedule_next_locked()
            self._condition.notify_all()
        return self.status()

    def status(self):
        # type: () -> dict
        """Return a JSON-safe scheduler status snapshot."""
        with self._condition:
            active = self._thread is not None and self._thread.is_alive()
            next_run = None
            if self._next_run is not None:
                remaining = max(0, self._next_run - self._clock())
                next_run = time.time() + remaining
            return {
                "scheduler": "web",
                "installed": True,
                "active": active,
                "enabled": self._enabled,
                "running": self._running,
                "interval": self._interval,
                "next_run": next_run,
                "last_run": self._last_run,
                "last_error": self._last_error,
                "blocked_reason": self._blocked_reason,
            }

    def _guard_allows_run(self):
        # type: () -> tuple[bool, str | None]
        if self._guard is None:
            return True, None
        try:
            result = self._guard()
        except Exception as error:
            self._logger.exception("Cannot verify whether automatic synchronization may run")
            return False, text_type(error)
        if isinstance(result, tuple):
            return bool(result[0]), result[1]
        return bool(result), None if result else "Automatic synchronization is blocked."

    def _run(self):
        # type: () -> None
        while True:
            with self._condition:
                while not self._stopping:
                    if not self._enabled:
                        self._next_run = None
                        self._condition.wait()
                        continue
                    if self._next_run is None:
                        self._schedule_next_locked()
                    delay = self._next_run - self._clock()
                    if delay > 0:
                        self._condition.wait(delay)
                        continue
                    break
                if self._stopping:
                    return

            allowed, reason = self._guard_allows_run()
            with self._condition:
                if self._stopping:
                    return
                if not self._enabled:
                    continue
                if not allowed:
                    self._blocked_reason = reason
                    self._schedule_next_locked()
                    continue
                self._blocked_reason = None
                self._running = True

            error_message = None
            try:
                self._callback()
            except Exception as error:
                error_message = text_type(error)
                self._logger.exception("Scheduled dashboard synchronization failed")
            finally:
                with self._condition:
                    self._running = False
                    self._last_run = time.time()
                    self._last_error = error_message
                    self._schedule_next_locked()
                    self._condition.notify_all()
