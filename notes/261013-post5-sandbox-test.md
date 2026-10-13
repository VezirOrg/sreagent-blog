# 2026-10-13 — Post 5: sandbox package test (result)

Follows [261013-post5-sandbox-packages.md](261013-post5-sandbox-packages.md) (the docs reading). Two harmless threads
on Post 5's lab agent, 2026-10-13 ~14:45–15:00 UTC. The agent ran every command with its **RunInTerminal** tool.
Verbatim outputs are in the private evidence folder.

| Command | Result |
|---|---|
| `python3 -c "import sys, sqlite3; …"` | ✅ Python 3.12.3, SQLite 3.45.1 |
| `import duckdb` / `import pyarrow` | ✅ both `ModuleNotFoundError`: not preinstalled |
| `import pandas` | ✅ 3.0.2 |
| `pip --version` | ✅ pip 24.0 (Debian's, `/usr/lib/python3/dist-packages`) |
| `pip install --user duckdb` | ✅ refused: `error: externally-managed-environment` (PEP 668, Debian's guard), not a network block |
| `subprocess.run(['echo', …])` | ✅ works |
| `python3 -m venv /tmp/p5venv` then `/tmp/p5venv/bin/pip install duckdb` | ✅ **installed duckdb 1.5.6 from PyPI** (21.6 MB wheel); `duckdb.sql('select 42')` returned `[(42,)]` |
| `urllib.request.urlopen('https://pypi.org/simple/duckdb/')` | ✅ HTTP 200 |

## Against the docs (D52: list, Emre decides)

1. [code-interpreter](https://learn.microsoft.com/azure/sre-agent/code-interpreter) says `pip install` is not
   available, outbound HTTP is blocked and `subprocess` is blocked. In the agent's terminal tool on this lab, a
   virtual environment installed a package from PyPI, PyPI answered, and `subprocess` ran. The doc page describes
   the code interpreter (`ExecutePythonCode`, a Container Apps session); the tool used here was RunInTerminal. They
   may be two different sandboxes, but the page does not say so.
2. [security-overview](https://learn.microsoft.com/azure/sre-agent/security-overview): "doesn't support arbitrary
   package installation". The system pip refuses (PEP 668), but a venv pip installs.

Not concluded: whether the venv install survives between threads (Learn: a fresh process per tool call), and whether
this works the same without the lab's network setup. The skill does not rely on it: D80 keeps SQLite and the
standard library.
