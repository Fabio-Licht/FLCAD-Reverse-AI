# S-0001 - Spatial Engine

| Field | Value |
|---|---|
| Specification | S-0001 |
| System | Spatial Engine |
| Project | FLCAD Reverse AI |
| Document type | Engineering software specification |
| Status | Proposed |
| Implementation status | Planned |

## 1. Objective

The Spatial Engine shall be the common geometric foundation of the FLCAD
Reverse AI platform. It shall provide a unified, high-performance mechanism
for indexing geometric data, executing spatial queries, and accessing
geometry required by engineering workflows.

Every engineering module that requires spatial access shall use the Spatial
Engine through its public contracts. Modules shall not create independent,
competing spatial-index implementations unless an approved architecture
decision explicitly requires one.

The Spatial Engine shall:

- Provide consistent spatial access across engineering modules.
- Separate spatial-query infrastructure from user-interface and rendering
  concerns.
- Support interactive operations on engineering meshes.
- Preserve traceability between query results and authoritative project
  objects.
- Allow algorithms to operate on spatial subsets instead of repeatedly
  scanning complete datasets.
- Provide a stable foundation on which recognition, comparison, inspection,
  and reconstruction workflows can evolve.

The Spatial Engine shall not determine engineering intent. It shall return
geometric evidence and spatial relationships to modules that interpret them.

## 2. Responsibilities

### 2.1 Spatial indexing

The Spatial Engine shall construct and maintain indexes over supported
geometric datasets. An index shall retain a defined association with its
source project object and source geometry revision.

The indexing strategy may vary with geometry type and query profile. Internal
implementation choices shall remain hidden behind the public Spatial Engine
contracts.

### 2.2 Fast geometric queries

The engine shall execute repeatable spatial queries without requiring client
modules to traverse entire meshes. Query results shall be deterministic for
identical geometry, parameters, tolerances, and engine configuration.

### 2.3 Ray casting support

The engine shall support ray intersections against indexed geometry for
viewport picking, engineering selection, visibility analysis, and geometric
inspection.

Ray-query results shall be capable of identifying:

- The intersected project object.
- The intersected geometric element.
- The intersection position.
- Distance along the ray.
- Relevant local geometric data, when requested.

### 2.4 Nearest-neighbor search

The engine shall find the nearest points or supported geometric elements to a
query position or query set. Searches shall support explicit distance limits,
result limits, and engineering tolerances.

### 2.5 Bounding boxes

The engine shall calculate and query axis-aligned bounding boxes. Oriented
bounding boxes may be supported where an approved workflow requires them.

Bounding volumes shall support:

- Dataset extent calculation.
- Broad-phase spatial rejection.
- Region selection.
- Scene framing and navigation.
- Candidate filtering for downstream algorithms.

### 2.6 Region search

The engine shall search indexed geometry within a defined spatial region.
Supported region definitions shall be introduced through explicit contracts
and may include spheres, boxes, rays, planes, or other approved geometric
volumes.

Region searches shall return source-linked candidates. They shall not
silently convert candidates into accepted engineering features.

### 2.7 Visibility queries

The engine shall support geometric visibility and occlusion queries required
by selection, inspection, and interactive engineering workflows.

Logical project visibility and geometric line-of-sight are separate
concepts. The Spatial Engine shall not replace project visibility state or
the visualization scene manager.

### 2.8 Feature lookup

When the Feature Graph is defined, the Spatial Engine shall support locating
features associated with a position, region, primitive, or indexed geometric
element.

Feature lookup shall preserve the distinction between:

- Geometric candidates.
- Recognized primitives.
- Accepted engineering features.
- Relationships recorded in the Feature Graph.

TODO: Define Feature Graph lookup contracts after the Feature Graph domain
model is approved.

### 2.9 Primitive lookup

The engine shall support spatial lookup of recognized primitive candidates
and accepted primitive references. Primitive identity, fit quality, source
evidence, and acceptance state shall remain owned by their respective domain
services.

The Spatial Engine shall index and retrieve primitives; it shall not duplicate
the fitting and quality logic in the existing geometry modules.

## 3. Components

The conceptual internal structure shall be:

```text
Spatial Engine
├── Octree
├── BVH
├── Spatial Index
├── Query Engine
├── Intersection Engine
├── Selection Engine
└── Visibility Engine
```

These are logical components. This specification does not require each
component to be implemented as a separate process, package, or class.

### 3.1 Octree

