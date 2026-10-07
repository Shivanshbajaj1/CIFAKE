# PipeWatch — Requirements Specification

**Predictive Utility Coordination & Road Excavation Intelligence**
**Location:** Dehradun, Uttarakhand, India
**Classification:** B.Tech AI/ML Final Year Project — Serious Infrastructure Intelligence Platform
**Document Version:** 1.1
**Date:** October 2026
**Supersedes:** v1.0 (October 2026)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Scope and Boundaries](#2-scope-and-boundaries)
3. [Stakeholders and Core Users](#3-stakeholders-and-core-users)
4. [System Architecture Overview](#4-system-architecture-overview)
5. [Data Model](#5-data-model)
6. [Functional Requirements](#6-functional-requirements)
7. [AI/ML Requirements](#7-aiml-requirements)
8. [Synthetic Data Requirements](#8-synthetic-data-requirements)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Technology Stack](#10-technology-stack)
11. [User Stories and Acceptance Criteria](#11-user-stories-and-acceptance-criteria)
12. [API Specification (Outline)](#12-api-specification-outline)
13. [Testing Requirements](#13-testing-requirements)
14. [Future Extensibility](#14-future-extensibility)
15. [Glossary](#15-glossary)

---

## 1. Project Overview

### 1.1 Problem Statement

Infrastructure projects in urban areas are frequently planned and executed in isolation by separate agencies — water boards, telecom operators, road authorities, municipal corporations, and electricity departments. This siloed approach results in a well-documented and costly failure pattern:

- A road corridor is excavated for water work and restored.
- Within months, the same corridor is excavated again for fiber optic laying.
- The freshly restored road surface is broken again, often within its warranty period.
- Each cycle incurs duplicated excavation costs, restoration costs, traffic disruption, and accelerated road deterioration.
- There is no shared institutional memory of what has happened to a road corridor, when, and by whom.

In Dehradun, as in most Tier-2 Indian cities experiencing rapid infrastructure growth, this coordination failure is acute. Multiple agencies — Jal Sansthan (water), UPCL (electricity), BSNL/private telecom operators, PWD (road), and municipal bodies — work under different governance structures with no unified project visibility.

### 1.2 What PipeWatch Is

PipeWatch is a **geospatial infrastructure intelligence platform** whose central purpose is:

**TO IDENTIFY SPATIAL AND TEMPORAL CONFLICTS BETWEEN INFRASTRUCTURE PROJECTS, PREDICT THE RISK OF REPEAT ROAD EXCAVATION, MAINTAIN A HISTORICAL MEMORY OF ROAD/UTILITY WORK, AND RECOMMEND BETTER PROJECT COORDINATION.**

It does this by:

- Maintaining a persistent, queryable memory of road corridor infrastructure events (excavations, resurfacing, utility installations).
- Detecting spatial and temporal conflicts between planned and active infrastructure projects.
- Predicting the probability of repeat excavation on a road segment within a configurable future time window using ML models.
- Assigning each road segment a transparent, formula-driven **PipeWatch Infrastructure Stress Index (PISI)** — a decision-support index, not a physical road condition measurement.
- Providing a What-If scheduling simulator to evaluate coordination strategies.
- Generating evidence-based coordination recommendations to planners.

### 1.3 What PipeWatch Is Not

This boundary is permanent and must be enforced at every design decision.

| It is NOT | Reason for explicit exclusion |
|---|---|
| A pothole or civic complaint app | Complaint aggregation is a different problem domain with different users |
| A Google Maps clone | Navigation, routing, and POI search are out of scope |
| A general 311 / citizen services portal | PipeWatch targets institutional planners, not general public |
| A chatbot or conversational AI interface | Primary interface is map + dashboard, not conversation |
| A billing or procurement system | Financial workflows are out of scope |
| A real-time GPS tracking system | Live field tracking of machinery is out of scope |
| A generic "AI city dashboard" | PipeWatch is not a multipurpose smart-city platform |

PipeWatch must remain centered on: **spatial-temporal infrastructure coordination + repeat-excavation prediction + road/project memory + what-if scheduling + coordination intelligence.**

### 1.4 Project Intent

PipeWatch is designed as a **serious B.Tech AI/ML project** that:

- Applies geospatial analysis, predictive modeling, and explainable AI to a real urban infrastructure problem.
- Uses synthetic data that is structurally realistic and clearly labeled as such.
- Can be extended using real open datasets (OpenStreetMap, municipal APIs) in a later phase.
- Serves as a foundation for potential research publication or open-source contribution.

---

## 2. Scope and Boundaries

### 2.1 Geographic Scope

- **City:** Dehradun, Uttarakhand, India.
- **Road network:** A synthetic road network modeled on Dehradun's approximate road hierarchy (arterial, collector, local streets) covering the core urban area.
- **Coordinate system:** WGS84 (EPSG:4326) for storage; projected as needed for spatial calculations.

### 2.2 Temporal Scope

- **Historical data:** Synthetic records spanning 2020–2024 (5 years of history for Road Memory and model training).
- **Validation period:** 2024 (used for rolling validation; see Section 7.6).
- **Test period:** 2025 (held-out test set; strictly no training data from this period).
- **Active/planned data:** Synthetic projects active or planned within 2025–2026.
- **Prediction horizon:** Configurable; default 180 days forward.

### 2.3 In Scope for Version 1.0

- Road segment registry
- Utility project registry (7 utility types)
- Excavation event registry
- Resurfacing event registry
- Conflict detection (spatial + temporal) with explainable rule IDs
- Project Collision Simulation (hypothetical project conflict check)
- Repeat excavation risk prediction (ML) with data-leakage prevention
- Road Memory timeline
- PipeWatch Infrastructure Stress Index (PISI)
- What-If simulator (schedule comparison only)
- Coordination recommendations (rule-based + ML-informed)
- Dashboard and heatmap
- Gantt timeline view
- Synthetic data generation pipeline (documented causal model)
- Data provenance metadata on all outputs
- REST API (FastAPI)
- Map-based frontend (Next.js + MapLibre GL JS)
- SQLite persistence (dev); PostgreSQL/PostGIS migration path

### 2.4 Out of Scope for Version 1.0

- Real-time data ingestion from external APIs
- User authentication and role-based access control (stub only)
- Mobile application
- Email/SMS notifications
- Budget or cost estimation modules
- Integration with external project management tools
- Satellite or drone imagery analysis
- Public citizen-facing interface
- Proximity-based spatial conflict detection (architecture supports it; rules not implemented)

---

## 3. Stakeholders and Core Users

### 3.1 Primary Users

| Role | Description | Primary PipeWatch Actions |
|---|---|---|
| **Municipal Infrastructure Planner** | Coordinates project approvals across agencies, ensures road works are timed appropriately | Conflict detection, coordination recommendations, Gantt view, collision simulation |
| **Utility Project Coordinator** | Manages a single utility agency's project schedule | Submit/view project details, view overlap analysis, What-If simulation, collision simulation |
| **Road Authority Officer** | Responsible for road condition, resurfacing scheduling, and warranty enforcement | Road Memory, PISI, repeat excavation risk |
| **Infrastructure Project Manager** | Oversees execution of a specific project | View conflict alerts, timeline view |
| **Urban Planner / Researcher** | Studies infrastructure coordination patterns for policy or research | Risk heatmap, historical analysis, data export, model evaluation report |

### 3.2 System Personas (for acceptance criteria)

- **Priya** — Municipal Infrastructure Planner, needs to find conflicts before approving new projects.
- **Arjun** — Jal Sansthan (water) Project Coordinator, wants to see if his project clashes with upcoming telecom work.
- **Rekha** — PWD Road Officer, needs to know if a road has been excavated before scheduling resurfacing.
- **Dr. Mehta** — Urban Planning Researcher, wants to analyze patterns, evaluate the ML model, and export data.

---

## 4. System Architecture Overview

### 4.1 High-Level Components

```
┌────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                     │
│  Next.js 14+  ·  TypeScript  ·  MapLibre GL JS             │
│  Recharts / Plotly  ·  Tailwind CSS                        │
└────────────────────┬───────────────────────────────────────┘
                     │ HTTP/REST (JSON)
┌────────────────────▼───────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  Python 3.11+  ·  Pydantic v2  ·  Uvicorn                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Road/Project│  │   Conflict   │  │   ML Prediction  │  │
│  │  Data Layer  │  │   Engine     │  │   Service        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Road Memory │  │  PISI        │  │   Recommender    │  │
│  │  Service     │  │  Calculator  │  │   Engine         │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  What-If     │  │  Data Quality│  │  Provenance      │  │
│  │  Simulator   │  │  Service     │  │  Service         │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │ SQLAlchemy ORM
┌────────────────────▼───────────────────────────────────────┐
│               DATA LAYER                                    │
│  SQLite (dev)  →  PostgreSQL/PostGIS (prod migration path) │
│  GeoJSON files for road network (static seed data)         │
│  Parquet/CSV files for ML feature store                    │
└────────────────────────────────────────────────────────────┘
```

### 4.2 ML Pipeline (Separate Module)

```
┌──────────────────────────────────────────────────────┐
│                  ML PIPELINE                          │
│  scripts/generate_synthetic_data.py  (causal model)  │
│  scripts/build_feature_store.py      (leakage-safe)  │
│  scripts/train_model.py                              │
│  scripts/evaluate_model.py           (backtesting)   │
│  models/  (serialized artifacts: .joblib)            │
│  ml/explainer.py  (SHAP / feature importance)        │
│  ml/evaluation/  (eval reports per model version)    │
└──────────────────────────────────────────────────────┘
```

### 4.3 Separation of Concerns

| Layer | Responsibility |
|---|---|
| API Router | HTTP routing, request validation, response serialization only |
| Service Layer | Business logic, conflict rules, scoring formulas |
| Repository Layer | All database access; no SQL in service layer |
| ML Module | Feature engineering, model training, prediction; no HTTP code |
| Synthetic Data Scripts | Standalone scripts; no dependency on the API at runtime |
| Provenance Service | Attaches provenance metadata to API outputs; no business logic |

---

## 5. Data Model

### 5.1 Core Entities

#### 5.1.1 RoadSegment

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | string | Human-readable label (e.g., "Rajpur Road – Segment 3") |
| `road_class` | enum | `ARTERIAL`, `COLLECTOR`, `LOCAL` |
| `geometry` | LineString (GeoJSON) | Spatial geometry of the segment |
| `length_meters` | float | Computed from geometry |
| `ward` | string | Administrative ward in Dehradun |
| `zone` | string | Planning zone (e.g., "Central", "Rajpur", "ISBT") |
| `is_synthetic` | boolean | Always `true` in v1.0 |
| `created_at` | datetime | Record creation timestamp |

#### 5.1.2 UtilityProject

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | string | Project name |
| `utility_type` | enum | `WATER`, `SEWERAGE`, `DRAINAGE`, `ELECTRICITY`, `TELECOM`, `GAS`, `OTHER` |
| `agency` | string | Agency name (e.g., "Jal Sansthan", "UPCL") |
| `status` | enum | `PLANNED`, `ACTIVE`, `COMPLETED`, `CANCELLED`, `ON_HOLD` |
| `planned_start_date` | date | Planned project start |
| `planned_end_date` | date | Planned project end |
| `actual_start_date` | date \| null | Actual start (null if not started) |
| `actual_end_date` | date \| null | Actual end (null if not completed) |
| `description` | string | Free-text description |
| `affected_road_segments` | [UUID] | List of road segment IDs affected |
| `requires_excavation` | boolean | Whether the project involves road cutting |
| `requires_resurfacing` | boolean | Whether road restoration is planned |
| `is_synthetic` | boolean | Data origin flag |
| `created_at` | datetime | Record creation |
| `updated_at` | datetime | Last update |

#### 5.1.3 ExcavationEvent

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `road_segment_id` | UUID | FK → RoadSegment |
| `project_id` | UUID | FK → UtilityProject |
| `utility_type` | enum | Utility type involved |
| `start_date` | date | Excavation start |
| `end_date` | date \| null | Excavation end (null if ongoing) |
| `excavation_depth_cm` | float \| null | Depth in cm (optional) |
| `trench_length_meters` | float \| null | Length of trench (optional) |
| `notes` | string | Free-text notes |
| `is_synthetic` | boolean | Data origin flag |
| `data_source` | string | Source identifier for traceability |

#### 5.1.4 ResurfacingEvent

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `road_segment_id` | UUID | FK → RoadSegment |
| `project_id` | UUID \| null | FK → UtilityProject (if associated) |
| `start_date` | date | Resurfacing start |
| `end_date` | date | Resurfacing completion |
| `resurfacing_type` | enum | `PATCH`, `FULL`, `OVERLAY` |
| `quality_grade` | enum \| null | `A`, `B`, `C` (if recorded) |
| `warranty_months` | int \| null | Restoration warranty period |
| `contractor` | string \| null | Contractor name |
| `is_synthetic` | boolean | Data origin flag |

#### 5.1.5 ConflictRecord

A detected conflict between two projects on the same road segment, with a structured explanation.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `project_a_id` | UUID | FK → UtilityProject |
| `project_b_id` | UUID | FK → UtilityProject |
| `road_segment_id` | UUID | FK → RoadSegment (conflict location) |
| `conflict_type` | enum | `SPATIAL_OVERLAP`, `TEMPORAL_OVERLAP`, `SPATIAL_TEMPORAL` |
| `severity` | enum | `HIGH`, `MEDIUM`, `LOW` |
| `rule_id` | string | Identifier of the rule that produced this conflict (e.g., `SPATIAL_TEMPORAL_EXCAVATION_01`) |
| `spatial_reason` | string | Plain-language description of the spatial component |
| `temporal_reason` | string \| null | Plain-language description of the temporal component |
| `excavation_involvement` | string | Description of which projects involve excavation |
| `overlap_days` | int \| null | Number of overlapping days (temporal component) |
| `spatial_overlap_meters` | float \| null | Spatial overlap extent |
| `affected_corridor` | string \| null | Human-readable corridor description |
| `detection_method` | enum | `RULE_BASED`, `ML_ASSISTED` |
| `detected_at` | datetime | When the conflict was detected |
| `status` | enum | `OPEN`, `ACKNOWLEDGED`, `RESOLVED` |
| `resolution_note` | string \| null | How it was resolved |

#### 5.1.6 RiskPrediction

An ML-generated prediction of repeat excavation risk, stored as an immutable snapshot.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `road_segment_id` | UUID | FK → RoadSegment |
| `prediction_timestamp` | datetime | Exact moment the prediction was generated (ISO 8601) |
| `feature_snapshot_timestamp` | datetime | The point-in-time at which features were computed; all features reflect the world at this moment |
| `prediction_horizon_days` | int | Number of days forward the prediction covers (default: 180) |
| `probability` | float [0–1] | Predicted probability of at least one new excavation in the horizon |
| `risk_category` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `model_version` | string | Model artifact version identifier |
| `model_type` | string | e.g., `RandomForestClassifier`, `LogisticRegression`, `RuleBaseline` |
| `top_features` | JSON | Top 5 contributing features: name, value, direction, timestamp_basis |
| `feature_snapshot` | JSON | Complete feature vector used for this prediction (for reproducibility) |
| `is_synthetic_input` | boolean | Whether input features were derived from synthetic data |
| `provenance` | JSON | See Section 5.3 — provenance metadata |

**Immutability rule:** A `RiskPrediction` record must never be mutated after creation. Subsequent predictions create new records. The `feature_snapshot` field allows any prior prediction to be fully reproduced from the stored feature vector alone, regardless of later edits to historical data.

#### 5.1.7 InfrastructureStressIndex

Formerly "RoadStressScore". Renamed to PipeWatch Infrastructure Stress Index (PISI). Internal code may use `InfrastructureStressIndex`; user-facing labels must use "PipeWatch Infrastructure Stress Index."

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `road_segment_id` | UUID | FK → RoadSegment |
| `calculated_at` | datetime | Calculation timestamp |
| `index_value` | float [0–100] | Overall PISI value |
| `component_excavation_count` | float | Sub-score: excavation frequency |
| `component_utility_diversity` | float | Sub-score: number of distinct utility types |
| `component_recency` | float | Sub-score: recency of last excavation |
| `component_resurfacing_gap` | float | Sub-score: time since last resurfacing relative to warranty |
| `component_conflict_count` | float | Sub-score: number of detected conflicts |
| `formula_version` | string | Formula version for auditability |
| `index_category` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |

#### 5.1.8 CoordinationRecommendation

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `generated_at` | datetime | Generation timestamp |
| `affected_projects` | [UUID] | Project IDs this recommendation addresses |
| `affected_segment_ids` | [UUID] | Road segments involved |
| `recommendation_type` | enum | `MERGE_WINDOW`, `SEQUENCE_REORDER`, `DEFER_PROJECT`, `INSPECT_BEFORE_RESURFACE` |
| `priority` | enum | `HIGH`, `MEDIUM`, `LOW` |
| `title` | string | Short title (≤ 120 chars) |
| `rationale` | string | Detailed plain-language explanation |
| `evidence` | JSON | Supporting facts with provenance (conflict IDs, event dates, prediction IDs) |
| `estimated_avoided_excavations` | int \| null | Deterministic count only; never inferred from ML |
| `status` | enum | `PENDING`, `ACCEPTED`, `REJECTED`, `EXPIRED` |
| `provenance` | JSON | See Section 5.3 |

### 5.2 Data Origin Labeling

Every entity that can contain real-world data must carry an `is_synthetic` flag. The API must propagate this flag to all responses. The frontend must visually distinguish synthetic data from any future real data.

### 5.3 Data Provenance Metadata

Every important API output (predictions, conflicts, PISI scores, recommendations, simulation results) must include a `provenance` JSON object with the following fields:

| Field | Type | Description |
|---|---|---|
| `evidence_sources` | [string] | List of provenance categories: `SYNTHETIC_HISTORICAL_EVENT`, `SYNTHETIC_PROJECT`, `DETERMINISTIC_CALCULATION`, `ML_PREDICTION`, `SIMULATION` |
| `calculation_method` | string | The rule ID, formula version, or model version that produced this output |
| `input_data_timestamps` | JSON | For ML predictions: the `feature_snapshot_timestamp`. For PISI: the `calculated_at`. For conflicts: `detected_at`. |
| `is_synthetic` | boolean | Whether all inputs were synthetic |

This provenance object is returned in-line with all relevant API responses. It is not an optional field.

---

## 6. Functional Requirements

### 6.1 Road Network Visualization

**FR-MAP-01:** The system shall display the Dehradun road network on an interactive map using MapLibre GL JS.

**FR-MAP-02:** Road segments shall be rendered with visual differentiation by road class (ARTERIAL = thicker/brighter, COLLECTOR = medium, LOCAL = thinner).

**FR-MAP-03:** Road segments shall be color-coded dynamically based on a selected overlay mode:
- Default: Road class color scheme
- Risk overlay: colored by current `risk_category` from the latest `RiskPrediction`
- PISI overlay: colored by `InfrastructureStressIndex.index_category` using a gradient scale
- Conflict overlay: colored by presence of `OPEN` conflict records
- Excavation frequency overlay: colored by `excavation_count_24m`

**FR-MAP-04:** Clicking a road segment shall open a detail panel showing:
- Segment name, road class, ward, zone
- Current PISI value with component breakdown and the disclaimer "This is a derived index, not a physical measurement of road condition."
- Latest risk prediction with probability, category, top features, and "ML Prediction — Not a confirmed event" label
- Count of excavation events (all time, last 2 years)
- Count of resurfacing events
- Link to Road Memory timeline for this segment
- Active/planned projects on this segment

**FR-MAP-05:** The map shall support pan, zoom (mouse wheel + pinch), and segment selection.

**FR-MAP-06:** The map shall display a visible legend for whichever overlay is active.

**FR-MAP-07:** The map shall display a banner indicating "DEMO DATA — Synthetic Infrastructure Records" at all times in v1.0.

**FR-MAP-08:** The map shall have filter controls to show/hide projects by utility type, by status, and by date range.

---

### 6.2 Utility Project Management

**FR-PROJ-01:** The system shall maintain a registry of utility projects with all fields defined in Section 5.1.2.

**FR-PROJ-02:** The system shall support creating, reading, updating, and soft-deleting utility projects via the API.

**FR-PROJ-03:** The system shall validate that `planned_end_date` is after `planned_start_date`.

**FR-PROJ-04:** The system shall validate that `actual_end_date`, if provided, is after `actual_start_date`.

**FR-PROJ-05:** The system shall allow associating a project with one or more road segments.

**FR-PROJ-06:** A project list view shall support filtering by: utility type, status, date range, road segment, and agency name.

**FR-PROJ-07:** When a project is created or updated, the conflict detection engine shall be triggered to recompute conflicts for the affected road segments.

**FR-PROJ-08:** Projects with `requires_excavation = true` shall be highlighted differently in the project list.

---

### 6.3 Historical Excavation and Resurfacing Records

**FR-HIST-01:** The system shall maintain a registry of excavation events linked to road segments and projects.

**FR-HIST-02:** The system shall maintain a registry of resurfacing events linked to road segments.

**FR-HIST-03:** Both event types shall be queryable by road segment, date range, utility type, and project.

**FR-HIST-04:** The system shall calculate, for any road segment:
- Total excavation count (all time)
- Excavation count in last 12 months
- Excavation count in last 24 months
- Distinct utility types that have excavated this segment
- Days since last excavation
- Days since last resurfacing
- Whether any resurfacing warranty is currently active

**FR-HIST-05:** The system shall flag road segments where excavation occurred within the warranty period of a preceding resurfacing event (warranty breach indicator).

**FR-HIST-06:** All historical records shall expose their `is_synthetic` flag and `data_source` field in API responses.

---

### 6.4 Conflict Radar — Spatial and Temporal Conflict Detection

#### 6.4.1 Detection Rules (v1.0)

**FR-CONF-01:** The system shall detect conflicts between any two `UtilityProject` records that share one or more road segments.

**FR-CONF-02 (Rule SPATIAL_ONLY_03):** A **spatial conflict** shall be recorded when two projects share at least one common road segment and their date ranges do NOT overlap within the temporal buffer window.

**FR-CONF-03 (Rule TEMPORAL_PROXIMITY_04):** A **temporal conflict** shall be recorded when two projects on the same road segment have overlapping or near-overlapping date ranges within the configurable buffer window (default: 30 days), but this condition alone is insufficient if neither project requires excavation.

**FR-CONF-04 (Rule SPATIAL_TEMPORAL_EXCAVATION_01):** A **spatial-temporal conflict** with severity HIGH shall be recorded when: (a) two projects share the same road segment, (b) their date ranges overlap or fall within the temporal buffer window, AND (c) both projects require excavation. This is the highest-priority conflict rule.

**FR-CONF-05 (Rule SPATIAL_TEMPORAL_MIXED_02):** A **spatial-temporal conflict** with severity MEDIUM shall be recorded when conditions (a) and (b) from FR-CONF-04 are met but only one project requires excavation.

**FR-CONF-06:** Conflict severity rules summary:

| Rule ID | Condition | Severity |
|---|---|---|
| `SPATIAL_TEMPORAL_EXCAVATION_01` | Same segment + temporal overlap + both excavate | HIGH |
| `SPATIAL_TEMPORAL_MIXED_02` | Same segment + temporal overlap + one excavates | MEDIUM |
| `SPATIAL_ONLY_03` | Same segment + no temporal overlap within 30d | LOW |
| `TEMPORAL_PROXIMITY_04` | Adjacent/same segment + within 30d, no excavation | LOW |

**FR-CONF-07:** Every conflict record shall carry: `rule_id`, `spatial_reason`, `temporal_reason`, `excavation_involvement`, `overlap_days`, `affected_corridor`, and `detection_method`. These are mandatory, non-nullable fields (where applicable to the rule type).

**FR-CONF-08:** Example of the required conflict explanation format:

```
Severity: HIGH
Rule: SPATIAL_TEMPORAL_EXCAVATION_01
Spatial reason: Project A (Water Main, Jal Sansthan) and Project B (Fiber Laying, BSNL)
                both affect Segment 102 (Rajpur Road – Segment 3).
Temporal reason: Project A runs 1 Jan–20 Jan; Project B runs 15 Jan–10 Feb.
                 Excavation windows overlap by 5 days (15–20 Jan).
Excavation: Both projects require excavation.
Affected corridor: Rajpur Road – Segment 3 (zone: Rajpur, ARTERIAL)
```

#### 6.4.2 Detection Engine Behavior

**FR-CONF-09:** The conflict detection engine shall be runnable on demand via an API endpoint and shall run automatically when projects are created or updated.

**FR-CONF-10:** No duplicate conflict records shall be created if the engine is re-run without data changes. The engine shall be idempotent.

**FR-CONF-11:** The Conflict Radar view shall display all `OPEN` conflicts in a table, sortable by severity, date, segment, and utility type.

**FR-CONF-12:** The Conflict Radar shall display summary counts: total open conflicts, by severity, by utility type.

**FR-CONF-13:** A conflict may be manually acknowledged or marked resolved, with a required resolution note (minimum 10 characters).

#### 6.4.3 Conflict Engine Extensibility Architecture

**FR-CONF-14:** The conflict engine shall be implemented as a **registered rule pipeline**. Each rule is a discrete, independently testable class or function that:
- Accepts two `UtilityProject` records and their associated segment data
- Returns a `ConflictRecord | None`
- Has a unique `rule_id` string

**FR-CONF-15:** The architecture must support future addition of the following rule types **without modifying existing rules**:

| Future Rule Type | Description |
|---|---|
| `EXACT_SEGMENT` | Exact shared segment (already implemented in v1.0) |
| `INTERSECTING_GEOMETRY` | Project geometries geometrically intersect |
| `PROXIMITY_BUFFER` | Project geometries are within a configurable distance (meters) |
| `SAME_CORRIDOR` | Projects share a named road corridor regardless of exact segment split |
| `SHARED_HIERARCHY` | Projects on roads of the same hierarchy class in the same zone |

These future rules are **not implemented in v1.0**. The architecture must permit their addition.

---

### 6.5 Repeat Excavation Risk Prediction

#### 6.5.1 Prediction Target Definition

**FR-RISK-01:** The ML prediction target is: **whether a given road segment will experience at least one NEW excavation event that starts after the `feature_snapshot_timestamp` and within the next `prediction_horizon_days` (default: 180).**

This definition is precise and must be enforced at every point in the pipeline:
- Feature computation must use only data with timestamps strictly before the `feature_snapshot_timestamp`.
- The target label must use only events with `start_date > feature_snapshot_timestamp`.
- No feature may use information from the prediction window.

#### 6.5.2 Data Leakage Prevention

**FR-RISK-02 (Leakage Rule L-01):** For every training example, the following constraint must hold:

```
FEATURE_TIMESTAMP < PREDICTION_TIMESTAMP ≤ TARGET_WINDOW_START
```

Where:
- `FEATURE_TIMESTAMP` = the latest event timestamp used to compute any feature
- `PREDICTION_TIMESTAMP` = the `feature_snapshot_timestamp` for that example
- `TARGET_WINDOW_START` = `feature_snapshot_timestamp` (target events start strictly after this)

**FR-RISK-03 (Leakage Rule L-02):** The following features from v1.0 require explicit timestamp-safe definitions:

| Feature | Permitted Definition | Prohibited Definition |
|---|---|---|
| `excavation_count_24m` | Count of excavations with `start_date` in [snapshot_ts − 24m, snapshot_ts) | Includes events after snapshot_ts |
| `days_since_last_excavation` | Days between snapshot_ts and the most recent excavation with `start_date < snapshot_ts` | Uses future events |
| `active_project_count` | Count of projects where `planned_start_date ≤ snapshot_ts ≤ planned_end_date` AND project was created before snapshot_ts | Includes projects announced after snapshot_ts |
| `planned_project_count` | **REMOVED from default feature set.** This feature is inherently forward-looking and cannot be used without a documented justification of what planning data would realistically be available. If retained as an optional feature, it must be placed in a separate "planning-aware" feature group with a leakage warning. | Any count of projects planned to start after snapshot_ts |
| `historical_conflict_count` | Count of conflict records with `detected_at < snapshot_ts` | Includes conflicts detected after snapshot_ts |

**FR-RISK-04:** The feature engineering pipeline (`scripts/build_feature_store.py`) must document, in code comments, the exact timestamp semantics for every feature. The format is:

```python
# Feature: excavation_count_24m
# Timestamp basis: snapshot_ts
# Includes: ExcavationEvent.start_date in [snapshot_ts - 730 days, snapshot_ts)
# Excludes: Any event with start_date >= snapshot_ts
```

**FR-RISK-05:** The feature store build script must accept a `--snapshot-date` argument. When constructing training examples, the script iterates over a set of snapshot dates; for each date, it computes features using only data before that date and checks the target using only events after it.

#### 6.5.3 Revised Feature Set

The following features are approved for the default feature set. All are measured at `feature_snapshot_timestamp` (snapshot_ts):

| Feature | Timestamp Basis | Description |
|---|---|---|
| `excavation_count_all_time` | < snapshot_ts | Total excavations ever recorded before snapshot |
| `excavation_count_24m` | [snapshot_ts − 24m, snapshot_ts) | Excavations in prior 24 months |
| `excavation_count_12m` | [snapshot_ts − 12m, snapshot_ts) | Excavations in prior 12 months |
| `days_since_last_excavation` | < snapshot_ts | Days since most recent excavation before snapshot |
| `days_since_last_resurfacing` | < snapshot_ts | Days since most recent resurfacing before snapshot |
| `distinct_utility_count` | < snapshot_ts | Count of distinct utility types that have excavated |
| `active_project_count` | active at snapshot_ts | Projects whose planned window contains snapshot_ts, announced before it |
| `historical_conflict_count` | detected_at < snapshot_ts | Conflict records detected before snapshot |
| `road_class_encoded` | static | ARTERIAL=2, COLLECTOR=1, LOCAL=0 |
| `segment_length_normalized` | static | Normalized segment length |
| `project_density_per_km` | [snapshot_ts − 24m, snapshot_ts) | Projects per km in prior 24 months |
| `resurfacing_within_warranty` | at snapshot_ts | Boolean: active warranty at snapshot time |

**Removed from default set:** `planned_project_count` (leakage risk; see FR-RISK-03).

#### 6.5.4 Prediction Behavior

**FR-RISK-06:** Predictions shall be stored as immutable `RiskPrediction` records (Section 5.1.6). Each run creates a new record; existing records are never modified.

**FR-RISK-07:** The ML model pipeline shall proceed in the following documented order:
1. **Rule Baseline:** `excavation_count_24m ≥ 2` → predict 1 (high risk); else 0. No probability, only binary output.
2. **Logistic Regression:** Interpretable; produces calibrated probabilities.
3. **Random Forest Classifier:** Improved accuracy; provides feature importances.
4. **(Optional) Gradient Boosting / XGBoost:** Only if justified by ablation results (see Section 7.5).

**FR-RISK-08:** Risk categories:

| Probability | Category |
|---|---|
| ≥ 0.75 | CRITICAL |
| 0.50 – 0.74 | HIGH |
| 0.25 – 0.49 | MEDIUM |
| < 0.25 | LOW |

**FR-RISK-09:** Every `RiskPrediction` API response shall include:
- `probability` (float, 4 decimal places)
- `risk_category` (enum)
- `prediction_timestamp` (ISO 8601)
- `feature_snapshot_timestamp` (ISO 8601)
- `prediction_horizon_days` (int)
- `model_version` (string)
- `model_type` (string)
- `top_features` (list of top 5: name, value, direction of influence, timestamp_basis)
- `feature_snapshot` (complete feature vector stored for reproducibility)
- `is_synthetic_input` (boolean)
- `provenance` (Section 5.3)

**FR-RISK-10:** The system shall never present a prediction as a confirmed fact. The UI must always label prediction outputs: **"ML Prediction — Not a confirmed event."**

**FR-RISK-11:** If the ML model is unavailable, the system falls back to the rule baseline and labels the result: **"Rule-Based Estimate — Not an ML Prediction."**

**FR-RISK-12:** The following two endpoints serve prediction read and write operations:
- `GET /api/v1/ml/predict/{segment_id}` — returns the latest stored `RiskPrediction` for the segment; does not create a new record.
- `POST /api/v1/ml/predict/{segment_id}/refresh` — triggers a fresh prediction, creates a new immutable `RiskPrediction` record, and returns it.

**FR-RISK-13:** `/api/v1/ml/batch-predict` refreshes predictions for all segments.

---

### 6.6 Road Memory Timeline

**FR-MEM-01:** Each road segment shall have a Road Memory — a chronological record of all infrastructure events on that segment.

**FR-MEM-02:** The Road Memory shall include: excavation events, resurfacing events, and project milestones (start/end dates of associated projects).

**FR-MEM-03:** The Road Memory shall be displayed as an interactive vertical timeline, ordered chronologically (oldest first).

**FR-MEM-04:** Each event shall display: event type (icon + label), date or date range, project name, utility type, agency, `is_synthetic` label, provenance category, and any notes.

**FR-MEM-05:** The Road Memory shall support filtering by event type and date range.

**FR-MEM-06:** The Road Memory shall visually highlight patterns of concern:
- Three or more excavations within a 24-month window → "Frequent Excavation" warning
- Excavation within warranty period of preceding resurfacing → "Warranty Breach" indicator
- Gap of less than 90 days between resurfacing and next excavation → "Premature Excavation" flag

**FR-MEM-07:** The Road Memory for a segment shall be available as a JSON export via the API, including provenance fields for every event.

---

### 6.7 PipeWatch Infrastructure Stress Index (PISI)

**FR-PISI-01:** The system shall compute a **PipeWatch Infrastructure Stress Index (PISI)** for every road segment. PISI is a **deterministic decision-support index derived from infrastructure disruption history.** It is not a physical measurement of road condition and has not been empirically validated against actual road damage data. This disclaimer must appear in the UI and documentation.

**FR-PISI-02:** The formula shall be versioned, documented, and deterministic. The v1.0 formula is:

```
PISI = w1 × C(excavation_count_norm)
     + w2 × C(utility_diversity_norm)
     + w3 × C(recency_penalty)
     + w4 × C(resurfacing_gap_penalty)
     + w5 × C(conflict_count_norm)
```

Where:
- `excavation_count_norm`   = min(excavation_count_24m / 5.0, 1.0) × 100
- `utility_diversity_norm`  = min(distinct_utility_count / 4.0, 1.0) × 100
- `recency_penalty`         = max(0, 100 − (days_since_last_excavation / 2.0))
- `resurfacing_gap_penalty` = 100 if warranty_breach else (100 − min(days_since_last_resurfacing / 365.0, 1.0) × 100)
- `conflict_count_norm`     = min(historical_conflict_count / 3.0, 1.0) × 100
- Weights: w1=0.30, w2=0.20, w3=0.20, w4=0.15, w5=0.15 (must sum to 1.0)

**FR-PISI-03:** PISI categories:

| PISI Value | Category | Color |
|---|---|---|
| 75 – 100 | CRITICAL | Red |
| 50 – 74 | HIGH | Orange |
| 25 – 49 | MEDIUM | Yellow |
| 0 – 24 | LOW | Green |

**FR-PISI-04:** The system shall store each PISI calculation with all component sub-scores, formula version, and `calculated_at` timestamp.

**FR-PISI-05:** The PISI shall be displayed in:
- The road segment detail panel (with component bar chart)
- The map overlay
- The dashboard (top 10 highest-PISI segments)

**FR-PISI-06:** The component breakdown must always be visible alongside the index value. The system must never display just a single number without its components.

**FR-PISI-07:** A "How is this calculated?" expandable section must appear in the UI wherever PISI is displayed. It must contain:
- The formula in plain text
- The weight of each component
- The disclaimer: **"This is a derived index, not a physical measurement of road condition."**

---

### 6.8 What-If Infrastructure Scheduling Simulator

**FR-SIM-01:** The What-If Simulator shall allow a user to define two named scheduling scenarios for a set of projects on a given road corridor.

**FR-SIM-02:** A **scenario** is a named ordered sequence of project events (utility type, start date, end date, requires_excavation, requires_resurfacing) on a selected road segment.

**FR-SIM-03:** The simulator shall accept two scenarios and compute comparison metrics for each.

**FR-SIM-04:** Metrics computed per scenario:

| Metric | Description |
|---|---|
| `total_excavation_count` | Total excavation events in the scenario |
| `repeat_excavation_count` | Excavations occurring within 180 days of a prior excavation on the same segment |
| `conflict_count` | Detected temporal/spatial conflicts within the scenario |
| `total_road_disturbance_days` | Sum of durations of all excavation-involving events |
| `coordination_opportunities` | Project pairs that could be merged into one excavation window |
| `resurfacing_count` | Resurfacing events in the scenario |
| `estimated_avoided_excavations` | Deterministic count: how many repeat excavations Scenario B avoids vs Scenario A |

**FR-SIM-05:** The simulator shall not estimate monetary savings or costs.

**FR-SIM-06:** The result shall include a narrative explanation generated from the metric data, not hard-coded.

**FR-SIM-07:** Simulation results shall be labeled: **"Simulation — Not a Committed Schedule."**

**FR-SIM-08:** Simulation results shall carry `provenance.evidence_sources = ["SIMULATION"]`.

---

### 6.9 Project Collision Simulation

**FR-COLL-01:** A planner shall be able to submit a **hypothetical new project** (not yet saved to the database) and ask: "What existing projects would this collide with?"

**FR-COLL-02:** The collision simulation shall use the same conflict detection engine as Section 6.4, applying the same rule pipeline, but operating on the hypothetical project without persisting any records.

**FR-COLL-03:** The response shall include for each detected collision:
- Conflicting project (name, utility type, agency, dates, status)
- Affected road segment(s)
- Overlap dates (if temporal)
- Conflict severity per rule
- Rule ID and explanation (same format as FR-CONF-08)
- Likely repeat-excavation implication (derived from current PISI and risk prediction for each affected segment)

**FR-COLL-04:** The result shall be labeled: **"Simulation — Not a Confirmed Conflict. The hypothetical project has not been saved."**

**FR-COLL-05:** The collision simulation shall be accessible from:
- The Conflict Radar view ("Check hypothetical project")
- The project creation form ("Check before saving")

**FR-COLL-06:** The collision simulation shall not create any database records. It is a pure read + computation operation.

---

### 6.10 Coordination Recommendation Engine

**FR-REC-01:** The recommendation engine shall generate `CoordinationRecommendation` records based on detected conflicts, Road Memory patterns, ML risk predictions, and What-If simulation outcomes.

**FR-REC-02:** Supported recommendation types:

| Type | Trigger Condition |
|---|---|
| `MERGE_WINDOW` | Two projects on same segment within 30 days → merge into one excavation window |
| `SEQUENCE_REORDER` | Resurfacing planned before all utility work complete → complete utilities first |
| `DEFER_PROJECT` | Active warranty + new project planned → suggest deferral or re-route |
| `INSPECT_BEFORE_RESURFACE` | 2+ excavations in 12 months → inspect before resurfacing commitment |

**FR-REC-03:** Each recommendation must include: `title`, `rationale`, `evidence` (with provenance), `recommendation_type`, `priority`.

**FR-REC-04:** Every recommendation carries the label: **"Advisory — Requires Planner Review."**

**FR-REC-05:** A planner may ACCEPT or REJECT with a required note. Rejected records are retained for audit.

**FR-REC-06:** The dashboard recommendations panel shows PENDING recommendations grouped by priority (HIGH first).

---

### 6.11 Infrastructure Conflict Dashboard

**FR-DASH-01:** The dashboard shall provide a high-level overview of the coordination situation across all road segments.

**FR-DASH-02:** Summary widgets:

| Widget | Description |
|---|---|
| Total Open Conflicts | Count, colored by severity breakdown |
| Active Projects | Count of ACTIVE projects |
| High-Risk Segments | Count of segments with CRITICAL or HIGH risk_category |
| Top 10 High-PISI Segments | Highest PipeWatch Infrastructure Stress Index segments |
| Recent Excavations | Last 30 days |
| Pending Recommendations | Count of PENDING recommendations |
| Data Freshness | Last synthetic data regeneration timestamp |

**FR-DASH-03:** Conflict Summary table: all OPEN conflicts sorted by severity with project names, segment, dates, severity, and rule ID.

**FR-DASH-04:** Charts: excavation frequency by utility type (bar), conflicts per month last 12 months (line), risk distribution (donut: CRITICAL/HIGH/MEDIUM/LOW).

**FR-DASH-05:** "Refresh All" button triggers data refresh for all widgets.

**FR-DASH-06:** Persistent "SYNTHETIC DATA" banner.

---

### 6.12 Risk Heatmap

**FR-HEAT-01:** The risk heatmap colors road segments by their current `risk_category` from the latest `RiskPrediction`.

**FR-HEAT-02:** Toggle between: risk heatmap / PISI heatmap / excavation frequency / conflict density.

**FR-HEAT-03:** Color legend with thresholds visible at all times.

**FR-HEAT-04:** Clicking a segment opens the detail panel.

**FR-HEAT-05:** Prediction horizon prominently displayed (e.g., "Risk predictions for next 180 days").

**FR-HEAT-06:** Persistent label: **"ML Predictions — Not Confirmed Events."**

---

### 6.13 Project Timeline Visualization (Gantt)

**FR-GANTT-01:** Gantt chart showing all infrastructure projects on a time axis.

**FR-GANTT-02:** Each row: project name, agency, utility type (color-coded), planned date range, actual date range overlay.

**FR-GANTT-03:** Conflicts between projects on the same segment visually marked (e.g., red border or hatched overlay) with the rule ID shown on hover.

**FR-GANTT-04:** Supports zoom to month/quarter/year; filters by utility type, segment, status, agency; toggle planned vs actual.

**FR-GANTT-05:** Clicking a project bar opens project detail panel.

---

### 6.14 Data Quality Indicators

**FR-DQ-01:** Track and expose data quality dimensions: completeness, consistency, freshness.

**FR-DQ-02:** Completeness: projects missing `actual_start_date`/`actual_end_date` when expected; excavation events missing `trench_length_meters`; segments with no events.

**FR-DQ-03:** Consistency: `actual_end_date < actual_start_date`; excavation events with no project; segments with no geometry.

**FR-DQ-04:** Data Quality panel: overall score (0–100), per-entity breakdown, flagged records.

**FR-DQ-05:** Data quality widget on dashboard.

**FR-DQ-06:** Synthetic data pipeline must pass its own data quality checks before loading.


---

## 7. AI/ML Requirements

### 7.1 Epistemic Honesty Principle

The system must maintain a strict distinction between four categories of information:

| Category | Definition | UI Treatment |
|---|---|---|
| **OBSERVED DATA** | Recorded historical events (excavations, resurfacing, project timelines) | Displayed as fact; labeled "Recorded" |
| **DETERMINISTIC RULES** | Conflict detection, PISI formula, coordination rules | Labeled with rule reference (e.g., `SPATIAL_TEMPORAL_EXCAVATION_01`, `PISI-v1.0`) |
| **ML PREDICTIONS** | Output of statistical models (risk probability, risk category) | Always labeled "ML Prediction"; probability shown; confidence qualifications required |
| **RECOMMENDATIONS** | System-generated advisory suggestions | Always labeled "Advisory"; rationale shown; requires planner decision |

**No ML prediction shall ever be presented as a confirmed event, an observation, or an established fact.**

### 7.2 Prediction Target and Leakage Contract

This section summarizes and formalizes the contract defined in FR-RISK-01 through FR-RISK-05.

**ML-CONTRACT-01:** The prediction task is binary classification: given a road segment's state at `feature_snapshot_timestamp`, predict whether at least one new `ExcavationEvent` with `start_date > feature_snapshot_timestamp` and `start_date ≤ feature_snapshot_timestamp + prediction_horizon_days` will be recorded.

**ML-CONTRACT-02:** The leakage constraint is: no feature value used in training or inference may be derived from events with timestamps ≥ `feature_snapshot_timestamp`.

**ML-CONTRACT-03:** The feature store builder must enforce this constraint programmatically, not only by convention. The build script must raise an error or log a warning if any computed feature value is traced to a data row with timestamp ≥ snapshot.

**ML-CONTRACT-04:** The `planned_project_count` feature is excluded from the default feature set due to inherent forward-looking information. If it is included in an ablation experiment (Group B+), the experiment report must document the leakage risk and justify its inclusion as "planning-available information."

### 7.3 Model Training Requirements

**ML-TRAIN-01:** Training, validation, and test sets shall use a **time-based split**, not a random split. See Section 7.6 for the backtesting protocol.

**ML-TRAIN-02:** All models shall be trained with a configurable random seed (passed as `--seed` argument).

**ML-TRAIN-03:** Feature scaling shall be applied (StandardScaler or MinMaxScaler) before logistic regression. Tree-based models shall use raw features.

**ML-TRAIN-04:** Class imbalance shall be handled explicitly (`class_weight='balanced'` or SMOTE) and the chosen approach documented.

**ML-TRAIN-05:** Hyperparameter tuning shall use time-series-aware cross-validation (e.g., `TimeSeriesSplit`) and all tuned parameters shall be logged in the evaluation report.

### 7.4 Model Evaluation Requirements

**ML-EVAL-01:** Every trained model shall be evaluated on the held-out test period with: Accuracy, Precision, Recall, F1-Score, ROC-AUC.

**ML-EVAL-02:** A calibration curve shall be generated to verify that predicted probabilities are well-calibrated (not just accurate in rank).

**ML-EVAL-03:** Feature importances (Random Forest) or coefficients (Logistic Regression) shall be logged and stored per model version.

**ML-EVAL-04:** Evaluation results shall be saved as `ml/evaluation/eval_report_{model_version}.json`.

**ML-EVAL-05:** The evaluation report for every model shall include:
- Metrics against the rule baseline (delta ROC-AUC, delta F1)
- A plain-language interpretation: does the improvement justify the added complexity?
- Documented limitations (e.g., "trained on synthetic data; relationships are simulated assumptions")

**ML-EVAL-06:** No fixed metric threshold (e.g., "ROC-AUC ≥ 0.65") shall be used as a pass/fail gate. Instead, the requirement is:
- Report the metric
- Compare against the rule baseline
- Explain whether the improvement is meaningful given the synthetic data generating process
- Document limitations

This approach is correct because a hard threshold cannot be justified without reference to the real-world data distribution, which is unknown for synthetic data.

### 7.5 Feature Ablation Experiment

**ML-ABLATION-01:** The model evaluation pipeline shall include a **feature ablation experiment** comparing at minimum three feature groups:

| Group | Features Included |
|---|---|
| **A — Historical Only** | `excavation_count_all_time`, `excavation_count_24m`, `excavation_count_12m`, `days_since_last_excavation`, `days_since_last_resurfacing`, `resurfacing_within_warranty`, `distinct_utility_count` |
| **B — Historical + Project Activity** | Group A + `active_project_count`, `historical_conflict_count`, `project_density_per_km` |
| **C — Full Feature Set** | Group B + `road_class_encoded`, `segment_length_normalized` |

**ML-ABLATION-02:** Each group shall be evaluated with the same model type (Random Forest) and the same train/test split. Results shall be compared in the ablation report.

**ML-ABLATION-03:** The ablation report shall answer: "Which information genuinely improves predictive performance? Does project activity data add signal beyond historical excavation patterns?"

**ML-ABLATION-04:** If Group A achieves comparable performance to Group C (delta ROC-AUC < 0.02), the evaluation report must note this explicitly, as it suggests additional features may not be contributing signal — possibly because the synthetic data's causal structure does not generate the intended relationships.

### 7.6 Temporal Backtesting Protocol

**ML-BACKTEST-01:** The model evaluation must use **sequential time-based validation**, not random cross-validation. The following protocol is required:

| Fold | Training Period | Validation Period |
|---|---|---|
| 1 | 2020–2022 | 2023 |
| 2 | 2020–2023 | 2024 |
| Final | 2020–2024 | 2025 (held-out test) |

**ML-BACKTEST-02:** The final test set (2025) must represent a strictly later period than the training data. No examples from 2025 may appear in any training fold.

**ML-BACKTEST-03:** The validation folds (2023, 2024) may be used for hyperparameter selection. The test fold (2025) is used once only, for final evaluation.

**ML-BACKTEST-04:** The backtesting protocol must be implemented in `scripts/evaluate_model.py` and must be reproducible by re-running the script with the same seed.

**ML-BACKTEST-05:** Average metrics across validation folds shall be reported alongside final test metrics. Large discrepancy between validation and test performance shall be flagged in the evaluation report.

### 7.7 Explainability Requirements

**ML-EXPLAIN-01:** For every prediction, the top 5 contributing features shall be returned with their values and direction of influence.

**ML-EXPLAIN-02:** The direction of influence shall be expressed as: "increases risk" or "decreases risk" (not raw SHAP values alone).

**ML-EXPLAIN-03:** For Random Forest models, SHAP values or permutation importances shall be used for feature attribution.

**ML-EXPLAIN-04:** The prediction explanation shall be rendered in the UI as a human-readable list, not as raw feature arrays.

**ML-EXPLAIN-05:** Each feature in the `top_features` list shall include its `timestamp_basis` field, so a reader understands what time window was used to compute that feature.

### 7.8 Model Versioning

**ML-VER-01:** Each trained model shall be saved with a version string in the filename (e.g., `rf_v1.2_20261001.joblib`).

**ML-VER-02:** The version string, training date, and feature group used shall be stored in every `RiskPrediction` record.

**ML-VER-03:** Old model artifacts shall not be deleted automatically.

---

## 8. Synthetic Data Requirements

### 8.1 Purpose and Labeling

**SD-01:** All data generated by the synthetic data pipeline shall have `is_synthetic = true`.

**SD-02:** The UI shall display a visible "DEMO — SYNTHETIC DATA" banner on every page.

**SD-03:** The README must describe the synthetic data as: "Generated from a stochastic causal model — not derived from real Dehradun municipal records."

**SD-04:** The pipeline shall be a standalone Python script (`scripts/generate_synthetic_data.py`) accepting `--seed`.

### 8.2 Causal Data-Generating Process

The synthetic data generator must simulate **plausible causal relationships** between road/project characteristics and excavation outcomes. This section documents the intended relationships. These are **simulated assumptions, not empirical claims about Dehradun.**

**SD-05:** The generator shall implement the following causal structure:

```
Road class + zone
    → Base excavation frequency (ARTERIAL: higher; LOCAL: lower)
    → Agency activity distribution (ARTERIAL corridors attract more agencies)

Segment length
    → Project duration distribution (longer segments → longer projects)

Historical excavation frequency (prior period)
    → Increased probability of excavation in current period
      (captures infrastructure density / activity hot spots)

Distinct utility count (prior period)
    → Increased probability of additional utility work
      (corridors used by many utilities remain high-activity)

Days since last excavation
    → Decreased short-term probability (excavation fatigue)
    → Increased medium-term probability (as conditions normalize)

Days since last resurfacing
    → Increased probability (freshly resurfaced roads attract new projects)
    → Warranty breach condition (excavation within warranty → flag)

Temporal project clustering
    → Projects for different agencies arrive in correlated bursts
      (e.g., summer construction season → multiple agencies active simultaneously)

Spatial project clustering
    → Projects on one segment in a corridor increase probability of adjacent segments
      being affected (utility networks run along corridors)

Project density per km
    → Higher density → higher repeat excavation probability
```

**SD-06:** The generator must implement these relationships as explicit parameters (e.g., base rates, multipliers, season probabilities). These parameters must be documented in code comments and in the script's `--help` output.

**SD-07:** Future excavation outcomes shall be generated **probabilistically** using the causal structure above — not by randomly injecting labels. Specifically: for each road segment and each time window, the generator computes a probability of excavation as a function of the causal variables, then draws a Bernoulli outcome.

**SD-08:** The generated dataset must preserve **causal ordering**: historical state → prediction timestamp → future outcome. No future event may be used to determine a past state.

### 8.3 Road Network (Synthetic)

**SD-09:** Generate a synthetic road network of approximately 50–100 named road segments modeled loosely on Dehradun's road hierarchy. Named corridors (e.g., Rajpur Road, Haridwar Road, Chakrata Road, Gandhi Road, EC Road) are used as inspirations for naming — not as actual GIS data.

**SD-10:** Assign road classes: ~10 ARTERIAL, ~20 COLLECTOR, ~30–70 LOCAL. ARTERIAL segments receive higher base excavation frequency in the causal model.

**SD-11:** Assign each segment to one of 5–7 Dehradun zones.

### 8.4 Project Data (Synthetic)

**SD-12:** Generate 80–120 utility projects spanning 2020–2026 across all 7 utility types.

**SD-13:** Project durations should reflect distributions consistent with the causal model: water/sewer 15–60 days; telecom 10–45 days; electricity 7–30 days.

**SD-14:** Deliberately produce 15–25 spatial-temporal conflict scenarios (as an emergent result of the clustering rules, not by hard-coding conflicts).

**SD-15:** The causal model should produce repeat excavation on 20–30% of road segments as an emergent outcome, not by forced injection.

### 8.5 Reproducibility

**SD-16:** Running `python scripts/generate_synthetic_data.py --seed 42` twice shall produce byte-identical output.

**SD-17:** The script shall include a `--describe-model` flag that prints the causal assumptions and parameter values used.

---

## 9. Non-Functional Requirements

### 9.1 Performance

**NFR-PERF-01:** The map shall render within 2 seconds on a standard development machine.

**NFR-PERF-02:** API responses for single-record queries shall complete within 200ms.

**NFR-PERF-03:** Conflict detection for all projects shall complete within 5 seconds for the synthetic dataset.

**NFR-PERF-04:** ML batch prediction for all segments shall complete within 30 seconds.

**NFR-PERF-05:** Dashboard initial load within 3 seconds.

### 9.2 Reliability

**NFR-REL-01:** All API endpoints shall return structured JSON error responses (never HTML error pages).

**NFR-REL-02:** The application shall handle missing or null data gracefully.

**NFR-REL-03:** The frontend shall display meaningful loading and error states for all data fetching.

### 9.3 Usability

**NFR-USE-01:** Professional infrastructure-control-room appearance: dark or neutral palette, high-contrast labels, clear information hierarchy.

**NFR-USE-02:** Map interactions shall not block the UI thread.

**NFR-USE-03:** All charts and maps shall include axis labels, legends, and tooltips.

**NFR-USE-04:** Target browsers: Chrome, Firefox, Edge (desktop). Mobile responsiveness desirable but secondary.

**NFR-USE-05:** All tables shall support sorting and pagination.

**NFR-USE-06:** Empty states shall display informative messages, not blank screens.

### 9.4 Maintainability

**NFR-MAINT-01:** Backend: PEP 8; ruff linter config included.

**NFR-MAINT-02:** Frontend: TypeScript strict mode; no unqualified `any`.

**NFR-MAINT-03:** All public API functions and classes shall have docstrings/JSDoc.

**NFR-MAINT-04:** No hard-coded configuration; use environment variables or config file.

**NFR-MAINT-05:** Database schema changes managed via Alembic migrations.

### 9.5 Extensibility (Future-Readiness)

**NFR-EXT-01:** Data ingestion layer: pluggable interface for substituting real GIS sources.

**NFR-EXT-02:** Repository layer: full abstraction; SQLite → PostgreSQL/PostGIS swap requires no service layer changes.

**NFR-EXT-03:** ML model interface: abstract class so new model types are addable without modifying the prediction service.

**NFR-EXT-04:** Conflict engine: registered rule pipeline (see FR-CONF-14/15) supporting future spatial rule types.

### 9.6 Security (Baseline)

**NFR-SEC-01:** All incoming data validated via Pydantic schemas before processing.

**NFR-SEC-02:** No raw SQL string concatenation; all queries via ORM.

**NFR-SEC-03:** CORS configured to allow only the known frontend origin in production config.

---

## 10. Technology Stack

| Component | Technology | Version Constraint |
|---|---|---|
| Frontend framework | Next.js | ≥ 14 |
| Frontend language | TypeScript | ≥ 5 (strict mode) |
| Map library | MapLibre GL JS | ≥ 4 |
| UI component library | Tailwind CSS + shadcn/ui or similar | — |
| Charting | Recharts or Plotly.js | — |
| Backend framework | FastAPI | ≥ 0.110 |
| Backend language | Python | ≥ 3.11 |
| Data validation | Pydantic | v2 |
| ORM | SQLAlchemy | ≥ 2.0 |
| Database (dev) | SQLite | Built-in |
| Database (prod path) | PostgreSQL + PostGIS | ≥ 15 |
| Migrations | Alembic | — |
| Geospatial (Python) | GeoPandas, Shapely | — |
| Data processing | Pandas, NumPy | — |
| ML library | scikit-learn | ≥ 1.4 |
| ML explainability | SHAP | — |
| Synthetic data | NumPy (causal model) | — |
| Testing (backend) | pytest | — |
| Testing (frontend) | Jest + React Testing Library | — |
| Linting (backend) | ruff | — |
| Linting (frontend) | ESLint + Prettier | — |
| Package manager (JS) | npm or pnpm | — |
| Package manager (Python) | pip + requirements.txt | Pin versions |
| Server (dev) | Uvicorn | — |

---

## 11. User Stories and Acceptance Criteria

### Epic 1: Road Network Map

**US-01**
> As **Priya**, I want to see all road segments on an interactive map so I can understand the geographic context of infrastructure projects.

- AC-01.1: Map loads and displays all synthetic segments within 2 seconds.
- AC-01.2: Segments visually differentiated by road class.
- AC-01.3: Pan and zoom work without freezing.
- AC-01.4: "DEMO — SYNTHETIC DATA" banner always visible.
- AC-01.5: Renders correctly on Chrome, Firefox, Edge at 1920×1080.

---

**US-02**
> As **Priya**, I want to click a road segment and see its key statistics without leaving the map.

- AC-02.1: Clicking a segment opens a detail panel within 300ms.
- AC-02.2: The panel shows: segment name, road class, ward, zone, **PipeWatch Infrastructure Stress Index** (value + category), risk category (with "ML Prediction" label), excavation count (all time and last 24m), active/planned project count.
- AC-02.3: The panel includes a "View Road Memory" link.
- AC-02.4: The panel shows the top 3 features contributing to the current risk prediction with their `timestamp_basis`.
- AC-02.5: If no prediction exists, the panel shows "No prediction available."
- AC-02.6: The PISI panel includes the disclaimer: "This is a derived index, not a physical measurement of road condition."

---

**US-03**
> As **Rekha**, I want to switch the map to a risk overlay to immediately identify high-risk segments.

- AC-03.1: A visible toggle allows switching between overlay modes (default / risk / PISI / conflict / excavation frequency).
- AC-03.2: Risk overlay: CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=green.
- AC-03.3: Legend visible at all times.
- AC-03.4: "ML Predictions — Not Confirmed Events" label visible on risk overlay.
- AC-03.5: Segments with no prediction rendered in neutral gray with legend entry "No Prediction."

---

### Epic 2: Project Management

**US-04**
> As **Arjun**, I want to register my water project so the system can check for conflicts.

- AC-04.1: Form accepts all required fields (Section 5.1.2).
- AC-04.2: Validates `planned_end_date > planned_start_date`.
- AC-04.3: API returns created project with UUID and all fields.
- AC-04.4: Conflict detection engine runs automatically after creation.
- AC-04.5: Project appears in project list within 1 second.

---

**US-05**
> As **Arjun**, I want to see all projects on a Gantt chart to identify timing overlaps.

- AC-05.1: Gantt renders all active and planned projects on a time axis.
- AC-05.2: Each bar colored by utility type.
- AC-05.3: Conflicting bars (same segment + overlapping dates) marked with visual conflict indicator showing the rule ID on hover.
- AC-05.4: Supports zoom to month/quarter/year.
- AC-05.5: Clicking a bar opens project detail.
- AC-05.6: Filterable by utility type and road segment.

---

### Epic 3: Conflict Radar

**US-06**
> As **Priya**, I want to see a list of all detected infrastructure conflicts to prioritize investigation.

- AC-06.1: Conflict Radar lists all OPEN conflicts.
- AC-06.2: Sortable by severity (default), date detected, segment, utility type.
- AC-06.3: Each row shows: severity badge, project A name, project B name, segment, overlap days, conflict type, rule ID, detected date.
- AC-06.4: Summary counts: total open, by severity.
- AC-06.5: Clicking a row opens detail panel with both project details, segment, conflict explanation (format per FR-CONF-08), and "Run What-If Simulation" shortcut.

---

**US-07**
> As **Priya**, I want the system to automatically detect a HIGH conflict when two excavation projects are planned on the same segment within 30 days of each other.

- AC-07.1: Given Project A (water, segment 102, 1 Jan–20 Jan, requires_excavation=true) and Project B (telecom, segment 102, 15 Jan–10 Feb, requires_excavation=true), the system creates a conflict with severity=HIGH, conflict_type=SPATIAL_TEMPORAL, rule_id=`SPATIAL_TEMPORAL_EXCAVATION_01`.
- AC-07.2: Conflict detected within 5 seconds of Project B being saved.
- AC-07.3: `overlap_days = 5`; `spatial_reason` and `temporal_reason` are non-null and human-readable.
- AC-07.4: Conflict appears in Conflict Radar immediately.
- AC-07.5: Re-running detection without data changes does not create duplicate records.

---

**US-08**
> As **Priya**, I want to mark a conflict as resolved with an audit note.

- AC-08.1: "Mark Resolved" action on conflict detail panel.
- AC-08.2: Requires `resolution_note` (minimum 10 characters).
- AC-08.3: Status changes to RESOLVED; disappears from OPEN list.
- AC-08.4: Accessible via "View Resolved Conflicts" filter.
- AC-08.5: Original `detected_at` timestamp and all explanation fields are retained.

---

**US-22** *(new)*
> As **Arjun**, I want to check what conflicts a hypothetical new project would create before I formally register it.

- AC-22.1: A "Check Hypothetical Project" action is accessible from the Conflict Radar and project creation form.
- AC-22.2: The form accepts the same fields as project creation but does not save to the database.
- AC-22.3: The response lists all conflicting existing projects with: severity, rule ID, overlap dates, affected segments, and plain-language explanation.
- AC-22.4: Each affected segment's current PISI and risk category are shown alongside the collision result.
- AC-22.5: The result is labeled: "Simulation — Not a Confirmed Conflict. The hypothetical project has not been saved."
- AC-22.6: No database records are created by this operation.

---

### Epic 4: Repeat Excavation Risk Prediction

**US-09**
> As **Rekha**, I want to see the repeat excavation risk probability for a specific road segment to decide whether to approve a new project.

- AC-09.1: Detail panel shows: probability (percentage), risk_category, prediction_timestamp, feature_snapshot_timestamp, model_version, prediction_horizon_days.
- AC-09.2: Labeled "ML Prediction — Not a confirmed event."
- AC-09.3: Top 5 contributing features shown as plain-language list with values and `timestamp_basis` for each feature.
- AC-09.4: "Refresh Prediction" button triggers a new on-demand prediction.
- AC-09.5: If ML model unavailable, falls back to rule baseline labeled "Rule-Based Estimate — Not an ML Prediction."

---

**US-10**
> As **Dr. Mehta**, I want to see model evaluation metrics to assess reliability before citing predictions in research.

- AC-10.1: "Model Info" panel accessible from the risk prediction display.
- AC-10.2: Shows: model type, model version, training date, feature group used, ROC-AUC, F1-score, precision, recall on the test period, and delta vs rule baseline.
- AC-10.3: Clearly states: "Trained on synthetic data. Relationships are simulated assumptions."
- AC-10.4: Downloadable evaluation report (JSON) accessible.
- AC-10.5: Calibration curve displayed as a chart.
- AC-10.6: Ablation experiment results (Group A / B / C) accessible in the same report.
- AC-10.7: Backtesting fold results (per-fold metrics) visible alongside final test metrics.

---

### Epic 5: Road Memory Timeline

**US-11**
> As **Rekha**, I want to see the complete history of a road segment to understand past disruption and check for warranty risks.

- AC-11.1: Timeline shows all excavation, resurfacing, and project milestone events chronologically.
- AC-11.2: Each event shows: type (icon), date range, project name, utility type, agency, data source (SYNTHETIC), provenance category.
- AC-11.3: Excavations within warranty period of prior resurfacing flagged "Warranty Breach" (red).
- AC-11.4: 3+ excavations within 24 months flagged "Frequent Excavation."
- AC-11.5: Filterable by event type and date range.
- AC-11.6: All events labeled with data source.

---

**US-12**
> As **Dr. Mehta**, I want to export the Road Memory as JSON.

- AC-12.1: "Download Road Memory" button triggers JSON file download.
- AC-12.2: JSON includes segment metadata, all events, project references, `is_synthetic` flags, and provenance fields.
- AC-12.3: Valid and parseable; matches displayed timeline.
- AC-12.4: Filename: `road_memory_{segment_name}_{date}.json`.

---

### Epic 6: PipeWatch Infrastructure Stress Index

**US-13**
> As **Rekha**, I want to understand why a road segment has a HIGH PISI so I can explain the priority to my supervisor.

- AC-13.1: Detail panel shows PISI value alongside a horizontal bar chart of all 5 component sub-scores.
- AC-13.2: Each component labeled with: name, weight, current sub-score value.
- AC-13.3: "How is this calculated?" expandable section shows the formula in plain text, with the disclaimer: "This is a derived index, not a physical measurement of road condition."
- AC-13.4: PISI category shown with color and threshold range.
- AC-13.5: `calculated_at` and `formula_version` shown.

---

**US-14**
> As **Priya**, I want to see the top 10 highest-PISI road segments on the dashboard to prioritize coordination.

- AC-14.1: Dashboard shows a ranked list of top 10 segments by PISI value.
- AC-14.2: Each item: rank, segment name, PISI value, category (color-coded), link to segment detail.
- AC-14.3: List updates when PISI is recalculated.
- AC-14.4: Clicking a segment name navigates to that segment on the map.

---

### Epic 7: What-If Simulator

**US-15**
> As **Priya**, I want to compare two scheduling scenarios to demonstrate the benefit of coordination.

- AC-15.1: Simulator allows defining two named scenarios with ≥ 2 project events each.
- AC-15.2: Each event has: utility type, start date, end date, requires_excavation, requires_resurfacing.
- AC-15.3: Returns comparison table with all metrics from FR-SIM-04.
- AC-15.4: Better scenario highlighted per metric.
- AC-15.5: No monetary figures displayed.
- AC-15.6: Labeled "Simulation — Not a Committed Schedule."
- AC-15.7: Completes within 3 seconds.
- AC-15.8: Result carries `provenance.evidence_sources = ["SIMULATION"]`.

---

**US-16**
> As **Arjun**, I want the simulation to show how many repeat excavations are avoided by coordinating water and telecom work.

- AC-16.1: Scenario A (sequential) shows repeat_excavation_count = 1.
- AC-16.2: Scenario B (coordinated) shows repeat_excavation_count = 0.
- AC-16.3: `estimated_avoided_excavations = 1`.
- AC-16.4: Narrative explanation generated from metric data.
- AC-16.5: Narrative is not hard-coded.

---

### Epic 8: Coordination Recommendations

**US-17**
> As **Priya**, I want to see coordination recommendations for detected conflicts.

- AC-17.1: Recommendations panel shows PENDING items sorted by priority.
- AC-17.2: Each recommendation shows: title, priority badge, type, affected projects, rationale, evidence items with provenance.
- AC-17.3: Labeled "Advisory — Requires Planner Review."
- AC-17.4: Clicking evidence items navigates to the relevant record.
- AC-17.5: HIGH priority count badge shown on navigation.

---

**US-18**
> As **Priya**, I want to accept or reject a recommendation with an audit trail.

- AC-18.1: ACCEPT and REJECT buttons on each PENDING recommendation.
- AC-18.2: REJECT requires a reason (minimum 10 characters).
- AC-18.3: Status updates immediately in UI.
- AC-18.4: History filter shows accepted/rejected decisions.
- AC-18.5: Records not deletable (status update only).

---

### Epic 9: Dashboard

**US-19**
> As **Priya**, I want a single dashboard view giving immediate situational overview.

- AC-19.1: Dashboard loads within 3 seconds.
- AC-19.2: All key widgets visible above the fold at 1920×1080: Open Conflicts, Active Projects, High-Risk Segments, Top 10 High-PISI Segments, Pending Recommendations.
- AC-19.3: "Refresh All" triggers data refresh.
- AC-19.4: "SYNTHETIC DATA" banner always visible.
- AC-19.5: Clicking any summary count navigates to corresponding detail view with filter pre-applied.

---

**US-20**
> As **Dr. Mehta**, I want a chart of excavation events by utility type to identify which utilities are most disruptive.

- AC-20.1: Bar chart shows excavation count by utility type.
- AC-20.2: All 7 utility types represented.
- AC-20.3: Axis labels, title, hover tooltips with exact count.
- AC-20.4: Updates on refresh.

---

### Epic 10: Data Quality

**US-21**
> As **Dr. Mehta**, I want to see the data quality score for the synthetic dataset.

- AC-21.1: Data Quality panel shows overall score (0–100) with per-entity-type breakdown.
- AC-21.2: Flagged records listed with specific issues.
- AC-21.3: Completeness and consistency shown separately.
- AC-21.4: Score recalculated on each check.
- AC-21.5: Accessible from dashboard.

---

## 12. API Specification (Outline)

All endpoints return `application/json`. All use snake_case. Error shape: `{ "detail": "...", "error_code": "..." }`. All responses for predictions, conflicts, PISI, recommendations, and simulations include a `provenance` field per Section 5.3.

### 12.1 Road Segments

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/segments` | List all road segments |
| GET | `/api/v1/segments/{id}` | Get segment by ID |
| GET | `/api/v1/segments/{id}/memory` | Get Road Memory timeline (includes provenance per event) |
| GET | `/api/v1/segments/{id}/stress` | Get current PISI for segment |
| GET | `/api/v1/segments/{id}/risk` | Get latest RiskPrediction for segment |
| POST | `/api/v1/segments/{id}/risk/refresh` | Trigger a fresh ML prediction (creates new RiskPrediction record) |
| GET | `/api/v1/segments/geojson` | GeoJSON FeatureCollection of all segments |

### 12.2 Projects

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/projects` | List all projects (filterable: utility_type, status, date range, segment, agency) |
| POST | `/api/v1/projects` | Create a new project |
| GET | `/api/v1/projects/{id}` | Get project by ID |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Soft-delete project |

### 12.3 Excavation and Resurfacing Events

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/excavations` | List excavation events (filterable) |
| POST | `/api/v1/excavations` | Create excavation event |
| GET | `/api/v1/excavations/{id}` | Get excavation event |
| GET | `/api/v1/resurfacing` | List resurfacing events |
| POST | `/api/v1/resurfacing` | Create resurfacing event |
| GET | `/api/v1/resurfacing/{id}` | Get resurfacing event |

### 12.4 Conflict Detection

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/conflicts` | List all conflicts (filterable by status, severity, rule_id) |
| GET | `/api/v1/conflicts/{id}` | Get conflict detail (includes full explanation fields) |
| POST | `/api/v1/conflicts/detect` | Run conflict detection for all or specific segments |
| PATCH | `/api/v1/conflicts/{id}/status` | Update conflict status (acknowledge/resolve) |
| POST | `/api/v1/conflicts/simulate` | **Project Collision Simulation** — check hypothetical project without saving |

### 12.5 ML Predictions

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/ml/predict/{segment_id}` | Get latest RiskPrediction for segment |
| POST | `/api/v1/ml/predict/{segment_id}/refresh` | Trigger fresh prediction (new immutable record) |
| POST | `/api/v1/ml/batch-predict` | Refresh predictions for all segments |
| GET | `/api/v1/ml/model-info` | Model metadata, evaluation metrics, ablation results, backtesting folds |

### 12.6 Infrastructure Stress Index

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/stress/recalculate` | Recalculate PISI for all segments |
| GET | `/api/v1/stress/top` | Get top N highest-PISI segments |

### 12.7 What-If Simulator

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/simulator/compare` | Submit two scenarios; returns comparison metrics + narrative + provenance |

### 12.8 Recommendations

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/recommendations` | List recommendations (filterable) |
| POST | `/api/v1/recommendations/generate` | Trigger recommendation generation |
| PATCH | `/api/v1/recommendations/{id}/decision` | Accept or reject a recommendation |

### 12.9 Dashboard

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/dashboard/summary` | All dashboard summary metrics in one call |

### 12.10 Data Quality

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/data-quality` | Get data quality report |
| POST | `/api/v1/data-quality/check` | Run data quality checks |

---

## 13. Testing Requirements

### 13.1 Backend Unit Tests (pytest)

**TEST-UNIT-01:** Unit tests shall cover all service layer functions with ≥ 80% line coverage.

**TEST-UNIT-02:** The conflict detection engine shall have unit tests covering:
- Spatial overlap only (rule `SPATIAL_ONLY_03`)
- Temporal overlap only (rule `TEMPORAL_PROXIMITY_04`)
- Both overlap + both excavate → HIGH (rule `SPATIAL_TEMPORAL_EXCAVATION_01`)
- Both overlap + one excavates → MEDIUM (rule `SPATIAL_TEMPORAL_MIXED_02`)
- No overlap (no conflict)
- Edge case: exactly 30 days apart (boundary of temporal window)
- Idempotency: running detection twice without data change produces no new records

**TEST-UNIT-03:** Every conflict test must assert that `rule_id`, `spatial_reason`, and `temporal_reason` are populated correctly.

**TEST-UNIT-04:** The PISI calculator shall have unit tests covering:
- Segment with zero events (PISI = 0)
- Segment with maximum inputs (PISI approaches 100)
- Each component in isolation with known inputs and expected sub-score values

**TEST-UNIT-05:** The synthetic data generator shall have tests verifying reproducibility (same seed → byte-identical output).

**TEST-UNIT-06:** The What-If simulator shall have tests for each metric with known inputs and expected outputs.

**TEST-UNIT-07:** The Project Collision Simulation endpoint shall have unit tests verifying:
- No database records are created
- The returned conflicts use the same rule logic as stored conflict detection
- The response carries `provenance.evidence_sources = ["SIMULATION"]`

### 13.2 Data Leakage Prevention Tests

**TEST-LEAK-01:** The feature store builder shall have tests that deliberately introduce an event timestamped after the snapshot date and verify the pipeline excludes it from all feature computations.

**TEST-LEAK-02:** A test shall verify that the target label for a training example uses only events strictly after the snapshot date.

**TEST-LEAK-03:** A test shall verify that `active_project_count` at snapshot_ts does not include any project created after snapshot_ts.

**TEST-LEAK-04:** These tests must be run as part of the standard test suite, not as one-off scripts.

### 13.3 API Integration Tests (pytest + HTTPX)

**TEST-API-01:** Integration tests for all API endpoints: happy path, validation error (422), not found (404).

**TEST-API-02:** Conflict detection integration test: insert two conflicting projects; verify HIGH conflict with correct rule_id and explanation fields.

**TEST-API-03:** ML prediction endpoint integration test: returns valid schema (probability ∈ [0,1], risk_category valid enum, top_features non-empty, feature_snapshot_timestamp present).

**TEST-API-04:** Collision simulation endpoint integration test: verify no records created, response carries SIMULATION provenance.

### 13.4 ML Tests

**TEST-ML-01:** Training script produces a model file and evaluation report on the synthetic dataset.

**TEST-ML-02:** The evaluation report shall include: per-fold backtesting metrics, final test metrics, delta vs rule baseline, ablation results for Groups A/B/C. There is no fixed pass/fail threshold; the test verifies the report is complete and all required fields are present.

**TEST-ML-03:** Prediction schema validation: probability ∈ [0,1], risk_category valid enum, top_features non-empty list, `feature_snapshot_timestamp` present and earlier than `prediction_timestamp`.

**TEST-ML-04:** Backtesting script must be runnable with `--seed 42` and produce the same fold metrics on repeated runs.

### 13.5 Frontend Tests (Jest + React Testing Library)

**TEST-FE-01:** Unit tests for utility functions (date formatting, score categorization, color mapping).

**TEST-FE-02:** Component tests: ConflictCard, RiskBadge, PISIPanel, RoadMemoryTimeline, ConflictExplanation.

**TEST-FE-03:** Tests verify "ML Prediction" labels render when prediction data is present.

**TEST-FE-04:** Tests verify "SYNTHETIC DATA" banner renders on all main pages.

**TEST-FE-05:** Tests verify PISI panel renders the disclaimer "This is a derived index, not a physical measurement of road condition."

---

## 14. Future Extensibility

| Feature | Notes |
|---|---|
| Real data ingestion | OpenStreetMap road network (Overpass API); Dehradun municipal open data if available |
| User authentication | JWT-based auth with RBAC |
| PostGIS migration | GeoPandas spatial queries → PostGIS native ST_ functions |
| Advanced ML models | XGBoost with SHAP, temporal sequence models |
| Proximity-based conflict detection | Architecture ready (FR-CONF-15); rules not yet implemented |
| Notification system | Email/SMS alerts for new HIGH conflicts |
| Mobile PWA | Responsive mobile interface |
| Audit trail | Full change history for all records |
| Multi-city support | Parametric city configuration layer |
| API rate limiting | For future public API access |
| Satellite imagery overlay | Road distress detection from aerial imagery |
| GIS file import | Upload Shapefiles or GeoJSON |
| PISI empirical validation | Calibrate index weights against real road condition surveys if data becomes available |

---

## 15. Glossary

| Term | Definition |
|---|---|
| **Road Segment** | A discrete, named section of a road independently tracked for infrastructure events |
| **Excavation Event** | A recorded instance of road cutting or trenching associated with a utility project |
| **Resurfacing Event** | A recorded instance of road restoration or resurfacing |
| **Conflict (Spatial)** | Two projects affecting at least one common road segment |
| **Conflict (Temporal)** | Two projects on the same segment whose date ranges overlap or fall within the temporal buffer window |
| **Conflict (Spatial-Temporal)** | Both spatial and temporal conditions true simultaneously |
| **Rule ID** | A unique string identifier for a specific conflict detection rule (e.g., `SPATIAL_TEMPORAL_EXCAVATION_01`) |
| **Project Collision Simulation** | A read-only operation that checks what conflicts a hypothetical, unsaved project would generate; produces no database records |
| **Repeat Excavation** | An excavation event on a segment that has already been excavated within a preceding time window (default: 180 days) |
| **Road Memory** | The chronological history of all infrastructure events on a road segment |
| **PipeWatch Infrastructure Stress Index (PISI)** | A deterministic decision-support index [0–100] derived from infrastructure disruption history. It is not a physical measurement of road condition and has not been empirically validated against actual road damage data. Internal code name: `InfrastructureStressIndex`. |
| **Risk Prediction** | An ML model output estimating the probability of repeat excavation within a configurable future window |
| **RiskPrediction (immutable record)** | A stored prediction record that must never be modified after creation; the `feature_snapshot` field allows reproduction of the prediction regardless of later data changes |
| **Feature Snapshot Timestamp** | The point-in-time at which all features for a prediction were computed; all features reflect the world strictly before this timestamp |
| **Data Leakage** | The use of information from the future prediction window when computing features for a training example; a violation of the leakage contract (FR-RISK-02) |
| **What-If Scenario** | A hypothetical project schedule created in the simulator for comparison; not a committed plan |
| **Coordination Recommendation** | An advisory suggestion requiring planner review before any action |
| **Temporal Buffer Window** | A configurable number of days (default: 30) used when evaluating temporal conflict proximity |
| **Warranty Breach** | An excavation during the active warranty period of a preceding resurfacing event on the same segment |
| **PISI Disclaimer** | Required UI text: "This is a derived index, not a physical measurement of road condition." |
| **Provenance** | Structured metadata attached to API outputs identifying the source category of each piece of evidence (SYNTHETIC_HISTORICAL_EVENT, SYNTHETIC_PROJECT, DETERMINISTIC_CALCULATION, ML_PREDICTION, SIMULATION) |
| **Epistemic Honesty** | The system design principle requiring strict categorical distinction between observed data, deterministic rules, ML predictions, and advisory recommendations |
| **is_synthetic** | A boolean flag on all data records in v1.0 indicating the data was generated by the synthetic pipeline and does not represent real infrastructure records |
| **Causal Data-Generating Process** | The synthetic data generator's explicit causal model relating road/project characteristics to excavation outcomes (Section 8.2) — a set of simulated assumptions, not empirical claims |
| **OBSERVED DATA** | Recorded historical events; presented as fact |
| **DETERMINISTIC RULES** | Logic from documented formulas and rule tables; reproducible and auditable |
| **ML PREDICTIONS** | Statistical model outputs; always labeled with probability, model version, and the caveat that they are not confirmed events |
| **RECOMMENDATIONS** | Advisory system outputs; always labeled as requiring planner review |

---

*End of PipeWatch Requirements Specification v1.1*
*Supersedes v1.0 — see Requirements Revision Summary for changes.*
*Document maintained in: `REQUIREMENTS.md` at workspace root*
*Next step: Technical design document (`DESIGN.md`) — authorized after this specification is approved.*
