#!/usr/bin/env python3
"""Look up work items, standards, canonical domain terms, or resource notes."""
import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        heading = ""
        pages = []
        pending = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            page = re.fullmatch(r"<!-- PDF第(\d+)页 -->", line.strip())
            if page:
                pending.append(int(page.group(1)))
                continue
            if not line.strip():
                continue
            if pending:
                pages, pending = pending, []
            if line.startswith("#"):
                heading = line.lstrip("# ")
            if query.casefold() in line.casefold():
                results.append({
                    "resource": str(path.relative_to(ROOT)),
                    "line": line_no,
                    "section": heading,
                    "pdf_pages": pages[:],
                    "pdf_page_system": "GJB 2547B-2024" if pages else None,
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
