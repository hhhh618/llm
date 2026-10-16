#!/usr/bin/env python3
"""GJB 2547B-2024 指标辅助计算：只用标准库，不作合格判定。"""

import argparse
import json
import math
import sys


class InputError(ValueError):
    pass


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{name} 必须为非负有限数")
    try:
        valid = math.isfinite(value)
    except (OverflowError, TypeError):
        valid = False
    if not valid or value < 0:
        raise InputError(f"{name} 必须为非负有限数")
    return value


def integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InputError(f"{name} 必须为不小于 {minimum} 的整数")
    return value


def label(value, name):
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{name} 必须为非空字符串")
    return value.strip()


def boolean(value, name):
    if not isinstance(value, bool):
        raise InputError(f"{name} 必须为 JSON 布尔值 true 或 false")
    return value


def selection(data, allowed):
    requested = data.get("metrics")
    if (not isinstance(requested, list) or not requested
            or any(not isinstance(item, str) for item in requested)):
        raise InputError("metrics 必须为非空指标名称数组")
    if len(set(requested)) != len(requested) or any(item not in allowed for item in requested):
        raise InputError(f"metrics 仅允许不重复的 {', '.join(sorted(allowed))}")
    return requested


def ratio(numerator, denominator, basis, unit="次数"):
    number(numerator, "分子")
    number(denominator, "分母")
    if denominator == 0:
        raise InputError(f"{basis} 分母为零，不能计算；不得以 0、100% 或无穷大代替")
    if numerator > denominator:
        raise InputError(f"{basis} 分子不得大于分母")
    value = numerator / denominator
    return {"numerator": numerator, "denominator": denominator,
            "basis_unit": unit, "ratio": value, "percent": value * 100,
            "basis": basis}


def isolation_context(data):
    if data.get("isolation_scope_confirmed") is not True:
        raise InputError("FIR 必须明确 isolation_scope_confirmed=true，确认隔离分类与产品层次、可更换单元及模糊度口径一致")
    return {"max_ambiguity": integer(data.get("max_ambiguity"), "max_ambiguity", 1),
            "isolation_unit": label(data.get("isolation_unit"), "isolation_unit")}


def fault_records(data):
    faults = data.get("faults")
    if not isinstance(faults, list) or not faults:
        raise InputError("faults 必须为非空故障模式数组")
    ids = set()
    records = []
    for index, fault in enumerate(faults):
        if not isinstance(fault, dict):
            raise InputError(f"faults[{index}] 必须为对象")
        fault_id = label(fault.get("id"), f"faults[{index}].id")
        if fault_id in ids:
            raise InputError(f"故障模式 id 重复：{fault_id}")
        ids.add(fault_id)
        rate = number(fault.get("failure_rate"), f"{fault_id}.failure_rate")
        records.append((fault_id, rate, fault))
    return records


def stable_sum(values):
    try:
        value = math.fsum(values)
    except (OverflowError, ValueError):
        raise InputError("故障率合计超出有限数范围，请使用一致的缩放或单位") from None
    return number(value, "故障率合计")


