# 规格 manifest 与命令

这是本技能的工程约定，版本 `1.0`，用于稳定引用、变更检查和活文档；不是 US、BDD 或 SDD 的通用标准。工具仅依赖 Python 标准库，不调用模型或项目接口，不执行输入中的命令。

## 先使用哪份文件

新任务运行 `init` 创建一个草稿文件；现成的 [空白模板](../assets/spec.template.json) 和 [库存预占示例](../examples/inventory/spec.json) 供查看结构。模板中的角色、规则、阈值或名称不能自动成为本项目要求。沿用项目已有的规范时，也可只借用流程和显式追踪关系。

manifest 放在被工作项目中，例如 `specs/reservation/spec.json`。`--project-root` 指向该项目，不是 manifest 所在目录或技能安装目录。代码、自动化和证据路径均相对此根目录；在指定根目录时校验存在性和边界。

## 数据结构

根字段：`schema_version: "1.0"`、`scope`、`contexts`、`concepts`、`rules`、`stories`、`criteria`、`cases`；`implementations` 与 `executions` 缺省为空数组。`scope` 含非空 `purpose`，以及 `in_scope`、`out_of_scope`、`assumptions` 字符串数组。领域阶段可先保留空的 US/AC/TC 数组，不能为了填表虚构需求。

除执行记录外，每个节点含稳定 `id` 和正整数 `revision`。上下文含 `key`（小写英文命名空间）、`label`、`responsibility`。其余节点含 `context_id`、语义 `name`、`status: draft | confirmed`，名称使用所属上下文 `key` 加点号开头。默认草稿；已有用户决定或已确认资料才能支持确认状态，模型自己填字段不构成业务确认。

| 数组 | 特有字段与引用 |
|---|---|
| `concepts` | `definition`：当前上下文中的概念定义 |
| `rules` | `statement`、非空 `concept_ids`：规则及其领域词 |
| `stories` | `role`、`capability`、`benefit`、非空 `concept_ids`：US |
| `criteria` | `story_ids`、非空 `rule_ids`、非空 `concept_ids`、`condition`、`expected`：AC；跨切规则或质量属性的 `story_ids` 可为空 |
| `cases` | 非空 `criterion_ids`、`given`、`when`、`then`：TC；可选 `automation: {path, symbol}`，规划时省略或为 null |
| `implementations` | 非空 `criterion_ids`、`path`、`symbol`：实现位置，保留该节点的 ID、修订与语义名 |

引用使用当前 manifest 中的稳定 ID，解析到该节点声明的修订；AC 和 TC 可以多对多。跨上下文引用产生审查提示，应在设计理由中说明语义映射，不能借同名字段自动合并模型。节点 ID 全局唯一，包括执行记录。`confirmed` 不是测试通过或验收完成状态。

历史执行记录是例外：其 `case_id` 在当前清单中已不存在时，保留记录并提示查阅旧快照，证据标为 `stale / case_removed`。无法仅凭当前清单判断该 ID 是否曾存在；未知孤儿记录也不能支持当前基线。若 ID 存在却属于其他节点类型，仍作为引用错误拒绝。普通 TC→AC 等规格引用不适用此例外。

## 执行记录与证据边界

`executions` 的每条记录包括 `id`、`case_id`、`case_revision`、`spec_digest`、`code_commit`（完整 40 位 SHA）、`environment`、`command`（非空字符串数组）、`result: passed | failed | blocked | not_run`、`artifact` 和带时区的 `recorded_at`。

这些字段只记录执行者报告的结果，工具不会凭记录证明命令真的执行或结果符合业务意图。主负责人核对原始输出、命令范围与独立判据后，才说明实际验证了哪些行为。一个 TC 的执行结果不能直接证明整个 AC 或 US 满足。已有执行记录是不可变快照，修正或重跑新增 ID，不原地篡改历史；`impact` 会报告已有记录被修改。

规格摘要使用去除 `executions`、将缺省 `implementations` 补为空数组后的对象，以 `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(',', ':'))` 序列化，计算 SHA-256，前缀为 `sha256:`。节点数组顺序参与摘要：即便只是重排也会保守地将旧记录判旧；`impact` 按 ID 比较节点，不把重排当节点内容变化。

