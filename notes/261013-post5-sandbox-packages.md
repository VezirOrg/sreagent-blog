# 2026-10-13 — Post 5: can the SRE Agent sandbox install Python packages?

Question from Emre (D80): can the agent's sandbox run `pip install duckdb` / `pyarrow`, or only use what is
preinstalled? Docs first (this note); the test comes when an agent exists.

## What Learn says (seen 2026-10-13)

Learn describes three places where the agent runs Python, and they do not say the same thing:

| Where | Install at run time? | Source |
|---|---|---|
| Code interpreter (`ExecutePythonCode`, `RunShellCommand`), an Azure Container Apps session | No: "`pip install` and `conda install` aren't available"; no outbound HTTP; `subprocess`/`os.system` blocked; files only in `/mnt/data/`. pandas, matplotlib, seaborn preinstalled. | [code-interpreter](https://learn.microsoft.com/azure/sre-agent/code-interpreter) 📄 |
| The agent's sandbox in general (a micro VM per agent) | "more than 700 preinstalled Python packages, but it doesn't support arbitrary package installation"; an egress proxy limits network access to known service domains. | [security-overview](https://learn.microsoft.com/azure/sre-agent/security-overview) 📄 |
| Python tools (custom tools) | Outbound connectivity enabled; 700+ preinstalled (pandas, requests, azure-identity, reportlab, …); a fresh container per call. | [python-code-execution](https://learn.microsoft.com/azure/sre-agent/python-code-execution) 📄 |
| Workspace configuration → **Packages** tab | An admin adds a pip (or NuGet .NET tool) package with an optional version; it is **preinstalled in the sandbox base image**, so it is there on every run. In Azure VNet mode a "Package manager access" toggle (or an FQDN rule) lets PyPI traffic out. | [network-integration](https://learn.microsoft.com/azure/sre-agent/network-integration#preinstalled-packages) 📄 |

Reading of the docs: the agent itself cannot `pip install` during a conversation; a package the skill needs is
added ahead of time by an admin in the Packages tab. That is a docs reading, not a result yet.

What we already know from our own runs (Post 4, 2026-10-09 lab log): the agent's terminal has `python3` with the
standard `sqlite3` module, and a skill's supporting files are real files there. That is why D80 picks SQLite and CSV.

## Test to run when an agent exists (harmless, read-only)

1. In a new thread: `python3 -c "import duckdb"`, `python3 -c "import pyarrow"`, `python3 -c "import sqlite3,
   sys; print(sqlite3.sqlite_version, sys.version)"`, and `pip --version`.
2. `pip install --user duckdb` (expect a refusal or a network error; record the exact text).
3. Optional, only with Emre's go: add `duckdb` in Workspace configuration → Packages, then repeat step 1.

Every result gets ✅ with the date, or stays 📄 (D44). If a test contradicts a doc line, the conflict goes to Emre
(D52).