The Octree component shall provide hierarchical subdivision of three-
dimensional space for workloads that benefit from location-based partitioning.
It may support neighborhood searches, spatial density queries, region
selection, and incremental spatial subdivision.

The component shall not be exposed as the only public indexing model.

### 3.2 Bounding Volume Hierarchy

The Bounding Volume Hierarchy, or BVH, shall accelerate intersection and
proximity operations by organizing geometric elements into nested bounding
volumes.

It is expected to support triangle-heavy meshes and ray-based queries.
Implementation shall account for construction cost, query performance,
geometry updates, and memory consumption.

### 3.3 Spatial Index

The Spatial Index shall coordinate the lifecycle of indexing structures. It
shall associate each index with:

- A source project object.
- A geometry identity or revision.
- Supported query capabilities.
- Coordinate-system information.
- Index validity state.

It shall prevent clients from unknowingly querying stale indexes after
geometry changes.

### 3.4 Query Engine

The Query Engine shall be the primary coordinator for spatial requests. It
shall validate query inputs, select the appropriate internal index, apply
tolerances and filters, and return structured results.

The Query Engine shall provide consistent semantics regardless of the
internal acceleration structure used.

### 3.5 Intersection Engine

The Intersection Engine shall execute ray, segment, bounding-volume, and
other approved geometric intersection operations.

It shall distinguish broad-phase candidate detection from precise
intersection results where this improves performance.

### 3.6 Selection Engine

The Selection Engine shall translate spatial query results into geometric
selection candidates. It shall support the existing separation between
viewport picking, scene representation, and logical project selection.

The Selection Engine shall not own application selection state. Accepted
selection remains coordinated through the established project and
visualization selection mechanisms.

### 3.7 Visibility Engine

The Visibility Engine shall evaluate line-of-sight, obstruction, and exposed
geometry where required by engineering workflows.

It shall consume authoritative geometry and spatial indexes without becoming
a replacement for rendering or logical visibility management.

## 4. Public API

The following operations define the conceptual public capability surface.
Names are descriptive and are not prescribed programming-language
signatures.

No implementation code is defined by this specification.

### 4.1 `CreateSpatialIndex()`

Creates an index for an identified geometry source. The operation shall
accept sufficient context to associate the index with the source project
object, geometry revision, coordinate system, and intended query
capabilities.

The result shall report whether the index is ready, invalid, unsupported, or
failed.

### 4.2 `UpdateSpatialIndex()`

Applies an incremental geometry change where supported. If an update cannot
preserve index correctness, the engine shall require or initiate a complete
rebuild according to the approved lifecycle policy.

### 4.3 `RemoveSpatialIndex()`

Releases the index associated with a geometry source without deleting the
authoritative project geometry.

### 4.4 `FindNearestPoints()`

Returns the nearest indexed points or mesh vertices according to explicit
distance, quantity, and filtering constraints.

Results shall include distance and source identity.

### 4.5 `FindPrimitives()`

Returns recognized or accepted primitives that intersect or fall within the
specified spatial criteria.

The operation shall not perform primitive fitting unless explicitly
delegated to the Primitive Recognition module through a separate workflow.

### 4.6 `FindFeatures()`

Returns Feature Graph entities associated with a spatial query after the
Feature Graph contract is implemented.

TODO: Define this operation with the Feature Graph specification.

### 4.7 `RayIntersection()`

Returns ordered intersections between a ray and indexed geometry. The
operation shall support nearest-hit and multiple-hit modes.

### 4.8 `SearchRegion()`

Returns geometric candidates inside or intersecting a defined search region.
Boundary inclusion, tolerance, result ordering, and maximum-result behavior
shall be explicit.

### 4.9 `SearchBoundingBox()`

Returns indexed objects or geometric elements that intersect or are contained
within a bounding box.

### 4.10 `QueryVisibility()`

Evaluates visibility or occlusion between approved query entities. Results
shall identify the geometry responsible for obstruction where requested and
computationally practical.

### 4.11 API behavior

All public operations shall:

- Use explicit coordinate-system and tolerance context.
- Return structured, source-linked results.
- Distinguish an empty valid result from an execution failure.
- Detect invalid or stale indexes.
- Define ordering where result order is significant.
- Support cancellation for operations that may exceed interactive latency
  targets.
- Avoid exposing internal Octree or BVH implementation details to clients.

TODO: Define concrete data contracts, error categories, asynchronous
execution behavior, and versioning before implementation.

## 5. Performance Requirements

### 5.1 Dataset scale

