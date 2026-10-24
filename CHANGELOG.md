# Changelog

## 0.4.0 - 2026-10-24

- 新增 DDD 领域建模 Skill 1.0.0，明确核心概念、上下文边界和概念一致性；测试与验证设计更新为2.2.0，修复计数交集下界及检索页码来源继承，并增加回归测试。

## 0.3.0 - 2026-10-23

- 新增 agent-workflow Skill 1.0.0：以验收、单 Agent 基线、工具与上下文、恢复、按需并行和持续评测渐进设计或改进工作流；提供按需参考模板、一手来源与双宿主调用示例。

## 0.2.0 — 2026-10-16

- 将 `test-verification-design` Skill `2.1.0` 迁入 `skills/test-verification-design/`，与 `personal-twin`、`knowledge-maintenance` 共享 `llm` 插件。
- 增加 Codex 与 Claude Code 市场入口，市场名及插件名均为 `llm`，共同引用仓库根目录；两份插件清单版本统一为 `0.2.0`。
- 增加插件结构检查和同步版本准备工具，补充安装、更新、调用及后续发布说明。
- 保留迁入 Skill 的专业内容、标准资源和既有脚本行为；已知问题及资料使用边界见 [Skill README](skills/test-verification-design/README.md)。
- 原 [llm-agent-plugin](https://github.com/hhhh618/llm-agent-plugin) 市场继续保留，既有安装来源不会自动迁移。
