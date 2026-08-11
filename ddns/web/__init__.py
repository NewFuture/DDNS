# -*- coding: utf-8 -*-
"""Embedded DDNS management dashboard."""

from .server import create_server, serve
from .service import DashboardService

__all__ = ["DashboardService", "create_server", "serve"]
