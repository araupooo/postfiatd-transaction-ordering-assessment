#!/bin/bash
# clean_reproduce.sh — full fresh-environment reproduction check.
#
# Copies the pack to a throwaway directory, drops all shipped outputs
# and SHA256SUMS, re-runs every generation step from scratch via
# scripts/run_all.sh, and compares the fresh numbers with the shipped
# ones via scripts/compare_reproduce.py. Exits 0 only if every
# comparison check passes.
#
# The fresh outputs are copied back into outputs/fresh-clone-* so the
# reproduction itself is evidence. The reproduction log is deterministic
# (no timestamps, no workdir paths) so SHA256SUMS stays stable across
# runs. Only deterministic comparisons are made: JSON deep-compare
# ignoring volatile fields, digest compare for logs after stripping
# timestamp lines; timing values are never compared absolutely.
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d /tmp/pftl-ordering-repro.XXXXXX)"
echo "clean_reproduce.sh workdir: $WORK"
mkdir -p "$WORK/shipped"
# Save the shipped outputs and fixtures for comparison.
if [ -d "$PACK_ROOT/outputs" ]; then
  cp -r "$PACK_ROOT/outputs" "$WORK/shipped/outputs"
fi
if [ -f "$PACK_ROOT/fixtures/source-hashes.json" ]; then
  mkdir -p "$WORK/shipped/fixtures"
  cp "$PACK_ROOT/fixtures/source-hashes.json" "$WORK/shipped/fixtures/"
fi
if [ -d "$PACK_ROOT/fixtures/source-excerpts" ]; then
  mkdir -p "$WORK/shipped/fixtures/source-excerpts"
  cp "$PACK_ROOT/fixtures/source-excerpts/"*.txt "$WORK/shipped/fixtures/source-excerpts/" 2>/dev/null || true
fi

cp -r "$PACK_ROOT" "$WORK/pack"
cd "$WORK/pack" || exit 1

# Drop everything the generation steps produce, so the run is from scratch.
rm -rf outputs
mkdir -p outputs/derived
rm -f SHA256SUMS
rm -f run-manifest.json
rm -f fixtures/source-hashes.json
rm -f fixtures/source-excerpts/*.txt

echo "--- step 1: run_all.sh (fresh copy) ---"
bash scripts/run_all.sh || { echo "run_all.sh FAILED in fresh copy"; exit 1; }
echo "--- step 2: compare with shipped ---"
python3 scripts/compare_reproduce.py "$WORK/shipped" "$WORK/pack" \
  || { echo "compare_reproduce.py FAILED"; exit 1; }

echo "--- step 3: copy fresh outputs back as fresh-clone-* evidence ---"
for f in outputs/*.json outputs/*.log; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  cp "$f" "$PACK_ROOT/outputs/fresh-clone-$base"
done
for f in outputs/derived/*; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  cp "$f" "$PACK_ROOT/outputs/fresh-clone-derived-$base"
done
# Deterministic compare log (no timestamps, no workdir paths).
{
  echo "clean_reproduce.sh fresh run"
  echo "shipped simulator status: $(python3 -c "import json;print(json.load(open('$WORK/shipped/outputs/derived/run-summary.json'))['steps']['simulator'])")"
  echo "fresh simulator status: $(python3 -c "import json;print(json.load(open('outputs/derived/run-summary.json'))['steps']['simulator'])")"
  echo "shipped probe status: $(python3 -c "import json;print(json.load(open('$WORK/shipped/outputs/derived/run-summary.json'))['steps']['probe'])")"
  echo "fresh probe status: $(python3 -c "import json;print(json.load(open('outputs/derived/run-summary.json'))['steps']['probe'])")"
  echo "compare: $(python3 -c "import json;d=json.load(open('outputs/derived/compare-results.json'));print('%d/%d checks PASS' % (d['passed'], d['total']))")"
} > "$PACK_ROOT/outputs/fresh-clone-compare.log"
cat "$PACK_ROOT/outputs/fresh-clone-compare.log"

# Fresh-clone evidence changed the pack; regenerate digests.
bash "$PACK_ROOT/scripts/make_sha256sums.sh" || exit 1
bash "$PACK_ROOT/scripts/verify_digests.sh" || exit 1
echo "clean_reproduce.sh: ALL CHECKS PASSED"
