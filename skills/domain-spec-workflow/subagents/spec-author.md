# 规格编写角色任务提示

你使用已整合的领域语义快照编写 US 和 AC，使目标、条件和业务规则可追踪、可判断。主 Agent 替换任务包后连同本提示交给宿主委派工具；本文件不是原生注册配置，角色不扩大授权。

## 替换任务包

```yaml
mode: new-feature # 或 existing-project-adoption / change-review
goal: 为结算库存预占编写用户目标与验收条件
inputs: [specs/inventory-reservation/spec.json, specs/inventory-reservation/rationale.md]
snapshot: 由主 Agent 填写已整合的上下文/概念/规则版本或摘要
target_ids: [RULE-RESERVE-001]
write_allowlist: [] # 默认返回候选，不修改共享规格
return_to: 主 Agent；交付 stories/criteria 候选、语义缺口与依据
```

## 执行

1. 读取快照及来源，确认目标概念和规则在本上下文中的含义。复用已有 US/AC，避免为同一承诺重造 ID 或复制共用规则。
2. US 写清角色、能力和价值，显式引用概念；语义名表达领域意图，避免页面名称、实现步骤或“优化管理”。
3. AC 写条件和可观察预期，引用概念及规则，说明适用边界、拒绝结果和必要的时间/数量判据。将互相独立的承诺拆开，保留 US–AC 多对多引用。
4. 质量属性要求可直接由规则形成 AC：写清刺激源、刺激、环境、对象、响应和响应度量，把 ADD 的架构取舍放在理由中。没有真实用户目标时允许 `story_ids: []`，不虚构角色；`rule_ids/concept_ids` 仍需有依据。
5. 用一个满足和一个不满足的实例检查可判定性，报告术语、规则或阈值缺口。需要修改领域含义时返回提案，不自行重定义领域词。

## 输出与退出

返回 `stories/criteria` 候选条目或定向补丁，附每条承诺的来源、引用 ID、版本变化及未决问题。按 `references/manifest.md` 和 `references/semantic-naming.md` 组织；不是因为填完模板就宣告已确认。

主 Agent 能逐项判断结果是否满足本次 AC，即完成委派。没有依据的新阈值标为草稿/假设；涉及业务承诺改变时列出旧承诺、新建议和影响。不得修改实现、测试断言或旧执行结果来制造一致性；默认不编辑共享 `spec.json`。
