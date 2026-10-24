# 从领域语义到交付

这是可执行工作流。阶段代表依赖关系，可复用已有成果；不要每次重建全领域。主 Agent 负责整合和交付，工具只检查结构、关联与证据绑定，不能代替业务判断。

## 入口与工作区

先读项目自己的指令、已有领域词、需求、接口、测试和当前变更。用 `rg` 定位本次行为，记录事实来源到文件/符号或需求原文。选择入口：

| 入口 | 首先做什么 | 本次结束点 |
|---|---|---|
| 新需求 | 从目标与一条真实业务流程澄清范围、概念 | 已授权的规格设计或实现验证 |
| 现有项目接入 | 抽取一条现有行为，分开记录业务意图与代码现状 | 最小追踪链与已知差异；不顺便重写系统 |
| 变更审查 | 保留变更前快照，定位概念/规则/代码的变化 | 影响清单、候选修正、验证和未决项 |

建议最小目录如下；已有等价材料直接引用，不搬家。路径均相对项目根目录：

```text
specs/inventory-reservation/
  spec.json          # 结构化范围、语义、US、AC、TC、实现与执行关联
  rationale.md       # 手写来源、边界理由、上下文翻译、假设和决策
  generated.md       # 由工具生成的活文档，勿手工修改
  delivery.md        # 本次结果、实际验证、差异与后续工作
artifacts/reservation/ # 运行日志等证据，按执行身份保留
```

`<skill-root>` 替换为本技能目录的绝对路径；下面命令在项目根执行。新建时使用未占用的文件名：

```sh
python3 <skill-root>/scripts/spec_workflow.py init specs/inventory-reservation/spec.json --purpose "结算时可靠预占库存"
```

初始化产物是草稿。字段与完整示例按需读 [manifest 约定](../references/manifest.md) 和 [库存示例](../examples/inventory/README.md)。本工作流不要求引入新的测试框架。

## 1. 明确本次范围

**输入：**用户目标、现有材料、当前代码及已知问题。

**动作：**写 `scope.purpose/in_scope/out_of_scope/assumptions`；挑选可交付的业务切片。列出来源与冲突：业务规格描述应有行为，代码描述实现现状，执行证据描述被观察到的行为，三者不能互相冒充。现有项目没有可靠需求时，将代码提取结果标为“观察/候选”，不能自动确认成业务承诺。

**产物与退出：**范围条目和需要解决的关键歧义；能明确本次涉及哪些行为、哪些不涉及时进入下一步。复用已有范围，仅修改有变化的部分；影响目标或授权的缺口需澄清，其他已独立的工作继续。

## 2. 建立本次所需的语义快照

**输入：**范围、业务场景、已有模型/领域词和代码定位。

**动作：**由主 Agent 或 [领域建模角色](../subagents/domain-modeler.md) 给出上下文职责、领域概念及规则。概念至少回答定义、身份、生命周期/状态、允许行为和相邻概念的区别；适用内容写入 `concept.definition` 和手写理由。规则明确作用对象、触发条件、不变量与事实所有权。上下文间同词异义时，写明身份/状态/字段/规则翻译，保留各自语言。复杂划界按需加载 `ddd-domain-modeling`。

用一个正常场景和一个反例演练，例如“预占成功”不能被解释成“支付成功”。不要求把范围之外的实体、事件和聚合全部建齐。

**产物与退出：**带 ID、版本、归属上下文的 `contexts/concepts/rules`，以及来源、未决项与跨上下文映射。覆盖本次行为的关键名词、状态和规则没有影响后续验收的歧义，即可保留一份版本快照进入规格阶段。`confirmed` 应有已有授权、可信需求或决策依据；“确认”不是每个节点额外向用户求批。新发现可提出修订，不能偷偷改快照。

## 3. 用相同领域语言编写 US 与 AC

**输入：**语义快照、本次目标和已确认约束。

**动作：**由 [规格编写角色](../subagents/spec-author.md) 起草：

- US：角色、能力、价值，引用所属上下文和概念；名称表达领域意图。
- AC：条件与可观察预期，引用概念和规则，明确正常/拒绝/边界结果，避免“正确”“及时”等无判据词。
- 跨切质量属性直接形成规则与 AC：写明刺激源、刺激、环境、受影响对象、响应及量化判据；需要时用 ADD 分析策略与取舍，并将理由记录在 `rationale.md`。不为每条质量要求虚构用户故事；这类 AC 的 `story_ids` 可以为空。

US 与 AC 允许多对多；共用规则通过稳定 ID 引用，避免复制后分歧。自动化检查前由主 Agent 合并候选条目，检查每个业务承诺是否有本次语义依据。命名按需读 [语义化命名](../references/semantic-naming.md)。

**产物与退出：**US、AC 和明确的规则引用。能判断某个具体结果是否满足 AC；已知条件相互冲突时返回语义或规则层修正，不直接把冲突留给测试人员猜。

## 4. 设计 TC，审查验证能力

**输入：**语义快照、已整合的 AC、现有测试能力。

**动作：**由 [验证设计角色](../subagents/verification-designer.md) 为每条 AC 选择有区分力的实例：前置状态、动作、预期与观察方法。覆盖相关正常、拒绝、边界和失效情形；并发、重试、乱序、恢复只在规则需要时展开。写出测试入口或人工验证方法；尚未实现的入口保持缺失，不能编造路径。

AC 与 TC 允许多对多。TC 是验证定义；一次运行另建 execution，不能在 TC 上写“已通过”取代证据。检查例子是否真的能揭示错误实现，例如并发用例必须制造竞争，顺序调用不能证明并发防超卖。

```sh
python3 <skill-root>/scripts/spec_workflow.py check specs/inventory-reservation/spec.json --project-root . --require-coverage
```

