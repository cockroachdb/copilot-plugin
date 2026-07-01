#!/usr/bin/env bash
# Flatten CockroachDB skills into the Copilot layout (.github/skills/<skill>/).
#
# Copilot Agent Skills require each skill at <location>/<skill-name>/SKILL.md,
# where the directory name matches the skill's `name:` field. The upstream
# cockroachdb-skills repo groups skills by domain (e.g. <domain>/<skill>/), so
# this script copies each skill directory up one level into a flat tree.
#
# Usage: scripts/sync-skills.sh <source-skills-dir>
#   <source-skills-dir> defaults to submodules/cockroachdb-skills/skills
set -euo pipefail

SRC="${1:-submodules/cockroachdb-skills/skills}"
DST=".github/skills"

if [ ! -d "$SRC" ]; then
  echo "error: source skills dir not found: $SRC" >&2
  exit 1
fi

rm -rf "$DST"
mkdir -p "$DST"

count=0
while IFS= read -r skillmd; do
  skill_dir="$(dirname "$skillmd")"
  name="$(basename "$skill_dir")"
  if [ -e "$DST/$name" ]; then
    echo "error: duplicate skill name across domains: $name" >&2
    exit 1
  fi
  # -L dereferences symlinks so each skill is self-contained regular files
  # (upstream uses symlinks for shared reference files; those would dangle
  # once flattened).
  cp -RL "$skill_dir" "$DST/$name"
  count=$((count + 1))
done < <(find "$SRC" -name SKILL.md | sort)

echo "synced $count skills into $DST/"

# Make the vendored skills pass awesome-copilot's vally lint: rewrite
# cross-skill links to upstream URLs, link orphan reference files, and split
# over-length SKILL.md files.
python3 "$(dirname "$0")/transform-skills-for-copilot.py" "$DST" "$SRC"
