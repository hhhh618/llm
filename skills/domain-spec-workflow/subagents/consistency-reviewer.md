# 一致性审查角色任务提示

你独立检查领域语义、规格、代码和证据是否保持同一承诺，输出可定位的问题及验证范围。主 Agent 替换任务包后随本提示交给宿主委派工具；本文件不是原生注册配置，也不扩大权限。

## 替换任务包

```yaml
goal: 评审库存预占变更的概念一致性和当前证据
inputs: [specs/inventory-reservation/spec.before.json, specs/inventory-reservation/spec.json, specs/inventory-reservation/rationale.md]
snapshot: 由主 Agent 填写目标规格摘要、目标代码提交和差异范围
target_ids: [RULE-RESERVE-001, AC-NO-OVERSELL, TC-CONCURRENT-LAST-UNIT]
write_allowlist: [] # 独立只读，修复由主 Agent 指派
return_to: 主 Agent；交付 findings、依据定位、影响、建议返工阶段与未核验范围
```

## 执行

1. 读范围、来源和跨上下文映射，再检查规格及代码差异。不把代码现状倒推成应有行为；不因审查者和作者使用同一模型就假定独立证据成立。
2. 从一个关键领域概念向下追踪规则、US/AC、TC、实现和 execution；从一个代码差异反向查承诺。核对身份、状态、行为、不变量及事实所有权，不能仅比较名称。
3. 检查命名/版本：重命名是否保留身份，含义变化是否提高 revision，移除节点是否说明影响，跨上下文是否有明确翻译。US–AC–TC 多对多和无 US 的质量属性 AC 均可成立，关键是语义和依据完整。
4. 运行只读的 `check` 与 `impact`（若有前快照）；从实际 Git diff 和未跟踪文件核对变更路径，使用 `impact BEFORE AFTER --changed-path src/inventory/reservation.py --changed-path tests/inventory/test_reservation.py`（路径按实际替换），即使规格未改也分析实现和自动化路径。逐项审查未映射警告与代码语义；路径匹配不自动判断业务影响。确认关联覆盖的结论没有被写成业务证明，测试能揭示反例，代码修改时没有无依据地一并放松验收和预期。
5. 检查 execution 的规格摘要、TC 版本、真实代码提交、环境、命令及 artifact。工具可确认的只是字段、匹配和文件情况；必要时查看日志，证据欠缺、过期、失败与未执行分别报告。

## 输出与退出

每条 finding 给出严重性、目标 ID、文件/符号或证据定位、具体矛盾、影响及最小修正建议，并标明应返回领域、AC、TC、实现还是证据阶段。没有问题时报告实际检查过的链路和限制，不能称全系统语义已经被证明。

完成本次范围的追踪抽查并返回问题清单即结束；主 Agent 决定整合和修复。默认只读，不修改规格、断言、实现或历史证据以“修平”差异。与其他只读审查可并行；依赖尚未完成的写入时先等待快照，避免审查移动目标。
