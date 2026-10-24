#!/usr/bin/env python3
"""Local specification traceability; never executes commands from a manifest."""
import argparse
from collections import defaultdict, deque
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


GROUPS = ("contexts", "concepts", "rules", "stories", "criteria", "cases",
          "implementations", "executions")
OPTIONAL = ("implementations", "executions")
REFERENCE_FIELDS = {
    "rules": ("concept_ids",),
    "stories": ("concept_ids",),
    "criteria": ("story_ids", "rule_ids", "concept_ids"),
    "cases": ("criterion_ids",),
    "implementations": ("criterion_ids",),
}
NAME = re.compile(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*\Z", re.ASCII)
SHA = re.compile(r"[0-9a-fA-F]{40}\Z", re.ASCII)
LIMITATION = ("Checks establish structure and explicit link coverage only; they do not "
              "prove consistent meaning, correct behavior, or business acceptance. "
              "Execution results are claims, not independent acceptance evidence.")


class InputError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def read_spec(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (OSError, ValueError) as exc:
        raise InputError(f"Cannot read JSON manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise InputError("Manifest root must be an object")
    return data


def digest(data):
    """Absent optional arrays canonicalize to []; executions never enter the hash."""
    snapshot = dict(data)
    snapshot.setdefault("implementations", [])
    snapshot.pop("executions", None)
    encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def issue(code, path, message):
    return {"code": code, "path": path, "message": message}


def relative_path(value):
    if not isinstance(value, str) or not value.strip():
        raise InputError("Expected a nonempty relative file path")
    path = PurePosixPath(value)
    if (path.is_absolute() or ".." in path.parts or "\\" in value or
            any(ord(char) < 32 for char in value) or
            ":" in value or value in (".", "")):
        raise InputError("Path must be relative, use '/', and contain no '..' or drive prefix")
    return path


def resolve_path(value):
    try:
        return Path(value).resolve()
    except OSError as exc:
        raise InputError(f"Cannot resolve path {value}: {exc}") from exc
    except RuntimeError as exc:
        # Python 3.9 reports a filesystem symlink loop as RuntimeError rather
        # than OSError. Keep this conversion at the actual resolve boundary.
        if "symlink loop" not in str(exc).lower():
            raise
        raise InputError(f"Cannot resolve path {value}: {exc}") from exc


def project_file(value, project_root=None):
    path = relative_path(value)
    if project_root is None:
        return None
    root = resolve_path(project_root)
    resolved = resolve_path(root / str(path))
    if not resolved.is_relative_to(root):
        raise InputError("Resolved path escapes the project root")
    return resolved


def validate(data, project_root=None, require_coverage=False):
    errors, warnings = [], []

    def error(code, path, message):
        errors.append(issue(code, path, message))

    def string(obj, key, path):
        value = obj.get(key)
        if not isinstance(value, str) or not value.strip():
            error("required_string", f"{path}.{key}", "Expected a nonblank string")
            return None
        return value

    def strings(obj, key, path):
        values = obj.get(key)
        if not isinstance(values, list):
            error("required_array", f"{path}.{key}", "Expected an array of nonblank strings")
        elif any(not isinstance(v, str) or not v.strip() for v in values):
            error("string_array", f"{path}.{key}", "Every entry must be a nonblank string")

    def file_path(obj, key, path, artifact=False):
        value = string(obj, key, path)
        if value is None:
            return
        try:
            resolved = project_file(value, project_root)
        except InputError as exc:
            error("unsafe_path", f"{path}.{key}", str(exc))
            return
        if resolved is not None and not resolved.is_file():
            item = issue("missing_artifact" if artifact else "missing_file",
                         f"{path}.{key}", f"File does not exist: {value}")
            # Missing evidence is a visible state, not a malformed specification.
            (warnings if artifact else errors).append(item)

    if data.get("schema_version") != "1.0":
        error("schema_version", "schema_version", "Expected schema_version '1.0'")
    if project_root is not None:
        try:
            if not resolve_path(project_root).is_dir():
                error("project_root", "project_root", "Project root must be an existing directory")
        except InputError as exc:
            error("unsafe_path", "project_root", str(exc))
    scope = data.get("scope")
    if not isinstance(scope, dict):
        error("scope", "scope", "Expected scope object")
    else:
        string(scope, "purpose", "scope")
        for key in ("in_scope", "out_of_scope", "assumptions"):
            strings(scope, key, "scope")

    records = {}
    groups = {}
    for group in GROUPS:
        values = data.get(group, [] if group in OPTIONAL else None)
        if not isinstance(values, list):
            error("required_array", group, "Expected an array of records")
            values = []
        groups[group] = []
        for index, record in enumerate(values):
            path = f"{group}[{index}]"
            if not isinstance(record, dict):
                error("record", path, "Expected an object")
                continue
            groups[group].append((record, path))
            record_id = string(record, "id", path)
            if record_id is not None:
                if record_id in records:
                    error("duplicate_id", f"{path}.id", f"Duplicate stable ID: {record_id}")
                else:
                    records[record_id] = (group, record, path)
            if group != "executions":
                revision = record.get("revision")
                if type(revision) is not int or revision < 1:
                    error("revision", f"{path}.revision", "Expected a positive integer; booleans are invalid")
            if group not in ("contexts", "executions"):
                string(record, "context_id", path)
                name = string(record, "name", path)
                if name is not None and NAME.fullmatch(name) is None:
                    error("semantic_name", f"{path}.name", "Expected a lowercase ASCII dot/hyphen semantic path")
                if record.get("status") not in ("draft", "confirmed"):
                    error("status", f"{path}.status", "Expected draft or confirmed")

    context_keys = set()
    for record, path in groups["contexts"]:
        key = string(record, "key", path)
        if key is not None:
            if NAME.fullmatch(key) is None:
                error("context_key", f"{path}.key", "Expected a lowercase ASCII namespace")
            if key in context_keys:
                error("duplicate_context_key", f"{path}.key", f"Duplicate context namespace: {key}")
            context_keys.add(key)
        for key in ("label", "responsibility"):
            string(record, key, path)

    semantic_names = set()
    for group in GROUPS[1:-1]:
        for record, path in groups[group]:
            context_id = record.get("context_id")
            context = records.get(context_id) if isinstance(context_id, str) else None
            if context is None or context[0] != "contexts":
                error("context_reference", f"{path}.context_id", "Must reference a context ID")
            else:
                prefix = context[1].get("key")
                name = record.get("name")
                if isinstance(prefix, str) and isinstance(name, str) and not name.startswith(prefix + "."):
                    error("context_namespace", f"{path}.name", f"Name must start with '{prefix}.'")
            name = record.get("name")
            if isinstance(name, str):
                identity = (group, context_id if isinstance(context_id, str) else "", name)
                if identity in semantic_names:
                    error("duplicate_name", f"{path}.name", f"Duplicate semantic name: {name}")
                semantic_names.add(identity)

    def refs(record, key, expected_group, path, nonempty=True):
        values = record.get(key)
        if not isinstance(values, list) or (nonempty and not values):
            error("reference_array", f"{path}.{key}",
                  "Expected a nonempty reference array" if nonempty else "Expected a reference array")
            return
        seen = set()
        for index, value in enumerate(values):
            ref_path = f"{path}.{key}[{index}]"
            if not isinstance(value, str) or not value.strip():
                error("reference", ref_path, "Expected a nonblank ID")
                continue
            if value in seen:
                error("duplicate_reference", ref_path, f"Duplicate reference: {value}")
            seen.add(value)
            target = records.get(value)
            if target is None or target[0] != expected_group:
                error("reference", ref_path, f"Must reference {expected_group}: {value}")
            elif target[1].get("context_id") != record.get("context_id"):
                warnings.append(issue("cross_context_review", ref_path,
                                      f"Foreign reference {value}: document mapping and fact ownership in human review; meanings are not unified automatically"))

    for record, path in groups["concepts"]:
        string(record, "definition", path)
    for record, path in groups["rules"]:
        string(record, "statement", path)
        refs(record, "concept_ids", "concepts", path)
    for record, path in groups["stories"]:
        for key in ("role", "capability", "benefit"):
            string(record, key, path)
        refs(record, "concept_ids", "concepts", path)
    for record, path in groups["criteria"]:
        for key in ("condition", "expected"):
            string(record, key, path)
        refs(record, "story_ids", "stories", path, nonempty=False)
        refs(record, "rule_ids", "rules", path)
        refs(record, "concept_ids", "concepts", path)
    for record, path in groups["cases"]:
        for key in ("given", "when", "then"):
            string(record, key, path)
        refs(record, "criterion_ids", "criteria", path)
        automation = record.get("automation")
        if automation is not None:
            if not isinstance(automation, dict):
                error("automation", f"{path}.automation", "Expected object or null")
            else:
                file_path(automation, "path", f"{path}.automation")
                string(automation, "symbol", f"{path}.automation")
    for record, path in groups["implementations"]:
        refs(record, "criterion_ids", "criteria", path)
        file_path(record, "path", path)
        string(record, "symbol", path)

    for record, path in groups["executions"]:
        case_id = string(record, "case_id", path)
        target = records.get(case_id) if case_id else None
        if case_id and target is None:
            warnings.append(issue("historical_case_reference", f"{path}.case_id",
                                  "Case is absent from the current baseline: historical or unknown execution requires earlier snapshot review and remains stale"))
        elif target is not None and target[0] != "cases":
            error("case_reference", f"{path}.case_id", "Must reference a case ID")
        if type(record.get("case_revision")) is not int or record["case_revision"] < 1:
            error("case_revision", f"{path}.case_revision", "Expected a positive integer")
        value = string(record, "spec_digest", path)
        if value is not None and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
            error("spec_digest", f"{path}.spec_digest", "Expected sha256: plus 64 lowercase hex digits")
        value = string(record, "code_commit", path)
        if value is not None and SHA.fullmatch(value) is None:
            error("code_commit", f"{path}.code_commit", "Expected full 40-hex Git SHA")
        string(record, "environment", path)
        strings(record, "command", path)
        if record.get("command") == []:
            error("command", f"{path}.command", "Expected a nonempty command array")
        if record.get("result") not in ("passed", "failed", "blocked", "not_run"):
            error("result", f"{path}.result", "Expected passed, failed, blocked or not_run")
        file_path(record, "artifact", path, artifact=True)
        value = string(record, "recorded_at", path)
        if value is not None:
            try:
                timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                    raise ValueError("Timezone required")
            except ValueError:
                error("recorded_at", f"{path}.recorded_at", "Expected ISO8601 timestamp with timezone")

    linked_stories = {v for r, _ in groups["criteria"]
                      for v in r.get("story_ids", []) if isinstance(v, str)} if all(
                          isinstance(r.get("story_ids"), list) for r, _ in groups["criteria"]) else set()
    linked_criteria = {v for r, _ in groups["cases"]
                       for v in r.get("criterion_ids", []) if isinstance(v, str)} if all(
                           isinstance(r.get("criterion_ids"), list) for r, _ in groups["cases"]) else set()
    uncovered_stories = sorted(r["id"] for r, _ in groups["stories"]
                               if isinstance(r.get("id"), str) and r["id"] not in linked_stories)
    uncovered_criteria = sorted(r["id"] for r, _ in groups["criteria"]
                                if isinstance(r.get("id"), str) and r["id"] not in linked_criteria)
    for group, missing in (("stories", uncovered_stories), ("criteria", uncovered_criteria)):
        for record_id in missing:
            (errors if require_coverage else warnings).append(issue(
                "uncovered", group, f"No downstream link for {record_id}; link coverage is not semantic or behavioral proof"))
    coverage = {"kind": "structural_links_only", "uncovered_stories": uncovered_stories,
                "uncovered_criteria": uncovered_criteria,
                "complete": not (uncovered_stories or uncovered_criteria)}
    if project_root is None:
        warnings.append(issue("paths_unverified", "project_root",
                              "No project root supplied: path syntax checked, file existence unverified"))
    return {"ok": not errors, "spec_digest": digest(data), "coverage": coverage,
            "counts": {g: len(groups[g]) for g in GROUPS},
            "errors": errors, "warnings": warnings, "limitation": LIMITATION}


def nodes(data):
    return {record["id"]: (group, record) for group in GROUPS
            for record in (data.get(group, []) if isinstance(data.get(group, []), list) else [])
            if isinstance(record, dict) and isinstance(record.get("id"), str)}


def semantic(value, reference_fields=()):
    if isinstance(value, dict):
        # Only direct, schema-defined references have unordered semantics.
        # Unknown extension fields (including nested *_ids) stay ordinary content.
        return {key: sorted(item) if key in reference_fields else semantic(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [semantic(item) for item in value]
    return value


def dependencies(data):
    edges = defaultdict(set)
    for group in GROUPS[1:]:
        for record in data.get(group, []):
            record_id = record["id"]
            if group == "executions":
                edges[record["case_id"]].add(record_id)
                continue
            edges[record["context_id"]].add(record_id)
            for key in REFERENCE_FIELDS.get(group, ()):
                for target in record[key]:
                    edges[target].add(record_id)
                    if group == "implementations" and key == "criterion_ids":
                        edges[record_id].add(target)
    return edges


def snapshot_staleness(data, record):
    cases = {c["id"]: c for c in data["cases"]}
    reasons = []
    case = cases.get(record["case_id"])
    if case is None:
        reasons.append("case_removed")
    elif record["case_revision"] != case["revision"]:
        reasons.append("case_revision_changed")
    if record["spec_digest"] != digest(data):
        reasons.append("spec_digest_changed")
    return reasons


def impact(before, after, changed_paths=None):
    errors, warnings = [], []
    old, new = nodes(before), nodes(after)
    added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
    for name, data in (("before", before), ("after", after)):
        result = validate(data)
        errors.extend({**e, "path": name + "." + e["path"]} for e in result["errors"])
        warnings.extend({**w, "path": name + "." + w["path"]} for w in result["warnings"])
    if errors:
        return {"ok": False, "added": added, "removed": removed, "errors": errors,
                "warnings": warnings, "limitation": LIMITATION}
    changed_paths = sorted({str(relative_path(path)) for path in (changed_paths or [])})
    code_seeds, matched_paths = set(), set()
    for snapshot in (before, after):
        for group in ("implementations", "cases"):
            for record in snapshot.get(group, []):
                value = record.get("path") if group == "implementations" else (record.get("automation") or {}).get("path")
                if value is not None and str(relative_path(value)) in changed_paths:
                    code_seeds.add(record["id"])
                    matched_paths.add(str(relative_path(value)))
    unmapped_paths = sorted(set(changed_paths) - matched_paths)
    for path in unmapped_paths:
        warnings.append(issue("unmapped_changed_path", path,
                              "Changed path has no implementation/automation link; review its scope and missing mappings manually"))
    changed, semantic_changed, revision_only = [], [], []
    for record_id in sorted(old.keys() & new.keys()):
        old_group, old_record = old[record_id]
        new_group, new_record = new[record_id]
        if old_group != new_group:
            errors.append(issue("identity_kind_changed", record_id, "Stable ID cannot change record kind"))
        old_refs, new_refs = REFERENCE_FIELDS.get(old_group, ()), REFERENCE_FIELDS.get(new_group, ())
        if semantic(old_record, old_refs) == semantic(new_record, new_refs) and old_group == new_group:
            continue
        changed.append(record_id)
        if new_group != "executions":
            if new_record["revision"] <= old_record.get("revision", 0):
                errors.append(issue("revision_not_increased", record_id,
                                    "Changed existing node requires a higher revision; preserve its stable ID"))
            old_content = {k: v for k, v in old_record.items() if k != "revision"}
            new_content = {k: v for k, v in new_record.items() if k != "revision"}
            (semantic_changed if semantic(old_content, old_refs) != semantic(new_content, new_refs) else revision_only).append(record_id)
        else:
            errors.append(issue("execution_mutated", record_id,
                                "Execution records are snapshots; append a new ID instead of changing a result"))
    scope_changed = semantic(before["scope"]) != semantic(after["scope"])
    seeds = set(added + removed + changed) | code_seeds
    if scope_changed:
        seeds.update(old)
        seeds.update(new)
    edges = dependencies(before)
    for source, targets in dependencies(after).items():
        edges[source].update(targets)
    affected, queue = set(seeds), deque(seeds)
    while queue:
        for target in edges[queue.popleft()]:
            if target not in affected:
                affected.add(target)
                queue.append(target)
    code_affected, queue = set(code_seeds), deque(code_seeds)
    while queue:
        for target in edges[queue.popleft()]:
            if target not in code_affected:
                code_affected.add(target)
                queue.append(target)
    stale = []
    for record in after.get("executions", []):
        reasons = snapshot_staleness(after, record)
        if record["id"] in old and record["case_id"] in code_affected:
            reasons.append("code_path_changed_requires_reverification")
        if reasons:
            stale.append({"id": record["id"], "reasons": reasons})
    return {"ok": not errors, "added": added, "changed": changed, "removed": removed,
            "semantic_changed": semantic_changed, "revision_only": revision_only,
            "scope_changed": scope_changed, "affected": sorted(affected),
            "affected_downstream": sorted(affected - seeds), "stale_executions": stale,
            "changed_paths": changed_paths, "code_affected_nodes": sorted(code_affected),
            "unmapped_changed_paths": unmapped_paths,
            "before_digest": digest(before), "after_digest": digest(after),
            "errors": errors, "warnings": warnings, "limitation": LIMITATION,
            "digest_note": "Node/reference array reordering is ignored by impact comparison; digest retains array order and can conservatively stale execution records. Scope changes affect all nodes."}


def evidence(data, project_root=None, code_commit=None):
    output = []
    for record in data.get("executions", []):
        reasons = snapshot_staleness(data, record)
        if code_commit is not None and record["code_commit"].lower() != code_commit.lower():
            reasons.append("code_commit_changed")
        artifact = project_file(record["artifact"], project_root)
        missing = artifact is not None and not artifact.is_file()
        if missing:
            reasons.append("artifact_missing")
        if code_commit is None:
            reasons.append("target_code_commit_unknown")
        if project_root is None:
            reasons.append("artifact_existence_unverified")
        freshness = ("stale" if any(r.endswith("changed") or r == "case_removed" for r in reasons)
                     else "missing_artifact" if missing else "unverified" if reasons else "matching_record")
        output.append({"id": record["id"], "case_id": record["case_id"],
                       "reported_result": record["result"], "freshness": freshness,
                       "reasons": reasons, "artifact": record["artifact"]})
    return output


def cell(value):
    text = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(
        "|", "&#124;").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def source_marker(source, project_root=None):
    source = resolve_path(source)
    if project_root is not None:
        root = resolve_path(project_root)
        if source.is_relative_to(root):
            relative = source.relative_to(root).as_posix()
            return f"<!-- generated by domain-spec-workflow; source-project-relative: {relative} -->"
    return f"<!-- generated by domain-spec-workflow; source: {source} -->"


def render_markdown(data, source, project_root=None, code_commit=None):
    rows = [source_marker(source, project_root),
            "# Domain specification and traceability", "", "Generated view. Edit the source manifest; keep manually authored rationale in a separate file.",
            "", LIMITATION, "", f"Spec digest: `{digest(data)}`",
            f"Target code commit: `{code_commit or 'unknown / unverified'}`", "",
            "Array order participates in the digest. Unrelated specification edits can conservatively stale old records.",
            "", "## Scope", "", cell(data["scope"]["purpose"]), ""]
    for key in ("in_scope", "out_of_scope", "assumptions"):
        rows.append(f"- {key}: {cell(data['scope'][key]) or '(none recorded)'}")

    def table(title, headers, values):
        rows.extend(["", "## " + title, "", "| " + " | ".join(headers) + " |",
                     "| " + " | ".join("---" for _ in headers) + " |"])
        count = 0
        for row in values:
            rows.append("| " + " | ".join(cell(v) for v in row) + " |")
            count += 1
        if count == 0:
            rows.append("| " + " | ".join(["None recorded"] + [""] * (len(headers) - 1)) + " |")

    table("Contexts", ["ID / revision", "Namespace", "Label", "Responsibility"],
          ((f"{r['id']}@{r['revision']}", r["key"], r["label"], r["responsibility"]) for r in data["contexts"]))
    common = ["ID / revision", "Semantic name", "Context", "Status"]

    def base(record):
        return [f"{record['id']}@{record['revision']}", record["name"], record["context_id"], record["status"]]

    table("Domain concepts", common + ["Definition"],
          (base(r) + [r["definition"]] for r in data["concepts"]))
    table("Domain rules", common + ["Concepts", "Statement"],
          (base(r) + [r["concept_ids"], r["statement"]] for r in data["rules"]))
    table("US — user stories", common + ["Concepts", "Role", "Capability", "Benefit"],
          (base(r) + [r["concept_ids"], r["role"], r["capability"], r["benefit"]] for r in data["stories"]))
    table("AC — acceptance criteria", common + ["US", "Rules", "Concepts", "Condition", "Expected"],
          (base(r) + [r["story_ids"] or "(rule-derived; no US)", r["rule_ids"], r["concept_ids"],
                      r["condition"], r["expected"]] for r in data["criteria"]))
    table("TC — test cases", common + ["AC", "Given", "When", "Then", "Automation"],
          (base(r) + [r["criterion_ids"], r["given"], r["when"], r["then"],
                      (r["automation"]["path"] + " :: " + r["automation"]["symbol"])
                      if r.get("automation") else "not automated"] for r in data["cases"]))
    table("Implementation links", common + ["AC", "Path", "Symbol"],
          (base(r) + [r["criterion_ids"], r["path"], r["symbol"]] for r in data.get("implementations", [])))
    records = evidence(data, project_root, code_commit)
    reported_cases = {r["case_id"] for r in records}
    table("Execution records — reported results, never automatic acceptance",
          ["Execution", "TC", "Reported result", "Freshness", "Reasons", "Artifact"],
          ([r["id"], r["case_id"], r["reported_result"], r["freshness"], r["reasons"], r["artifact"]]
           for r in records))
    rows.extend(["", "A `case_removed` record refers to a case absent from the current baseline "
                 "(historical or unknown); review earlier snapshots before interpreting it."])
    table("Cases without execution records", ["TC", "Evidence state"],
          ((r["id"], "missing / not executed") for r in data["cases"] if r["id"] not in reported_cases))
    table("Structural link coverage", ["Layer", "Uncovered IDs"],
          ((key, values or "none; links alone do not prove acceptance") for key, values in
           (("US without AC", validate(data)["coverage"]["uncovered_stories"]),
            ("AC without TC", validate(data)["coverage"]["uncovered_criteria"]))))
    return "\n".join(rows) + "\n", records


def write_render(data, source, output, project_root=None, code_commit=None):
    source = resolve_path(source)
    destination = Path(output)
    if destination.suffix.lower() != ".md":
        raise InputError("Render output must be an explicit .md file")
    if destination.is_symlink():
        raise InputError("Refusing a symlink output")
    resolved = resolve_path(destination)
    protected = {source}
    roots = {source.parent, resolve_path(project_root)} if project_root else {source.parent}
    # Protect both spec-relative and project-root-relative input paths.
    for group in ("implementations", "cases", "executions"):
        for record in data.get(group, []):
            value = (record.get("automation") or {}).get("path") if group == "cases" else record.get(
                "artifact" if group == "executions" else "path")
            if value:
                protected.update(project_file(value, root) for root in roots)
    if resolved in protected:
        raise InputError("Refusing to overwrite source spec, implementation, automation or artifact")
    markers = (source_marker(source, project_root) + "\n", source_marker(source) + "\n")
    if destination.exists():
        if not destination.is_file() or not destination.read_text(encoding="utf-8").startswith(markers):
            raise InputError("Refusing to overwrite an existing file not generated for this exact source")
        if destination.stat().st_nlink > 1:
            raise InputError("Refusing a hard-linked output")
    markdown, records = render_markdown(data, source, project_root, code_commit)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markdown, encoding="utf-8")
    return records


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError(message)


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("dest")
    init.add_argument("--purpose", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("spec")
    check.add_argument("--project-root")
    check.add_argument("--require-coverage", action="store_true")
    compare = subparsers.add_parser("impact")
    compare.add_argument("before")
    compare.add_argument("after")
    compare.add_argument("--changed-path", action="append", default=[])
    render = subparsers.add_parser("render")
    render.add_argument("spec")
    render.add_argument("--output", required=True)
    render.add_argument("--project-root")
    render.add_argument("--code-commit")
    args = None
    try:
        args = parser.parse_args(argv)
        if args.command == "init":
            if not args.purpose.strip():
                raise InputError("Purpose must be nonblank")
            data = read_spec(resolve_path(__file__).parents[1] / "assets" / "spec.template.json")
            data["scope"]["purpose"] = args.purpose
            destination = Path(args.dest)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            result = {"ok": True, "path": str(resolve_path(destination)), "spec_digest": digest(data),
                      "limitation": LIMITATION}
        elif args.command == "impact":
            result = impact(read_spec(args.before), read_spec(args.after), args.changed_path)
        else:
            data = read_spec(args.spec)
            result = validate(data, args.project_root, getattr(args, "require_coverage", False))
            if args.command == "render" and result["ok"]:
                if args.code_commit is not None and SHA.fullmatch(args.code_commit) is None:
                    raise InputError("--code-commit must be a full 40-hex Git SHA")
                records = write_render(data, args.spec, args.output, args.project_root, args.code_commit)
                result.update({"output": str(resolve_path(args.output)), "evidence": records})
        result["command"] = args.command
    except (InputError, OSError, UnicodeError) as exc:
        result = {"ok": False, "command": args.command if args else None,
                  "errors": [issue("input_error", "", str(exc))], "warnings": [], "limitation": LIMITATION}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
