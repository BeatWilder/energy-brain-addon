#!/usr/bin/env sh
set -eu

echo "=== V1968-V1999 Predbat-inspired EMS cockpit smoke ==="

NEW_FILES="
docs/v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit.md
app/__init__.py
app/v1968/__init__.py
app/v1968/predbat_concept_audit.py
app/v1969/__init__.py
app/v1969/tesla_style_cockpit_spec.py
tests/test_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit.py
tools/run_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit_smoke.sh
"

echo
echo "=== tests ==="
pytest -q -o cache_dir=energy-brain-addon/.pytest_cache tests/test_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit.py
echo "PASS: tests completed"

echo
echo "=== forbidden runtime surface grep ==="
tmp_terms="$(mktemp)"
trap 'rm -f "$tmp_terms"' EXIT
{
  printf '%s%s\n' "call_" "service("
  printf '%s%s%s\n' "hass" "." "services"
  printf '%s%s\n' "requests" "."
  printf '%s%s%s\n' "aio" "http" "."
  printf '%s%s%s\n' "url" "lib" "."
  printf '%s%s\n' ".publish" "("
  printf '%s%s%s\n' "Alpha" "ESS" "("
  printf '%s%s\n' "set_state" "("
  printf '%s%s\n' "service" ":"
  printf '%s%s%s\n' "input" "_boolean" "."
  printf '%s%s%s\n' "input" "_number" "."
  printf '%s%s%s\n' "input" "_select" "."
  printf '%s%s\n' "switch" "."
  printf '%s%s\n' "climate" "."
  printf '%s%s\n' "notify" "."
  printf '%s%s%s\n' "shell" "_command" "."
} > "$tmp_terms"

found=0
for file in $NEW_FILES; do
  if grep -F -n -f "$tmp_terms" "$file"; then
    found=1
  fi
done

if [ "$found" -ne 0 ]; then
  echo "FAIL: forbidden runtime surface string found"
  exit 1
fi
echo "PASS: forbidden runtime surface strings absent from newly added files"

echo
echo "=== protected runtime/controller diff ==="
protected_fail=0
for path in \
  "../app/energy_brain_v5.py" \
  "../archive/app_old_versions/energy_brain_v5.py" \
  "energy_brain/controller.py" \
  "energy_brain/main.py" \
  "energy_brain/ha_client.py"
do
  if [ ! -e "$path" ]; then
    echo "$path: protected path not present in this checkout"
    continue
  fi
  case "$path" in
    ../*) diff_cmd="git -C .. diff --quiet -- ${path#../}" ;;
    *) diff_cmd="git diff --quiet -- $path" ;;
  esac
  if sh -c "$diff_cmd"; then
    echo "$path: PASS no diff"
  else
    echo "$path: FAIL protected diff present"
    case "$path" in
      ../*) git -C .. diff -- "${path#../}" ;;
      *) git diff -- "$path" ;;
    esac
    protected_fail=1
  fi
done

if [ "$protected_fail" -ne 0 ]; then
  exit 1
fi

echo
echo "PASS: V1968-V1999 smoke completed"
