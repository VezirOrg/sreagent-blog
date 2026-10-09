#!/usr/bin/env python3
r"""Convert a Windows Performance Monitor CSV (PDH-CSV, e.g. from `relog x.blg -f csv`) into a SQLite database.

PerfMon writes one wide row per sample: a timestamp column, then one column per counter path such as
  \\HOST\Process(svchost#3)\Private Bytes
This script turns it into a long, indexed layout that is cheap to query with SQL:

  meta(key, value)                     source file, time zone header, sample interval, row/column counts
  samples(sample_id, ts)               one row per CSV row; ts is ISO 8601 local time as PerfMon wrote it
  counters(counter_id, path, host, object, instance, base_instance, counter, n_values, n_blank,
           min_value, max_value, avg_value, first_value, last_value)
  vals(counter_id, sample_id, value)   one row per non-blank cell
  perf (view)                          ts, host, object, counter, instance, value

PerfMon quirks handled:
  - first header cell is "(PDH-CSV 4.0) (<time zone>)(<bias>)"; it is kept in meta
  - blank cells and cells holding a single space (counter missing in that sample) are not stored
  - instance names with "#N" suffixes (svchost#3) are kept as-is in `instance`; `base_instance` drops the
    suffix. PerfMon re-numbers #N when processes start and exit, so follow a process by its
    "ID Process" counter, not by its #N name, when that matters
  - month/day order of the timestamp is detected from the data (or forced with --dayfirst/--monthfirst)
  - UTF-8 (with or without BOM), UTF-16 and cp1252 input

Python standard library only (csv, sqlite3). Usage:
  python3 perfmon_csv_to_sqlite.py capture.csv capture.db [--dayfirst | --monthfirst] [--force]
"""
import argparse
import csv
import datetime as dt
import os
import re
import sqlite3
import sys

PATH_RE = re.compile(r'^\\\\(?P<host>[^\\]+)\\(?P<object>[^\\(]+?)(?:\((?P<instance>.*)\))?\\(?P<counter>[^\\]+)$')
SUFFIX_RE = re.compile(r'#\d+$')
TS_FORMATS = ('%m/%d/%Y %H:%M:%S.%f', '%m/%d/%Y %H:%M:%S')


