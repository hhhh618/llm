# Tactical Design Patterns

Use these building blocks inside each Bounded Context after strategic design.

## Core Building Blocks

### Entity
- Has a unique identity that remains stable over time.
- Has a lifecycle (created, changed, eventually archived or deleted).
- Equality is based on identity, not attributes.
- Example: MirrorSession, Order, Customer.

### Value Object
- Defined only by its attributes.
- Immutable.
- Equality by value.
- Can be freely shared and replaced.
- Examples: Direction (Ingress/Egress/Both), Money, Address, PortIdentifier, SessionStatus.

### Aggregate
- A cluster of Entities and Value Objects treated as a single consistency unit.
- Has one Aggregate Root — the only entry point for external commands.
- Invariants must always hold inside the aggregate boundary.
- Transactions should ideally modify only one aggregate at a time.
- Keep aggregates small.

### Aggregate Root Responsibilities
- Enforce invariants
- Accept commands and decide whether to apply them
- Raise Domain Events when significant state changes occur
- Protect internal entities from direct external access

### Domain Event
- Something significant that happened in the domain (past tense).
- Immutable fact.
- Other parts of the system (or other contexts) may react to it.
- Examples: MirrorSessionActivated, OrderPaid, PaymentFailed.

### Domain Service
- Stateless operation that does not naturally belong to a single Entity or Value Object.
- Operates on multiple domain objects.
- Use sparingly; prefer putting behavior on Entities or Aggregates when possible.

### Repository
- Provides the illusion of an in-memory collection of Aggregates.
- Responsible for retrieving and persisting Aggregate Roots.
- Belongs to the domain layer interface; implementation is infrastructure.

### Factory
- Encapsulates complex creation logic for Aggregates or Entities.
- Ensures the object is created in a valid state.

## Design Rules
1. Start with the Aggregate Root and its key behaviors.
2. Put business rules inside the model, not in application services or controllers.
3. Prefer Value Objects over primitive types for concepts that have meaning (Direction, Money, Email, etc.).
4. Explore commands and invariants alongside the information people need to make decisions; choose read models and implementation architecture according to actual requirements.
5. Name everything with the Ubiquitous Language of the current Bounded Context.
6. Protect the Aggregate boundary: external objects talk only to the Root.

## From Event Storming to Aggregates
- Look at clusters of events and commands that change together and must stay consistent.
- The nouns that own those state changes are candidate Aggregate Roots.
- A command may be routed to an aggregate operation or domain service when appropriate; external observations and rejected commands need not map one-to-one to aggregate methods.
- Determine which observations are domain events, external events, or integration events; do not assume each board event is emitted by an aggregate.

## Rich vs Anemic Model
- Rich: behavior and data live together; methods express business language.
- Anemic: pure data classes + external procedural logic. Avoid for core domain.

## Invariants Example (Port Mirroring)
- A session must have at least one source and one destination before it can be activated.
- Destination port cannot be the same as any source port (or must follow device-specific rules).
- Maximum number of concurrent sessions per device.
- Direction must be explicitly set for every source.

Capture these as methods or private validation on the Aggregate Root.