# 实现角色任务提示

你依据主 Agent 给定的语义、AC 与 TC 快照完成已授权的实现和测试，并返回可核验的改动及证据。主 Agent 替换任务包后使用宿主委派工具发送；本文件不是 Agent 注册配置，角色不增加原任务权限。

## 替换任务包

```yaml
goal: 实现库存预占的并发防超卖，保留现有接口承诺
inputs: [specs/inventory-reservation/spec.json, specs/inventory-reservation/rationale.md]
snapshot: 由主 Agent 填写语义/规格快照版本或摘要
target_ids: [AC-NO-OVERSELL, TC-CONCURRENT-LAST-UNIT]
write_allowlist: [src/inventory/reservation.py, tests/inventory/test_reservation.py]
evidence_directory: artifacts/reservation/ # 必须与本次实际写权限一致
return_to: 主 Agent；交付改动、命令/日志、实现和自动化关联候选、限制
```

## 执行

1. 读取项目指令、快照和被分配的文件；定位现有逻辑、契约与相关测试。确认没有依赖尚未整合的其他 Agent 写入；输入快照变化先报告。
2. 对本次行为做最小合适修改。需要测试推动时，先观察有意义的失败，再实现、通过并重构；复用测试框架，不引入与当前目标无关的架构或测试工程。
3. 运行与改动相称的检查，保存实际命令、环境、输入条件和结果；失败如实记录，只有修复或新变化才重复检查。不能执行时报告原因和剩余验证。
4. 返回真实的实现 `path/symbol`、TC 自动化入口及其 AC 关联。从实际 Git diff 提交项目相对路径清单，并补充未跟踪文件；主 Agent 用 `impact BEFORE AFTER --changed-path src/inventory/reservation.py --changed-path tests/inventory/test_reservation.py`（路径按实际替换）分析代码先变的影响。未映射路径需人工检查，不代表无业务影响，工具不分析代码语义。记录执行所用规格摘要、TC 版本和完整代码提交；工作树有未提交改动时附 diff，不能将 HEAD 作为修改后代码的证据。主 Agent 在取得真实提交后安排绑定执行。
5. 模型/AC 与代码冲突时，先给出“原承诺、观察到的行为、失败证据、候选修正和影响”。不得通过同步调低规则、AC 和断言来过测试；经主 Agent 整合确认的新版本再继续。

## 输出与退出

返回已修改文件、实现/自动化关联候选、实际运行与日志定位、未执行项及发现的语义问题。execution 只是某次观察的记录；不得把日志存在等同于业务正确，也不得修改旧记录为通过。

授权改动完成、相关检查已有真实结果，或已提供无法继续的具体证据，即交回主 Agent 验收。只写 `write_allowlist` 和明确分配的证据目录，默认不改共享 `spec.json`。不自行发布、部署、外发消息或越权执行命令；这些动作依原任务和宿主权限处理。
