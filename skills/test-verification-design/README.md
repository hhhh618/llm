# 测试与验证设计

**领域模型、统一语言、多标准参考与证据追踪**

- 调用名：`test-verification-design`
- 当前版本：`2.1.0`
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

## 本地检查

Python 脚本仅依赖标准库。以下命令在技能目录运行：

```sh
python3 scripts/lookup.py --item 304
python3 scripts/lookup.py --term TestRun
python3 scripts/lookup.py --standard "IEEE 1012-2024"
```

指标脚本通过 JSON 输入执行，示例及各模式说明见 [指标与计算](resources/07-指标与计算.md)。计算结果是预计或点估计，不自动表示验收合格。

## 版本与已知问题

2.1.0 更新调用名、中文名、能力说明及对应版本元数据；专业规则、脚本及标准资源保持2.0.0行为。原版评测记录仍归属旧调用名及2.0.0版本。

此前评测确认的两处缺陷尚未在这次改名中修复：

- `metrics.py` 对同一总体的严重故障与已检出故障交集缺少下界校验，某些不可能的计数组合仍会产生点估计。
- `lookup.py --query` 在跨来源汇总段中可能继承错误的 PDF 页码。引用前应核对匹配行内的条款与页码。

## 来源

GJB 扫描件、MIL 资料和转换工作流的来源及核验范围见 [来源与使用边界](resources/00-来源与使用边界.md)。随附 [pdf2skill MIT 许可](assets/pdf2skill-LICENSE.txt) 仅适用于原转换工作流，标准文件保留其原有权利声明。
