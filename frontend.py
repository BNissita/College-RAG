from __future__ import annotations

import html
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


SUPPORTED_FUNCTIONS = ("generate_response", "query", "get_response", "main")
BASE_DIR = Path.cwd().resolve()


def _resolve_backend_file(backend_file: str) -> tuple[Path | None, str | None]:
    input_path = Path(backend_file).expanduser()
    if input_path.is_absolute():
        return None, "Use a relative path inside this project directory."
    file_path = (BASE_DIR / input_path).resolve()
    if BASE_DIR not in file_path.parents and file_path != BASE_DIR:
        return None, "Backend file must be inside the project directory."
    if file_path.suffix != ".py":
        return None, "Backend file must be a .py file."
    return file_path, None


def run_backend(backend_file: str, prompt: str) -> str:
    file_path, error = _resolve_backend_file(backend_file)
    if error:
        return error
    if file_path is None:
        return "Invalid backend file path."
    if not file_path.exists():
        return f"Backend file not found: {file_path}"

    spec = importlib.util.spec_from_file_location("backend_module", file_path)
    if spec is None or spec.loader is None:
        return f"Unable to load backend file: {file_path}"

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for function_name in SUPPORTED_FUNCTIONS:
        function = getattr(module, function_name, None)
        if callable(function):
            try:
                result = function(prompt)
                return str(result)
            except Exception as exc:  # noqa: BLE001
                return f"Backend execution failed: {exc}"

    supported = ", ".join(SUPPORTED_FUNCTIONS)
    return f"No supported function found. Expected one of: {supported}"


def build_page(result: str = "") -> str:
    escaped_result = html.escape(result)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>College RAG Frontend</title>
    <style>
      body {{
        margin: 0;
        font-family: Arial, sans-serif;
        background: #f5f7fb;
        color: #1f2937;
      }}
      .container {{
        max-width: 800px;
        margin: 40px auto;
        padding: 24px;
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
      }}
      h1 {{
        margin-top: 0;
      }}
      label {{
        font-weight: 600;
        display: block;
        margin-bottom: 8px;
      }}
      input, textarea {{
        width: 100%;
        padding: 10px;
        margin-bottom: 16px;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        box-sizing: border-box;
      }}
      button {{
        padding: 10px 16px;
        border: 0;
        border-radius: 6px;
        background: #2563eb;
        color: #fff;
        cursor: pointer;
      }}
      pre {{
        margin-top: 20px;
        padding: 12px;
        border-radius: 6px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        white-space: pre-wrap;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>College RAG Frontend</h1>
      <form id="query-form">
        <label for="backend_file">Python file path</label>
        <input id="backend_file" name="backend_file" value="app.py" required />
        <label for="prompt">Question</label>
        <textarea id="prompt" name="prompt" rows="4" placeholder="Ask a question..." required></textarea>
        <button type="submit">Submit</button>
      </form>
      <pre id="result">{escaped_result}</pre>
    </div>
    <script>
      const form = document.getElementById('query-form');
      const result = document.getElementById('result');
      form.addEventListener('submit', async (event) => {{
        event.preventDefault();
        result.textContent = 'Loading...';
        const payload = {{
          backend_file: document.getElementById('backend_file').value,
          prompt: document.getElementById('prompt').value
        }};
        const response = await fetch('/query', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        const data = await response.json();
        result.textContent = data.result;
      }});
    </script>
  </body>
</html>"""


class FrontendHandler(BaseHTTPRequestHandler):
    def _respond(self, body: str, content_type: str = "text/html", status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self._respond("Not found", "text/plain", 404)
            return
        self._respond(build_page())

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/query":
            self._respond(json.dumps({"result": "Not found"}), "application/json", 404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length)
        try:
            data = json.loads(payload or "{}")
        except json.JSONDecodeError:
            self._respond(json.dumps({"result": "Invalid JSON payload."}), "application/json", 400)
            return
        backend_file = str(data.get("backend_file", "")).strip()
        prompt = str(data.get("prompt", "")).strip()
        result = run_backend(backend_file, prompt) if backend_file and prompt else "Please provide a file path and prompt."
        self._respond(json.dumps({"result": result}), "application/json")


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), FrontendHandler)
    print(f"Frontend running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
