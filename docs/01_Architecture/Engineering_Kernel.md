# Engineering Kernel

## Overview

The Engineering Kernel is the central component of FLCAD Reverse AI.

Unlike traditional CAD kernels that manage only geometric operations, the Engineering Kernel coordinates every engineering process inside the platform.

It acts as the communication hub between all Engineering Engines.

---

# Responsibilities

The Engineering Kernel is responsible for:

- Project lifecycle
- Engineering Features
- Reference Geometry
- Command System
- Undo / Redo
- Event Dispatching
- Selection Management
- Scene Management
- Engineering Database
- Engine Communication
- Plugin Integration

---

# Core Components

## Project Manager

Responsible for:

- Opening projects
- Saving projects
- Project metadata
- Native FLG format

---

## Command Manager

Responsible for:

- Command execution
- Undo
- Redo
- Command history

---

## Engineering Feature Manager

Responsible for managing:

- Planes
- Cylinders
- Axes
- Points
- Curves
- Surfaces
- Solids

Every engineering entity inside the platform is represented as an Engineering Feature.

---

## Event Bus

Responsible for communication between all Engines.

No Engine communicates directly with another Engine.

Every request passes through the Engineering Kernel.

---

## Reference Manager

Stores every engineering reference generated during project execution.

Examples:

- Datums
- Coordinate Systems
- Axes
- Construction Geometry

---

## Plugin Manager

Allows third-party modules to integrate with the platform.

---

# Communication Model

```
Recognition Engine
        │
        ▼
Engineering Kernel
        │
        ▼
CAD Engine
```

Future communication:

```
Mesh Engine
CAD Engine
Recognition Engine
Inspection Engine
Vision AI Engine
CAM Engine

        │
        ▼

Engineering Kernel
```

---

# Design Principles

The Engineering Kernel must always be:

- Fast
- Stable
- Modular
- Testable
- Independent
- Extensible

---

# Long-Term Vision

The Engineering Kernel will become the central engineering platform capable of coordinating multiple Engineering Engines running locally or in the cloud.

It is the foundation of FLCAD Reverse AI.