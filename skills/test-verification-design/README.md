# 测试与验证设计

**领域模型、统一语言、多标准参考与证据追踪**

- 调用名：`test-verification-design`
- 当前版本：`2.2.0`
- 原调用名：`gjb2547b-testability`

面向测试/验证平台、诊断工具及普通软件的需求、领域模型、架构、接口和验证设计；同时保留装备测试性工作项目、条款导读及指标计算能力。

## 使用

```text
用 $test-verification-design 为验证管理平台建立领域模型和统一语言，给出需求、设计、执行、证据及结论的追踪关系。
```

```text
用 $test-verification-design 为库存预占 API 设计正常、边界、并发和故障恢复验证方案。
```

完整入口见 [SKILL.md](SKILL.md)，具体资源按任务加载。标准名称与版本、证据等级及适用边界见 [多标准对照](resources/09-多标准对照.md) 和 [标准索引](resources/standards-index.json)。

领域建模补充了子域/限界上下文/聚合/部署边界的区别、事实所有权、跨界翻译以及身份/状态/规则的概念一致性。详见 [领域模型与统一语言](resources/10-领域模型与统一语言.md)；测试场景见 [软件需求与验证设计](resources/11-软件需求与验证设计.md)。通用业务模型也可使用同插件的 [DDD 技能](../ddd-domain-modeling/SKILL.md)。

## 本地检查

Python 脚本仅依赖标准库。以下命令在技能目录运行：

```sh
python3 scripts/lookup.py --item 304
python3 scripts/lookup.py --term TestRun
python3 scripts/lookup.py --standard "IEEE 1012-2024"
```

指标脚本通过 JSON 输入执行，示例及各模式说明见 [指标与计算](resources/07-指标与计算.md)。计算结果是预计或点估计，不自动表示验收合格。

仓库根目录可运行 `python3 -m unittest discover -s tests -v` 验证计数边界和检索来源行为。

## 版本与修复

2.1.0 更新调用名、中文名、能力说明及对应版本元数据；专业规则、脚本及标准资源保持2.0.0行为。原版评测记录仍归属旧调用名及2.0.0版本。

2.2.0 修复此前评测确认的两处缺陷，并补充 DDD 与概念一致性内容：

- `metrics.py` 对同一总体的严重故障与已检出故障交集校验完整上下界，拒绝不可能的计数组合。
- `lookup.py --query` 按标题作用域处理页码，优先明确的本行引用；来源未知或混合时不擅自赋为 GJB。没有可确定页码的匹配保留空页码；检索输出用于定位，正式引用仍需核对原文。

历史 2.0.0 评测不自动证明新版本通过；本次验证为仓库回归测试，不扩大标准全文的核验范围。

## 来源

GJB 扫描件、MIL 资料和转换工作流的来源及核验范围见 [来源与使用边界](resources/00-来源与使用边界.md)。随附 [pdf2skill MIT 许可](assets/pdf2skill-LICENSE.txt) 仅适用于原转换工作流，标准文件保留其原有权利声明。
