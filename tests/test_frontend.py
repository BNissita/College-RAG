import tempfile
import textwrap
import unittest
from pathlib import Path

from frontend import BASE_DIR, run_backend


class RunBackendTests(unittest.TestCase):
    def _write_backend(self, code: str) -> str:
        temp_dir = tempfile.TemporaryDirectory(dir=BASE_DIR)
        self.addCleanup(temp_dir.cleanup)
        file_path = Path(temp_dir.name) / "backend.py"
        file_path.write_text(textwrap.dedent(code), encoding="utf-8")
        return str(file_path.relative_to(BASE_DIR))

    def test_returns_missing_file_message(self) -> None:
        result = run_backend("does-not-exist.py", "hi")
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

    def test_rejects_absolute_path(self) -> None:
        backend_file = str((BASE_DIR / "backend.py").resolve())
        result = run_backend(backend_file, "hello")
        self.assertIn("Use a relative path", result)

    def test_returns_backend_exception_message(self) -> None:
        backend_file = self._write_backend(
            """
            def query(prompt):
                raise RuntimeError("boom")
            """
        )
        result = run_backend(backend_file, "hello")
        self.assertIn("Backend execution failed: boom", result)


if __name__ == "__main__":
    unittest.main()
