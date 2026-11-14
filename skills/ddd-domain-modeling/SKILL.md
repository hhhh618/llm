---
name: ddd-domain-modeling
description: Facilitate Event Storming and domain-driven design for business or technical domains, from discovery and process mapping to bounded contexts, aggregates, business rules, and scenario validation. Use when the user asks for 建模, 领域建模, 领域划分, or 事件风暴 in a business or technical domain, as well as DDD, aggregate design, or bounded context design.
---

# Event Storming and Domain Modeling

Help domain experts and delivery teams discover and validate a shared model of business behavior. Adapt depth to the user's scope: facilitate a live workshop, analyze supplied material, model an existing system, or prepare a structured draft. Respond in the user's language. An AI-generated board is a proposal, not a substitute for stakeholder knowledge.

## Ground rules

- Establish the objective, scope, participants, source material, current versus future process, and intended depth from available context. Ask only for consequential missing information; proceed with labeled assumptions and useful independent work.
- Record sources and distinguish **confirmed**, **inferred/proposed**, **unknown**, and **disputed**. Cite supplied artifacts or code locations when available; preserve conflicting interpretations as hotspots. Never present invented business rules as verified facts.
- Use business language. Events name meaningful facts in past tense, including hypothetical future-process events clearly labeled as proposals. Distinguish commands (intent), events (facts), policies (conditional reactions), and state. A command may be rejected and not every event originates in a local command.
- Avoid jumping from a timeline directly to a definitive context or aggregate. Candidate boundaries and invariants require business and consistency evidence. Domain events do not mandate event sourcing, microservices, or automatic cross-context publishing.
- Scale output to the requested scope. A session may stop at any level; record the current board, decisions, open questions, and next step so work can resume without inventing certainty.

## Workflow

1. **Align.** Define vision, outcome, scope and exclusions, stakeholders, starting and ending points, evidence, and whether the work is as-is or to-be. For a short or focused request, select only the necessary levels.
2. **Discover: Big Picture.** Gather meaningful domain events, arrange chronology and branching, walk stories, capture language, pain points and uncertainty. Seek domain-expert correction. Groupings suggest investigation areas, not established boundaries.
3. **Explore a process.** For a selected flow add actors, commands, decisions/policies, read information, external systems, exceptions, parallel paths and time. Record causal links and hotspots, including rejections and compensation where relevant.
4. **Design the model.** Classify subdomains where useful; define context responsibilities, language and relationships. Within selected contexts, propose entities, value objects, aggregates, behavior, lifecycle and invariants based on business consistency. Describe integration and failure handling where needed.
5. **Validate and iterate.** Walk actual normal, boundary and failure scenarios with stakeholders; trace rules to behavior and observable outcomes. Mark unresolved assumptions and tradeoffs. Only translate the validated scope to implementation when requested.

For facilitation steps, level entry/exit, questions, remote and solo adaptations, read [event-storming](references/event-storming.md). For context mapping, aggregate boundaries, integration and validation, read [domain-modeling](references/domain-modeling.md). Use [board and output templates](assets/event-storming-template.md), [aggregate template](assets/aggregate-template.md), and [checklist](references/checklist.md) as relevant. For examples of tactical patterns or network devices, consult [tactical patterns](references/tactical-patterns.md) and [network example](references/network-device-example.md). Consult [anti-patterns](references/anti-patterns.md) for review.

## Deliverables

Choose the artifacts that suit the user's requested level: vision and scope; event timeline and causal flows; glossary by context; hotspots and evidence; context map and ownership; aggregate/command/event/rule catalog; state transitions and validation scenarios. Keep proposals, gaps, decisions, owners and next steps visible. In collaborative workshops, record what participants actually said and leave disagreements open until the responsible people resolve them.
