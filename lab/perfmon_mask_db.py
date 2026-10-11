#!/usr/bin/env python3
"""Mask names in a PerfMon SQLite database made by perfmon_csv_to_sqlite.py, writing a new database.

PerfMon counter paths carry real names: app pools, sites, queues, services, agents, products. This tool replaces
each one with a neutral placeholder from a private mapping file, so the masked database can be shared or analysed.

  mapping.csv   two columns with a header row: real,placeholder  (e.g. MyPaymentsPool,AppPool1)
                Kept private: it is the key back to the real names.

Replacement is case-insensitive on whole occurrences in counters.path, host, object, instance and base_instance;
an all-lowercase occurrence gets the lowercase placeholder. Longer names are replaced first. meta.source_file is
replaced by the masked file name. Index statistics are rebuilt and the file is vacuumed. The tool then fails if any
real name is still present, in the tables or anywhere in the file's raw bytes (case-insensitive).

Python standard library only. Usage:
  python3 perfmon_mask.py capture.db mapping.csv capture-masked.db [--force]
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


def masker(mapping):
    pats = [(re.compile(re.escape(real), re.IGNORECASE), ph) for real, ph in mapping]

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
    for real, _ in mapping:
        n = db.execute('SELECT count(*) FROM counters WHERE path LIKE ? OR host LIKE ? OR instance LIKE ? OR object LIKE ?',
                       (f'%{real}%',) * 4).fetchone()[0]
        n += db.execute('SELECT count(*) FROM meta WHERE value LIKE ?', (f'%{real}%',)).fetchone()[0]
        if n:
            left.append((real, n))
    db.execute('VACUUM')
    db.close()
    # verify again on the raw bytes of the file (free pages, indexes, statistics)
    with open(a.out, 'rb') as f:
        raw = f.read().lower()
    left += [(real, 'raw bytes') for real, _ in mapping if real.lower().encode() in raw]
    print(f'mapping entries: {len(mapping)}; counters changed: {changed}')
    if left:
        print(f'FAILED: {len(left)} real names still present (names not printed)')
        sys.exit(1)
    print('verify: no real name left')


if __name__ == '__main__':
    main()
