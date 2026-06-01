from __future__ import annotations

import argparse
import asyncio
import logging

from . import __version__
from .app import DXClusterApp
from .config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rbn-dxcluster")
    parser.add_argument("--version", action="version", version=f"rbn-dxcluster {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="run the Telnet DX Cluster server")
    serve.add_argument("--config", default="config/config.example.yaml")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "serve":
        config = load_config(args.config)
        logging.basicConfig(
            level=getattr(logging, config.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        asyncio.run(DXClusterApp(config).run())
