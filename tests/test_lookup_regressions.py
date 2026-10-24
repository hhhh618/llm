"""Search results must keep PDF pages within a provable source and scope."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" /
          "test-verification-design" / "scripts" / "lookup.py")
SPEC = importlib.util.spec_from_file_location("testability_lookup", SCRIPT)
lookup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lookup)
GJB_SOURCE = "**来源：** 《GJB 2547B-2024 装备测试性工作通用要求》。\n"


class PageProvenanceTests(unittest.TestCase):
    def search_cli(self, query):
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--query", query, "--limit", "50"],
            text=True, capture_output=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def search_fixture(self, content, query="needle", limit=50):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "resources").mkdir()
            (root / "resources" / "fixture.md").write_text(content, encoding="utf-8")
            with patch.object(lookup, "ROOT", root):
                return lookup.search(query, limit)

    def test_current_cross_reference_summary_does_not_inherit_previous_pages(self):
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--query", "常见问法"],
            text=True, capture_output=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        match, = json.loads(process.stdout)["matches"]
        self.assertEqual(match["resource"], "resources/08-模板与案例.md")
        self.assertEqual(match["pdf_pages"], [])
        self.assertIsNone(match["pdf_page_system"])

    def test_existing_standard_id_and_title_metadata_keeps_marked_pages(self):
        # Exercise actual resources whose standard number precedes the book
        # title. Derive the section and page from their source marker, then
        # verify the CLI's provenance fields rather than matching output text.
        for prefix in ("03-", "04-", "05-", "06-"):
            path, = (lookup.ROOT / "resources").glob(prefix + "*.md")
            lines = path.read_text(encoding="utf-8").splitlines()
            marker = next(i for i, line in enumerate(lines)
                          if line.startswith("<!-- PDF第"))
            page = int(lines[marker].removeprefix("<!-- PDF第").removesuffix("页 -->"))
            heading = next(line.lstrip("# ") for line in lines[marker + 1:]
                           if line.startswith("## "))
            with self.subTest(resource=path.name):
                results = self.search_cli(heading)
                match, = [entry for entry in results["matches"]
                          if entry["resource"] == str(path.relative_to(lookup.ROOT))]
                self.assertEqual(match["pdf_pages"], [page])
                self.assertEqual(match["pdf_page_system"], "GJB 2547B-2024")

    def test_cited_standard_in_source_comment_does_not_claim_gjb_pages(self):
        result = self.search_cli("不能直接并入虚警统计")
        match, = result["matches"]
        self.assertEqual(match["resource"], "resources/06-使用与改进.md")
        self.assertEqual(match["pdf_pages"], [34, 57, 58])
        self.assertEqual(match["pdf_page_system"], "GJB 2547B-2024")

    def test_prose_citation_does_not_reassign_local_page_numbers(self):
        result = self.search_cli("各层次产品应制定准则")
        match, = result["matches"]
        self.assertEqual(match["resource"], "resources/04-设计与分析.md")
        # This line contains the primary document's PDF pages and a citation
        # to GJB/Z 190. Without a separate source declaration, remain cautious.
        self.assertEqual(match["pdf_pages"], [])
        self.assertIsNone(match["pdf_page_system"])

    def test_heading_hierarchy_inherits_parent_but_never_previous_sibling(self):
        result = self.search_fixture(GJB_SOURCE + """
<!-- PDF第10页 -->
<!-- PDF第12页 -->
## needle parent
parent needle
### needle child
child needle
<!-- PDF第20页 -->
### needle marked sibling
marked needle
### needle sibling
inherited needle
## needle new chapter
unknown needle
""")
        matches = result["matches"]
        self.assertEqual([match["pdf_pages"] for match in matches],
                         [[10, 12]] * 4 + [[20]] * 2 + [[10, 12]] * 2 + [[], []])
        self.assertIsNone(matches[-1]["pdf_page_system"])

    def test_explicit_title_and_local_source_pages_override_earlier_markers(self):
        result = self.search_fixture(GJB_SOURCE + """
<!-- PDF第10页 -->
## first
### needle title（PDF 40—41）
title needle
### next
来源：正文8.3（PDF第24页，印刷第19页）。
source needle
正文另见PDF第34页，needle。
""")
        self.assertEqual([match["pdf_pages"] for match in result["matches"]],
                         [[40, 41], [40, 41], [24], [34]])

    def test_unknown_document_source_does_not_default_to_gjb(self):
        result = self.search_fixture("<!-- PDF第8页 -->\n## needle\nneedle body\n")
        for match in result["matches"]:
            self.assertEqual(match["pdf_pages"], [])
            self.assertIsNone(match["pdf_page_system"])

    def test_multiple_standard_sources_are_never_merged(self):
        result = self.search_fixture(GJB_SOURCE + """
