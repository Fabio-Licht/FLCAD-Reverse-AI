# FLCAD Reverse AI Engineering Constitution

This document is the permanent engineering handbook for AI agents and
developers working on FLCAD Reverse AI. It defines how contributors must
reason about the product, its architecture, and every proposed change.

The rules in this document apply to the entire repository.

## 1. Project Vision

FLCAD Reverse AI is being built as an intelligent Digital Engineering
Platform, not merely as another reverse-engineering application.

Its purpose is to help engineers move from scanned reality to engineering
knowledge, intentional geometry, and manufacturing-ready information. The
platform must eventually support a complete digital engineering workflow
while preserving human engineering judgment.

The current Genesis implementation establishes the desktop application,
engineering kernel foundations, mesh visualization, reference geometry,
primitive recognition, alignment, patterns, and an early capability-driven
Engineering Brain.

Every contribution must strengthen the platform foundation. A local feature
must not compromise the long-term modular architecture.

## 2. Core Philosophy

The project follows these non-negotiable principles:

- Think like an experienced reverse-engineering engineer.
- Understand the part before attempting to reconstruct it.
- Reconstruct engineering intent, not only visible mesh geometry.
- Treat mesh data as evidence of a design, not as the design itself.
- AI assists; the engineer decides.
- Preserve human control over critical engineering decisions.
- Reuse the existing architecture before introducing new abstractions.
- Never duplicate logic.
- Keep modules independent, replaceable, testable, and maintainable.
- Treat performance as a product capability.
- Treat documentation as part of the engineering deliverable.

Automation must remain explainable. The application should present the
evidence, assumptions, fit quality, and consequences needed for an engineer
to approve or reject a result.

## 3. Engineering Principles

### Engineering intent first

A successful reconstruction represents why geometry exists and how its
features relate. A collection of disconnected fitted surfaces is not, by
itself, an engineering reconstruction.

### Evidence before decisions

Recognition and reconstruction decisions must be based on measurable mesh
evidence. Fit residuals, confidence, tolerances, source regions, and relevant
quality indicators must remain available where the current model supports
them.

### Human validation

Preview and confirmation are important parts of engineering workflows.
Automatic results must not silently replace deliberate user decisions.

### One source of truth

Logical project state belongs in the project model. Rendered actors are
representations of that state, not an alternative project database.
Reference entities must be managed through the established reference and
project mechanisms.

### Reversible operations

User-visible changes should use the command architecture when undo and redo
are meaningful. A workflow must keep the logical project, reference records,
project tree, selection state, and rendered scene consistent.

### Explicit boundaries

Geometry computation, project state, visualization, UI, and workflow
orchestration have different responsibilities. New work must respect those
boundaries even where the current application still contains transitional
coupling.

### Evolution without speculative systems

Build only what the current task and architecture require. Planned engines
and services must not be represented as implemented until working code and
documentation exist.

## 4. Software Architecture

FLCAD Reverse AI is currently a Python desktop modular monolith.

The application entry point creates a PySide6 application and the main
window. The main window currently acts as the composition root and connects
the principal runtime subsystems:

```text
User Interface / Main Window
        |
        +-- Core
        |     +-- Project model and manager
        |     +-- Commands and undo/redo
        |     +-- Command presets
        |
        +-- Geometry
        |     +-- Plane and cylinder fitting
        |     +-- Region growth and refinement
        |     +-- Quality evaluation
        |     +-- Alignment and patterns
        |     +-- Reference entities
        |
        +-- Visualization
        |     +-- Scene
        |     +-- Selection and picking
        |     +-- Navigation
        |     +-- Reference display
        |
        +-- Mesh I/O
              +-- STL loading
```

The principal module responsibilities are:

- `src/core`: logical project state, project metadata, commands, history, and
  application-level consistency mechanisms.
- `src/geometry`: numerical geometry algorithms and engineering reference
  entities.
- `src/visualization`: VTK/PyVista scene, selection, picking, navigation, and
  display helpers.
- `src/ui`: PySide6 windows, panels, dialogs, previews, and current workflow
  coordination.
