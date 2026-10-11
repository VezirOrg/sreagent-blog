#!/usr/bin/env python3
"""Mask names in a raw PerfMon CSV before it is handed to the perfmon-triage skill (lab step 0), writing a new CSV.

PerfMon counter paths carry real names: hosts, app pools, sites, queues, services, agents, products. This tool
replaces each one with a neutral placeholder from a private mapping file, so the masked CSV can be analysed.

  mapping.csv   two columns with a header row: real,placeholder  (e.g. MyPaymentsPool,AppPool1)
                Kept private: it is the key back to the real names.

Match rule (the same as perfmon_mask_db.py, unchanged): case-insensitive, every occurrence, longer names first;
an all-lowercase occurrence gets the lowercase placeholder. It runs over every line of the file (header and data).
The output is UTF-8. The tool then fails if any real name is still present anywhere in the output
(case-insensitive); it never prints a real name.

Python standard library only. Usage:
  python3 perfmon_mask_csv.py capture.csv mapping.csv capture-masked.csv [--force]
"""
import argparse
import csv
import os
import re
import sys


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv_in')
    ap.add_argument('mapping')
    ap.add_argument('csv_out')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if os.path.abspath(a.csv_in) == os.path.abspath(a.csv_out):
        sys.exit('the output must be a new file')
    if os.path.exists(a.csv_out):
        if not a.force:
            sys.exit(f'{a.csv_out} exists; use --force')
        os.remove(a.csv_out)
    mapping = load_mapping(a.mapping)
    mask = masker(mapping)
    # quick pre-check: only lines holding some real name go through the (slower) masker
    any_real = re.compile('|'.join(re.escape(r) for r, _ in mapping), re.IGNORECASE) if mapping else None
    lines = changed = header_cells = 0
    with open_text(a.csv_in) as fin, open(a.csv_out, 'w', encoding='utf-8', newline='') as fout:
        for line in fin:
            lines += 1
            if any_real and any_real.search(line):
                new = mask(line)
                if new != line:
                    changed += 1
                    if lines == 1:
                        header_cells = sum(1 for x, y in zip(next(csv.reader([line])), next(csv.reader([new])))
                                           if x != y)
                line = new
            fout.write(line)
    # verify: no real name left anywhere in the output
    left = 0
    with open(a.csv_out, encoding='utf-8', newline='') as f:
        for line in f:
            low = line.lower()
            left += sum(1 for r, _ in mapping if r.lower() in low)
    print(f'mapping entries: {len(mapping)}; lines: {lines:,}; lines changed: {changed:,}; '
          f'header cells changed: {header_cells:,}')
    if left:
        print(f'FAILED: {left} real-name occurrences still present (names not printed)')
        sys.exit(1)
    print('verify: no real name left')


if __name__ == '__main__':
    main()
