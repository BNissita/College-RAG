# College-RAG

## Frontend

This repository now includes a minimal web frontend in `/home/runner/work/College-RAG/College-RAG/frontend.py`.

Run it with:

```bash
python frontend.py
```

Open `http://127.0.0.1:8000` and provide:

- `Python file path`: path to your backend `.py` file
- `Question`: user prompt

The frontend will load the provided file and call the first supported function found:
`generate_response`, `query`, `get_response`, or `main`.
