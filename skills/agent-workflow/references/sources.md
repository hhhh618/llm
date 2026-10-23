# 一手来源与适用边界

本技能由 2026-10-23 的业界实践检索整理。核心顺序属于综合方法，不是统一标准；阈值、样本量、Agent 数量与具体框架须按任务验证。

只在需要解释依据、选择具体运行时或更新机制时读取相关来源。执行具体 SDK 配置前查当前官方文档，并记录实际使用版本。

| 来源 | 支持的实践 | 边界 |
| --- | --- | --- |
| [Anthropic：Building effective agents](https://www.anthropic.com/research/building-effective-agents) | 固定 workflow 与动态 agent 的区分，逐步增加复杂度 | 2024-12-19 工程指南；具体生态会变化 |
| [OpenAI：Orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration) | 专家作为工具与所有权转交，明确责任 | SDK 文档，接口依版本核对 |
| [Anthropic：Writing effective tools](https://www.anthropic.com/research/writing-tools-for-agents) | 任务导向工具、明确错误、高信号返回与实际轨迹评估 | 2025-09-11 工程经验，需本地评测 |
| [Anthropic：Context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 按需上下文、结构化笔记与压缩 | 2025-09-29 指南，摘要仍可能丢失信息 |
| [LangGraph：Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)、[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | checkpoint、调试 replay、人工恢复与节点重执行 | 框架状态不能保证外部动作只执行一次 |
| [Temporal：Workflow](https://docs.temporal.io/workflow-definition)、[Activity](https://docs.temporal.io/activity-definition) | 确定性编排、外部调用边界、重试与幂等 | 不是其他框架的恢复语义 |
| [Google/MIT：Scaling Agent Systems v1](https://arxiv.org/html/2512.08296v1) | 总 token 预算匹配下比较单 Agent 与多 Agent，收益依任务结构 | 2025-12-09 特定模型和基准实验，不能外推统一收益 |
| [Anthropic：Demystifying evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 环境结果、独立 trials、评分器校准与失败回流 | 2026-01-09 方法总结，起始样本建议不等于充分统计证明 |
| [τ-bench v1](https://arxiv.org/html/2406.12045v1) | 终态和过程约束，pass^k 重复可靠性 | 2024-06-17 原论文，旧模型成绩不代表当前能力 |
| [Anthropic：Harness design](https://www.anthropic.com/research/harness-design-long-running-apps) | 明确完成标准，模型升级后对组件做删减比较 | 2026-03-24 个案经验，不是受控性能排名 |

维护时优先修正真实使用中被证据支持的问题；不要把某次失败、某个模型弱点或示例中的数值升级成所有任务必须遵循的规则。
