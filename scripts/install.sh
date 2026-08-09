#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/install.sh [--update] [--no-init] /absolute/path/to/project

Install Hunt Skill into <project>/.agents/skills/hunt-skill.

Options:
  --update   Back up and replace an existing installed skill.
  --no-init  Do not initialize the project's .audit directory/database.
  --help     Show this help.
EOF
}

update=0
initialize_audit=1
project=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --update)
      update=1
      shift
      ;;
    --no-init)
      initialize_audit=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$project" ]]; then
        printf 'Only one project path may be supplied.\n' >&2
        exit 2
      fi
      project="$1"
      shift
      ;;
  esac
done

if [[ -z "$project" ]]; then
  usage >&2
  exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
source_skill="$repo_root/skill/hunt-skill"

if [[ ! -f "$source_skill/SKILL.md" ]]; then
  printf 'Skill payload is missing: %s\n' "$source_skill" >&2
  exit 1
fi

if [[ ! -d "$project" ]]; then
  printf 'Project directory does not exist: %s\n' "$project" >&2
  exit 1
fi

project="$(cd "$project" && pwd)"
install_parent="$project/.agents/skills"
target="$install_parent/hunt-skill"
temporary="$install_parent/.hunt-skill.installing.$$"
backup=""

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || {
  printf 'Python 3.11 or newer is required.\n' >&2
  exit 1
}

mkdir -p "$install_parent"

if [[ -e "$target" && $update -ne 1 ]]; then
  printf 'Hunt Skill is already installed at %s\n' "$target" >&2
  printf 'Rerun with --update to back up and replace it.\n' >&2
  exit 1
fi

cleanup() {
  if [[ -e "$temporary" ]]; then
    rm -rf "$temporary"
  fi
}
trap cleanup EXIT

cp -R "$source_skill" "$temporary"

if [[ -e "$target" ]]; then
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  backup="$install_parent/.hunt-skill.backup-$timestamp"
  mv "$target" "$backup"
fi

mv "$temporary" "$target"
trap - EXIT

auditctl="$target/scripts/auditctl.py"
python3 "$auditctl" doctor --repo "$project"

if [[ $initialize_audit -eq 1 ]]; then
  python3 "$auditctl" init --repo "$project"
fi

printf '\nHunt Skill installed: %s\n' "$target"
if [[ -n "$backup" ]]; then
  printf 'Previous installation backed up: %s\n' "$backup"
fi
if [[ $initialize_audit -eq 1 ]]; then
  printf 'Next: edit %s/.audit/SCOPE_FILES.txt and run snapshot.\n' "$project"
else
  printf 'Audit initialization skipped (--no-init).\n'
fi