def weighted_prediction(data):
    requested = selection(data, {"FDR", "FIR"})
    unit = label(data.get("failure_rate_unit"), "failure_rate_unit")
    records = fault_records(data)
    detected = []
    for fault_id, rate, fault in records:
        if boolean(fault.get("detected"), f"{fault_id}.detected"):
            detected.append((fault_id, rate, fault))
    total_rate = stable_sum(rate for _, rate, _ in records)
    detected_rate = stable_sum(rate for _, rate, _ in detected)
    results = {}
    context = {"failure_rate_unit": unit, "fault_ids": [item[0] for item in records]}
    if "FDR" in requested:
        results["FDR"] = ratio(detected_rate, total_rate, "预计：可检测故障率合计 / 全部故障率合计", unit)
    if "FIR" in requested:
        context.update(isolation_context(data))
        isolated = []
        for fault_id, rate, fault in detected:
            if "isolation_ambiguity" not in fault:
                raise InputError(f"{fault_id} 缺少 isolation_ambiguity；未知分类不能默认作未隔离")
            ambiguity = fault["isolation_ambiguity"]
            # null 明确表示已确认不能按此口径隔离；整数为候选可更换单元数。
            if ambiguity is not None:
                ambiguity = integer(ambiguity, f"{fault_id}.isolation_ambiguity", 1)
                if ambiguity <= context["max_ambiguity"]:
                    isolated.append(rate)
        for fault_id, _, fault in records:
            if not fault["detected"] and fault.get("isolation_ambiguity") is not None:
                raise InputError(f"{fault_id} 未检出却给出隔离模糊度，数据不一致")
        results["FIR"] = ratio(stable_sum(isolated), detected_rate,
                               "预计：满足规定隔离模糊度的故障率合计 / 已检出故障率合计", unit)
    return results, context


def count_assessment(data):
    requested = selection(data, {"FDR", "CFDR", "FIR", "FAR"})
    counts = data.get("counts")
    if not isinstance(counts, dict):
        raise InputError("counts 必须为计数对象")
    allowed = {"faults", "detected", "isolated", "critical_faults", "detected_critical_faults", "alarms", "false_alarms"}
    if any(key not in allowed for key in counts):
        raise InputError("counts 含不支持的字段，请核对计数名称")
    counts = {key: integer(value, key) for key, value in counts.items()}
    constraints = [("detected", "faults"), ("isolated", "detected"),
                   ("critical_faults", "faults"), ("detected_critical_faults", "critical_faults"),
                   ("detected_critical_faults", "detected"), ("false_alarms", "alarms")]
    for smaller, larger in constraints:
        if smaller in counts and larger in counts and counts[smaller] > counts[larger]:
            raise InputError(f"{smaller} 不得大于 {larger}")
    definitions = {"FDR": ("detected", "faults", "评估点估计：正确检测的责任故障次数 / 责任故障总次数"),
                   "CFDR": ("detected_critical_faults", "critical_faults", "评估点估计：正确检测的严重故障次数 / 严重故障总次数"),
                   "FIR": ("isolated", "detected", "评估点估计：满足规定隔离模糊度的故障次数 / 正确检测的故障次数"),
                   "FAR": ("false_alarms", "alarms", "评估点估计：确认虚警次数 / 报警总次数")}
    context = {}
    mapping = data.get("alarm_fault_mapping")
    if mapping is not None:
        if mapping != "one_alarm_per_detected_fault":
            raise InputError("alarm_fault_mapping 仅支持 one_alarm_per_detected_fault；其他映射应另行核对原始记录")
        for key in ("detected", "alarms", "false_alarms"):
            if key not in counts:
                raise InputError(f"逐条报警口径需要 counts.{key}")
        if counts["detected"] + counts["false_alarms"] > counts["alarms"]:
            raise InputError("逐条报警口径下，正确检测次数与虚警次数之和不得大于报警总次数；允许尚未分类报警，不要求相等")
        context["alarm_fault_mapping"] = mapping
    if "FIR" in requested:
        context.update(isolation_context(data))
    results = {}
    for metric in requested:
        numerator, denominator, basis = definitions[metric]
        if numerator not in counts or denominator not in counts:
            raise InputError(f"{metric} 需要 counts.{numerator} 和 counts.{denominator}")
        results[metric] = ratio(counts[numerator], counts[denominator], basis)
    return results, context


