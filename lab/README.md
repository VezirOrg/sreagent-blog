# lab/ — test-side tools for the PerfMon triage skill

The `perfmon-triage` skill takes raw PerfMon CSV files and converts them to SQLite itself
(`tools/perfmon_csv_to_sqlite.py`, shipped with the skill). Masking is **not** part of the skill. It is the first
step of every lab test, done here, before anything reaches the skill or the agent.

## Step 0 of every test: mask the CSV

```sh
python3 -I lab/perfmon_mask_csv.py capture.csv mapping.csv capture-masked.csv
```

- `mapping.csv` has two columns with a header row: `real,placeholder`, one row per name to hide (hosts, app pools,
  sites, queues, services, agents, products). It is private: never in this repository, a prompt or the storage.
  Keep it permanently; it is the only way back to the real names.
- Match rule: case-insensitive, every occurrence, longer names first; an all-lowercase occurrence gets the lowercase
  placeholder. It runs over every line (header and data). The output is UTF-8.
- The tool fails (exit 1) if any real name is still in the output. It prints counts only, never a name.
- Name the masked file neutrally (`srv02-masked.csv`, not the original file name, which may carry a host name).

Then hand **only the masked CSV** to the skill: upload it where the agent can read it, or give its path to a local
test. Several CSV parts of one capture are masked one by one with the same mapping.

## Other tools

- `perfmon_mask_db.py`: the earlier masking step, which worked on a database built from an unmasked CSV. It is kept
  to rebuild the databases of tests run before the CSV masking step existed. New tests mask the CSV.