<!-- PDF第10页 -->
## GJB section
needle GJB 2547B-2024 PDF第10页；MIL-HDBK-2165 PDF第20页。
## MIL-HDBK-2165（PDF第17页）
needle MIL
## summary
needle unknown
""")
        mixed, mil, unknown = result["matches"]
        self.assertEqual(mixed["pdf_pages"], [])
        self.assertIsNone(mixed["pdf_page_system"])
        self.assertEqual(mil["pdf_pages"], [17])
        self.assertEqual(mil["pdf_page_system"], "MIL-HDBK-2165")
        self.assertEqual(unknown["pdf_pages"], [])

    def test_mixed_document_metadata_needs_a_local_source(self):
        content = ("**来源：** GJB 2547B-2024 和 MIL-HDBK-2165。\n"
                   "<!-- PDF第8页 -->\n## needle unknown\n"
                   "## GJB 2547B-2024（PDF第12页）\nneedle known\n")
        unknown, known = self.search_fixture(content)["matches"]
        self.assertEqual(unknown["pdf_pages"], [])
        self.assertEqual(known["pdf_pages"], [12])
        self.assertEqual(known["pdf_page_system"], "GJB 2547B-2024")

    def test_local_source_does_not_become_document_metadata(self):
        content = """# mixed
## GJB
来源：GJB 2547B-2024 PDF第10页。
needle known
## unknown
<!-- PDF第8页 -->
needle unknown
"""
        known, unknown = self.search_fixture(content)["matches"]
        self.assertEqual(known["pdf_pages"], [10])
        self.assertEqual(known["pdf_page_system"], "GJB 2547B-2024")
        self.assertEqual(unknown["pdf_pages"], [])
        self.assertIsNone(unknown["pdf_page_system"])

    def test_unrecognized_publication_cannot_reuse_a_known_source(self):
        fixtures = [
            GJB_SOURCE + "<!-- PDF第10页 -->\n## first\n"
            "来源：《另一份资料》（PDF第8页）。\nneedle\n",
            "**来源：** 《GJB 2547B-2024》与《另一份资料》。\n"
            "<!-- PDF第10页 -->\n## needle\n",
            GJB_SOURCE + "<!-- PDF第10页 -->\n## parent\n"
            "### 《另一份资料》（PDF第8页）\nneedle\n",
            GJB_SOURCE + "<!-- PDF第10页 -->\n## first\n"
            "来源：其他标准条款，PDF第8页。\nneedle\n",
        ]
        for content in fixtures:
            with self.subTest(content=content):
                match, = self.search_fixture(content)["matches"]
                self.assertEqual(match["pdf_pages"], [])
                self.assertIsNone(match["pdf_page_system"])

    def test_limit_and_output_shape_remain_compatible(self):
        result = self.search_fixture(GJB_SOURCE + "needle\nneedle\nneedle\n", limit=1)
        self.assertEqual(result["total_matches"], 3)
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(set(result["matches"][0]), {
            "resource", "line", "section", "pdf_pages", "pdf_page_system", "text"})

    def test_clause_only_source_uses_explicit_document_identity(self):
        content = GJB_SOURCE + "## local\n来源：A.5.2.4，PDF38。\nneedle\n"
        match, = self.search_fixture(content)["matches"]
        self.assertEqual(match["pdf_pages"], [38])
        self.assertEqual(match["pdf_page_system"], "GJB 2547B-2024")

    def test_source_subject_ends_before_commentary_about_another_standard(self):
        content = GJB_SOURCE + """
<!-- PDF第58页 -->
## local
来源：A.8.2.1.2。应按 GJB 1775 分类编码。
needle primary PDF第34页。
needle prose cites GJB 1775（PDF第58页）。
needle still primary
"""
        primary, ambiguous, unchanged = self.search_fixture(content)["matches"]
        self.assertEqual(primary["pdf_pages"], [34])
        self.assertEqual(primary["pdf_page_system"], "GJB 2547B-2024")
        self.assertEqual(ambiguous["pdf_pages"], [])
        self.assertIsNone(ambiguous["pdf_page_system"])
        self.assertEqual(unchanged["pdf_pages"], [58])
        self.assertEqual(unchanged["pdf_page_system"], "GJB 2547B-2024")


if __name__ == "__main__":
    unittest.main()
