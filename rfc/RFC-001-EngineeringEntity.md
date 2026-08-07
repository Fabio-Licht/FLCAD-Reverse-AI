# RFC-001: EngineeringEntity

| Field | Value |
|---|---|
| RFC | RFC-001 |
| Title | EngineeringEntity |
| Project | FLCAD Reverse AI |
| Category | Core architecture |
| Status | Proposed |
| Audience | Software architects, engineering-domain leads, module owners |
| Scope | Platform-wide engineering object model |

## Purpose

This RFC proposes `EngineeringEntity` as the common conceptual base for
every engineering object represented inside the FLCAD platform.

FLCAD is intended to understand engineering intent, not merely store
geometric objects. A mesh, detected plane, reference axis, reconstructed
feature, comparison result, and future manufacturing entity have different
domain meanings, but they share fundamental platform concerns:

- Identity.
- Naming and classification.
- Geometry and engineering metadata.
- State and lifecycle.
- Provenance.
- Confidence.
- Relationships.
- Visibility and selection.
- Constraints.
- Change history and versioning.

These concerns should have one consistent architectural meaning across the
platform. Every engineering object should therefore inherit from, implement,
or otherwise conform to the common `EngineeringEntity` contract.
The exact implementation mechanism is deliberately outside the scope of this
RFC. The requirement is semantic conformance, not a prescribed programming
language construct.

A common entity architecture improves scalability because platform services
can operate on stable contracts rather than module-specific object models.
Persistence, visualization, commands, comparison, AI reasoning, plugins, and
future engineering engines can work with new entity types without requiring
each cross-cutting service to be redesigned.

The model is intended to extend the architecture already represented by
project objects, reference entities, metadata, and the early engineering
feature foundation. It must not create an unmanaged, competing object
registry.

## Motivation

### Fragmented object models in engineering software

Traditional CAD and engineering applications frequently evolve as collections
of subsystems. Mesh processing, CAD, inspection, sketching, rendering,
manufacturing, automation, and plugins may each define and manage objects
differently.

This fragmentation commonly produces:

- Different identity schemes across modules.
- Geometry stored separately from its engineering meaning.
- Module-specific naming, visibility, selection, and ownership rules.
- Relationships that exist only inside individual tools.
- Lost provenance after conversions or exports.
- Confidence information detached from recognized results.
- Inconsistent serialization and persistence.
- Undo and redo behavior that varies between object families.
- AI systems that receive disconnected geometry without trustworthy context.
- Plugin integrations that require special handling for every object type.
- Comparison and inspection results that cannot be traced cleanly to the
  objects they evaluate.

The result may appear modular at the UI level while remaining semantically
fragmented underneath.

### Unified entity model

A unified entity model gives all engineering modules a shared language for
identity, state, provenance, relationships, and change. Specialized modules
remain responsible for their own domain behavior, but they no longer redefine
fundamental platform concepts.

The proposed model enables:

- Stable references between modules.
- Traceability from source evidence to accepted engineering knowledge.
- Consistent lifecycle and validation rules.
- Shared serialization and persistence infrastructure.
- Cross-domain relationship analysis.
- Explainable AI decisions grounded in entity provenance and confidence.
- Generic event, command, history, visibility, selection, and plugin
  mechanisms.

Uniformity must not erase domain meaning. A plane and a mesh remain different
engineering types with different validation rules. The common model
standardizes their shared platform behavior while allowing type-specific
geometry, attributes, constraints, and services.

## EngineeringEntity

An `EngineeringEntity` is a uniquely identifiable unit of engineering
knowledge managed by the FLCAD platform.

An entity may represent imported evidence, a recognized primitive, an
engineer-confirmed reference, a calculated result, or another approved
engineering object. Being an entity does not imply that the object is valid,
confirmed, geometric, visible, or suitable for manufacturing. Those facts
must be expressed explicitly through type, lifecycle state, provenance,
confidence, relationships, and validation.

### UUID

Every entity shall have a globally unique and stable identifier.

The UUID shall:

- Remain stable across renaming, display changes, and persistence cycles.
- Be independent of collection position and human-readable names.
- Support reliable references from relationships, commands, events, and
  external integrations.
- Never be silently reused for a semantically different entity.

Identity retention after transformation, replacement, duplication, or
version creation requires a separate architectural decision.

### Name

The name is the stable program-facing or project-facing designation of the
entity. Naming rules should avoid ambiguity within the relevant project
scope.

Changing a name shall not change entity identity.

### Display Name

The display name is the human-facing label shown in the UI, reports, and
engineering workflows. It may be localized or formatted differently from the
stable name.

