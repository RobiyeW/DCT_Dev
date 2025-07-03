import unittest
from unittest.mock import MagicMock, patch
from test_runner import TestRunner
from unittest.mock import patch, MagicMock, PropertyMock

"""
Unit tests for the TestRunner class.
These tests cover the connection, command sending, response receiving, and disconnection functionalities.
"""

class TestTestRunner(unittest.TestCase):

    @patch('serial.Serial')
    def test_connect_success(self, mock_serial):
        # Arrange
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance

        runner = TestRunner(port='COM_TEST', baudrate=9600)

        # Act
        runner.connect()

        # Assert
        mock_serial.assert_called_with(
            port='COM_TEST',
            baudrate=9600,
            timeout=2
        )
        mock_instance.flushInput.assert_called_once()
        self.assertTrue(runner.is_connected())

    @patch('serial.Serial')
    def test_send_command(self, mock_serial):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance
        mock_instance.read_all.return_value = b"OK\n"

        runner = TestRunner(port='COM_TEST')
        runner.connect()

        # Act
        response = runner.send_command("TEST")

        # Assert
        mock_instance.write.assert_called_with(b"TEST\n")
        self.assertEqual(response, "OK")

    @patch('serial.Serial')
    def test_receive_response(self, mock_serial):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance

        # PropertyMock to simulate .in_waiting changing
        type(mock_instance).in_waiting = PropertyMock(side_effect=[1] + [0]*10)

        mock_instance.read_all.return_value = b"RESPONSE\n"

        runner = TestRunner()
        runner.connect()

        # Act
        response = runner.receive_response(timeout=1)

        # Assert
        self.assertEqual(response, "RESPONSE")

    @patch('serial.Serial')
    def test_close_connection(self, mock_serial):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance

        runner = TestRunner()
        runner.connect()

        # Act
        runner.close_connection()

        # Assert
        mock_instance.close.assert_called_once()

    @patch('serial.Serial')
    def test_is_connected_false(self, mock_serial):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.is_open = False
        mock_serial.return_value = mock_instance

        runner = TestRunner()
        runner.connect()

        # Act / Assert
        self.assertFalse(runner.is_connected())


if __name__ == '__main__':
    unittest.main()
