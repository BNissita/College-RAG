import tempfile
import textwrap
import unittest
from pathlib import Path

from frontend import run_backend


class RunBackendTests(unittest.TestCase):
    def _write_backend(self, code: str) -> str:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        file_path = Path(temp_dir.name) / "backend.py"
        file_path.write_text(textwrap.dedent(code), encoding="utf-8")
        return str(file_path)

    def test_returns_missing_file_message(self) -> None:
        result = run_backend("/tmp/does-not-exist.py", "hi")
        self.assertIn("Backend file not found:", result)

    def test_calls_supported_function(self) -> None:
        backend_file = self._write_backend(
            """
            def query(prompt):
                return f"answer:{prompt}"
            """
        )
        self.assertEqual(run_backend(backend_file, "hello"), "answer:hello")

    def test_returns_message_when_no_supported_function(self) -> None:
        backend_file = self._write_backend(
            """
            def something_else(prompt):
                return prompt
            """
        )
        result = run_backend(backend_file, "hello")
        self.assertIn("No supported function found", result)


if __name__ == "__main__":
    unittest.main()
