# test_runner.py
import time
import serial
from serial import SerialException, SerialTimeoutException
from serial.tools import list_ports


class TestRunner:
    """
    Manage serial comms with the DCT MCU.

    Key behaviors for GUI use:
      - available_ports(): enumerate ports for a dropdown
      - connect(port, baudrate): open with a short read timeout for smooth polling
      - send_command(cmd): appends '\n' if missing
      - receive_response(): RETURN ONE LINE or None (non-blocking-ish, obeys short timeout)
      - close_connection(): safe teardown
    """

    def __init__(self, port='COM3', baudrate=9600, timeout=0.05):
        """
        :param port: default serial port (string)
        :param baudrate: default baud (int)
        :param timeout: read timeout in seconds (keep small for GUI polling)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout  # keep small (e.g., 0.02–0.1) so GUI stays responsive
        self.ser = None

    # ---------- Port discovery ----------
    @staticmethod
    def available_ports():
        """
        Returns: list[(device, description)] e.g. [("COM4", "Arduino Uno"), ...]
        """
        out = []
        try:
            for p in list_ports.comports():
                out.append((p.device, p.description or ""))
        except Exception:
            pass
        return out

    # ---------- Connection control ----------
    def connect(self, port=None, baudrate=None, timeout=None):
        """
        Open the serial port with given settings (overrides the defaults if provided).
        """
        if port is not None:
            self.port = port
        if baudrate is not None:
            self.baudrate = baudrate
        if timeout is not None:
            self.timeout = timeout

        self.close_connection()
        try:
            self.ser = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,       # short read timeout for polling
                write_timeout=0.25,         # short write timeout
                exclusive=True              # prevent multiple opens where supported
            )
            # Give the MCU a moment to settle after opening the port.
            time.sleep(0.2)
            # Clear any stale bytes
            try:
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
            except Exception:
                pass
            return True
        except Exception as e:
            self.ser = None
            # Let caller surface this in the GUI
            raise

    def is_connected(self):
        return (self.ser is not None) and self.ser.is_open

    def __del__(self):
        try:
            self.close_connection()
        except Exception:
            pass  # best-effort during GC

    def close_connection(self):
        if self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception:
                pass
        self.ser = None

    # ---------- I/O ----------
    def send_command(self, command: str) -> bool:
        """
        Send a single-line command. A trailing newline is appended if missing.

        Returns True on success, False on failure.
        """
        if not self.is_connected():
            return False
        try:
            line = command if command.endswith("\n") else (command + "\n")
            self.ser.write(line.encode("utf-8"))
            self.ser.flush()
            return True
        except (SerialTimeoutException, SerialException, OSError):
            return False

    def receive_response(self):
        """
        Non-blocking-ish: return ONE complete line (without trailing CR/LF) or None.
        Uses the serial port's timeout; keep it small for smooth GUI polling.
        """
        if not self.is_connected():
            return None
        try:
            raw = self.ser.readline()  # reads up to '\n' or until timeout
            if not raw:
                return None
            # Normalize line endings and decode safely
            return raw.decode("utf-8", errors="ignore").rstrip("\r\n")
        except (SerialException, OSError, UnicodeDecodeError):
            return None

    # Optional helper if you want to drain multiple lines in one tick
    def receive_lines(self, max_lines: int = 50):
        """
        Read up to max_lines lines quickly. Returns list[str].
        """
        lines = []
        for _ in range(max_lines):
            line = self.receive_response()
            if not line:
                break
            lines.append(line)
        return lines