文档生成时，只有摘要、TC 修订、明确传入的目标代码提交和可核对的证据路径相符，才能标记记录适用于当前基线；这仍不是独立验证结论。没有目标提交或证据无法核对时保留未知/未核验。未执行、失败、旧基线和未知均保留可见，不汇总故事“验收通过”。环境与观测范围应一起阅读，不能把单元环境的记录外推到生产。

## 命令与操作顺序

```sh
python3 <skill-dir>/scripts/spec_workflow.py init specs/reservation/spec.json --purpose "结算时预占库存"
python3 <skill-dir>/scripts/spec_workflow.py check specs/reservation/spec.json --project-root .
python3 <skill-dir>/scripts/spec_workflow.py check specs/reservation/spec.json --project-root . --require-coverage
python3 <skill-dir>/scripts/spec_workflow.py impact /tmp/reservation-before.json specs/reservation/spec.json
python3 <skill-dir>/scripts/spec_workflow.py impact /tmp/reservation-before.json specs/reservation/spec.json --changed-path src/reservation.py --changed-path tests/test_reservation.py
python3 <skill-dir>/scripts/spec_workflow.py render specs/reservation/spec.json --output docs/reservation.generated.md --project-root . --code-commit <完整SHA>
```

`init` 的目标是新文件路径，自动创建父目录，拒绝覆盖。`check` 检查数据类型、引用、命名空间、路径；`--require-coverage` 另外检查已有 US 都有关联 AC，所有 AC 都有关联 TC。结构关联完整仍需场景充分性和领域语义审查。

`impact` 比较两个不可混淆的快照：已存在节点的内容变化应提高修订；重命名保留 ID，记录修订，删除必须显示其影响；范围变化保守影响整体。报告受影响的下游节点和旧执行记录，不能自动决定业务变更是否合理。旧快照可从 Git 或现有基线读取到临时文件，不先覆盖历史。

`impact` 只比较快照中的路径与关联，不接受 `--project-root`，因此前后快照均保留 `paths_unverified` 提示；历史文件未必存在于当前工作树。当前代码、自动化和证据的存在性另用带 `--project-root` 的 `check` 或 `render` 核对。

实现或自动化先变而规格未变时，从实际 Git 差异取得项目相对路径，通过可重复的 `--changed-path` 参数传入。工具匹配 `implementations.path` 与 `cases.automation.path` 并传播影响；这些代码变化本身不要求增加未变规格的修订。未映射路径保留警告，不能判作无影响；路径映射不分析代码语义。报告包含 `changed_paths`、`code_affected_nodes`、`unmapped_changed_paths`；旧有、受影响用例的执行记录会提示需要重新验证，新追加记录仍需按目标提交核对。

命令返回 JSON：共同字段有 `ok`、`errors`、`warnings` 和能力边界说明；`check` 返回 `spec_digest`、节点数量和 `coverage.kind=structural_links_only`。`impact` 返回增改删、受影响节点与旧记录；`render` 返回每条执行的 `reported_result` 和 `freshness`（`stale`、`missing_artifact`、`unverified`、`matching_record`）。`matching_record` 只表示记录与所给基线相符，不能直接解释为业务验收通过。

`render` 写独立 `.md` 生成视图，拒绝覆盖源规格、代码、自动化或证据文件。已有文件只有属于本工具且来源匹配的生成文档才能刷新；普通手写文件和符号链接不覆盖。指定 `--project-root` 且源规格在项目内时，来源标识使用项目相对路径，项目换目录或克隆后仍可刷新；未指定根目录或源规格在项目外时使用绝对来源。同一绝对来源的旧生成视图可在刷新时迁移，不能仅凭文件名接管其他来源的文档。手写解释放在另一个文件。工具失败时读取其 JSON 诊断并修复，不因解析失败改写源材料。

## 最小闭环

先填范围、上下文、领域词及规则 → 选定一条 US/AC/TC 链 → 通过结构检查 → 实现并运行目标项目测试 → 保存真实执行记录 → 生成包含证据状态的活文档。下一次变更从旧/新快照的影响报告继续。执行样例与格式检查只证明工具机制可用，实际项目仍需自己的规则、实现和判据。