The Spatial Engine shall be designed for meshes containing millions of
triangles. Validation shall include representative engineering meshes rather
than only synthetic or trivially small datasets.

No fixed maximum mesh size is established until benchmark datasets and
supported workstation profiles are approved.

TODO: Define minimum, typical, and stress-test triangle counts.

### 5.2 Interactive latency

Queries used for picking, selection, and direct viewport interaction shall
support real-time interaction on the approved reference hardware.

The target for ordinary interactive queries shall be a response within one
display frame where feasible and within 100 milliseconds for queries that
require broader traversal. Operations exceeding the interactive threshold
shall expose progress or execute outside the UI thread.

TODO: Confirm latency budgets using representative meshes and reference
hardware.

### 5.3 Index construction

Index construction shall not make the application unresponsive. Large index
builds shall be cancellable or processed outside high-frequency interaction
paths.

Index construction time shall be measured independently from query time.

TODO: Establish construction-time targets per million triangles.

### 5.4 Parallel processing

Index construction and independent batch queries should support parallel
processing where determinism, library constraints, and workload size justify
it.

Parallel execution shall not introduce unsafe access to VTK/PyVista objects,
project state, or UI components.

### 5.5 Incremental updates

The engine shall support incremental updates for geometry changes where the
selected index structure can guarantee correctness. Incremental update cost
should be proportional to the changed region rather than total dataset size.

The engine shall detect cases in which rebuilding is safer or faster.

### 5.6 Memory behavior

The engine shall:

- Avoid unnecessary duplication of mesh coordinates and connectivity.
- Use contiguous data representations where practical.
- Reuse allocated query buffers where safe.
- Release invalidated indexes predictably.
- Minimize memory fragmentation during repeated index creation and updates.
- Report or expose index memory consumption for diagnostics.

### 5.7 Measurement

Performance claims shall be supported by reproducible benchmarks recording:

- Hardware and software environment.
- Source mesh size and characteristics.
- Index construction time.
- Query latency distribution, not only the fastest result.
- Peak and retained memory.
- Update cost.
- Concurrency configuration.

## 6. Future Extensions

The following extensions are planned subjects of future specifications. They
are not implementation requirements of the initial Spatial Engine.

### 6.1 GPU acceleration

TODO: Specify GPU-supported index construction, traversal, data transfer,
device selection, fallback behavior, numerical consistency, and supported
hardware.

### 6.2 Out-of-core meshes

TODO: Specify indexing and querying for meshes that exceed available system
memory, including storage layout, caching, paging, and deterministic query
semantics.

### 6.3 Distributed processing

TODO: Specify partitioning, remote execution, result aggregation, failure
handling, security, and consistency for distributed spatial workloads.

### 6.4 Streaming meshes

TODO: Specify index behavior for geometry arriving or changing as a stream,
including partial validity, revision tracking, update ordering, and query
consistency.

### 6.5 Level of Detail

TODO: Specify Level-of-Detail generation, selection, error metrics, query
accuracy, visualization interaction, and traceability to full-resolution
geometry.

## 7. Dependencies

### 7.1 Primitive Recognition

Primitive Recognition shall use the Spatial Engine to identify candidate
points, triangles, neighborhoods, and regions efficiently.

The Spatial Engine shall not duplicate:

- Plane or cylinder fitting.
- Region-growth engineering criteria.
- Residual calculations.
- Primitive quality evaluation.
- Engineer acceptance workflows.

Primitive Recognition shall return structured primitive results that may
subsequently be indexed for lookup.

### 7.2 Feature Graph

The Feature Graph shall own engineering feature identity and relationships.
The Spatial Engine may index feature locations and resolve spatial queries to
Feature Graph identifiers.

The Spatial Engine shall not infer or own semantic feature relationships.

TODO: Define the integration contract after the Feature Graph specification
is approved.

### 7.3 Engineering Brain

The Engineering Brain may request spatial capabilities as steps in an
engineering strategy. It shall access them through registered services or
capability providers rather than internal index structures.

Spatial query results supplied to the Engineering Brain shall be
explainable, source-linked, and accompanied by relevant quality or
completeness information.

### 7.4 Intelligent Comparison

Comparison workflows shall use the Spatial Engine for correspondence
candidates, proximity searches, spatial partitioning, and accelerated
deviation evaluation.

The Comparison module shall own comparison meaning, alignment requirements,
tolerances, classification, and reporting.

### 7.5 Sketch

