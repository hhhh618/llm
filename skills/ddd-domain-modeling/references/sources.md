# 一手来源与适用边界

核验日期：2026-10-24。以下是定义和设计思想的追溯入口，内容以原创概括为主，不替代原著；示例和检查方法是本技能的工程化整理。

| 来源 | 支持范围与使用边界 |
|---|---|
| Eric Evans, [Domain-Driven Design Reference: Definitions and Pattern Summaries, 2015](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf) | 追溯 Bounded Context、Ubiquitous Language、Entity、Value Object、Aggregate、Repository、Domain Event、Service 和 Context Map 等模式定义。它是模式摘要，不能单独证明当前业务如何划界；本文未复制其模式目录或展开全文 |
| Martin Fowler, [Bounded Context](https://martinfowler.com/bliki/BoundedContext.html), 2014-01-15 | 支持大型模型按上下文保持内部一致、相同词可能有不同含义、模型之间需明确映射。不是“一上下文必须一微服务”的依据 |
| Martin Fowler, [Ubiquitous Language](https://martinfowler.com/bliki/UbiquitousLanguage.html), 2006-10-31 | 支持领域专家与开发者共建严谨语言，并在对话中验证、随理解演进。不是只维护一份名词表 |
| Frederick P. Brooks, Jr., [The Design of Design 官方样章](https://ptgmedia.pearsoncmg.com/images/9780201362985/samplepages/0201362988_sample.pdf), 2010，Chapter 6 | “The Challenge Is Conceptual Integrity!” 和 “How to Get Conceptual Integrity with Team Design?” 讨论整体设计的概念连贯性、用户理解及团队设计中的责任。只引用样章已公开内容，不编造中文版本页码 |
| Brooks / Eóin Woods, [Interview with Fred Brooks on the Publication of The Design of Design](https://www.informit.com/articles/article.aspx?ns=18574&p=1600886), 2010-06-08 | Brooks 将 conceptual integrity 与易学、易用、易维护和扩展联系起来，也主张尽早用真实使用场景获得反馈。该访谈没有把 DDD 的限界上下文或统一语言作为术语提出 |
| Microsoft, [Designing a DDD-oriented microservice](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice) | 追溯领域层规则、应用层编排和基础设施持久化的职责区分。示例采用 .NET 与微服务；本技能不把其技术栈和项目分层视为所有 DDD 项目的要求 |
| Microsoft, [Domain events: Design and implementation](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation) | 追溯领域事件与集成事件的用途及提交后对外传播的要求。本文依据受众和契约划分二者，未把是否经过消息队列当成唯一判断标准 |
| Microsoft, [Use domain analysis to model microservices](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis) | 支持先分析领域、识别模型边界，再考虑服务划分；本文的通用流程也适用于模块化单体，不要求采用微服务 |

## 如何衔接 Brooks 与 DDD

Brooks 的概念完整性是整体设计要求；DDD 的限界上下文和统一语言是处理领域模型的具体方法。将“内部身份、状态、行为、不变量相容，边界间显式翻译，用户可理解整体承诺”作为检查项，是本技能综合两者作出的工程解释，不能写成《设计原本》给出的 DDD 清单。

概念连贯并不要求全局只有一个模型。多模型能否共同形成清晰、可信的行为，需要进一步审查交互契约和端到端场景；不能仅凭各自术语表一致就宣布整体设计一致。
