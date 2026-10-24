"""Regression tests for traceability boundaries, evidence state and safe output."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "domain-spec-workflow"
SCRIPT = SKILL / "scripts" / "spec_workflow.py"
MODULE = importlib.util.spec_from_file_location("spec_workflow", SCRIPT)
workflow = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(workflow)
EXAMPLE = json.loads((SKILL / "examples" / "inventory" / "spec.json").read_text())
COMMIT = "a" * 40


class SpecWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(EXAMPLE)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, data=None, name="spec.json"):
        target = self.root / name
        target.write_text(json.dumps(self.data if data is None else data), encoding="utf-8")
        return target

    def cli(self, *arguments, ok=True):
        run = subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)],
                             capture_output=True, text=True, check=False)
        self.assertNotIn("Traceback", run.stderr + run.stdout)
        result = json.loads(run.stdout)
        self.assertEqual(result["ok"], ok, run.stdout + run.stderr)
        self.assertEqual(run.returncode, 0 if ok else 1, run.stderr)
        return result

    def codes(self, data=None, **kwargs):
        return {e["code"] for e in workflow.validate(self.data if data is None else data, **kwargs)["errors"]}

    def add_implementation(self):
        (self.root / "inventory.py").write_text("# placeholder; no behavior claimed\n")
        self.data["implementations"] = [{
            "id": "IMPL-RESERVE", "context_id": "CTX-INVENTORY",
            "name": "inventory.reservation.implementation", "revision": 1, "status": "draft",
            "criterion_ids": ["AC-NO-OVERSELL"], "path": "inventory.py", "symbol": "reserve"}]

    def add_execution(self, result="passed", artifact="result.txt"):
        record = {"id": "RUN-1", "case_id": "TC-LAST-UNIT", "case_revision": 1,
                  "spec_digest": workflow.digest(self.data), "code_commit": COMMIT,
                  "environment": "fixture only; not a business execution",
                  "command": ["never-run-this-command", "--fixture"], "result": result,
                  "artifact": artifact, "recorded_at": "2026-10-24T09:00:00+08:00"}
        self.data["executions"] = [record]
        (self.root / artifact).write_text("Fixture record; does not prove inventory acceptance\n")
        return record

    def test_many_to_many_example_has_only_structural_coverage(self):
        result = self.cli("check", SKILL / "examples" / "inventory" / "spec.json", "--require-coverage")
        self.assertTrue(result["coverage"]["complete"])
        self.assertEqual(result["coverage"]["kind"], "structural_links_only")
        self.assertEqual(result["counts"]["executions"], 0)
        self.assertIn("do not prove", result["limitation"])
        shared_criterion = next(item for item in self.data["criteria"] if item["id"] == "AC-RESTORE")
        shared_case = next(item for item in self.data["cases"] if item["id"] == "TC-RELEASE-TWICE")
        self.assertEqual(set(shared_criterion["story_ids"]), {"US-RESERVE", "US-RELEASE"})
        self.assertEqual(set(shared_case["criterion_ids"]), {"AC-RELEASE-ONCE", "AC-RESTORE"})

    def test_init_allows_domain_first_stage_and_refuses_overwrite(self):
        target = self.root / "nested" / "spec.json"
        self.cli("init", target, "--purpose", "Clarify reservation language")
        self.cli("check", target, "--require-coverage")
        original = target.read_bytes()
        self.assertEqual(json.loads(original)["stories"], [])
        self.cli("init", target, "--purpose", "A different scope", ok=False)
        self.assertEqual(target.read_bytes(), original)
        self.cli("init", self.root / "empty.json", "--purpose", "  ", ok=False)

    def test_digest_canonicalizes_optional_arrays_and_excludes_executions(self):
        absent = copy.deepcopy(self.data)
        absent.pop("implementations")
        absent.pop("executions")
        self.assertEqual(workflow.digest(absent), workflow.digest(self.data))
        original = workflow.digest(self.data)
        self.add_execution()
        self.assertEqual(original, workflow.digest(self.data))
        self.data["rules"][0]["statement"] += " (revised)"
        self.assertNotEqual(original, workflow.digest(self.data))

    def test_types_names_namespaces_and_identity_are_validated(self):
        changes = [
            ("concepts", "revision", True, "revision"),
            ("concepts", "revision", 0, "revision"),
            ("concepts", "definition", " ", "required_string"),
            ("concepts", "status", "accepted", "status"),
            ("concepts", "name", "Inventory.Stock", "semantic_name"),
            ("concepts", "name", "checkout.stock-item", "context_namespace"),
            ("concepts", "context_id", "CON-STOCK", "context_reference"),
            ("contexts", "key", "库存", "context_key"),
        ]
        for group, field, value, code in changes:
            with self.subTest(group=group, field=field, value=value):
                altered = copy.deepcopy(self.data)
                altered[group][0][field] = value
                self.assertIn(code, self.codes(altered))
        self.data["concepts"][1]["id"] = self.data["concepts"][0]["id"]
        self.assertIn("duplicate_id", self.codes())

    def test_references_are_typed_explicit_and_nonempty(self):
        for values, code in (([], "reference_array"), (["MISSING"], "reference"),
                             (["US-RESERVE"], "reference"), ([{}], "reference"),
                             (["CON-STOCK", "CON-STOCK"], "duplicate_reference")):
            with self.subTest(values=values):
                altered = copy.deepcopy(self.data)
                altered["rules"][0]["concept_ids"] = values
                self.assertIn(code, self.codes(altered))

    def test_foreign_concepts_require_review_without_forcing_vocabulary(self):
        self.data["contexts"].append({"id": "CTX-CHECKOUT", "key": "checkout",
                                      "label": "Checkout", "responsibility": "Own checkout", "revision": 1})
        self.data["stories"][0].update(context_id="CTX-CHECKOUT", name="checkout.reserve-stock")
        result = workflow.validate(self.data)
        self.assertTrue(result["ok"])
        self.assertIn("cross_context_review", {w["code"] for w in result["warnings"]})
        self.data["contexts"][1]["key"] = "inventory"
        self.assertIn("duplicate_context_key", self.codes())

    def test_rule_derived_criteria_need_no_fabricated_user_story(self):
        self.data["stories"] = []
        for criterion in self.data["criteria"]:
            criterion["story_ids"] = []
        result = workflow.validate(self.data, require_coverage=True)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["coverage"]["complete"])
        del self.data["criteria"][0]["story_ids"]
        self.assertIn("reference_array", self.codes())

    def test_coverage_gate_reports_unlinked_records_and_remains_distinct_from_proof(self):
        self.data["cases"] = []
        without_gate = workflow.validate(self.data)
        self.assertTrue(without_gate["ok"])
        gated = workflow.validate(self.data, require_coverage=True)
        self.assertFalse(gated["ok"])
        self.assertEqual(set(gated["coverage"]["uncovered_criteria"]),
                         {item["id"] for item in self.data["criteria"]})
        self.data["criteria"] = []
        self.assertEqual(len(workflow.validate(self.data)["coverage"]["uncovered_stories"]), 2)

    def test_project_paths_reject_traversal_absolute_windows_and_null(self):
        self.add_implementation()
        for path in ("../secret", "/tmp/secret", "C:\\secret", "nested/../../secret", "bad\x00file"):
            with self.subTest(path=path):
                self.data["implementations"][0]["path"] = path
                self.assertIn("unsafe_path", self.codes(project_root=self.root))

    def test_symlink_escape_and_missing_files_are_errors(self):
        self.add_implementation()
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        self.data["implementations"][0]["path"] = "escape/not-in-project.py"
        self.assertIn("unsafe_path", self.codes(project_root=self.root))
        self.data["implementations"][0]["path"] = "missing.py"
        self.assertIn("missing_file", self.codes(project_root=self.root))
        self.assertIn("project_root", self.codes(project_root=self.root / "absent"))
        self.data["implementations"] = []
        self.data["cases"][0]["automation"] = {"path": "missing.py", "symbol": "test_reserve"}
        self.assertIn("missing_file", self.codes(project_root=self.root))

    def test_symlink_loops_in_inputs_roots_and_outputs_return_json_errors(self):
        (self.root / "loop").symlink_to("loop")
        self.add_implementation()
        self.data["implementations"][0]["path"] = "loop/inventory.py"
        source = self.write()
        for args in (("check", source, "--project-root", self.root),
                     ("render", source, "--project-root", self.root,
                      "--output", self.root / "generated.md")):
            result = self.cli(*args, ok=False)
            self.assertIn("unsafe_path", {e["code"] for e in result["errors"]})
        self.data["implementations"] = []
        source = self.write()
        result = self.cli("check", source, "--project-root", self.root / "loop", ok=False)
        self.assertIn("unsafe_path", {e["code"] for e in result["errors"]})
        self.cli("render", source, "--output", self.root / "loop" / "generated.md", ok=False)
        self.cli("check", self.root / "loop" / "spec.json", ok=False)

    def test_execution_fields_are_typed_and_ids_globally_unique(self):
        self.add_execution()
        for field, value, code in (("case_revision", True, "case_revision"),
                                    ("code_commit", "abcd", "code_commit"),
                                    ("recorded_at", "2026-10-24T09:00:00", "recorded_at"),
                                    ("result", "accepted", "result"),
                                    ("command", [], "command"),
                                    ("spec_digest", "sha256:wrong", "spec_digest"),
                                    ("case_id", "US-RESERVE", "case_reference"),
                                    ("id", "CON-STOCK", "duplicate_id")):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.data)
                altered["executions"][0][field] = value
                self.assertIn(code, self.codes(altered))

    def test_matching_record_requires_commit_digest_case_and_artifact(self):
        self.add_execution()
        record = workflow.evidence(self.data, self.root, COMMIT)[0]
        self.assertEqual(record["freshness"], "matching_record")
        self.assertEqual(record["reported_result"], "passed")
        unbound = workflow.evidence(self.data)[0]
        self.assertEqual(unbound["freshness"], "unverified")
        self.assertIn("target_code_commit_unknown", unbound["reasons"])
        self.assertIn("artifact_existence_unverified", unbound["reasons"])
        self.assertEqual(workflow.evidence(self.data, self.root, "b" * 40)[0]["freshness"], "stale")

    def test_failed_blocked_and_not_run_results_remain_visible(self):
        for status in ("failed", "blocked", "not_run"):
            with self.subTest(status=status):
                self.add_execution(status)
                record = workflow.evidence(self.data, self.root, COMMIT)[0]
                self.assertEqual(record["reported_result"], status)
                self.assertEqual(record["freshness"], "matching_record")

    def test_missing_artifact_is_visible_without_erasing_claimed_failure(self):
        self.add_execution("failed")
        (self.root / "result.txt").unlink()
        check = workflow.validate(self.data, self.root)
        self.assertTrue(check["ok"])
        self.assertIn("missing_artifact", {w["code"] for w in check["warnings"]})
        record = workflow.evidence(self.data, self.root, COMMIT)[0]
        self.assertEqual(record["freshness"], "missing_artifact")
        self.assertEqual(record["reported_result"], "failed")

    def test_spec_and_case_changes_stale_records(self):
        self.add_execution()
        before = copy.deepcopy(self.data)
        self.data["cases"][0]["revision"] = 2
        self.data["cases"][0]["then"] += "; inspect both request outcomes"
        result = workflow.impact(before, self.data)
        self.assertTrue(result["ok"])
        self.assertEqual(result["stale_executions"][0]["id"], "RUN-1")
        self.assertEqual(set(result["stale_executions"][0]["reasons"]),
                         {"case_revision_changed", "spec_digest_changed"})

    def test_content_changes_require_higher_revision_and_propagate_downstream(self):
        before = copy.deepcopy(self.data)
        self.data["concepts"][0]["definition"] += "; quantities are integers"
        result = workflow.impact(before, self.data)
        self.assertFalse(result["ok"])
        self.assertIn("revision_not_increased", {e["code"] for e in result["errors"]})
        self.assertIn("TC-LAST-UNIT", result["affected_downstream"])
        self.data["concepts"][0]["revision"] += 1
        self.assertTrue(workflow.impact(before, self.data)["ok"])

    def test_rename_preserves_identity_and_revision_only_changes_are_reported(self):
        before = copy.deepcopy(self.data)
        self.data["concepts"][0].update(name="inventory.stock-at-location", revision=2)
        result = workflow.impact(before, self.data)
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["semantic_changed"], ["CON-STOCK"])
        self.data = copy.deepcopy(before)
        self.data["concepts"][0]["revision"] = 2
        self.assertEqual(workflow.impact(before, self.data)["revision_only"], ["CON-STOCK"])

    def test_removal_is_reported_even_when_remaining_links_are_broken(self):
        before = copy.deepcopy(self.data)
        self.data["concepts"].pop(0)
        result = workflow.impact(before, self.data)
        self.assertFalse(result["ok"])
        self.assertIn("CON-STOCK", result["removed"])
        self.assertIn("reference", {e["code"] for e in result["errors"]})

    def test_removed_case_preserves_historical_failed_execution_as_stale(self):
        self.add_execution("failed")
        before = copy.deepcopy(self.data)
        self.data["cases"] = [case for case in self.data["cases"] if case["id"] != "TC-LAST-UNIT"]
        self.assertTrue(workflow.validate(self.data, self.root, require_coverage=True)["ok"])
        previous = self.write(before, "before.json")
        current = self.write()
        result = self.cli("impact", previous, current)
        self.assertEqual(result["removed"], ["TC-LAST-UNIT"])
        self.assertEqual(result["stale_executions"][0]["id"], "RUN-1")
        self.assertIn("case_removed", result["stale_executions"][0]["reasons"])
        self.assertIn("historical_case_reference", {w["code"] for w in result["warnings"]})
        output = self.root / "generated.md"
        rendered = self.cli("render", current, "--output", output, "--project-root", self.root,
                            "--code-commit", COMMIT)
        self.assertEqual(rendered["evidence"][0]["reported_result"], "failed")
        self.assertEqual(rendered["evidence"][0]["freshness"], "stale")
        self.assertIn("case absent from the current baseline", output.read_text())
        self.assertIn("| RUN-1 | TC-LAST-UNIT | failed | stale |", output.read_text())

    def test_unknown_case_execution_is_stale_but_wrong_type_reference_is_invalid(self):
        self.add_execution()
        record = self.data["executions"][0]
        record["case_id"] = "UNKNOWN-HISTORICAL-CASE"
        check = workflow.validate(self.data, self.root)
        self.assertTrue(check["ok"])
        self.assertIn("historical_case_reference", {w["code"] for w in check["warnings"]})
        evidence = workflow.evidence(self.data, self.root, COMMIT)[0]
        self.assertEqual(evidence["freshness"], "stale")
        self.assertIn("case_removed", evidence["reasons"])
        record["case_id"] = "US-RESERVE"
        self.assertIn("case_reference", self.codes())
        record["case_id"] = " "
        self.assertIn("required_string", self.codes())

    def test_node_and_reference_reordering_does_not_count_as_semantic_change(self):
        self.add_execution()
        before = copy.deepcopy(self.data)
        self.data["concepts"].reverse()
        next(item for item in self.data["criteria"] if item["id"] == "AC-RESTORE")["story_ids"].reverse()
        result = workflow.impact(before, self.data)
        self.assertTrue(result["ok"])
        self.assertEqual(result["changed"], [])
        self.assertEqual(result["affected"], [])
        self.assertNotEqual(result["before_digest"], result["after_digest"])
        self.assertEqual(result["stale_executions"][0]["reasons"], ["spec_digest_changed"])

    def test_unknown_reference_like_extensions_remain_ordinary_content(self):
        self.data["concepts"][0]["source_ids"] = [{"id": "REQ-1"}, 7, None, "external"]
        self.data["concepts"][0]["metadata"] = {"concept_ids": [{"external": True}, "not-a-local-ref"]}
        self.data["concepts"][1]["source_ids"] = ["CON-STOCK"]
        source = self.write()
        self.cli("check", source)
        unchanged = self.cli("impact", source, source)
        self.assertEqual(unchanged["changed"], [])
        before = copy.deepcopy(self.data)
        self.data["concepts"][0]["source_ids"].reverse()
        result = workflow.impact(before, self.data)
        self.assertFalse(result["ok"])
        self.assertEqual(result["changed"], ["CON-STOCK"])
        self.assertNotIn("CON-RESERVATION", result["affected_downstream"])
        self.data["concepts"][0]["revision"] += 1
        self.assertTrue(workflow.impact(before, self.data)["ok"])

    def test_duplicate_json_keys_are_rejected_at_every_object_depth(self):
        source = self.write()
        original = source.read_text()
        duplicates = (
            original.replace('"schema_version": "1.0"', '"schema_version": "0", "schema_version": "1.0"', 1),
            original.replace('"revision": 1', '"revision": 99, "revision": 1', 1),
            original.replace('"schema_version": "1.0"',
                             '"schema_version": "1.0", "extension": {"key": 1, "key": 2}', 1),
        )
        for index, text in enumerate(duplicates):
            with self.subTest(index=index):
                duplicate = self.root / "duplicate.json"
                duplicate.write_text(text)
                for args in (("check", duplicate), ("impact", source, duplicate),
                             ("render", duplicate, "--output", self.root / "generated.md")):
                    result = self.cli(*args, ok=False)
                    self.assertIn("Duplicate JSON object key", result["errors"][0]["message"])

    def test_scope_change_conservatively_affects_all_nodes(self):
        before = copy.deepcopy(self.data)
        self.data["scope"]["in_scope"].append("Warehouse transfer")
        result = workflow.impact(before, self.data)
        self.assertTrue(result["scope_changed"])
        self.assertEqual(set(result["affected"]), set(workflow.nodes(self.data)))

    def test_implementation_change_reaches_criteria_cases_and_execution(self):
        self.add_implementation()
        self.add_execution()
        before = copy.deepcopy(self.data)
        self.data["implementations"][0].update(symbol="reserve_atomically", revision=2)
        result = workflow.impact(before, self.data)
        self.assertTrue(result["ok"])
        self.assertTrue({"AC-NO-OVERSELL", "TC-LAST-UNIT", "RUN-1"}.issubset(result["affected_downstream"]))

    def test_same_semantic_name_can_be_shared_by_story_and_implementation(self):
        self.add_implementation()
        self.data["implementations"][0]["name"] = self.data["stories"][0]["name"]
        self.assertTrue(workflow.validate(self.data, self.root)["ok"])
        self.data["stories"][1]["name"] = self.data["stories"][0]["name"]
        self.assertIn("duplicate_name", self.codes())

    def test_code_only_change_propagates_without_revising_business_meaning(self):
        self.add_implementation()
        self.add_execution()
        before = copy.deepcopy(self.data)
        result = workflow.impact(before, self.data, ["./inventory.py", "unknown.py"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["changed"], [])
        self.assertEqual(result["changed_paths"], ["inventory.py", "unknown.py"])
        self.assertEqual(result["unmapped_changed_paths"], ["unknown.py"])
        self.assertIn("TC-LAST-UNIT", result["code_affected_nodes"])
        self.assertEqual(result["stale_executions"][0]["reasons"],
                         ["code_path_changed_requires_reverification"])
        source = self.write()
        cli_result = self.cli("impact", source, source, "--changed-path", "inventory.py",
                              "--changed-path", "unknown.py")
        self.assertEqual(cli_result["changed_paths"], result["changed_paths"])
        self.cli("impact", source, source, "--changed-path", "../outside.py", ok=False)

    def test_changed_automation_path_maps_case_and_new_run_is_not_mechanically_stale(self):
        self.data["cases"][0]["automation"] = {"path": "test_inventory.py", "symbol": "test_reserve"}
        self.add_execution()
        before = copy.deepcopy(self.data)
        second = copy.deepcopy(self.data["executions"][0])
        second["id"] = "RUN-2"
        second["code_commit"] = "b" * 40
        self.data["executions"].append(second)
        result = workflow.impact(before, self.data, ["test_inventory.py"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["unmapped_changed_paths"], [])
        self.assertIn("TC-LAST-UNIT", result["code_affected_nodes"])
        self.assertEqual([r["id"] for r in result["stale_executions"]], ["RUN-1"])

    def test_execution_records_cannot_be_rewritten_as_new_success(self):
        self.add_execution("failed")
        before = copy.deepcopy(self.data)
        self.data["executions"][0]["result"] = "passed"
        result = workflow.impact(before, self.data)
        self.assertFalse(result["ok"])
        self.assertIn("execution_mutated", {e["code"] for e in result["errors"]})

    def test_render_requires_explicit_safe_generated_output(self):
        source = self.write(name="spec.md")
        self.cli("render", source, "--output", source, ok=False)
        user_file = self.root / "rationale.md"
        user_file.write_text("User rationale that must survive\n")
        self.cli("render", source, "--output", user_file, ok=False)
        self.assertEqual(user_file.read_text(), "User rationale that must survive\n")
        generated = self.root / "generated.md"
        self.cli("render", source, "--output", generated)
        self.cli("render", source, "--output", generated)
        other_source = self.write(name="different-source.json")
        self.cli("render", other_source, "--output", generated, ok=False)
        symlink = self.root / "link.md"
        symlink.symlink_to(user_file)
        self.cli("render", source, "--output", symlink, ok=False)

    def test_generated_view_can_refresh_after_project_is_copied_elsewhere(self):
        original = self.root / "original"
        (original / "specs" / "inventory").mkdir(parents=True)
        source = original / "specs" / "inventory" / "spec.json"
        source.write_text(json.dumps(self.data))
        output = original / "docs" / "generated.md"
        self.cli("render", source, "--output", output, "--project-root", original)
        marker = "<!-- generated by domain-spec-workflow; source-project-relative: specs/inventory/spec.json -->"
        self.assertEqual(output.read_text().splitlines()[0], marker)
        copied = self.root / "copied-checkout"
        shutil.copytree(original, copied)
        relocated_source = copied / "specs" / "inventory" / "spec.json"
        relocated_output = copied / "docs" / "generated.md"
        self.cli("render", relocated_source, "--output", relocated_output, "--project-root", copied)
        self.assertEqual(relocated_output.read_text().splitlines()[0], marker)
        self.assertNotIn(str(original), relocated_output.read_text())

    def test_relative_marker_rejects_other_source_and_legacy_only_accepts_exact_path(self):
        source = self.write()
        output = self.root / "generated.md"
        self.cli("render", source, "--output", output)
        legacy = output.read_text()
        self.assertIn(f"source: {source.resolve()}", legacy.splitlines()[0])
        self.cli("render", source, "--output", output, "--project-root", self.root)
        self.assertIn("source-project-relative: spec.json", output.read_text().splitlines()[0])
        other_source = self.write(name="different.json")
        self.cli("render", other_source, "--output", output, "--project-root", self.root, ok=False)
        wrong_relative = output.read_text().replace("source-project-relative: spec.json",
                                                  "source-project-relative: other/spec.json", 1)
        output.write_text(wrong_relative)
        self.cli("render", source, "--output", output, "--project-root", self.root, ok=False)
        self.assertEqual(output.read_text(), wrong_relative)
        wrong_absolute = legacy.replace(str(source.resolve()), "/another-checkout/spec.json", 1)
        output.write_text(wrong_absolute)
        self.cli("render", source, "--output", output, "--project-root", self.root, ok=False)
        self.assertEqual(output.read_text(), wrong_absolute)

    def test_source_outside_explicit_project_root_keeps_absolute_identity(self):
        source = self.write()
        project = self.root / "project"
        project.mkdir()
        output = project / "generated.md"
        self.cli("render", source, "--output", output, "--project-root", project)
        self.assertEqual(output.read_text().splitlines()[0],
                         f"<!-- generated by domain-spec-workflow; source: {source.resolve()} -->")
        self.cli("render", source, "--output", output, "--project-root", project)

    def test_render_refuses_implementation_automation_and_artifact_collisions(self):
        self.add_implementation()
        for path in ("implementation.md", "automation.md", "artifact.md"):
            (self.root / path).write_text("Preserve this input\n")
        self.data["implementations"][0]["path"] = "implementation.md"
        self.data["cases"][0]["automation"] = {"path": "automation.md", "symbol": "test_reserve"}
        self.add_execution(artifact="artifact.md")
        source = self.write()
        originals = {p: (self.root / p).read_bytes() for p in ("implementation.md", "automation.md", "artifact.md")}
        for path in originals:
            self.cli("render", source, "--output", self.root / path, "--project-root", self.root, ok=False)
            self.assertEqual((self.root / path).read_bytes(), originals[path])

    def test_render_escapes_tables_and_shows_missing_stale_and_failed_evidence(self):
        self.data["concepts"][0]["definition"] = "SKU | location\n<script>"
        self.add_execution("failed")
        self.data["executions"][0]["case_revision"] = 99
        source, output = self.write(), self.root / "generated.md"
        result = self.cli("render", source, "--output", output, "--project-root", self.root,
                          "--code-commit", COMMIT)
        rendered = output.read_text()
        self.assertIn("SKU &#124; location<br>&lt;script&gt;", rendered)
        self.assertIn("missing / not executed", rendered)
        self.assertIn("failed", rendered)
        self.assertEqual(result["evidence"][0]["freshness"], "stale")
        self.assertIn("never automatic acceptance", rendered)

    def test_manifest_commands_are_documentary_and_never_executed(self):
        self.add_execution()
        marker = self.root / "must-not-exist"
        self.data["executions"][0]["command"] = [sys.executable, "-c", f"open({str(marker)!r}, 'w').write('oops')"]
        source = self.write()
        self.cli("check", source, "--project-root", self.root)
        self.cli("render", source, "--output", self.root / "generated.md", "--project-root", self.root,
                 "--code-commit", COMMIT)
        self.assertFalse(marker.exists())

    def test_malformed_json_missing_data_and_cli_errors_return_json(self):
        self.cli("check", self.root / "absent.json", ok=False)
        broken = self.root / "broken.json"
        for text in ("{", "[]", "{}", '{"scope": []}'):
            with self.subTest(text=text):
                broken.write_text(text)
                self.cli("check", broken, ok=False)
        self.cli("check", ok=False)
        self.cli("bogus-command", ok=False)
        self.cli("render", self.write(), "--output", self.root / "out.md", "--code-commit", "HEAD", ok=False)

    def test_malformed_nested_values_are_controlled_validation_errors(self):
        for group in workflow.GROUPS:
            for invalid in (None, "wrong", 1, {}, [None], ["wrong"], [{}]):
                with self.subTest(group=group, value=invalid):
                    altered = copy.deepcopy(self.data)
                    altered[group] = invalid
                    result = workflow.validate(altered)
                    self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