Future sketch workflows may use the Spatial Engine for projection targets,
snapping candidates, intersections, and spatial references.

The Sketch module shall own sketch constraints and parametric sketch
semantics.

TODO: Define the Sketch integration after a Sketch module contract exists.

### 7.6 Inspection

Inspection workflows may use the Spatial Engine for sampling, nearest-surface
queries, visibility, measurement access, and accelerated region evaluation.

The Inspection module shall own metrology rules, datum systems, tolerances,
uncertainty, and acceptance classification.

TODO: Define the Inspection integration after its engineering requirements
are approved.

### 7.7 CAM

Future CAM workflows may use the Spatial Engine for geometric access,
collision candidates, visibility, stock-region lookup, and spatial
partitioning.

The CAM module shall own manufacturing process meaning, tool definitions,
toolpaths, machine constraints, and safety validation.

TODO: Define the CAM integration after a CAM architecture and safety model
exist.

### 7.8 Existing platform services

The Spatial Engine shall integrate with the existing architecture without
creating competing sources of truth:

- `ProjectManager` remains the owner of logical project objects.
- Geometry modules remain the owners of established fitting,
  transformation, quality, and reference logic.
- `SceneManager` remains responsible for rendered scene representations.
- Selection state remains coordinated through the existing project and
  visualization mechanisms.
- User-visible mutations remain compatible with commands and undo/redo.

## 8. Acceptance Criteria

The Spatial Engine shall be accepted only when all mandatory criteria below
are demonstrated on approved reference hardware and benchmark datasets.

### 8.1 Functional criteria

1. An index can be created for a supported mesh and associated unambiguously
   with its project object and geometry revision.
2. Nearest-point queries return the same valid results as a verified
   exhaustive reference calculation within the approved numerical tolerance.
3. Ray-intersection queries identify the correct nearest hit and return hits
   in deterministic distance order.
4. Region and bounding-box searches return all expected candidates without
   results outside the specified boundary semantics.
5. Stale indexes are detected after relevant geometry changes and cannot
   silently return results as current.
6. Empty results, invalid inputs, unsupported operations, cancellations, and
   internal failures are distinguishable.
7. Query results retain traceability to source project objects and geometric
   elements.
8. Logical project visibility, rendered visibility, and geometric occlusion
   remain distinct.
9. Existing fitting, quality, project, scene, and selection logic is reused
   rather than duplicated.

### 8.2 Accuracy criteria

1. Query accuracy is validated against deterministic reference
   implementations.
2. Coordinate systems and tolerances are explicit in every tested query.
3. Degenerate triangles, duplicate points, empty meshes, disconnected
   regions, and boundary cases have defined outcomes.
4. Acceleration structures do not change engineering results beyond approved
   numerical tolerances.

TODO: Establish numerical tolerance values for each query family.

### 8.3 Performance criteria

1. The engine successfully indexes and queries the approved
   multi-million-triangle benchmark meshes.
2. At least 95 percent of ordinary interactive picking and nearest-element
   queries complete within the approved interactive latency budget after the
   index is ready.
3. No spatial operation blocks the UI thread beyond the approved
   responsiveness threshold.
4. Repeated index construction, query, update, and release cycles do not
   produce unbounded retained memory.
5. Incremental updates, where supported, produce results equivalent to a
   complete rebuilt index.
6. Benchmark reports include construction time, median query time,
   95th-percentile query time, peak memory, retained memory, and dataset
   characteristics.

TODO: Approve reference hardware, benchmark meshes, construction-time
targets, memory limits, and final latency thresholds.

### 8.4 Architecture criteria

1. Client modules use public Spatial Engine contracts and do not depend on
   Octree or BVH internals.
2. Pure spatial services have no dependency on PySide6 UI classes.
3. Visualization concerns do not become authoritative engineering data.
4. The implementation has a defined integration point with project geometry
   lifecycle and revision tracking.
5. Public contracts are documented and covered by automated tests.
6. Architecture documentation distinguishes implemented capabilities from
   planned extensions.

### 8.5 Verification deliverables

Acceptance evidence shall include:

- Automated functional and accuracy tests.
- Reproducible performance benchmarks.
- Memory and index-lifecycle tests.
- Degenerate and boundary-case tests.
- Integration tests with project, scene, and selection workflows.
- Public API documentation.
- An architecture decision record for the selected index implementations.
- A report of known limitations and deferred TODO items.

No implementation shall be declared compliant solely because it exposes the
conceptual operation names in this specification.
