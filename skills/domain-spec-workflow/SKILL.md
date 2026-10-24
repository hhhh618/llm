---
name: domain-spec-workflow
description: 将明确范围内的领域词和模型转成 US–AC–TC、实现关联、验证证据及活文档，并执行规格变更影响分析。用于按领域语义推进功能开发、接入已有项目或审查规格与代码漂移；普通问答和局部无行为变更不自动展开完整流程。
metadata:
  version: "1.0.0"
---

# 领域规格工作流

实际完成当前任务：先澄清本次范围和上下文中的领域含义，再形成用户故事（US）、验收条件（AC）和测试用例（TC），按授权实现并验证。沿用已有规格、代码、词汇及测试，不为套用方法重写项目。

## 开始执行

先读 [执行工作流](workflows/domain-to-delivery.md)，选择新需求、已有项目接入或变更审查路径；小任务沿用已有领域模型，只补本次缺口。确定项目根目录、已有产物和本次交付范围。设计请求交付设计与待执行项；实现请求继续做到改动、实际验证和证据，不停在计划上。

需要可机读的追踪与活文档时，用 [manifest 约定](references/manifest.md) 和随附工具；已有可靠规格格式可以保留，用显式关联实现相同检查，不强制迁移。新 manifest 的默认位置为目标项目 `specs/<功能>/spec.json`，不写入技能安装目录。

```sh
python3 <skill-dir>/scripts/spec_workflow.py init specs/reservation/spec.json --purpose "结算时预占库存"
```

把草稿中的示例值替换为本项目事实；范围、概念、规则和业务判据依据用户材料，不从模板推导。领域定义有歧义时先完成可独立确认的部分，列出影响和待决事项；不把整个领域建完作为开始一个故事的条件。

## 执行中的语义约束

- **范围先于故事。** 每个 US 明确所属上下文，使用已定义的领域词。词汇记录定义与身份边界，领域规则记录状态与不变量；同词跨上下文保留各自含义和翻译。
- **三层有明确职责。** US 表达角色、能力及价值；AC 给出可观察的满足条件；TC 规定具体前置、动作、预期与判据。AC/TC 允许多对多；跨切规则和质量属性可以直接导出 AC，不虚构角色故事。TC 与每次执行记录分开。
- **语义名与身份分开。** 名称来自上下文中的领域行为或规则；稳定 ID 用于引用，修改内容保留身份并记录修订。详见 [语义命名](references/semantic-naming.md)。
- **实现现状与规范意图区分。** 代码发现用于理解当前行为；修改验收条件须有业务依据。不能为使测试通过，同时将规格与预期改成错误实现。
- **按层验证。** 结构检查验证字段、引用和关联；测试验证特定场景的行为；语义是否符合用户目的还需审查。测试数量或引用完整不自动证明覆盖充分。

## 按依赖使用 subagent

有可独立交付的分工或复核收益时，读取相应任务提示并通过宿主实际提供的委派工具派发；发现可用工具后再映射参数，不伪造工具名或调用回执。下面的文件是任务提示，安装本技能不会自动注册宿主原生 agent。

| 任务 | 提示文件 | 前置与写入归属 |
|---|---|---|
| 澄清范围、概念和规则 | [domain-modeler](subagents/domain-modeler.md) | 读取用户材料；输出领域草案与热点 |
| 编写 US/AC | [spec-author](subagents/spec-author.md) | 使用主负责人选定的领域修订；不自行改定义 |
| 设计 TC 与观测 | [verification-designer](subagents/verification-designer.md) | 使用指定 AC；输出正常、边界、异常及证据方案 |
| 修改实现与自动化 | [implementer](subagents/implementer.md) | 使用指定规格基线；只改分配的代码与测试 |
| 独立一致性复核 | [consistency-reviewer](subagents/consistency-reviewer.md) | 对照原始意图、旧/新基线和实际证据，只读报告 |

主负责人持有共享 manifest 的合并权：给任务包附上必要输入、精确路径/修订、范围、可写文件、预期输出和验收人，实际检查返回产物再合并。领域澄清、US/AC、TC、实现有依赖，按已满足的输入顺序执行；独立只读审查或不同所有权的实现可并行。没有委派能力时，由主 Agent 顺序执行相同角色步骤，并说明未做独立复核。

## 检查、变更与活文档

按 [manifest 约定](references/manifest.md) 保存字段和引用，执行：

```sh
python3 <skill-dir>/scripts/spec_workflow.py check specs/reservation/spec.json --project-root . --require-coverage
python3 <skill-dir>/scripts/spec_workflow.py impact <旧规格快照.json> specs/reservation/spec.json --changed-path <实际变更的代码或测试相对路径>
python3 <skill-dir>/scripts/spec_workflow.py render specs/reservation/spec.json --output docs/reservation.generated.md --project-root . --code-commit <实际完整提交SHA>
```

先读取工具 JSON 诊断并修正引用、覆盖或修订错误，再运行目标项目的相关测试。工具不执行 manifest 中的命令；按当前任务授权运行实际检查，再保存命令、结果、环境、规格摘要、代码提交及证据位置。没有真实执行就保留未执行，不能制造通过记录。

从旧基线比较影响再形成新基线；概念/规则、AC、实现或契约变更都检查下游。代码/测试先变时从实际 Git 差异取得路径，逐个传入可重复的 `--changed-path`，检查未映射路径；没有代码差异时省略该参数。复用现有变更授权，只有影响业务承诺且缺少依据的部分才请求决定。旧失败与旧证据保留。生成视图只刷新受管理的文档；手写设计理由、假设和决策保留在独立文件并链接到相应 ID。

交付实际产物、采用的领域修订、US–AC–TC 关联、变更影响、运行证据与未解决项。明确结构有效、场景已验证和业务已认可的区别，不从执行记录自动汇总成“故事已验收”。

需要确定各方法如何用于当前步骤时读取 [方法分工](references/method-map.md)；追溯定义时读取 [来源](references/sources.md)。需要更多领域建模细节，可按需使用同插件的 `ddd-domain-modeling`；Agent 恢复和预算问题可参考 `agent-workflow`。本入口提供执行所需约束，不以加载其他技能为前置条件。