def open_text(path):
    with open(path, 'rb') as f:
        head = f.read(4)
    if head[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return open(path, encoding='utf-16', newline='')
    try:
        with open(path, encoding='utf-8-sig') as f:
            for _ in f:
                pass
        return open(path, encoding='utf-8-sig', newline='')
    except UnicodeDecodeError:
        return open(path, encoding='cp1252', newline='')


def parse_path(path):
    m = PATH_RE.match(path)
    if not m:
        return None, None, None, None
    inst = m.group('instance')
    return m.group('host'), m.group('object'), inst, m.group('counter')


def detect_dayfirst(first_cells):
    """True if the first field of the date is the day (some value > 12), False if it is the month."""
    a = [int(c.split('/')[0]) for c in first_cells if c.count('/') == 2]
    b = [int(c.split('/')[1]) for c in first_cells if c.count('/') == 2]
    if any(x > 12 for x in a):
        return True
    if any(x > 12 for x in b):
        return False
    return False  # ambiguous: PDH-CSV default is month first


def parse_ts(cell, dayfirst):
    cell = cell.strip()
    if dayfirst:
        d, m, rest = cell.split('/', 2)
        cell = f'{m}/{d}/{rest}'
    for fmt in TS_FORMATS:
        try:
            return dt.datetime.strptime(cell, fmt)
        except ValueError:
            pass
    raise ValueError(f'unparsed timestamp: {cell!r}')


def to_float(cell):
    s = cell.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        if ',' in s and '.' not in s:
            return float(s.replace(',', '.'))
        raise


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv_path')
    ap.add_argument('db_path')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--dayfirst', action='store_true')
    g.add_argument('--monthfirst', action='store_true')
    ap.add_argument('--force', action='store_true', help='overwrite an existing database')
    args = ap.parse_args()

    if os.path.exists(args.db_path):
        if not args.force:
            sys.exit(f'{args.db_path} exists; use --force to overwrite')
        os.remove(args.db_path)

    # pass 1: the first column, to decide day/month order
    with open_text(args.csv_path) as f:
        r = csv.reader(f)
        header = next(r)
        first_cells = [row[0] for row in r if row]
    if args.dayfirst or args.monthfirst:
        dayfirst = args.dayfirst
    else:
        dayfirst = detect_dayfirst(first_cells)

    db = sqlite3.connect(args.db_path)
    db.executescript('''
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE samples(sample_id INTEGER PRIMARY KEY, ts TEXT NOT NULL);
        CREATE TABLE counters(counter_id INTEGER PRIMARY KEY, path TEXT NOT NULL, host TEXT, object TEXT,
            instance TEXT, base_instance TEXT, counter TEXT, n_values INTEGER, n_blank INTEGER,
            min_value REAL, max_value REAL, avg_value REAL, first_value REAL, last_value REAL);
        CREATE TABLE vals(counter_id INTEGER NOT NULL, sample_id INTEGER NOT NULL, value REAL NOT NULL,
            PRIMARY KEY(counter_id, sample_id)) WITHOUT ROWID;
    ''')

    paths = header[1:]
    unparsed = 0
    for i, p in enumerate(paths, start=1):
        host, obj, inst, ctr = parse_path(p)
        if obj is None:
            unparsed += 1
        base = SUFFIX_RE.sub('', inst) if inst is not None else None
        db.execute('INSERT INTO counters(counter_id, path, host, object, instance, base_instance, counter) '
                   'VALUES (?,?,?,?,?,?,?)', (i, p, host, obj, inst, base, ctr))

    stats = {i: [0, 0, None, None, 0.0, None, None] for i in range(1, len(paths) + 1)}  # n, blank, min, max, sum, first, last
    n_rows = bad_cells = short_rows = 0
    prev_ts = None
    deltas = {}
    batch = []
    with open_text(args.csv_path) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if not row or not row[0].strip():
                continue
            n_rows += 1
            ts = parse_ts(row[0], dayfirst)
            if prev_ts is not None:
                d = round((ts - prev_ts).total_seconds())
                deltas[d] = deltas.get(d, 0) + 1
            prev_ts = ts
            db.execute('INSERT INTO samples VALUES (?,?)', (n_rows, ts.isoformat(sep=' ', timespec='milliseconds')))
            if len(row) - 1 < len(paths):
                short_rows += 1
            for cid, cell in enumerate(row[1:len(paths) + 1], start=1):
                st = stats[cid]
                try:
                    v = to_float(cell)
                except ValueError:
                    bad_cells += 1
                    v = None
                if v is None:
                    st[1] += 1
                    continue
                st[0] += 1
                st[2] = v if st[2] is None or v < st[2] else st[2]
                st[3] = v if st[3] is None or v > st[3] else st[3]
                st[4] += v
                if st[5] is None:
                    st[5] = v
                st[6] = v
                batch.append((cid, n_rows, v))
            if len(batch) > 500000:
                db.executemany('INSERT INTO vals VALUES (?,?,?)', batch)
                batch.clear()
    db.executemany('INSERT INTO vals VALUES (?,?,?)', batch)
    for cid, st in stats.items():
        missing = n_rows - st[0] - st[1]  # cells absent from short rows
        db.execute('UPDATE counters SET n_values=?, n_blank=?, min_value=?, max_value=?, avg_value=?, '
                   'first_value=?, last_value=? WHERE counter_id=?',
                   (st[0], st[1] + missing, st[2], st[3], st[4] / st[0] if st[0] else None, st[5], st[6], cid))

    interval = max(deltas, key=deltas.get) if deltas else None
    first_ts, last_ts = db.execute('SELECT min(ts), max(ts) FROM samples').fetchone()
    meta = {
        'source_file': os.path.basename(args.csv_path),
        'pdh_header': header[0],
        'timestamp_order': 'day/month/year' if dayfirst else 'month/day/year',
        'rows': n_rows, 'counter_columns': len(paths), 'unparsed_paths': unparsed,
        'bad_cells': bad_cells, 'short_rows': short_rows,
        'first_ts': first_ts, 'last_ts': last_ts,
        'sample_interval_s': interval,
        'interval_histogram': ', '.join(f'{k}s x{v}' for k, v in sorted(deltas.items(), key=lambda kv: -kv[1])[:10]),
        'converter': 'perfmon_csv_to_sqlite.py',
    }
    db.executemany('INSERT INTO meta VALUES (?,?)', [(k, str(v)) for k, v in meta.items()])
    db.executescript('''
        CREATE INDEX vals_sample ON vals(sample_id);
        CREATE INDEX counters_obj ON counters(object, counter, instance);
        CREATE INDEX samples_ts ON samples(ts);
        CREATE VIEW perf AS
            SELECT s.ts, c.host, c.object, c.counter, c.instance, v.value
            FROM vals v JOIN counters c USING(counter_id) JOIN samples s USING(sample_id);
        ANALYZE;
    ''')
    db.commit()
    db.execute('VACUUM')
    db.close()
    for k, v in meta.items():
        print(f'{k}: {v}')


if __name__ == '__main__':
    main()
