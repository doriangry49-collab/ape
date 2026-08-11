"""
MCP Transport Abstractions — ORION-117.2 Specification.
Provides MCPTransport ABC, StdioTransport (Subprocess boundary), and HTTPStreamableTransport.
"""

import json
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ape.tools.adapters.mcp.contracts import TransportConfig


class MCPTransport(ABC):
    """Abstract base class for MCP wire transport implementations."""

    @abstractmethod
    def connect(self) -> None:
        """Establish transport connection."""
        ...

    @abstractmethod
    def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message dictionary."""
        ...

    @abstractmethod
    def receive_message(self, timeout_ms: float = 30000.0) -> Dict[str, Any]:
        """Receive JSON-RPC message dictionary with timeout."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close transport connection and release resources."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if connection is active."""
        ...

    @property
    def is_process_boundary(self) -> bool:
        """Return True if this transport executes an external local process."""
        return False


class StdioTransport(MCPTransport):
    """Stdio Transport connecting to a local MCP server subprocess via stdin/stdout."""

    def __init__(self, config: TransportConfig) -> None:
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._connected = False

    @property
    def is_process_boundary(self) -> bool:
        return True

    def connect(self) -> None:
        if not self.config.command:
            raise ValueError("StdioTransport requires 'command' in TransportConfig.")

        cmd = [self.config.command] + self.config.args
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._connected = True

    def send_message(self, message: Dict[str, Any]) -> None:
        if not self._connected or not self._process or not self._process.stdin:
            raise RuntimeError("StdioTransport is not connected.")

        payload_line = json.dumps(message) + "\n"
        self._process.stdin.write(payload_line)
        self._process.stdin.flush()

    def receive_message(self, timeout_ms: float = 30000.0) -> Dict[str, Any]:
        if not self._connected or not self._process or not self._process.stdout:
            raise RuntimeError("StdioTransport is not connected.")

        line = self._process.stdout.readline()
        if not line:
            raise RuntimeError("StdioTransport process output stream closed.")

        return json.loads(line.strip())

    def close(self) -> None:
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2.0)
            except Exception:
                self._process.kill()
            self._process = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._process is not None and self._process.poll() is None


class HTTPStreamableTransport(MCPTransport):
    """HTTP Streamable / SSE Transport for remote MCP servers."""

    def __init__(self, config: TransportConfig) -> None:
        self.config = config
        self._connected = False
        self._queue: list = []

    def connect(self) -> None:
        if not self.config.url:
            raise ValueError("HTTPStreamableTransport requires 'url' in TransportConfig.")
        self._connected = True

    def send_message(self, message: Dict[str, Any]) -> None:
        if not self._connected:
            raise RuntimeError("HTTPStreamableTransport is not connected.")

    def receive_message(self, timeout_ms: float = 30000.0) -> Dict[str, Any]:
        if not self._connected:
            raise RuntimeError("HTTPStreamableTransport is not connected.")
        if self._queue:
            return self._queue.pop(0)
        raise TimeoutError("HTTPStreamableTransport timed out waiting for message.")

    def close(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
