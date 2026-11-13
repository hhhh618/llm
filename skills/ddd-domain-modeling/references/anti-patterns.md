# Common Anti-Patterns in Domain Modeling

Avoid these frequent mistakes.

## Discovery Phase
- Starting with database tables or existing code structure
- Writing future-tense or solution-oriented language on event stickies
- Letting one senior person dominate while others stay silent
- Treating Event Storming as a requirements gathering questionnaire instead of collaborative exploration
- Ignoring hotspots and forcing artificial consensus

## Strategic Design
- Creating too many tiny Bounded Contexts without clear language boundaries
- Putting everything into one giant context “because it is simpler”
- Using the same term with different meanings across contexts without explicit translation
- Neglecting the Context Map (relationships matter)

## Tactical Design
- Anemic domain model: data classes + all logic in services or application layer
- Huge Aggregates that try to enforce too many unrelated invariants
- Exposing internal Entities directly to the outside world
- Using primitive types (string, int) for concepts that have real meaning (Direction, Money, Status)
- Putting infrastructure concerns (SQL, HTTP, messaging) inside domain objects
- Designing only for the happy path and leaving edge cases as afterthoughts

## Process & Collaboration
- Modeling alone when domain experts are available
- Treating the model as finished after the first pass
- Jumping to code generation or detailed class diagrams before validating with scenarios
- Over-modeling Supporting or Generic subdomains at the expense of the Core Domain

## Language
- Developers inventing technical names instead of adopting business language
- Business people accepting technical jargon because “the developers understand it”
- Glossary that is never updated when the model evolves

## Recovery Advice
When you notice an anti-pattern:
1. Stop and name it explicitly.
2. Return to the relevant earlier phase (usually Event Storming or Aggregate design).
3. Re-validate with a concrete business scenario.
4. Prefer a simpler, clearer model over a “complete” but confusing one.

The goal is a model that domain experts recognize as their own and that developers can implement without constant translation.