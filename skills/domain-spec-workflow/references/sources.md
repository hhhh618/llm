# 来源与本技能的工程约定

核验日期：2026-10-24。按需追溯，不需要每次执行加载全部来源。下列内容为原创概括；来源支持方法思想，不能代替当前项目的领域证据。

| 来源 | 支持范围与边界 |
|---|---|
| Eric Evans, [DDD Reference, 2015](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf) | 上下文、统一语言和领域建模模式的原作者摘要。沿用仓库 DDD 技能已核验的来源；本技能不从它推导强制 US–AC–TC 数据结构 |
| Martin Fowler, [Bounded Context](https://martinfowler.com/bliki/BoundedContext.html)、[Ubiquitous Language](https://martinfowler.com/bliki/UbiquitousLanguage.html) | 模型内部语义一致、边界间显式关联，以及与领域专家共同使用和修正语言；不要求全局单一模型 |
| GitHub, [What is Spec-Driven Development?](https://github.github.io/spec-kit/concepts/sdd.html) | Spec Kit 对意图先行、逐步细化及规格驱动实现的官方解释；文档明确不统一规定规格变更后的保留/修改方式，不能把该工具等同于所有 SDD |
| Dan North, [Introducing BDD](https://dannorth.net/blog/introducing-bdd/) | 行为语言、故事的目标与价值、实例和可执行验收思想；本技能把 AC 与具体 TC 分开追踪是工程选择，并非原文规定的三层存储模式 |
| Cucumber, [Gherkin Reference](https://cucumber.io/docs/gherkin/reference/) | Given/When/Then 的场景结构及规则与实例的关系；语法本身不保证场景覆盖充分或业务理解正确 |
| SEI, [Attribute-Driven Design Method Collection](https://www.sei.cmu.edu/library/attribute-driven-design-method-collection/) | 功能、质量属性和约束作为架构输入，通过场景、策略与分解分析取舍；本技能只在相关场景采用，不宣称实现完整 ADD 方法 |
| Agile Alliance, [TDD](https://agilealliance.org/glossary/tdd/)、[XP](https://agilealliance.org/glossary/xp/) | 方法维护组织的术语入口，支持测试推动实现与重构、工程实践相互支撑；它们不是本技能 manifest 的规范来源 |
| [Agile Manifesto Principles](https://agilemanifesto.org/principles.html) | 原始原则：持续交付价值、接纳变化、业务与开发协作、技术卓越和定期调整。阶段依赖不能被解释成冻结全部需求的前置流程 |

## 哪些是本仓库自己的约定

本技能将范围/上下文/领域词放在 US 之前，用 US–AC–TC、多对多关联、稳定 ID、revision、规格摘要、代码提交和执行证据连接需求与实现。JSON 字段、ASCII 语义名、五个角色任务提示、主 Agent 整合共享规格、保守失效算法与 Markdown 活文档均为本仓库的工程选择，不是上述来源共同制定的标准。

结构校验支持发现漏填、失效引用、版本与路径问题；执行证据支持某个条件下观察到的结果。语义一致、测试充分和业务接受需要相应的领域判断与具体证据，不能由清单齐全或一次全绿自动得出。