- `src/mesh_io`: external mesh loading.
- `src/recognition`: an emerging recognition-controller boundary.
- `src/engineering`: engineering-domain models, planning, capability
  dispatch, workflow execution, and feature abstractions.

Dependencies should point toward stable domain and service abstractions.
Numerical geometry must not depend on the UI. Project state must not depend
on its rendered representation. Rendering code must not become the owner of
engineering data.

The main window currently contains substantial workflow logic. New work
should avoid increasing this concentration when an existing domain,
service, command, controller, or engine boundary is appropriate. Refactoring
must be incremental and must preserve working behavior.

TODO: Integrate the Engineering Brain with the desktop application through
stable application-service boundaries.

TODO: Complete the intended event-based communication mechanism between
engineering engines.

TODO: Implement project persistence and the planned native project format
when their specifications are approved.

TODO: Define plugin integration only when a concrete plugin contract exists.

## 5. Reverse Engineering Workflow

The current reverse-engineering workflow is mesh-driven and
engineer-supervised:

```text
Import STL
    -> inspect and navigate the mesh
    -> select seed evidence
    -> grow and refine a mesh region
    -> fit an engineering primitive
    -> evaluate fit quality
    -> preview the result
    -> engineer confirms or adjusts
    -> create project/reference objects through commands
```

The workflow must retain the distinction between:

- The source mesh.
- The selected or grown mesh region.
- The mathematical fit.
- The quality assessment.
- The accepted engineering reference.
- The rendered representation.

Selection parameters, seed points, source object relationships, fit
metadata, and accepted results must not be conflated. Recalculation should
reuse valid prior evidence where the existing workflow supports it.

Recognition algorithms must handle imperfect scan data deliberately.
Outliers, incomplete coverage, tessellation density, noise, and ambiguous
regions are engineering conditions, not exceptional afterthoughts.

## 6. Spatial Engine

The current spatial foundation is distributed across the geometry and
visualization modules:

- NumPy-based vector, fitting, transformation, and pattern operations.
- PyVista/VTK mesh datasets and rendered geometry.
- Context picking from viewport coordinates to scene and mesh evidence.
- Scene transformations and engineering alignment.
- Reference points, axes, planes, and cylinders.

Spatial calculations must use explicit coordinate systems, normalized
directions where required, stable numerical tolerances, and clearly defined
units. Transformations must preserve the relationship between project data
and scene representations.

Geometry algorithms belong in `src/geometry` or a future approved spatial
service, not in dialog event handlers. Visualization-specific geometry
belongs in the visualization layer and must not be mistaken for authoritative
engineering geometry.

TODO: Define a formal Spatial Engine boundary after the existing geometry,
scene, picking, and transformation responsibilities are consolidated.

TODO: Define explicit project-wide unit and tolerance policies.

TODO: Define coordinate-system and datum models beyond the currently
implemented reference entities.

## 7. Primitive Recognition

The implemented primitive-recognition foundation supports planes and
cylinders.

Current capabilities include:

- Plane fitting from points.
- Plane residual and quality evaluation.
- Planar mesh-region growth.
- Cylinder fitting and axis refinement.
- Cylinder residual and quality evaluation.
- Cylindrical region growth and refinement.
- Multi-seed cylindrical-region handling.
- Interactive previews and engineer confirmation.

Primitive recognition must separate candidate discovery, region extraction,
mathematical fitting, quality assessment, presentation, and acceptance.
Algorithms must return structured results rather than depending on UI side
effects.

Fit quality must remain visible and usable. A fitted primitive is not
automatically a valid engineering feature. Acceptance depends on the
evidence, intended tolerance, scan condition, and engineer judgment.

The existing numerical implementations must be reused. New controllers,
adapters, or workflow layers must call the established geometry functions
instead of reproducing them.

TODO: Connect the recognition controllers and Engineering Brain recognition
adapter to real plane and cylinder recognition services.

TODO: Define approved contracts for additional primitive types before
implementing them.

## 8. Feature Graph

The current project model supports typed project objects, parent
relationships, source-object metadata, and engineering reference entities.
The engineering package also contains an early `EngineeringFeature`,
repository, and factory foundation.

These pieces are not yet a complete Feature Graph.

