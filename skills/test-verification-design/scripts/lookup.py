#!/usr/bin/env python3
"""Look up work items, standards, canonical domain terms, or resource notes."""
import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD = re.compile(
    r"GJB\s*(?:/Z\s*)?\d+[A-Z]?(?:\s*[-—–－]\s*\d{4})?"
    r"|MIL\s*[-—–－]\s*(?:HDBK|STD)\s*[-—–－]\s*\d+[A-Z]?(?:\s*[-—–－]\s*\d{4})?"
    r"|(?:ISO(?:/IEC)?(?:/IEEE)?|IEEE)\s*\d+(?:\.\d+)*(?:\s*[-:：—–－]\s*\d{4})?",
    re.IGNORECASE)
PDF_PAGES = re.compile(
    r"PDF\s*第?\s*(\d+(?:\s*[-—–~～]\s*\d+)?"
    r"(?:\s*[、,，]\s*\d+(?:\s*[-—–~～]\s*\d+)?)*)"
    r"(?:\s*页|(?=[\s，,。；;）)]|$))", re.IGNORECASE)


def standard_sources(text):
    """Read explicit standard identities; never infer GJB from a bare PDF page."""
    sources = set()
    for match in STANDARD.finditer(unicodedata.normalize("NFKC", text)):
        source = re.sub(r"\s+", "", match.group()).upper()
        source = re.sub(r"[—–－]", "-", source).replace("：", ":")
        if source.startswith("GJB"):
            source = re.sub(r"^(GJB(?:/Z)?)(?=\d)", r"\1 ", source)
        elif source.startswith(("IEEE", "ISO")):
            source = re.sub(r"^(IEEE|ISO(?:/IEC)?(?:/IEEE)?)(?=\d)", r"\1 ", source)
        sources.add(source)
    return sources


def explicit_pages(text):
    pages = set()
    for match in PDF_PAGES.finditer(text):
        for item in re.split(r"[、,，]", match.group(1)):
            bounds = [int(value) for value in re.split(r"[-—–~～]", item)]
            first, last = bounds[0], bounds[-1]
            if first < 1 or last < first or last - first > 1000:
                return []
            pages.update(range(first, last + 1))
    return sorted(pages)


def resolved_source(text, fallback=None):
    text = unicodedata.normalize("NFKC", text)
    sources = standard_sources(text)
    # An additional unnamed publication is still another source, even when its
    # title does not use a standard identifier understood by this index. A
    # directly preceding ID and title, e.g. GJB 2547B-2024《装备测试性...》,
    # identify one publication rather than two independent sources.
    for title in re.finditer(r"《([^》]+)》", text):
        if not standard_sources(title.group(1)):
            prefix = text[:title.start()].rstrip()
            if not any(match.end() == len(prefix) for match in STANDARD.finditer(prefix)):
                return None
    return next(iter(sources)) if len(sources) == 1 else None if sources else fallback


def source_statement(line):
    match = re.match(r"^(?:\*\*)?来源[：:](?:\*\*)?\s*(.*)", line)
    # Later sentences can discuss standards cited by the primary publication;
    # they do not redefine the source of this section's PDF page numbers.
    return match.group(1).split("。", 1)[0] if match else None


def document_source(lines):
    for line in lines:
        # Only document metadata can establish the root source. A declaration
        # inside a content section must remain local to that heading's scope.
        if re.match(r"^(?:#{2,6}\s|<!--\s*PDF)", line):
            break
        statement = source_statement(line)
        if statement is not None:
            return resolved_source(statement)
    return None


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())


def indexed_lookup(query, entries, id_key, name_keys):
    needle = normalized(query)
    if not needle:
        raise ValueError("检索词不得只包含空格或标点")
    exact, partial = [], []
    for entry in entries:
        names = [entry[id_key], *entry.get("aliases", [])]
        names.extend(entry.get(key, "") for key in name_keys)
        names = [normalized(name) for name in names if isinstance(name, str) and name]
        if needle in names:
            exact.append(entry)
        elif any(needle in name for name in names):
            partial.append(entry)
    matches = exact or partial
    if not matches:
        raise ValueError(f"索引中没有找到 {query!r}，可改用 --query 检索正文")
    return {"query": query, "match_count": len(matches),
            "selection_required": len(matches) > 1, "matches": matches}


