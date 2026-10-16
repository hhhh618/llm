# Changelog

## 0.2.0 — 2026-10-16

- 将 `test-verification-design` Skill `2.1.0` 迁入 `skills/test-verification-design/`，与 `personal-twin`、`knowledge-maintenance` 共享 `llm` 插件。
- 增加 Codex 与 Claude Code 市场入口，市场名及插件名均为 `llm`，共同引用仓库根目录；两份插件清单版本统一为 `0.2.0`。
- 增加插件结构检查和同步版本准备工具，补充安装、更新、调用及后续发布说明。
- 保留迁入 Skill 的专业内容、标准资源和既有脚本行为；已知问题及资料使用边界见 [Skill README](skills/test-verification-design/README.md)。
- 原 [llm-agent-plugin](https://github.com/hhhh618/llm-agent-plugin) 市场继续保留，既有安装来源不会自动迁移。