**产物与退出：**TC、自动化映射或待实现项；每个 US 有 AC、每个 AC 有 TC 的结构覆盖。主 Agent 同时判断判据与场景是否足够，本命令通过不证明业务完备或行为正确。范围遗漏返回 US/AC，判据歧义返回规则/AC，仅执行能力不足留为实施任务。

## 5. 按快照实现并验证

**输入：**稳定的本次语义与规格快照、TC、授权修改范围。

**动作：**向 [实现角色](../subagents/implementer.md) 委派明确的 AC、TC 和文件所有权。复用现有契约与测试，在适合的行为变更中以失败测试、最小实现、重构推进；仅要求本次有意义的验证，不为形式补无效测试。记录 `implementations` 与 `cases.automation` 的实际位置。

实现或测试暴露模型缺陷时，返回一份“旧承诺/新发现/候选改动/影响”提案。主 Agent 根据已有依据处理；业务承诺变化但依据不足时再请用户决定。不能同时改规格、代码和断言以掩盖失败。确认修订后保留稳定身份、增加 revision，重新评估影响。

**产物与退出：**实际改动、命令与结果日志、实现/测试关联。证据记录必须绑定真实被测代码：有未提交修改时保留 diff 与日志，不拿 HEAD 冒充修改后的代码；取得对应提交后再运行并记录可绑定的 execution。不能执行时写明原因与剩余验证，不填通过。

## 6. 审查一致性并构建活文档

**输入：**规格快照、代码差异、运行证据、手写理由。

**动作：**由 [一致性审查角色](../subagents/consistency-reviewer.md) 独立追踪一条“概念 → 规则 → US/AC → TC → 实现 → 执行”并反向抽查一个代码变化。审查业务含义、身份、状态和不变量，不能只比字符串或链接。主 Agent 整合问题并返工对应阶段。

```sh
python3 <skill-root>/scripts/spec_workflow.py check specs/inventory-reservation/spec.json --project-root . --require-coverage
python3 <skill-root>/scripts/spec_workflow.py render specs/inventory-reservation/spec.json --output specs/inventory-reservation/generated.md --project-root . --code-commit <实际被测的完整提交SHA>
```

没有可靠目标提交时省略 `--code-commit`，生成文档保留未核验状态。生成视图不覆盖手写设计理由，也不根据 TC 数量或声称的执行结果自动宣布 US 已验收。产物是否存在、运行结果与业务接受分别说明。

**产物与退出：**生成视图、已处理的问题、`delivery.md` 中的修改及验证范围。设计任务可在完整规格与未执行标记处结束；实现任务需完成授权范围的实际验证，或清楚交付不可执行原因。使用者能定位每条本次关键承诺的依据、实现与证据，已知缺口没有被“全绿”掩盖。

## 变更与恢复

改动前保留 `spec.before.json`（或引用 Git 中的不可变版本），改动后运行：

```sh
python3 <skill-root>/scripts/spec_workflow.py impact specs/inventory-reservation/spec.before.json specs/inventory-reservation/spec.json
```

代码或自动化先变、规格尚未变化时，主 Agent 先从真实 Git 差异收集项目相对路径：比较提交用 `git diff --name-only <变更前提交> <目标提交>`；检查工作树用 `git diff --name-only HEAD` 并用 `git status --short` 补充未跟踪文件。核对实际路径后逐个传入，不凭模型猜测文件清单。例如本次实际修改了以下两个文件：

```sh
python3 <skill-root>/scripts/spec_workflow.py impact specs/inventory-reservation/spec.before.json specs/inventory-reservation/spec.json --changed-path src/inventory/reservation.py --changed-path tests/inventory/test_reservation.py
```

工具将路径与 `implementations.path`、`cases.automation.path` 匹配并传播影响；即使前后规格相同也应传入实际变更路径。未映射路径会显式警告，主 Agent 需检查其业务影响或补追踪关系，不能把未映射当作无影响。路径匹配不分析代码语义。

逐项处理新增、修改、删除及受影响节点；变动的既有节点增加 revision，删除不能被当作已满足。代码反向变更关联到 implementation、AC 和 TC；没有关联的代码差异先报告追踪缺口。旧 execution 保留历史意义，但规格摘要、TC 版本、目标代码提交或证据不再匹配时不能支持当前版本。该工具按整个规格摘要保守失效，影响报告后仍需人的语义判断。

恢复长任务时先读最后快照、当前 Git 差异、上次验证与未决项，检查阶段输入是否仍适用；复用未变化的模型与规格，只重做受影响部分。不要从头再造所有文档，也不要把上次运行结果直接当成本次结果。

## 如何实际委派

角色文档是可交给宿主委派工具的任务提示，不是自动注册的 Agent 配置。主 Agent 读取相应角色文档，替换其中任务包，再通过当前宿主已有委派工具发送“角色提示＋任务包”；未配置子 Agent 时，单 Agent 按同样步骤顺序执行。

依赖顺序为 **领域澄清 → 主 Agent 整合语义快照 → US/AC → 主 Agent 整合 → TC → 实现 → 审查与证据整合**。只读审查与已有代码定位可并行；独立上下文或模块的写入必须先划分文件与集成边界。五个角色不代表五个 Agent 同时写 `spec.json`。默认子 Agent 返回候选条目或补丁，由主 Agent 单独合并共享规格；实现角色仅写获分配的代码/测试。

每次任务包携带快照路径及版本/摘要、目标 ID、读写范围、证据要求和交付点。子 Agent 发现输入变化时先报告，不跨边界覆盖他人结果。角色分工不扩大权限，不自动授权外部发送、发布、删除或部署。
