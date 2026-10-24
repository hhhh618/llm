# llm

**liliming’s personal digital twin**

This repository stores the reusable, non-sensitive parts of liliming’s
knowledge, preferences, workflows, and AI-agent instructions.

这是个人知识与工作流插件，同时作为长期维护的插件市场。市场名和插件名均为 `llm`，安装标识为 `llm@llm`。Codex 与 Claude Code 使用各自的市场清单和插件清单，共享同一份 `skills/` 与 `knowledge/`。

## 能力

| Skill | 用途 |
| --- | --- |
| [personal-twin](skills/personal-twin/SKILL.md) | 按需使用个人知识、偏好和工作流 |
| [knowledge-maintenance](skills/knowledge-maintenance/SKILL.md) | 整理可复用的非敏感知识 |
| [agent-workflow](skills/agent-workflow/SKILL.md) | 以验收驱动 Agent 工作流设计、诊断、恢复、按需并行和持续评测 |
| [ddd-domain-modeling](skills/ddd-domain-modeling/SKILL.md) | 澄清核心概念、划分限界上下文、建立统一语言并维护概念一致性 |
| [test-verification-design](skills/test-verification-design/README.md) | 测试与验证设计：领域模型、统一语言、多标准参考与证据追踪 |

`ddd-domain-modeling` 用于通用业务或技术领域，先澄清语义、规则与责任，再决定上下文和聚合。`test-verification-design` 面向测试/验证平台、诊断工具及普通软件的需求、领域模型、架构、接口和验证方案，也保留装备测试性工作、条款导读及指标计算能力；其领域词典不替代被测产品的业务模型。两个技能按任务选用，不要求同时加载。

## 结构

```text
llm/
├── .agents/plugins/marketplace.json   # Codex 市场入口
├── .codex-plugin/plugin.json         # Codex 插件清单
├── .claude-plugin/
│   ├── marketplace.json              # Claude Code 市场入口
│   └── plugin.json                   # Claude Code 插件清单
├── knowledge/                        # 稳定的个人上下文与工作偏好
├── skills/
│   ├── personal-twin/
│   ├── knowledge-maintenance/
│   ├── agent-workflow/
│   ├── ddd-domain-modeling/
│   └── test-verification-design/
├── tests/                            # 计算与来源定位的回归测试
├── tools/
│   ├── check_plugin.py
│   └── release_plugin.py
└── CHANGELOG.md
```

两个市场入口都指向仓库根目录的 `llm` 插件。新增 Skill 时放入 `skills/<调用名>/SKILL.md`，由同一插件一起发布。

## 安装与调用

### Codex

```sh
codex plugin marketplace add hhhh618/llm --ref main
codex plugin add llm@llm
```

安装后开启新会话，在技能选择器中选择 `llm` 插件下的 `test-verification-design`，或输入：

```text
用 $test-verification-design 为验证管理平台建立领域模型和统一语言，给出需求、设计、执行、证据及结论的追踪关系。
```

### Claude Code

```sh
claude plugin marketplace add hhhh618/llm
claude plugin install llm@llm
```

安装后开启新会话，调用：

```text
/llm:test-verification-design 为库存预占 API 设计正常、边界、并发和故障恢复验证方案。
```

### Agent 工作流技能

`agent-workflow` Skill `1.0.0` 将“验收定义 → 单 Agent 基线 → 工具与上下文优化 → 状态恢复 → 按需并行 → 持续评测”作为渐进决策顺序。支持新建、诊断、局部改进、评测和按此方法执行复杂任务；已有能力可沿用，小任务采用轻量核验。技能提供验收与委派契约、恢复和幂等规则、可比预算评测及一手来源，不依赖特定框架或额外 MCP 服务。

Codex 调用示例：

```text
用 $agent-workflow 诊断现有研究 Agent 遗漏引用的问题，保留现有架构，先定义验收并检查单 Agent 基线，再做最小改进和验证。
```