A future Feature Graph should express engineering relationships rather than
only object containment. Examples must be introduced only when backed by an
approved model and real workflow requirements.

Until that model exists:

- Use the current project object and reference mechanisms.
- Preserve `parent_id`, `source_object_id`, creation method, confidence, fit
  error, and custom metadata where relevant.
- Do not create a competing object registry.
- Do not claim that inferred feature relationships are authoritative.
- Keep graph-related experiments isolated from production project state.

TODO: Define Feature Graph nodes, relationship types, identity rules,
dependency behavior, validation, and persistence.

TODO: Reconcile `ProjectObject`, reference records, and
`EngineeringFeature` into an approved long-term domain model.

## 9. Engineering Brain

The Engineering Brain is the emerging intent-driven orchestration layer.
Its current architecture is:

```text
EngineeringGoal
    -> Planner
    -> EngineeringIntent
    -> EngineeringStrategy
    -> EngineeringTask sequence
    -> WorkflowRunner
    -> Executor
    -> CapabilityManager
    -> CapabilityProvider / adapter
```

The current planner is rule-based. The capability manager resolves named
capabilities to providers. The recognition adapter is presently a prototype
and does not execute the production recognition algorithms.

The Engineering Brain must coordinate engineering work; it must not
duplicate the work of geometry, recognition, visualization, or project
services. Its plans must be inspectable, its task state explicit, and its
decisions explainable.

AI planning may augment this architecture in the future, but AI output must
be treated as a proposal subject to domain constraints and engineer
approval.

TODO: Replace prototype capability actions with real service adapters.

TODO: Add providers for approved kernel capabilities.

TODO: Replace fixed session and task identifiers with a defined identity
strategy.

TODO: Define failure, cancellation, retry, progress, and rollback behavior
for multi-step workflows.

TODO: Add AI or hybrid planning only after deterministic workflow contracts
and evaluation criteria exist.

## 10. Reconstruction Workflow

Reconstruction must progress from evidence to intent:

```text
Mesh evidence
    -> recognized primitive candidates
    -> validated engineering references
    -> spatial relationships
    -> feature understanding
    -> reconstruction strategy
    -> engineer-reviewed result
```

The current implementation reaches validated references, alignment, and
reference patterns. It does not yet implement a complete CAD reconstruction
pipeline.

Every future reconstruction step must:

- Identify its source evidence.
- Record assumptions and relevant quality.
- Preserve traceability to source objects.
- Expose uncertain or ambiguous decisions.
- Use reversible project operations where applicable.
- Allow engineer review before critical acceptance.

TODO: Define the CAD/B-Rep reconstruction boundary.

TODO: Define how validated references become reconstruction features.

TODO: Define dependency-driven recalculation across accepted features.

TODO: Define reconstruction validation against the source mesh.

## 11. Intelligent Comparison

The current architecture contains geometric quality evaluation for fitted
planes and cylinders. It does not yet contain a complete inspection or
intelligent comparison engine.

Future comparison must be engineering-aware. Raw point-to-surface deviation
alone cannot explain design intent, feature identity, datum relationships,
or functional significance.

Until an approved comparison architecture exists, reuse current residual and
quality functions for their defined purposes. Do not label local fit metrics
as full-part inspection or intelligent comparison.

TODO: Define comparison inputs, alignment prerequisites, tolerance models,
outputs, visualization, and reporting.

TODO: Define how comparison results relate to project objects and the future
Feature Graph.

TODO: Define the boundary between recognition quality, reconstruction
validation, and metrology/inspection.

## 12. Coding Standards

### General rules

- Follow the existing Python package organization and naming conventions.
- Use type annotations for public interfaces and non-trivial internal data.
- Prefer dataclasses for structured domain results where appropriate.
- Keep functions and classes focused on one responsibility.
- Use clear engineering terminology rather than vague technical names.
- Add comments for engineering rationale, invariants, and numerical choices;
  do not narrate obvious syntax.
- Keep public behavior explicit. Avoid hidden global state.
- Validate inputs at module boundaries and raise meaningful errors.
- Preserve deterministic behavior unless nondeterminism is a deliberate,
  documented requirement.

### Architecture rules

