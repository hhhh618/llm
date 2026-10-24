# 语义化命名、身份与版本

名称表达当前领域意图，稳定 ID 用于追踪身份，revision 标识某次定义。三者分开维护。本技能使用小写 ASCII 语义名便于代码和工具交换，领域定义、角色、条件与说明可用中文；它不是要求业务人员改用英文沟通。

## 从上下文语言命名

先确定概念属于哪个上下文，再按 `<context.key>.<领域对象或主题>.<意图或条件>` 命名。名称须以归属上下文的 key 加点为前缀，点和连字符用于分段；具体允许字符见 [manifest](manifest.md)。不要在名称中堆叠整个需求或编码数据。

| 类别 | 稳定 ID 示例 | 语义名示例 | 表达内容 |
|---|---|---|---|
| 上下文 | `CTX-INVENTORY` | key 为 `inventory` | 库存模型成立的范围 |
| 领域概念 | `CONCEPT-RESERVATION` | `inventory.reservation` | 预占的身份与生命周期 |
| 领域规则 | `RULE-NO-OVERSELL` | `inventory.reservation.available-stock-nonnegative` | 必须保持的库存不变量 |
| US | `US-CHECKOUT-RESERVE` | `inventory.reserve-stock-for-checkout` | 角色希望达成的目标与价值 |
| AC | `AC-NO-OVERSELL` | `inventory.reservation.prevent-overselling` | 可观察的业务承诺 |
| TC | `TC-CONCURRENT-LAST-UNIT` | `inventory.reservation.concurrent-requests-for-last-unit` | 用以检验承诺的具体情境 |

不使用 `test-001`、`handle-data`、`save-record` 代替领域意图。测试代码可采用宿主语言的 snake_case 等惯例，通过 `automation.path/symbol` 关联 TC；不必让文件名与 manifest 名逐字相同。

## 演进时怎样处理

- **改措辞或重命名：**仍是同一概念/承诺时保留 ID。该清单的已存在节点内容变动均提高 revision，包含文字修改；同时说明“措辞调整/含义变化”，不要把语义名当成引用主键。
- **改变行为：**保留身份且递增 revision，列明旧承诺、新承诺和受影响关联，重新评估 TC 与证据。调整“最多一个成功”为“两个均排队成功”涉及语义，不能称作重构。
- **拆分、合并或移除：**明确旧 ID 与新 ID 的对应和去向；影响审查必须看到删除，不能简单重用旧 ID 代表另一个概念。辅助工具报告移除和关联缺口，迁移理由由主 Agent 记录。
- **跨上下文：**允许 `inventory.reservation` 与 `payment.authorization` 各有身份与规则。通过手写映射说明如何关联、哪些状态不可等同；不要用全局同义词表抹平差别。

## 命名评审动作

读到名字时，能否定位上下文、概念和具体意图？给一个正常场景和一个反例，检查规格、接口、代码与测试是否沿用同一种含义。发现“成功”“完成”“可用”“有效”等词时，要求在定义或规则中说明状态、对象和观察时点。

检查 ID 是否只代表同一身份；`name` 和文字变化是否提高 revision；代码重命名后实现定位是否仍有效；跨上下文引用是否有明确翻译。工具只能检查字符、前缀、引用与版本差异，不能自动判定两段自然语言语义等价。
