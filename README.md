# College-RAG

## Frontend

This repository now includes a minimal web frontend in `frontend.py`.

Run it with:

```bash
python frontend.py
```

Open `http://127.0.0.1:8000` and provide:

- `Python file`: select a backend `.py` file discovered inside this project
- `Question`: user prompt

The frontend will load the provided file and call the first supported function found:
`generate_response`, `query`, `get_response`, or `main`.