Claude Code 调用示例：

```text
/llm:agent-workflow 为订单助手设计可恢复的工具工作流，明确外部操作结果未知时的处理和验收方法。
```

### DDD 与概念一致性

`ddd-domain-modeling` Skill `1.0.0` 区分领域/子域、限界上下文、聚合和部署边界。先用真实场景辨明身份、生命周期、行为和不变量，再确定每个上下文内的统一语言；跨上下文保留差异，通过有版本的契约翻译。概念一致性覆盖需求、模型、API、代码、界面及验证中的整体含义，不能仅靠统一命名达到，也不要求全系统共享一个对象模型。

```text
用 $ddd-domain-modeling 为订单、支付和履约梳理核心概念，解释各上下文中“订单”的含义，划分事实所有权、聚合不变量和跨界契约，并检查概念一致性。
```

Claude Code 使用 `/llm:ddd-domain-modeling` 调用。核心概念、边界判据、跨上下文示例及 Brooks《设计原本》的参考依据见该技能按需加载的资料。

## 更新已安装插件

Codex 先刷新市场，再安装该市场的插件版本：

```sh
codex plugin marketplace upgrade llm
codex plugin add llm@llm
```

Claude Code：

```sh
claude plugin marketplace update llm
claude plugin update llm@llm
```

更新完成后重启会话以加载新内容。这些命令用于手动更新；仓库变更本身不会自动更新本机缓存。

## 版本与发布

插件版本记录在 [Codex 清单](.codex-plugin/plugin.json) 与 [Claude Code 清单](.claude-plugin/plugin.json)，两处保持一致。Skill 自身的内容版本记录在其元数据中，独立于插件版本：本次准备插件 `0.4.0`，新增 `ddd-domain-modeling` 为 `1.0.0`，`test-verification-design` 更新为 `2.2.0`，`agent-workflow` 保持 `1.0.0`。主分支、版本标签与 GitHub Release 是不同状态；清单更新不代表已发布 Release。最新内容以清单和 [CHANGELOG](CHANGELOG.md) 为准。

长期维护只需继续在此仓库修改共享内容。准备下一次插件发布时，在仓库根目录运行：

```sh
python3 tools/release_plugin.py 0.4.1 --note "描述本次变更"
python3 tools/check_plugin.py
python3 -m unittest discover -s tests -v
```

结构检查与脚本回归也由 [GitHub Actions](.github/workflows/validate.yml) 在拉取请求和主分支更新时执行。

发布工具同步两份插件清单并更新变更记录，只准备本地版本，不会提交、推送或安装。检查差异与敏感信息后，再提交到 GitHub，并为发布创建版本标签或 GitHub Release。用户随后执行上面的更新命令即可取得新版本。只有 Skill 内容本身发生版本变化时，才另外更新其版本元数据。

迁入来源为 [hhhh618/llm-agent-plugin](https://github.com/hhhh618/llm-agent-plugin)，原市场及其发布记录继续保留。原安装 `test-verification-design@llm-agent-plugin` 的用户需要另行安装 `llm@llm`；安装来源不会因迁入自动切换。确认新插件可用后，可移除旧插件以避免重复入口。

## 来源与许可

仓库根 MIT 许可适用于本项目自有内容，不授予随附标准文件的额外权利。标准资料保留原权利声明，来源、版本和使用边界见 [Skill 来源说明](skills/test-verification-design/resources/00-来源与使用边界.md)。[pdf2skill MIT 许可](skills/test-verification-design/assets/pdf2skill-LICENSE.txt) 仅适用于其原转换工作流。

## Design principles

1. Keep facts separate from instructions.
2. Prefer small, focused knowledge files.
3. Record confidence and dates for facts that may change.
4. Turn repeated successful workflows into skills.
5. Review every change before publishing it.

The repository must not contain passwords, API keys, private session logs,
browser history, or other sensitive personal data.
