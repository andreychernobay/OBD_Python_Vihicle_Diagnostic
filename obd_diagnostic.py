"""OBD-II diagnostic tool CLI.

Provides options to check DTCs, clear DTCs and read live data.
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable, List, Optional, Tuple

try:
    import obd
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "The 'python-obd' package is required to run this script. "
        "Install it with 'pip install python-obd'"
    ) from exc


class OBDDiagnosticError(RuntimeError):
    """Raised when a diagnostic operation fails."""


class OBDDiagnosticTool:
    """Wrapper around :mod:`python-obd` for common diagnostic tasks."""

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
        fast: bool = False,
        timeout: Optional[float] = None,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._fast = fast
        self._timeout = timeout
        self._connection: Optional[obd.OBD] = None

    def connect(self) -> None:
        """Establish a connection to the OBD-II adapter."""
        if self._connection is not None and self._connection.is_connected():
            return

        kwargs = {
            "portstr": self._port,
            "baudrate": self._baudrate,
            "fast": self._fast,
        }
        if self._timeout is not None:
            kwargs["timeout"] = self._timeout

        connection = obd.OBD(**kwargs)
        if not connection.is_connected():
            raise OBDDiagnosticError(
                "Failed to connect to the OBD-II adapter. "
                "Check the port and that the adapter is powered."
            )

        self._connection = connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> obd.OBD:
        if self._connection is None or not self._connection.is_connected():
            raise OBDDiagnosticError("No active OBD-II connection. Call connect() first.")
        return self._connection

    def check_dtcs(self) -> List[Tuple[str, str]]:
        """Return the list of current Diagnostic Trouble Codes (DTCs)."""
        response = self.connection.query(obd.commands.GET_DTC)
        if response.is_null():
            return []
        return response.value  # type: ignore[return-value]

    def erase_dtcs(self) -> None:
        """Clear Diagnostic Trouble Codes from the ECU."""
        response = self.connection.query(obd.commands.CLEAR_DTC)
        if response.is_null() or not response.is_success():
            raise OBDDiagnosticError("Failed to clear DTCs from the ECU.")

    def iter_live_data(self) -> Iterable[Tuple[str, Optional[str]]]:
        """Yield (command name, string value) for supported live-data sensors."""
        for command in sorted(self.connection.supported_commands, key=lambda c: c.name):
            # Mode 1 contains current data, Mode 2 freeze frame data. Include both.
            if command.mode not in {1, 2}:
                continue
            if command == obd.commands.GET_DTC or command == obd.commands.CLEAR_DTC:
                continue

            response = self.connection.query(command)
            if response.is_null():
                value = None
            else:
                value = str(response.value)
            yield command.name, value


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OBD-II diagnostic tool")
    parser.add_argument("--port", help="Serial port of the OBD-II adapter", default=None)
    parser.add_argument("--baudrate", type=int, help="Serial baudrate", default=None)
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use fast initialization (may not be supported by all adapters)",
    )
    parser.add_argument("--timeout", type=float, help="Connection timeout in seconds")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check", help="Read current Diagnostic Trouble Codes")
    subparsers.add_parser("erase", help="Erase Diagnostic Trouble Codes")

    live_parser = subparsers.add_parser("live", help="Read live data from sensors")
    live_parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Delay between consecutive live data refreshes (seconds)",
    )
    live_parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of refresh iterations for live data (0 for infinite)",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    tool = OBDDiagnosticTool(
        port=args.port, baudrate=args.baudrate, fast=args.fast, timeout=args.timeout
    )

    try:
        tool.connect()
        if args.command == "check":
            dtcs = tool.check_dtcs()
            if not dtcs:
                print("No Diagnostic Trouble Codes reported.")
            else:
                for code, description in dtcs:
                    print(f"{code}: {description}")
        elif args.command == "erase":
            tool.erase_dtcs()
            print("Diagnostic Trouble Codes cleared successfully.")
        elif args.command == "live":
            iteration = 0
            while True:
                print("\nLive sensor data:")
                for name, value in tool.iter_live_data():
                    if value is None:
                        value = "No data"
                    print(f"  {name}: {value}")
                iteration += 1
                if args.iterations > 0 and iteration >= args.iterations:
                    break
                time.sleep(max(args.interval, 0.1))
    except OBDDiagnosticError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        tool.close()

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