def search(query, limit):
    results = []
    for path in sorted((ROOT / "resources").glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        source = document_source(lines)
        heading = ""
        pages = []
        pending = []
        # Each heading owns its source/pages. A sibling returns to the parent
        # scope instead of inheriting the preceding section's last PDF marker.
        scopes = [{"level": 0, "source": source, "pages": []}]
        for line_no, line in enumerate(lines, 1):
            page = re.fullmatch(r"<!-- PDF第(\d+)页 -->", line.strip())
            if page:
                pending.append(int(page.group(1)))
                continue
            if not line.strip():
                continue
            title = re.match(r"^(#{1,6})\s+(.+)", line)
            sources = standard_sources(line)
            local_pages = explicit_pages(line)
            if title:
                level = len(title.group(1))
                while scopes[-1]["level"] >= level:
                    scopes.pop()
                parent = scopes[-1]
                source = resolved_source(line, parent["source"])
                pages = local_pages or pending or (parent["pages"] if source == parent["source"] else [])
                scopes.append({"level": level, "source": source, "pages": pages[:]})
                heading = title.group(2).rstrip("# ")
            else:
                if pending:
                    pages = pending[:]
                statement = source_statement(line)
                if statement is not None:
                    # An explicit local source declaration governs the section
                    # and its children. Mixed sources cannot share one page list.
                    # Clause-only references can use the established document
                    # source; an unrecognized publication cannot inherit it.
                    same_document = re.match(r"^(?:正文|附录|资料性|§|A\.|\d+\.|表|图)", statement)
                    previous_source = source
                    source = resolved_source(statement, source if same_document else None)
                    pages = explicit_pages(statement) or (pages if source == previous_source else [])
                    scopes[-1].update(source=source, pages=pages[:])
            pending = []
            match_source = resolved_source(line, source)
            match_pages = local_pages or pages
            # A standard mentioned in prose may be a reference of the scoped
            # publication. It cannot claim that publication's pages, even when
            # the same line includes a PDF marker. Only an explicit source or
            # heading can establish a different page system.
            if match_source is None or (sources and match_source != source):
                match_pages = []
            if query.casefold() in line.casefold():
                results.append({
                    "resource": str(path.relative_to(ROOT)),
                    "line": line_no,
                    "section": heading,
                    "pdf_pages": match_pages[:],
                    "pdf_page_system": match_source if match_pages else None,
                    "text": line[:1200],
                })
    return {"query": query, "total_matches": len(results), "matches": results[:limit]}


def main():
    parser = argparse.ArgumentParser(description="测试与验证设计：领域词典、多标准、GJB工作项目及资源检索")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--item", type=int, help="现版工作项目编号，例如304")
    group.add_argument("--query", help="按文字检索，例如虚警")
    group.add_argument("--standard", help="查标准版本/状态/证据等级，例如 IEEE 1012-2024")
    group.add_argument("--term", help="查统一语言，例如 TestExecution、TestRun 或 验证")
    parser.add_argument("--limit", type=int, default=8, help="最多显示匹配数，1~50")
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error("--limit 必须为1~50")
    try:
        if args.item is not None:
            index = json.loads((ROOT / "resources/work-items.json").read_text(encoding="utf-8"))
            item = next((x for x in index["items"] if x["id"] == args.item), None)
            if item is None:
                parser.error("该编号不在现版20个工作项目中；不要套用旧版编号")
            result = {"standard": index["standard"], "item": item, "stage_note": index["stage_note"]}
        elif args.standard is not None:
            index = json.loads((ROOT / "resources/standards-index.json").read_text(encoding="utf-8"))
            result = indexed_lookup(args.standard, index["standards"], "canonical_id", ["title"])
            result["status_checked_at"] = index["status_checked_at"]
            result["evidence_levels"] = index["evidence_levels"]
            result["note"] = "范围和状态索引不等于全文条款核验；多个候选时明确版次，不自动选最新版"
        elif args.term is not None:
            index = json.loads((ROOT / "resources/domain-vocabulary.json").read_text(encoding="utf-8"))
            result = indexed_lookup(args.term, index["terms"], "canonical_name", ["label_zh", "label_en"])
            result["definition_status"] = index["definition_status"]
            result["note"] = "工作定义须结合上下文与项目确认，不宣称各标准逐字等价"
        else:
            query = args.query.strip()
            if not query or len(query) > 200:
                parser.error("检索词须为1~200个字符")
            result = search(query, args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f"读取技能资源失败：{exc}\n")
    except ValueError as exc:
        parser.exit(1, f"检索未完成：{exc}\n")


if __name__ == "__main__":
    main()