Display names are not valid substitutes for UUID-based references.

### Entity Type

The entity type identifies the engineering category and determines which
domain services, geometry representations, attributes, constraints, and
validation policies apply.

Entity types must be governed. Arbitrary type strings must not become an
uncontrolled parallel schema.

### Geometry

Geometry is the spatial representation associated with the entity when the
entity has geometric content.

Geometry may be:

- Source evidence.
- A mathematical primitive.
- A reference representation.
- A calculated or generated result.
- Absent for non-geometric engineering entities.

The entity contract shall not force every geometry type into one storage
format. It shall provide a consistent way to identify, access, version, and
relate geometry while specialized geometry services retain ownership of
their algorithms.

Rendered actors are not authoritative entity geometry.

### Metadata

Metadata contains governed descriptive information shared across the
platform. It may include source identifiers, creation method, quality
summaries, units, coordinate context, notes, and other approved descriptors.

Metadata shall not become an unstructured replacement for properly modeled
properties.

### Attributes

Attributes are typed engineering values associated with the entity. Examples
may include measured or fitted parameters that are meaningful for the entity
type.

Attributes shall define units, precision, origin, and validation where those
properties affect engineering interpretation.

### Relationships

Relationships connect an entity to other entities and carry explicit
engineering semantics. Relationships are discussed in detail below.

Relationships shall use entity UUIDs and governed relationship types.

### State

State identifies the entity's lifecycle status and the degree of engineering
authority that may be assigned to it.

State shall not be inferred solely from visibility, existence, confidence, or
selection.

### Visibility

Visibility expresses whether the entity is logically enabled for display in
the current project context.

Logical visibility is distinct from:

- Geometric occlusion.
- View-frustum inclusion.
- Layer visibility.
- Temporary preview display.
- Whether a renderer has created an actor.

### Selection

Selection expresses the entity's logical selection state for an active user
or interaction context.

The architecture must eventually define whether selection is stored on the
entity, in a project interaction context, or as a user-scoped relationship.
The common contract must nevertheless make selection behavior consistent
across entity types.

### Layer

Layer associates the entity with an organizational or visibility grouping.

Layer semantics, identity, nesting, and interaction with visibility require a
dedicated specification before implementation.

### Owner

Owner identifies the responsible user, subsystem, project context, or
organizational authority, according to an approved ownership model.

Ownership must not be confused with provenance. An entity may be owned by a
project while having been created by a user, algorithm, or AI workflow.

### Source

Source identifies the evidence or upstream entities from which the entity was
derived.

Source information should support traceability to imported files, source
meshes, selected regions, recognized primitives, calculations, and upstream
engineering entities where applicable.

Source is more than free-form text. It should be represented through
provenance records and relationships when reliable machine interpretation is
required.

### Confidence

Confidence expresses the assessed reliability of a detected, inferred,
calculated, or generated engineering claim. It is discussed in detail below.

Confidence shall not replace fit error, tolerances, validation state, or
engineer approval.

### History

History records meaningful changes to the entity or provides access to the
records that describe those changes.

History should identify:

- What changed.
- When it changed.
- Who or what initiated the change.
- The prior and resulting versions or states.
- The command or workflow context.
- Relevant reason or approval information.

History requirements must be reconciled with the command architecture and
project persistence design.

### Version

Version identifies the revision of the entity's engineering content.

Version changes must follow defined rules. A display-only interaction should
not necessarily create an engineering revision, while changed geometry,
attributes, constraints, or authoritative relationships may require one.

Entity version is distinct from application version, file-format version, and
document revision.

### Timestamp

Timestamps record significant lifecycle and change events. At minimum, the
architecture should distinguish creation and last-modified times.

Time values shall use a defined time standard and preserve sufficient
precision and timezone meaning for persistence and collaboration.

### Constraints

Constraints express requirements imposed on the entity or between entities.
They may describe geometric, dimensional, relational, or workflow conditions
after the relevant constraint domains are specified.

Constraints shall be explicit, traceable, and verifiable. A relationship is
not automatically a constraint, and a detected relationship is not
automatically an enforced constraint.

### Tags

Tags provide controlled or user-defined classification for search,
organization, and workflow grouping.

Tags shall not replace entity types, lifecycle states, or governed
relationships.

### Custom Properties

Custom properties provide an extension mechanism for module-specific,
project-specific, or plugin-specific data that does not yet belong in the
governed core schema.

Custom properties require:

- A namespaced owner.
- A defined value type.
- Serialization rules.
- Versioning expectations.
- Validation where engineering meaning is involved.

