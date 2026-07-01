#!/usr/bin/env python3
"""Make the flattened Copilot skills pass awesome-copilot's vally lint.

Three transforms, applied in place to the flattened skills tree:

1. valid-refs: rewrite cross-skill relative links (targets that escape the
   skill directory, i.e. start with ``../``) to absolute GitHub URLs on the
   upstream cockroachdb-skills repo. In the flattened layout these relative
   links are broken anyway, so this is both a lint fix and a correctness fix.
2. orphan-files: ensure every file under ``references/`` is linked from
   SKILL.md, by appending an "Additional references" section for any that are
   not already linked.
3. file length: keep SKILL.md at or under 500 lines by moving whole trailing
   ``## `` sections into a linked ``references/additional-details.md``.

Usage: transform-skills-for-copilot.py <dest-skills-dir> <source-skills-dir>
  dest   = .github/skills           (flattened: <dest>/<name>/SKILL.md)
  source = <repo>/skills            (upstream layout: <source>/<domain>/<name>/)
"""

import os
import re
import sys

UPSTREAM_BASE = "https://github.com/cockroachlabs/cockroachdb-skills/blob/main"
MAX_LINES = 500

INLINE_LINK = re.compile(r"(\]\()(\.\./[^)]+)(\))")
REF_LINK = re.compile(r"(^\[[^\]]+\]:\s*)(\.\./\S+)", re.MULTILINE)


def name_to_domain(source_root):
    """Map each skill leaf name to its upstream domain directory name."""
    mapping = {}
    for dirpath, _dirs, files in os.walk(source_root):
        if "SKILL.md" in files:
            name = os.path.basename(dirpath)
            domain = os.path.basename(os.path.dirname(dirpath))
            mapping[name] = domain
    return mapping


def upstream_url(skill_domain, skill_name, file_reldir, target):
    """Resolve a ../-relative target to an absolute upstream GitHub URL."""
    # Directory of the .md file within the upstream repo.
    base = "skills/%s/%s" % (skill_domain, skill_name)
    file_dir = os.path.normpath(os.path.join(base, file_reldir)) if file_reldir else base
    # Split target into path and optional #anchor.
    path, _, anchor = target.partition("#")
    resolved = os.path.normpath(os.path.join(file_dir, path)).replace(os.sep, "/")
    url = "%s/%s" % (UPSTREAM_BASE, resolved)
    if anchor:
        url += "#" + anchor
    return url


def rewrite_links(text, skill_domain, skill_name, file_reldir):
    def _inline(m):
        return m.group(1) + upstream_url(skill_domain, skill_name, file_reldir, m.group(2)) + m.group(3)

    def _ref(m):
        return m.group(1) + upstream_url(skill_domain, skill_name, file_reldir, m.group(2))

    text = INLINE_LINK.sub(_inline, text)
    text = REF_LINK.sub(_ref, text)
    return text


def linked_reference_targets(skill_md_text):
    """Relative reference paths already linked from SKILL.md."""
    targets = set()
    for m in re.finditer(r"\]\((references/[^)#]+)", skill_md_text):
        targets.add(m.group(1).strip())
    return targets


def all_reference_files(skill_dir):
    refs = []
    refdir = os.path.join(skill_dir, "references")
    for dirpath, _dirs, files in os.walk(refdir):
        for f in files:
            rel = os.path.relpath(os.path.join(dirpath, f), skill_dir).replace(os.sep, "/")
            refs.append(rel)
    return sorted(refs)


def split_for_length(skill_dir, text):
    """Move trailing ## sections into references/additional-details.md until
    SKILL.md is <= MAX_LINES. Returns the (possibly shortened) SKILL.md text."""
    lines = text.split("\n")
    if len(lines) <= MAX_LINES:
        return text

    # Indices of level-2 section headers.
    headers = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    if not headers:
        return text  # nothing safe to move

    moved = []
    # Move whole trailing sections until we're under the limit (reserve a few
    # lines for the appendix link we append below).
    while len(lines) > (MAX_LINES - 6) and len(headers) > 1:
        start = headers.pop()
        moved.insert(0, "\n".join(lines[start:]).rstrip())
        lines = lines[:start]

    if not moved:
        return text

    appendix = "# Additional details\n\n" + "\n\n".join(moved) + "\n"
    refs_dir = os.path.join(skill_dir, "references")
    os.makedirs(refs_dir, exist_ok=True)
    with open(os.path.join(refs_dir, "additional-details.md"), "w", encoding="utf-8") as f:
        f.write(appendix)

    body = "\n".join(lines).rstrip()
    body += (
        "\n\n## Additional details\n\n"
        "Further sections for this skill are in "
        "[references/additional-details.md](references/additional-details.md).\n"
    )
    return body


def ensure_no_orphans(skill_dir, text):
    """Append links for any references/ files not already linked."""
    refs = all_reference_files(skill_dir)
    if not refs:
        return text
    linked = linked_reference_targets(text)
    missing = [r for r in refs if r not in linked]
    if not missing:
        return text
    lines = ["", "## Additional references", ""]
    for r in missing:
        label = os.path.basename(r)
        lines.append("- [%s](%s)" % (label, r))
    lines.append("")
    return text.rstrip() + "\n" + "\n".join(lines)


def process_skill(skill_dir, domain):
    name = os.path.basename(skill_dir)

    # 1. Rewrite cross-skill links in every markdown file of the skill.
    for dirpath, _dirs, files in os.walk(skill_dir):
        for f in files:
            if not f.endswith(".md"):
                continue
            p = os.path.join(dirpath, f)
            reldir = os.path.relpath(dirpath, skill_dir)
            reldir = "" if reldir == "." else reldir
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
            new = rewrite_links(text, domain, name, reldir)
            if new != text:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)

    skill_md = os.path.join(skill_dir, "SKILL.md")
    with open(skill_md, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()

    # 2. Length: move trailing sections into a linked appendix.
    text = split_for_length(skill_dir, text)
    # 3. Orphans: link any remaining unlinked references files.
    text = ensure_no_orphans(skill_dir, text)

    with open(skill_md, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    if len(sys.argv) != 3:
        print("usage: transform-skills-for-copilot.py <dest-skills-dir> <source-skills-dir>", file=sys.stderr)
        sys.exit(2)
    dest, source = sys.argv[1], sys.argv[2]
    domains = name_to_domain(source)
    count = 0
    for entry in sorted(os.listdir(dest)):
        skill_dir = os.path.join(dest, entry)
        if not os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
            continue
        domain = domains.get(entry)
        if not domain:
            print("warning: no upstream domain for skill %r; skipping link rewrite" % entry, file=sys.stderr)
            continue
        process_skill(skill_dir, domain)
        count += 1
    print("transformed %d skills for Copilot/vally compliance" % count)


if __name__ == "__main__":
    main()
