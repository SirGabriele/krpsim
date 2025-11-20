import unittest

from contextlib import redirect_stderr
from io import StringIO
from unittest.mock import patch

from krpsim import main
from parsing.parser import parse


class TestParser(unittest.TestCase):

    @patch('sys.argv', ['krpsim.py', 'non_existing_file.txt', '0'])
    def test_main_non_existing_file(self):
        # Given
        # Redirects the output into a variable
        captured_output = StringIO()
        expected = (
            "usage: python3.10 krpsim.py <input_file> <delay>\n"
            f"krpsim.py: error: argument input_file: File 'non_existing_file.txt' does not exist"
        )

        # When
        with self.assertRaises(SystemExit) as cm:
            with redirect_stderr(captured_output):
                main()
        actual = captured_output.getvalue().strip()

        # Then
        self.assertEqual(actual, expected)

    @patch('sys.argv', ['krpsim.py', 'resources/simple', 'delay'])
    def test_main_invalid_delay(self):
        # Given
        # Redirects the output into a variable
        captured_output = StringIO()
        expected = (
            "usage: python3.10 krpsim.py <input_file> <delay>\n"
            f"krpsim.py: error: argument delay: invalid int value: 'delay'"
        )

        # When
        with self.assertRaises(SystemExit) as cm:
            with redirect_stderr(captured_output):
                main()
        actual = captured_output.getvalue().strip()

        # Then
        self.assertEqual(actual, expected)

    def test_parse_file_not_found_should_raise_file_not_found_error(self):
        # Given
        non_existing_file_name = "non-existing-file"
        delay = 0

        # When
        with self.assertRaises(FileNotFoundError) as cm:
            parse(non_existing_file_name, delay)

        # Then
        self.assertIn(
            f"No such file or directory: '{non_existing_file_name}'",
            str(cm.exception)
        )

    def test_parse_delay_wrong_type_should_raise_type_error(self):
        # Given
        non_existing_file_name = "non-existing-file"
        badly_typed_delay = "delay"

        # When
        with self.assertRaises(TypeError) as cm:
            parse(non_existing_file_name, badly_typed_delay)

        # Then
        self.assertIn(
            "delay must be an integer.",
            str(cm.exception)
        )


if __name__ == "__main__":
    unittest.main()