Custom properties must not be used to bypass architectural review for
platform-critical concepts.

## Entity Lifecycle

The lifecycle describes the engineering authority and usage of an entity.
Transitions must be explicit and auditable.

The following states are proposed:

```text
Draft
  -> Detected
  -> Validated
  -> Confirmed
  -> Referenced
  -> Locked

Any applicable active state
  -> Modified
  -> Validated or Confirmed

Any applicable state
  -> Deprecated
  -> Archived
```

This diagram is illustrative. Not every entity must pass through every state,
and not every transition is valid for every entity type.

### Draft

The entity exists as incomplete work, a temporary engineering proposal, or
an object whose required information is not yet complete.

A draft shall not be treated as verified engineering knowledge.

### Detected

The entity was identified from source evidence by a recognition or analysis
process.

Detected entities shall retain source evidence, recognition method, quality
metrics, and confidence where applicable. Detection does not imply
validation.

### Validated

The entity has passed the defined technical validation for its type and
workflow.

Validation may include geometric quality, tolerance, consistency, constraint,
or completeness checks. The validation method and result must be traceable.

### Confirmed

The entity has been accepted by an authorized engineer or by an explicitly
approved confirmation workflow.

Confirmation is an engineering decision. High confidence alone shall not
silently promote an entity to Confirmed.

### Referenced

The entity is being used as an authoritative reference by one or more
downstream entities or workflows.

Transition into this state should verify that the entity meets the required
validation and confirmation policy.

### Locked

The entity is protected from ordinary modification because it is approved,
referenced, released, or otherwise controlled.

Locking does not make an entity geometrically correct. It controls mutation.
Authorized changes must follow an explicit unlock or revision workflow.

### Modified

The entity's authoritative engineering content changed after a prior
validation, confirmation, or reference state.

Modification may invalidate confidence, validation, constraints, cached
spatial indexes, comparisons, and dependent entities. The platform must not
silently retain stale authority after material change.

### Deprecated

The entity remains available for traceability but should no longer be used
for new engineering work.

A deprecated entity may identify a replacement or reason for deprecation.

### Archived

The entity is retained for historical, regulatory, or project-record
purposes and is removed from normal active workflows.

Archiving is not equivalent to deletion.

### Lifecycle governance

The final state machine must define:

- Valid transitions by entity type.
- Transition authority.
- Required validation and approval evidence.
- Effects on dependent entities.
- Interaction with undo and redo.
- Deletion and restoration semantics.
- Version and history behavior.

These details require a follow-up specification before implementation.

## Provenance

Every entity must know how it was created because engineering trust depends
on traceability.

Two geometrically identical entities may have different engineering
authority when one was imported from a controlled source, another was fitted
from noisy scan data, and a third was proposed by an AI system. Without
provenance, downstream modules and engineers cannot determine what evidence
supports an entity or whether recalculation is possible.

Provenance shall identify:

- Creation origin.
- Creating user, service, module, algorithm, or AI workflow.
- Source entities and external inputs.
- Creation time.
- Method and relevant parameters.
- Software or model version where reproducibility depends on it.
- Resulting confidence and quality evidence.
- Subsequent transformation or derivation chain.

The proposed origin categories include:

### Imported

Created from an external file, device, service, or project source. Provenance
should retain source identity, format, import settings, and integrity
information where available.

### Recognized

Detected by a recognition workflow from geometric evidence. Provenance should
retain source regions or entities, recognition parameters, fit quality,
algorithm version, and confidence.

### Calculated

Produced deterministically from engineering inputs, such as an intersection,
alignment, measurement, or derived parameter. Provenance should identify the
inputs and calculation method.

### Generated

Produced by a system workflow from defined rules, patterns, or other
engineering entities. Provenance should distinguish rule-based generation
from AI generation.

### Created by User

Explicitly authored or defined by an engineer. Provenance should identify the
user action and relevant input values without implying that manual creation
is automatically validated.

### Created by AI

Proposed or generated by an AI-assisted workflow. Provenance must identify
the model or agent context, source evidence, confidence, assumptions, and
required human confirmation.

AI-created entities shall never conceal their origin by being labeled only
as generated or calculated.

Provenance shall be append-only in meaning. Corrections may supersede an
incorrect record, but the historical creation chain must not be silently
rewritten.

## Confidence

Confidence is a quantified assessment of how strongly available evidence
supports a specific engineering claim.

Examples:

| Entity or claim | Example confidence |
|---|---:|
| Detected plane | 99.8% |
| Detected cylinder | 96.2% |
| Inferred radius value | 74.0% |

