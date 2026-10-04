#!/usr/bin/env bash
# Scrub check for publishable content. Exits non-zero if anything looks like a lab identifier or a secret.
# Usage: scripts/scrub-check.sh [path ...]   (default: content docs notes HANDOVER.md README.md)
# Optional denylist of real lab names, one regex per line, kept OUTSIDE the repo:
#   files/scrub-denylist.txt  (or set SCRUB_DENYLIST=/path/to/list)
set -u
cd "$(dirname "$0")/.."
paths=("$@"); [ ${#paths[@]} -eq 0 ] && paths=(content docs notes HANDOVER.md README.md)
existing=(); for p in "${paths[@]}"; do [ -e "$p" ] && existing+=("$p"); done
fail=0
check() { # label, extended regex
  local hits; hits=$(grep -rnEI --exclude=scrub-check.sh -e "$2" "${existing[@]}" 2>/dev/null)
  if [ -n "$hits" ]; then echo "== $1"; echo "$hits"; fail=1; fi
}
check "GUID" '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
check "private IPv4" '\b(10\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9]{1,3}\.[0-9]{1,3}\b'
check "JWT" 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
check "secret-looking" '(AccountKey|SharedAccessSignature|[Pp]assword|[Ss]ecret)[[:space:]]*[=:][[:space:]]*[^<[:space:]]{6,}'
check "SAS token" '[?&]sig=[A-Za-z0-9%]{20,}'
deny="${SCRUB_DENYLIST:-files/scrub-denylist.txt}"
if [ -f "$deny" ]; then
  while IFS= read -r pat; do
    [ -z "$pat" ] || [ "${pat:0:1}" = "#" ] && continue
    check "denylist: $pat" "$pat"
  done < "$deny"
else
  echo "note: no denylist at $deny (lab names not checked)"
fi
[ $fail -eq 0 ] && echo "scrub-check: clean" || echo "scrub-check: FAILED"
exit $fail
