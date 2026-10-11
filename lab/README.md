# lab/ — test-side tools for the PerfMon triage skill

The `perfmon-triage` skill takes raw PerfMon CSV files and converts them to SQLite itself
(`tools/perfmon_csv_to_sqlite.py`, shipped with the skill). Masking is **not** part of the skill. It is the first
step of every lab test, done here, before anything reaches the skill or the agent.

## Step 0 of every test: mask the CSV

```sh
python3 -I lab/perfmon_mask_csv.py capture.csv mapping.csv capture-masked.csv --denylist denylist.txt
```

- `mapping.csv` has two columns with a header row: `real,placeholder`, one row per name to hide (hosts, app pools,
  sites, queues, services, agents, products). It is private: never in this repository, a prompt or the storage.
  Keep it permanently; it is the only way back to the real names.
- Match rule (rule b): case-insensitive, longer names first. A name of 5 or more characters is replaced wherever it
  occurs, also inside a longer token; a shorter name only as a whole word (no letter or digit right before or after
  it), so it cannot change ordinary words or counter and object names. An all-lowercase occurrence gets the
  lowercase placeholder. It runs over every line (header and data). The output is UTF-8.
- `denylist.txt` (required) is the private list of every real name ever seen in these captures, one per line. A
  mapping covers one batch of captures; the denylist covers them all, so a name the batch's mapping missed is still
  caught.
- The tool fails (exit 1) if any mapping name or any denylist name is still in the output under the same rule. It
  prints counts and line numbers only, never a name. If it fails, nothing is uploaded: add the missing name to a
  new dated mapping (never edit an old one) and mask again.
- Name the masked file neutrally (`srv02-masked.csv`, not the original file name, which may carry a host name).

Then hand **only the masked CSV** to the skill: upload it where the agent can read it, or give its path to a local
test. Several CSV parts of one capture are masked one by one with the same mapping.

## Other tools

- `perfmon_mask_db.py`: the earlier masking step, which worked on a database built from an unmasked CSV. It is kept
  to rebuild the databases of tests run before the CSV masking step existed. New tests mask the CSV. It uses the same
  rule b; its extra raw-byte scan of the database file can still hit a name by chance in binary data, and on failure
  it names the mapping row, the name's length and where the hit is (never the name).