These values are illustrative only. They do not define current algorithm
performance or acceptance thresholds.

Confidence must be associated with the claim it evaluates. A cylinder may
have high confidence as a primitive classification while its radius has lower
confidence because the scan covers only a small arc. One entity-level number
must not erase meaningful differences among classification, geometry,
attributes, and relationships.

Confidence should be supported by:

- The method that produced it.
- The evidence evaluated.
- The calibration dataset or mathematical interpretation.
- Relevant fit and residual metrics.
- Known uncertainty or data limitations.
- The model or algorithm version.

Percentages must not be displayed unless they have a defined, calibrated
meaning. A score of `0.998` is not inherently a 99.8 percent probability.

### Use by AI

AI systems should use confidence to:

- Rank candidates.
- Decide when to request more evidence.
- Identify ambiguous features or relationships.
- Select conservative workflow branches.
- Explain uncertainty to the engineer.
- Recommend validation or comparison steps.
- Avoid propagating weak assumptions as facts.

AI systems must not:

- Treat confidence as proof.
- Confirm an entity solely because its score exceeds a threshold.
- combine scores from different methods without a defined calibration model.
- Hide low-confidence attributes inside a high-confidence entity.
- overwrite engineer decisions without an authorized workflow.

The engineer remains responsible for critical acceptance. Confidence informs
that decision; it does not replace it.

## Relationships

Engineering entities never exist in isolation. A reverse-engineered part is
understood through relationships among source evidence, primitives,
references, features, constraints, calculations, and downstream results.

A unified relationship model is the foundation for a future Feature Graph
and engineering knowledge model.

Each relationship should define:

- A governed relationship type.
- Source and target entity UUIDs.
- Directionality.
- Symmetry, where applicable.
- Provenance.
- Lifecycle state.
- Confidence for detected or inferred relationships.
- Tolerance and quality evidence where geometric meaning depends on them.
- Whether it is descriptive, inferred, validated, or constraining.
- History and version behavior.

The initial conceptual relationship vocabulary includes:

### Contains

One entity spatially or semantically contains another. Containment must
define whether it represents ownership, topology, grouping, or geometric
inclusion.

### Parallel

Two directional entities are parallel within an explicit angular tolerance.

### Perpendicular

Two directional entities are perpendicular within an explicit angular
tolerance.

### Coincident

Two geometric entities occupy a common location or geometric locus within an
explicit tolerance.

### Tangent

Two entities meet with tangential continuity according to the geometry types
and tolerance model.

### Intersect

Two entities share one or more geometric intersections. The relationship may
refer to calculated intersection entities.

### Depends On

The source entity requires the target entity for definition, calculation,
validation, or lifecycle authority. Dependency direction and invalidation
behavior must be explicit.

### References

The source entity uses the target as engineering context or authority without
necessarily depending on it for geometric definition.

### Parent

The entity is the organizational or domain parent of another entity.

### Child

The entity belongs under a parent entity. Parent and Child are inverse views
of the same governed relationship and must not drift into contradictory
records.

Relationship names alone are insufficient. Each type requires a formal
semantic definition before production use. Geometric relations must reuse
approved spatial and geometry services rather than duplicating calculations
inside the relationship model.

## Event Model

Every `EngineeringEntity` shall participate in a common event model.

Events allow project services, visualization, persistence, undo/redo,
dependency tracking, AI workflows, and future plugins to react to entity
changes without direct module-to-module coupling.

Conceptual event types include:

- `EntityCreated`
- `EntityModified`
- `EntityDeleted`
- `VisibilityChanged`
- `SelectionChanged`
- `ConstraintAdded`

Additional governed events will be required for state transitions,
relationships, validation, locking, provenance, and archival.

Each event should identify:

- Event identity.
- Entity UUID.
- Entity type.
- Event type.
- Timestamp.
- Initiating user, command, module, workflow, or AI agent.
- Entity version before and after the change, where applicable.
- Correlation with the command or engineering workflow.
- A structured description of the change.
- Whether the event is provisional, committed, reversed, or restored.

### Event semantics

`EntityCreated` indicates that a new entity identity entered the project.

`EntityModified` indicates a change to authoritative entity content. The event
must identify which governed properties changed.

`EntityDeleted` indicates removal from active project state. Deletion,
deprecation, and archival are different operations and shall produce
different semantics.

`VisibilityChanged` indicates a logical visibility change, not geometric
occlusion or renderer state.

`SelectionChanged` indicates a change in an interaction context. Multi-user
or multi-view selection scope requires future definition.