def mean_time(data):
    metric = data.get("metric")
    labels = {"MTTD": ("故障诊断累计用时", "故障诊断总次数"),
              "MTBFA": ("规定条件下产品累计运行时间", "确认虚警总次数"),
              "MTBFACF": ("规定条件下产品累计运行时间", "显示或报告严重故障的确认虚警总次数")}
    if not isinstance(metric, str) or metric not in labels:
        raise InputError("mean_time 的 metric 仅支持 MTTD、MTBFA、MTBFACF")
    total = number(data.get("total_time"), "total_time")
    count = integer(data.get("event_count"), "event_count")
    number(count, "event_count")
    unit = data.get("time_unit")
    if not isinstance(unit, str) or unit not in {"s", "min", "h"}:
        raise InputError("time_unit 必须为 s、min 或 h；输入时间必须已统一到该单位")
    if count == 0:
        raise InputError(f"{metric} event_count 为零，不能求点估计；应报告观察时间与零事件并按约定统计方案处理")
    value = total / count
    number(value, "平均时间")
    numerator, denominator = labels[metric]
    return {metric: {"total_time": total, "event_count": count, "value": value,
                     "unit": unit, "basis": f"{numerator} / {denominator}"}}, {"time_unit": unit}


def correlation_prediction(data):
    selection(data, {"FDR"})
    records = fault_records(data)
    unit = label(data.get("failure_rate_unit"), "failure_rate_unit")
    tests = data.get("tests")
    if not isinstance(tests, list):
        raise InputError("tests 必须为测试名称数组")
    tests = [label(item, "测试名称") for item in tests]
    if len(set(tests)) != len(tests):
        raise InputError("tests 中测试名称重复")
    matrix = data.get("matrix")
    if not isinstance(matrix, list) or len(matrix) != len(records):
        raise InputError("matrix 行数必须等于 faults 长度；行顺序应一一对应")
    detected_ids, rates = [], []
    for (fault_id, rate, _), row in zip(records, matrix):
        if not isinstance(row, list) or len(row) != len(tests):
            raise InputError(f"{fault_id} 的矩阵列数必须等于 tests 长度")
        if any(type(cell) not in {bool, int} or cell not in (0, 1) for cell in row):
            raise InputError("matrix 元素仅允许整数 0/1 或 JSON 布尔值")
        if any(row):
            detected_ids.append(fault_id)
            rates.append(rate)
    result = ratio(stable_sum(rates), stable_sum(rate for _, rate, _ in records),
                   "相关性模型预计：非空测试集故障的故障率合计 / 全部故障率合计", unit)
    return {"FDR": result}, {"failure_rate_unit": unit, "fault_ids": [item[0] for item in records],
                             "tests": tests, "detected_fault_ids": detected_ids,
                             "FIR_not_computed": "测试集不同不自动等于满足可更换单元/隔离模糊度口径"}


def calculate(data):
    if not isinstance(data, dict):
        raise InputError("输入 JSON 顶层必须为对象")
    modes = {"weighted_prediction": weighted_prediction, "count_assessment": count_assessment,
             "mean_time": mean_time, "correlation_prediction": correlation_prediction}
    mode = data.get("mode")
    if not isinstance(mode, str) or mode not in modes:
        raise InputError("mode 必须为 weighted_prediction、count_assessment、mean_time 或 correlation_prediction")
    results, context = modes[mode](data)
    return {"standard": "GJB 2547B-2024", "mode": mode, "results": results, "context": context,
            "conformity": "未判定", "confidence_limits": None,
            "limitation": "仅提供透明的预计或点估计；置信限、最小样本量、合格判据须按经确认的统计/试验方案另行处理"}


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"JSON 对象字段重复：{key}")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="输入 JSON 文件；省略时从标准输入读取")
    args = parser.parse_args(argv)
    try:
        if args.input:
            with open(args.input, encoding="utf-8") as stream:
                data = json.load(stream, object_pairs_hook=no_duplicate_keys)
        else:
            data = json.load(sys.stdin, object_pairs_hook=no_duplicate_keys)
        output = calculate(data)
    except (InputError, json.JSONDecodeError, OSError, UnicodeError) as error:
        print(json.dumps({"status": "invalid_input", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