- Search for an existing implementation before adding new logic.
- Extend existing services and abstractions when they own the responsibility.
- Do not copy geometry algorithms into UI, adapters, controllers, or tests.
- Do not let UI widgets become authoritative project storage.
- Do not manipulate rendered actors as a substitute for project commands.
- Keep Qt and VTK dependencies out of pure domain and numerical modules
  unless the responsibility genuinely requires them.
- Use capability providers as adapters, not as duplicate implementations.
- Maintain compatibility between project state, references, scene state,
  selection, and undo/redo.

### Change discipline

- Understand the complete affected workflow before editing code.
- Keep changes scoped and reviewable.
- Preserve unrelated work in the repository.
- Add or update tests for behavior that can be tested.
- Verify numerical work with representative normal, noisy, incomplete, and
  degenerate inputs where applicable.
- Do not silently change tolerances, units, coordinate conventions, or
  quality definitions.

TODO: Establish repository-wide formatter, linter, type-checker, and test
runner configurations.

TODO: Create an automated test suite; the current `tests` directory does not
yet provide project coverage.

TODO: Add a declared dependency and environment specification.

## 13. Performance Principles

Performance is a feature because engineering meshes and interactive 3D
workflows can be large.

- Measure before optimizing.
- Keep expensive computation out of high-frequency UI and rendering events.
- Prefer vectorized NumPy and appropriate VTK/PyVista operations over Python
  loops for large geometry data.
- Avoid unnecessary mesh, array, actor, and snapshot copies.
- Reuse computed regions, fits, and previews when their inputs are unchanged.
- Keep interaction responsive during selection, preview, navigation, and
  recalculation.
- Bound algorithms using explicit candidate regions when the engineering
  workflow permits it.
- Preserve numerical robustness while optimizing; a faster incorrect fit is
  not an improvement.
- Document performance-sensitive assumptions and expected data scale.

Optimizations must include evidence such as timing, profiling, memory
behavior, or a clearly demonstrated interaction bottleneck.

TODO: Establish representative mesh benchmarks and responsiveness targets.

TODO: Define background-execution and cancellation policies for expensive
workflows.

## 14. Documentation Standards

Documentation is part of the implementation.

Every significant architectural or engineering change must document:

- The engineering problem.
- The implemented behavior.
- The module and responsibility boundaries.
- The data flow and affected project state.
- Assumptions, units, tolerances, and numerical limitations.
- User decisions, previews, and failure behavior.
- Undo/redo and recalculation implications.
- Verification performed.
- Known limitations and explicit future work.

Architecture decisions that affect multiple modules should be recorded in an
ADR. Workflow-specific documents should describe the real implementation,
not only the intended result.

Documentation must clearly distinguish:

- Implemented behavior.
- Experimental or prototype behavior.
- Planned behavior marked as TODO.

Code, documentation, version labels, and diagrams must not contradict one
another. When behavior changes, update the relevant documentation in the
same change.

## 15. Future Vision

The long-term direction is a platform in which an engineer can provide an
engineering objective and receive an explainable, evidence-based workflow
coordinated across specialized engines.

The documented future platform may include CAD, AI, inspection,
manufacturing, persistence, collaboration, cloud, and mobile capabilities.
These remain future directions unless implemented in the repository.

The intended evolution is:

```text
Scanned reality
    -> spatial understanding
    -> primitive recognition
    -> engineering relationships
    -> intent-aware reconstruction
    -> intelligent comparison
    -> engineer decision
    -> reusable engineering knowledge
```

Future intelligence must build on trustworthy geometry, explicit domain
models, capability boundaries, project traceability, and measurable quality.
It must not bypass them.

TODO: Evolve the current modular monolith toward the documented Engineering
Kernel and independent-engine architecture as real module contracts emerge.

TODO: Define the complete Feature Graph and engineering knowledge model.

TODO: Define production AI governance, provenance, evaluation, confidence,
and human-approval requirements.

TODO: Define persistence, collaboration, cloud, and mobile architectures
only when their product requirements become concrete.

The permanent test for every future contribution is:

> Does this change help FLCAD Reverse AI understand engineering intent more
> accurately, explain its reasoning more clearly, preserve engineer control,
> and strengthen the platform architecture?