`ConstraintAdded` indicates that a governed constraint was attached to the
entity or established between entities.

Events shall describe facts that occurred. Commands express requested
actions. The architecture must not conflate the two.

The final event architecture must define delivery, ordering, transactions,
failure behavior, persistence, replay, coalescing, and compatibility with the
existing callback and command mechanisms before implementation.

## Why this architecture

### Undo

A shared entity identity and event vocabulary allow commands to capture
consistent before-and-after state across object types. Undo can restore
entity state and relationships without every module inventing its own object
tracking conventions.

### Redo

Stable identifiers, versions, and provenance allow a reverted operation to be
reapplied against the intended entity graph. Redo behavior can remain
consistent across geometry, metadata, relationships, visibility, and
constraints.

### Serialization

A governed base contract provides a predictable envelope for identity, type,
state, metadata, relationships, provenance, and extension data. Specialized
geometry and attributes may use type-specific serializers without losing
platform-wide semantics.

### Persistence

Persistence can store and retrieve entities through stable identities,
versions, relationships, and provenance rather than module-specific object
tables with incompatible behavior.

The entity model does not itself select a database or native file format.

### Artificial Intelligence

AI receives structured engineering context rather than isolated triangles or
untyped objects. Entity type, source, confidence, constraints, relationships,
and lifecycle state allow AI to distinguish evidence from hypotheses and
confirmed engineering knowledge.

### Feature Graph

Entities become graph nodes and governed relationships become graph edges.
The Feature Graph can focus on engineering semantics without first
normalizing incompatible module identities.

### Knowledge Kernel

A future Knowledge Kernel can reason over stable engineering facts,
provenance, constraints, and relationships. The proposed entity model is a
prerequisite, not an implementation, of such a kernel.

### Engineering Brain

The Engineering Brain can plan and execute tasks against common entity
contracts. Workflow tasks can declare their inputs, outputs, dependencies,
confidence, and expected lifecycle transitions without hard-coding every
module's internal model.

### Intelligent Comparison

Comparison results can reference exactly which source and target entities,
versions, geometries, datums, and tolerances were evaluated. Results can be
retained as traceable engineering knowledge instead of detached color maps.

### Inspection

Inspection workflows can associate measurements, datum references,
tolerances, uncertainty, and acceptance decisions with stable entities.
Inspection remains responsible for metrology semantics.

### CAM

Future CAM workflows can consume confirmed, versioned engineering entities
and retain dependencies from manufacturing information to its geometric and
engineering sources. CAM-specific safety and process models remain separate.

### Plugins

Plugins can interact with a stable platform contract and introduce namespaced
custom properties or approved entity types without replacing project
identity, history, provenance, or event systems.

Plugin extensions must remain serializable, versioned, and governed.

### Scalability outcome

The architecture allows the number of modules and entity types to grow
without multiplying the number of point-to-point integrations.

```text
Without a unified model:

Module A object model <-> Module B object model
Module A object model <-> Module C object model
Module B object model <-> Module C object model
...repeated for every new module

With EngineeringEntity:

Module A ─┐
Module B ─┼─> Common entity, relationship, lifecycle, and event contracts
Module C ─┘
```

The common contract reduces integration complexity, but it must not become a
monolithic class containing every domain behavior. Domain modules should
extend the shared semantics through composition, specialization, governed
attributes, and services.

## Architectural Considerations

This proposal overlaps with concepts already present in:

- The logical project object model.
- Project object metadata and parent/source relationships.
- Reference entities and the reference manager.
- Command snapshots and undo/redo.
- Scene and selection synchronization.
- The early `EngineeringFeature`, repository, and factory.
- Engineering Brain domain and capability models.

Adoption must reconcile these concepts. It must not introduce a third,
parallel source of truth.

Before implementation, follow-up decisions are required for:

- Inheritance versus protocol, composition, or aggregate conformance.
- Authoritative entity repository ownership.
- Entity and geometry versioning.
- Persistence format and schema evolution.
- Event transactions and ordering.
- Lifecycle transition policies.
- Relationship storage and validation.
- Selection and ownership scope.
- Custom-property governance.
- Migration from current project objects and engineering features.

## Decision Requested

Senior architecture review is requested on the following proposal:

> Adopt `EngineeringEntity` as the common semantic contract for all
> persistent or project-managed engineering objects in FLCAD, while keeping
> domain behavior in specialized modules and preventing duplicate object
> registries.

Approval of this RFC authorizes refinement of the entity contracts and
follow-up specifications. It does not authorize implementation or migration.
