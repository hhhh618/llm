# Complete Example — Switch Port Mirroring (SPAN)

This walkthrough shows how to apply the full DDD process to a technical network feature.

## 1. Vision and Scope
**Vision**: Allow network operators and security teams to copy selected traffic from one or more ports (or VLANs) to a monitoring port without affecting normal forwarding, enabling troubleshooting, performance analysis, and security inspection.

**Scope**: Local port mirroring (SPAN) on a single switch. Remote variants (RSPAN/ERSPAN) are out of scope for the first iteration.

**Key personas**: Network Administrator, NOC Operator, Security Analyst, Monitoring Appliance.

## 2. Event Storming (Summary)
**Key Domain Events** (past tense):
- Mirror Session Created
- Source Port Added
- Source Port Removed
- Destination Port Set
- Configuration Validated
- Configuration Validation Failed
- Mirror Session Activated
- Traffic Copy Started
- Mirror Session Deactivated
- Mirror Session Deleted
- Session Limit Exceeded

**Commands + Actors**:
- Network Admin → Create Mirror Session → Session Created
- Network Admin → Add Source (with Direction) → Source Port Added
- Network Admin → Set Destination Port → Destination Port Set
- System → Validate Configuration → Validated / Failed
- Network Admin → Activate Session → Session Activated
- Network Admin → Deactivate Session → Session Deactivated

**Hotspots**:
- Can the destination port still forward normal traffic?
- What happens when source and destination overlap?
- Device-imposed session count limits
- Direction constraints (some devices limit Tx or Both)
- How monitoring systems are notified of activation

## 3. Strategic Design
**Subdomain**: Supporting (Network Observability / Traffic Monitoring)

**Bounded Context**: Mirror Session Management
- Responsibility: lifecycle of local mirroring sessions, source/destination configuration, activation rules, and invariants.
- Ubiquitous Language: MirrorSession, Source, Direction, DestinationPort, SessionStatus, Activate, Deactivate.

Other related contexts (not detailed here): Device Inventory, Port Management, Monitoring Integration.

## 4. Tactical Design

### Aggregate: MirrorSession (Root)
**Identity**: SessionId (unique per device)

**Contained objects**:
- List of Sources (each Source = PortIdentifier + Direction)
- DestinationPort (Value Object)
- Status (Value Object: Created | Active | Inactive | Failed)
- Optional filters or sampling rate (future)

**Key Behaviors**:
- create(sessionId, device)
- addSource(port, direction)
- removeSource(port)
- setDestination(port)
- activate() — enforces invariants, raises MirrorSessionActivated
- deactivate()
- delete()

**Invariants**:
1. At least one source and one destination required before activation.
2. Destination must not conflict with sources according to device rules.
3. A device-wide session limit, if applicable, needs a device-level consistency owner or explicit coordination; a single session cannot enforce the global count by itself.
4. Direction is mandatory for every source.
5. Once Active, certain configuration changes may be restricted (device-dependent).

**Domain Events**:
- MirrorSessionCreated
- SourceAdded
- DestinationSet
- MirrorSessionActivated
- MirrorSessionDeactivated
- ConfigurationRejected

### Value Objects
- Direction: Ingress | Egress | Both
- PortIdentifier
- SessionStatus
- SessionId

## 5. Ubiquitous Language Glossary (excerpt)
| Term | Definition |
|------|------------|
| Mirror Session | A configured association of sources and one destination used to copy traffic |
| Source | A port or VLAN whose traffic is being copied, together with direction |
| Direction | Whether to copy ingress, egress, or both directions of traffic |
| Destination Port | The port that receives the copied traffic (usually connected to an analyzer) |
| Activate | Make the session start copying traffic after validation |

## 6. Validation Scenarios
- Create session → add two sources (Both) → set destination → activate → success
- Try to activate without destination → rejected
- Add destination that equals a source → rejected or marked as hotspot
- Exceed max sessions → Session Limit Exceeded event / rejection

## 7. Next Steps
- Map to device-specific CLI / NETCONF / OpenConfig adapters (Anti-Corruption Layer)
- Consider read model for “currently active sessions on device”
- Explore remote mirroring as a separate context or extension
- Implement domain events for integration with monitoring platforms

This illustrative example requires device-specific confirmation. The session aggregate protects session-local rules; device-wide limits need an appropriate separate consistency owner or coordination.
