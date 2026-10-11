#!/usr/bin/env python3
"""Mask names in a PerfMon SQLite database made by perfmon_csv_to_sqlite.py, writing a new database.

PerfMon counter paths carry real names: app pools, sites, queues, services, agents, products. This tool replaces
each one with a neutral placeholder from a private mapping file, so the masked database can be shared or analysed.

  mapping.csv   two columns with a header row: real,placeholder  (e.g. MyPaymentsPool,AppPool1)
                Kept private: it is the key back to the real names.

Match rule (D68, rule b; shared with perfmon_mask_csv.py), on counters.path, host, object, instance and
base_instance: case-insensitive, longer names first; a name of MIN_LEN (5) or more characters is replaced wherever
it occurs, a shorter name only as a whole word (no letter or digit right before or after it). An all-lowercase
occurrence gets the lowercase placeholder. meta.source_file is replaced by the masked file name. Index statistics
are rebuilt and the file is vacuumed. The tool then fails if any real name is still present under the same rule,
in the tables or anywhere in the file's raw bytes (case-insensitive).

Python standard library only. Usage:
  python3 perfmon_mask_db.py capture.db mapping.csv capture-masked.db [--force]
"""
import argparse
import csv
import os
import re
import shutil
import sqlite3
import sys

SUFFIX_RE = re.compile(r'#\d+$')


def load_mapping(path):
    with open(path, encoding='utf-8', newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('real')]
    rows.sort(key=lambda r: -len(r['real']))
    return [(r['real'], r['placeholder']) for r in rows]


MIN_LEN = 5


def name_pattern(real, min_len=MIN_LEN):
    """Rule b (D68): long names match anywhere; short names only as a whole word."""
    if len(real) >= min_len:
        return re.escape(real)
    return r'(?<![A-Za-z0-9])' + re.escape(real) + r'(?![A-Za-z0-9])'


def masker(mapping):
    pats = [(re.compile(name_pattern(real), re.IGNORECASE), ph) for real, ph in mapping]

    def mask(s):
        if s is None:
            return None
        for pat, ph in pats:
            s = pat.sub(lambda m: ph.lower() if m.group(0).islower() else ph, s)
        return s
    return mask


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('db')
    ap.add_argument('mapping')
    ap.add_argument('out')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if os.path.exists(a.out):
        if not a.force:
            sys.exit(f'{a.out} exists; use --force')
        os.remove(a.out)
    mapping = load_mapping(a.mapping)
    mask = masker(mapping)
    shutil.copyfile(a.db, a.out)
    db = sqlite3.connect(a.out)
    changed = 0
    for cid, path, host, obj, inst in db.execute('SELECT counter_id, path, host, object, instance FROM counters').fetchall():
        new = (mask(path), mask(host), mask(obj), mask(inst))
        if new != (path, host, obj, inst):
            changed += 1
            base = SUFFIX_RE.sub('', new[3]) if new[3] is not None else None
            db.execute('UPDATE counters SET path=?, host=?, object=?, instance=?, base_instance=? WHERE counter_id=?',
                       (*new, base, cid))
    db.execute("UPDATE meta SET value=? WHERE key='source_file'", (os.path.basename(a.out),))
    db.execute("INSERT OR REPLACE INTO meta VALUES ('masked', 'yes: names replaced by placeholders')")
    db.commit()
    # index statistics (sqlite_stat1/stat4) hold sampled keys: rebuild them from the masked data
    db.execute('ANALYZE')
    db.commit()
    # verify: no real name left anywhere in text columns
    left = []
    texts = [t for row in db.execute('SELECT path, host, object, instance, base_instance FROM counters') for t in row if t]
    texts += [v for (v,) in db.execute('SELECT value FROM meta') if v]
    for real, _ in mapping:
        pat = re.compile(name_pattern(real), re.IGNORECASE)
        n = sum(1 for t in texts if pat.search(t))
        if n:
            left.append((real, f'{n} text values'))
    db.execute('VACUUM')
    db.close()
    # verify again on the raw bytes of the file (free pages, indexes, statistics)
    with open(a.out, 'rb') as f:
        raw = f.read()
    left += [(real, 'raw bytes') for real, _ in mapping
             if re.search(name_pattern(real).encode(), raw, re.IGNORECASE)]
    print(f'mapping entries: {len(mapping)}; counters changed: {changed}')
    if left:
        with open(a.mapping, encoding='utf-8', newline='') as f:  # data row number in the mapping file
            rows = {r['real']: i for i, r in enumerate(csv.DictReader(f), start=1)}
        print(f'FAILED: {len(left)} real names still present (names not printed): ' +
              '; '.join(f'mapping row {rows[r]} (length {len(r)}): {where}' for r, where in left))
        sys.exit(1)
    print('verify: no real name left')


if __name__ == '__main__':
    main()
