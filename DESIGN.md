# PipeWatch — Technical Design Document

**Predictive Utility Coordination & Road Excavation Intelligence**
**Design Version:** 1.0
**Requirements Version:** 1.1
**Date:** October 2026

> This document is the authoritative technical design for PipeWatch. It is derived entirely from `REQUIREMENTS.md` v1.1. No new product features are introduced here. All design decisions are traceable to a requirement.

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Repository Structure](#2-repository-structure)
3. [Database Design](#3-database-design)
4. [Geospatial Design](#4-geospatial-design)
5. [Conflict Engine](#5-conflict-engine)
6. [Project Collision Simulation](#6-project-collision-simulation)
7. [Road Memory](#7-road-memory)
8. [PipeWatch Infrastructure Stress Index (PISI)](#8-pipewatch-infrastructure-stress-index-pisi)
9. [ML Data Pipeline](#9-ml-data-pipeline)
10. [Feature Store](#10-feature-store)
11. [Synthetic Data Generator](#11-synthetic-data-generator)
12. [ML Models](#12-ml-models)
13. [Temporal Backtesting](#13-temporal-backtesting)
14. [Feature Ablation](#14-feature-ablation)
15. [Explainability](#15-explainability)
16. [What-If Simulator](#16-what-if-simulator)
17. [Recommendation Engine](#17-recommendation-engine)
18. [API Design](#18-api-design)
19. [Frontend Design](#19-frontend-design)
20. [Main User Flow](#20-main-user-flow)
21. [Data Provenance](#21-data-provenance)
22. [Testing Architecture](#22-testing-architecture)
23. [Error Handling](#23-error-handling)
24. [Configuration](#24-configuration)
25. [Development Strategy](#25-development-strategy)
26. [Implementation Task Plan](#26-implementation-task-plan)

---

## 1. Architecture

### 1.1 System Overview

PipeWatch is a **modular monolith** — a single deployable unit whose internal modules are strictly separated by responsibility. This choice is intentional: the scale of synthetic data (~100 segments, ~120 projects) does not justify the operational overhead of microservices, but the code must be structured so that individual modules (ML pipeline, conflict engine, recommendation engine) can be reasoned about, tested, and replaced independently.

```
┌─────────────────────────────────────────────────────────────┐
│                     BROWSER CLIENT                           │
│                                                             │
│  Next.js 14 + TypeScript + MapLibre GL JS + Tailwind CSS   │
│  Recharts  ·  React Query  ·  Zustand (UI state)           │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST / JSON
                         │ (localhost:3000 → localhost:8000)
┌────────────────────────▼────────────────────────────────────┐
│                     FASTAPI APPLICATION                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API LAYER  (routers, request/response schemas)      │  │
│  └──────────────────────────┬─────────────────────────-─┘  │
│                             │                               │
│  ┌──────────────────────────▼──────────────────────────┐   │
│  │  SERVICE LAYER  (business logic, orchestration)     │   │
│  │                                                     │   │
│  │  ConflictEngine  ·  RoadMemoryService               │   │
│  │  PISICalculator  ·  RecommendationEngine            │   │
│  │  WhatIfSimulator ·  CollisionSimulator              │   │
│  │  PredictionService · DataQualityService             │   │
│  │  ProvenanceService                                  │   │
│  └──────────────────────────┬───────────────────────-──┘   │
│                             │                               │
│  ┌──────────────────────────▼──────────────────────────┐   │
│  │  REPOSITORY LAYER  (all DB access)                  │   │
│  │                                                     │   │
│  │  SegmentRepository  ·  ProjectRepository            │   │
│  │  ExcavationRepository · ResurfacingRepository       │   │
│  │  ConflictRepository  ·  PredictionRepository        │   │
│  │  PISIRepository  ·  RecommendationRepository        │   │
│  └──────────────────────────┬───────────────────────-──┘   │
│                             │ SQLAlchemy 2 async            │
└────────────────────────────-┼────────────────────────────-─┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     DATA LAYER                               │
│                                                             │
│  SQLite (dev)  ──►  PostgreSQL + PostGIS (prod migration)  │
│  GeoJSON seed files  ·  Parquet feature store              │
│  Joblib model artifacts                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     ML PIPELINE  (offline)                   │
│                                                             │
│  scripts/generate_synthetic_data.py                        │
│  scripts/build_feature_store.py                            │
│  scripts/train_model.py                                    │
│  scripts/evaluate_model.py                                 │
│                                                             │
│  Reads from: SQLite / Parquet feature store                │
│  Writes to:  models/*.joblib  ·  ml/evaluation/*.json      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Layer Responsibilities

| Layer | What it does | What it must NOT do |
|---|---|---|
| **API Layer** | Route HTTP requests, validate input with Pydantic, serialize responses | Contain business logic or query the DB directly |
| **Service Layer** | Implement all business logic: conflict rules, PISI formula, recommendations, simulation | Access the database directly (only via repositories) |
| **Repository Layer** | All SQLAlchemy queries — reads, writes, updates, soft deletes | Contain business logic |
| **ML Pipeline** | Feature engineering, model training, evaluation; standalone scripts | Import from the API or service layers |
| **Provenance Service** | Attach provenance metadata to service outputs before they reach the API layer | Make business decisions |

### 1.3 Why This Stack

| Component | Reason |
|---|---|
| **Next.js 14** | File-system routing, React Server Components for initial data, TypeScript first-class. No need for a separate SSR framework. |
| **MapLibre GL JS** | Open-source, vector-tile capable, highly customizable styling. Does not require a proprietary API key. Chosen over Mapbox for cost and IP reasons. |
| **Tailwind CSS** | Utility-first; prevents style inconsistencies across components; plays well with shadcn/ui component primitives. |
| **Recharts** | Declarative React charting; handles Gantt (bar), time series (line), donut, and bar charts with minimal configuration. |
| **FastAPI** | Async Python, first-class Pydantic v2 integration, automatic OpenAPI docs, typed path/query parameters. |
| **Pydantic v2** | Schema validation at the API boundary; v2 is significantly faster than v1 and has native discriminated unions for provenance types. |
| **SQLAlchemy 2** | Unified ORM with async support; expressive mapped columns; works with both SQLite and PostgreSQL with minimal change. |
| **Alembic** | Schema migration tool tightly coupled to SQLAlchemy; supports both SQLite and PostgreSQL migrations. |
| **GeoPandas + Shapely** | Isolated to the geospatial utility module; Shapely handles all geometry operations; abstracted behind a `SpatialAdapter` interface so PostGIS can replace it later. |
| **scikit-learn** | Standard ML library; Logistic Regression and Random Forest are natively supported; `Pipeline` class enables clean feature scaling + model packaging. |
| **SHAP** | Model-agnostic explainability; works with both tree-based and linear models; `TreeExplainer` is efficient for Random Forest. |
| **joblib** | scikit-learn's native serialization format; handles numpy arrays correctly; version-stamped filenames per ML-VER-01. |

### 1.4 Data Flow for a Risk Prediction Request

```
Browser                 FastAPI              PredictionService       Repository             ML Model
  │                        │                        │                    │                     │
  │  GET /segments/{id}/risk│                        │                    │                     │
  ├───────────────────────►│                        │                    │                     │
  │                        │  get_latest_prediction(segment_id)          │                     │
  │                        ├───────────────────────►│                    │                     │
  │                        │                        │  fetch segment     │                     │
  │                        │                        ├──────────────────►│                     │
  │                        │                        │◄──────────────────┤                     │
  │                        │                        │  fetch latest      │                     │
  │                        │                        │  RiskPrediction    │                     │
  │                        │                        ├──────────────────►│                     │
  │                        │                        │◄──────────────────┤                     │
  │                        │                        │  attach_provenance │                     │
  │                        │◄───────────────────────┤                    │                     │
  │  RiskPredictionResponse│                        │                    │                     │
  │◄───────────────────────┤                        │                    │                     │
```

---

## 2. Repository Structure

```
pipewatch/
│
├── README.md
├── REQUIREMENTS.md
├── REQUIREMENTS_REVISION_SUMMARY.md
├── DESIGN.md
│
├── .env.example                   # Template; never commit .env
├── .gitignore
├── docker-compose.yml             # Optional: postgres + app for later
│
├── backend/                       # FastAPI application
│   ├── pyproject.toml             # or setup.cfg / requirements.txt
│   ├── requirements.txt           # pinned versions
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/              # Migration scripts
│   │
│   ├── app/
│   │   ├── main.py                # FastAPI app creation, CORS, lifespan
│   │   ├── config.py              # Settings via pydantic-settings
│   │   ├── database.py            # Engine, session factory
│   │   │
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # DeclarativeBase, SoftDeleteMixin, TimestampMixin
│   │   │   ├── road_segment.py
│   │   │   ├── utility_project.py
│   │   │   ├── excavation_event.py
│   │   │   ├── resurfacing_event.py
│   │   │   ├── conflict_record.py
│   │   │   ├── risk_prediction.py
│   │   │   ├── infrastructure_stress_index.py
│   │   │   └── coordination_recommendation.py
│   │   │
│   │   ├── schemas/               # Pydantic v2 request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py          # ProvenanceSchema, PaginationSchema, ErrorSchema
│   │   │   ├── road_segment.py
│   │   │   ├── utility_project.py
│   │   │   ├── excavation_event.py
│   │   │   ├── resurfacing_event.py
│   │   │   ├── conflict.py
│   │   │   ├── risk_prediction.py
│   │   │   ├── stress_index.py
│   │   │   ├── recommendation.py
│   │   │   ├── simulator.py
│   │   │   └── dashboard.py
│   │   │
│   │   ├── repositories/          # All DB access
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # BaseRepository with soft-delete helpers
│   │   │   ├── segment_repo.py
│   │   │   ├── project_repo.py
│   │   │   ├── excavation_repo.py
│   │   │   ├── resurfacing_repo.py
│   │   │   ├── conflict_repo.py
│   │   │   ├── prediction_repo.py
│   │   │   ├── stress_index_repo.py
│   │   │   └── recommendation_repo.py
│   │   │
│   │   ├── services/              # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── road_memory.py
│   │   │   ├── pisi_calculator.py
│   │   │   ├── conflict_engine.py
│   │   │   ├── collision_simulator.py
│   │   │   ├── prediction_service.py
│   │   │   ├── whatif_simulator.py
│   │   │   ├── recommendation_engine.py
│   │   │   ├── data_quality.py
│   │   │   └── provenance.py
│   │   │
│   │   ├── conflict_rules/        # Registered conflict rule pipeline
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # AbstractConflictRule
│   │   │   ├── registry.py        # ConflictRuleRegistry
│   │   │   ├── spatial_only.py    # SPATIAL_ONLY_03
│   │   │   ├── temporal_proximity.py  # TEMPORAL_PROXIMITY_04
│   │   │   ├── spatial_temporal_excavation.py  # SPATIAL_TEMPORAL_EXCAVATION_01
│   │   │   └── spatial_temporal_mixed.py       # SPATIAL_TEMPORAL_MIXED_02
│   │   │
│   │   ├── geospatial/            # Isolated spatial logic
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py         # SpatialAdapter abstract class
│   │   │   ├── shapely_adapter.py # Shapely/GeoPandas implementation
│   │   │   └── utils.py           # GeoJSON conversion, length calc
│   │   │
│   │   └── routers/               # FastAPI routers (one per domain)
│   │       ├── __init__.py
│   │       ├── segments.py
│   │       ├── projects.py
│   │       ├── excavations.py
│   │       ├── resurfacing.py
│   │       ├── conflicts.py
│   │       ├── ml.py
│   │       ├── stress.py
│   │       ├── simulator.py
│   │       ├── recommendations.py
│   │       ├── dashboard.py
│   │       └── data_quality.py
│   │
│   └── tests/
│       ├── conftest.py            # Fixtures: test DB, test client
│       ├── unit/
│       │   ├── test_conflict_rules.py
│       │   ├── test_pisi_calculator.py
│       │   ├── test_road_memory.py
│       │   ├── test_whatif_simulator.py
│       │   ├── test_collision_simulator.py
│       │   └── test_provenance.py
│       ├── integration/
│       │   ├── test_segments_api.py
│       │   ├── test_projects_api.py
│       │   ├── test_conflicts_api.py
│       │   ├── test_ml_api.py
│       │   └── test_simulator_api.py
│       └── leakage/
│           ├── test_feature_leakage.py
│           └── test_target_leakage.py
│
├── frontend/                      # Next.js application
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── .env.local.example
│   │
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   │   ├── layout.tsx         # Root layout: fonts, global banner
│   │   │   ├── page.tsx           # Redirects to /dashboard
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   ├── map/
│   │   │   │   └── page.tsx
│   │   │   ├── conflicts/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── projects/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── gantt/
│   │   │   │   └── page.tsx
│   │   │   ├── segments/
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx
│   │   │   │       ├── memory/page.tsx
│   │   │   │       └── risk/page.tsx
│   │   │   ├── simulator/
│   │   │   │   └── page.tsx
│   │   │   ├── collision/
│   │   │   │   └── page.tsx
│   │   │   ├── recommendations/
│   │   │   │   └── page.tsx
│   │   │   ├── model-info/
│   │   │   │   └── page.tsx
│   │   │   └── data-quality/
│   │   │       └── page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.tsx       # Sidebar + top bar
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── SyntheticDataBanner.tsx  # Always-visible banner
│   │   │   │   └── PageHeader.tsx
│   │   │   ├── map/
│   │   │   │   ├── PipeWatchMap.tsx       # MapLibre container
│   │   │   │   ├── SegmentLayer.tsx       # MapLibre layer for segments
│   │   │   │   ├── OverlaySelector.tsx    # Risk / PISI / Conflict toggle
│   │   │   │   ├── MapLegend.tsx
│   │   │   │   └── SegmentDetailPanel.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── ConflictSummaryWidget.tsx
│   │   │   │   ├── ActiveProjectsWidget.tsx
│   │   │   │   ├── HighRiskSegmentsWidget.tsx
│   │   │   │   ├── TopPISIWidget.tsx
│   │   │   │   ├── RecentExcavationsWidget.tsx
│   │   │   │   ├── PendingRecommendationsWidget.tsx
│   │   │   │   ├── ExcavationByUtilityChart.tsx
│   │   │   │   ├── ConflictsPerMonthChart.tsx
│   │   │   │   └── RiskDistributionChart.tsx
│   │   │   ├── conflict/
│   │   │   │   ├── ConflictTable.tsx
│   │   │   │   ├── ConflictCard.tsx
│   │   │   │   ├── ConflictExplanationPanel.tsx
│   │   │   │   └── ConflictSeverityBadge.tsx
│   │   │   ├── prediction/
│   │   │   │   ├── RiskBadge.tsx
│   │   │   │   ├── RiskPredictionPanel.tsx
│   │   │   │   ├── TopFeaturesPanel.tsx
│   │   │   │   └── ModelInfoPanel.tsx
│   │   │   ├── pisi/
│   │   │   │   ├── PISIPanel.tsx
│   │   │   │   ├── PISIComponentChart.tsx
│   │   │   │   └── PISIFormulaDisclosure.tsx
│   │   │   ├── memory/
│   │   │   │   ├── RoadMemoryTimeline.tsx
│   │   │   │   ├── TimelineEvent.tsx
│   │   │   │   └── MemoryWarningBadge.tsx
│   │   │   ├── simulator/
│   │   │   │   ├── WhatIfScenarioForm.tsx
│   │   │   │   ├── ScenarioComparisonTable.tsx
│   │   │   │   └── ScenarioNarrative.tsx
│   │   │   ├── collision/
│   │   │   │   ├── CollisionSimulatorForm.tsx
│   │   │   │   └── CollisionResultPanel.tsx
│   │   │   ├── recommendations/
│   │   │   │   ├── RecommendationCard.tsx
│   │   │   │   └── RecommendationDecisionForm.tsx
│   │   │   └── shared/
│   │   │       ├── ProvenanceBadge.tsx
│   │   │       ├── DataSourceLabel.tsx
│   │   │       ├── LoadingState.tsx
│   │   │       ├── ErrorState.tsx
│   │   │       └── EmptyState.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── api/               # Typed API client functions
│   │   │   │   ├── client.ts      # Base fetch wrapper
│   │   │   │   ├── segments.ts
│   │   │   │   ├── projects.ts
│   │   │   │   ├── conflicts.ts
│   │   │   │   ├── predictions.ts
│   │   │   │   ├── pisi.ts
│   │   │   │   ├── simulator.ts
│   │   │   │   └── recommendations.ts
│   │   │   ├── types/             # TypeScript types mirroring API schemas
│   │   │   │   ├── index.ts
│   │   │   │   ├── segment.ts
│   │   │   │   ├── project.ts
│   │   │   │   ├── conflict.ts
│   │   │   │   ├── prediction.ts
│   │   │   │   ├── pisi.ts
│   │   │   │   └── provenance.ts
│   │   │   └── utils/
│   │   │       ├── dates.ts
│   │   │       ├── colors.ts      # Risk/PISI category → color mapping
│   │   │       ├── format.ts
│   │   │       └── geojson.ts
│   │   │
│   │   └── store/
│   │       └── mapStore.ts        # Zustand: active overlay, selected segment
│   │
│   └── tests/
│       ├── components/
│       └── utils/
│
├── ml/                            # ML pipeline source (not a web server)
│   ├── __init__.py
│   ├── features/
│   │   ├── __init__.py
│   │   ├── builder.py             # PointInTimeFeatureBuilder
│   │   ├── definitions.py         # Feature metadata + timestamp semantics
│   │   └── validator.py           # LeakageValidator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # AbstractPipeWatchModel
│   │   ├── rule_baseline.py
│   │   ├── logistic_regression.py
│   │   └── random_forest.py
│   ├── training/
│   │   ├── __init__.py
│   │   ├── splitter.py            # TemporalSplitter
│   │   ├── trainer.py
│   │   └── hyperparameters.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── backtesting.py
│   │   ├── ablation.py
│   │   └── calibration.py
│   ├── explainability/
│   │   ├── __init__.py
│   │   └── explainer.py
│   └── prediction/
│       ├── __init__.py
│       └── predictor.py           # Loaded at API startup; serves predictions
│
├── scripts/                       # Standalone CLI scripts
│   ├── generate_synthetic_data.py
│   ├── build_feature_store.py
│   ├── train_model.py
│   └── evaluate_model.py
│
├── data/
│   ├── seed/
│   │   └── dehradun_segments.geojson  # Synthetic road network
│   └── feature_store/
│       └── features_v1.parquet        # Built by build_feature_store.py
│
├── models/                        # Serialized ML artifacts
│   └── rf_v1.0_20261001.joblib    # example
│
└── docs/
    ├── adr/                       # Architecture Decision Records
    │   └── 001-modular-monolith.md
    └── api/                       # Auto-generated OpenAPI export
```

### 2.1 Key Structure Decisions

- `backend/app/conflict_rules/` is a **sibling to services**, not inside it. Rules are a plugin point, not an implementation detail of a single service class.
- `ml/` is completely independent of `backend/`. The ML pipeline reads the database directly or from the Parquet feature store. It does not import FastAPI, SQLAlchemy models, or service classes.
- `scripts/` contains only thin CLI entry points; all logic is in `ml/`.
- `data/feature_store/` is the handoff point between the offline ML pipeline and the inference-time prediction service.

---

## 3. Database Design

### 3.1 Base Classes and Mixins

```python
# backend/app/models/base.py

import uuid
from datetime import datetime, UTC
from sqlalchemy import DateTime, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class SoftDeleteMixin:
    """
    Records are never hard-deleted. deleted_at is set on 'deletion'.
    All queries must filter WHERE deleted_at IS NULL unless explicitly
    requesting deleted records.
    """
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

def generate_uuid() -> str:
    return str(uuid.uuid4())
```

### 3.2 RoadSegment

```python
# backend/app/models/road_segment.py

from sqlalchemy import String, Float, Enum as SAEnum, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, generate_uuid
import enum

class RoadClass(str, enum.Enum):
    ARTERIAL = "ARTERIAL"
    COLLECTOR = "COLLECTOR"
    LOCAL = "LOCAL"

class RoadSegment(Base, TimestampMixin):
    __tablename__ = "road_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    road_class: Mapped[RoadClass] = mapped_column(SAEnum(RoadClass), nullable=False)
    # Stored as GeoJSON string; parsed by the geospatial adapter at runtime
    geometry_geojson: Mapped[str] = mapped_column(Text, nullable=False)
    length_meters: Mapped[float] = mapped_column(Float, nullable=False)
    ward: Mapped[str] = mapped_column(String(100), nullable=False)
    zone: Mapped[str] = mapped_column(String(100), nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships (back-references)
    excavation_events: Mapped[list["ExcavationEvent"]] = relationship(
        back_populates="road_segment", lazy="select"
    )
    resurfacing_events: Mapped[list["ResurfacingEvent"]] = relationship(
        back_populates="road_segment", lazy="select"
    )
    stress_indices: Mapped[list["InfrastructureStressIndex"]] = relationship(
        back_populates="road_segment", lazy="select"
    )
    risk_predictions: Mapped[list["RiskPrediction"]] = relationship(
        back_populates="road_segment", lazy="select"
    )

    __table_args__ = (
        Index("ix_road_segments_road_class", "road_class"),
        Index("ix_road_segments_zone", "zone"),
    )
```

### 3.3 UtilityProject and the Project–Segment Association Table

The relationship between projects and road segments is **many-to-many**: one project can affect multiple segments; one segment can be affected by multiple projects.

```python
# backend/app/models/utility_project.py

from sqlalchemy import String, Float, Date, Boolean, Text, Enum as SAEnum, Table, Column, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid
import enum

# Association table — no ORM class needed; pure join table
project_segment_association = Table(
    "project_segments",
    Base.metadata,
    Column("project_id", String(36), ForeignKey("utility_projects.id", ondelete="CASCADE"), primary_key=True),
    Column("segment_id", String(36), ForeignKey("road_segments.id", ondelete="CASCADE"), primary_key=True),
)

class UtilityType(str, enum.Enum):
    WATER = "WATER"
    SEWERAGE = "SEWERAGE"
    DRAINAGE = "DRAINAGE"
    ELECTRICITY = "ELECTRICITY"
    TELECOM = "TELECOM"
    GAS = "GAS"
    OTHER = "OTHER"

class ProjectStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ON_HOLD = "ON_HOLD"

class UtilityProject(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "utility_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    utility_type: Mapped[UtilityType] = mapped_column(SAEnum(UtilityType), nullable=False)
    agency: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus), nullable=False)
    planned_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    requires_excavation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requires_resurfacing: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    road_segments: Mapped[list["RoadSegment"]] = relationship(
        secondary=project_segment_association,
        backref="projects",
        lazy="select"
    )

    __table_args__ = (
        Index("ix_utility_projects_utility_type", "utility_type"),
        Index("ix_utility_projects_status", "status"),
        Index("ix_utility_projects_planned_start_date", "planned_start_date"),
        Index("ix_utility_projects_planned_end_date", "planned_end_date"),
        Index("ix_utility_projects_deleted_at", "deleted_at"),
    )
```

### 3.4 ExcavationEvent

```python
# backend/app/models/excavation_event.py

class ExcavationEvent(Base, TimestampMixin):
    __tablename__ = "excavation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    road_segment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("road_segments.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("utility_projects.id", ondelete="RESTRICT"), nullable=False
    )
    utility_type: Mapped[UtilityType] = mapped_column(SAEnum(UtilityType), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    excavation_depth_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    trench_length_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_source: Mapped[str] = mapped_column(String(255), nullable=False)

    road_segment: Mapped["RoadSegment"] = relationship(back_populates="excavation_events")
    project: Mapped["UtilityProject"] = relationship()

    __table_args__ = (
        Index("ix_excavation_events_road_segment_id", "road_segment_id"),
        Index("ix_excavation_events_start_date", "start_date"),
        Index("ix_excavation_events_utility_type", "utility_type"),
    )
```

### 3.5 ResurfacingEvent

```python
class ResurfacingEvent(Base, TimestampMixin):
    __tablename__ = "resurfacing_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    road_segment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("road_segments.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("utility_projects.id", ondelete="SET NULL"), nullable=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    resurfacing_type: Mapped[ResurfacingType] = mapped_column(SAEnum(ResurfacingType), nullable=False)
    quality_grade: Mapped[QualityGrade | None] = mapped_column(SAEnum(QualityGrade), nullable=True)
    warranty_months: Mapped[int | None] = mapped_column(nullable=True)
    contractor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_resurfacing_events_road_segment_id", "road_segment_id"),
        Index("ix_resurfacing_events_end_date", "end_date"),
    )
```

### 3.6 ConflictRecord

```python
class ConflictRecord(Base, TimestampMixin):
    __tablename__ = "conflict_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_a_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("utility_projects.id", ondelete="RESTRICT"), nullable=False
    )
    project_b_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("utility_projects.id", ondelete="RESTRICT"), nullable=False
    )
    road_segment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("road_segments.id", ondelete="RESTRICT"), nullable=False
    )
    conflict_type: Mapped[ConflictType] = mapped_column(SAEnum(ConflictType), nullable=False)
    severity: Mapped[ConflictSeverity] = mapped_column(SAEnum(ConflictSeverity), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    spatial_reason: Mapped[str] = mapped_column(Text, nullable=False)
    temporal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    excavation_involvement: Mapped[str] = mapped_column(Text, nullable=False)
    overlap_days: Mapped[int | None] = mapped_column(nullable=True)
    spatial_overlap_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    affected_corridor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detection_method: Mapped[DetectionMethod] = mapped_column(SAEnum(DetectionMethod), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ConflictStatus] = mapped_column(SAEnum(ConflictStatus), nullable=False, default="OPEN")
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_conflict_records_road_segment_id", "road_segment_id"),
        Index("ix_conflict_records_severity", "severity"),
        Index("ix_conflict_records_status", "status"),
        Index("ix_conflict_records_rule_id", "rule_id"),
        Index("ix_conflict_records_detected_at", "detected_at"),
        # Composite uniqueness: prevents duplicate (A, B, segment, rule) records
        # Note: project_a_id and project_b_id must be stored in canonical order (a < b)
        # to ensure idempotency (see Section 5.4)
        Index(
            "uq_conflict_records_canonical",
            "project_a_id", "project_b_id", "road_segment_id", "rule_id",
            unique=True
        ),
    )
```

### 3.7 RiskPrediction (Immutable)

```python
class RiskPrediction(Base):
    """
    IMMUTABLE. Never update a row. Each prediction run inserts a new record.
    The feature_snapshot JSON column enables reproduction of any past
    prediction regardless of later data changes.
    """
    __tablename__ = "risk_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    road_segment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("road_segments.id", ondelete="RESTRICT"), nullable=False
    )
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    feature_snapshot_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prediction_horizon_days: Mapped[int] = mapped_column(nullable=False, default=180)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    risk_category: Mapped[RiskCategory] = mapped_column(SAEnum(RiskCategory), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_group: Mapped[str] = mapped_column(String(50), nullable=False)  # "A", "B", "C", or "FULL"
    top_features: Mapped[str] = mapped_column(Text, nullable=False)   # JSON array
    feature_snapshot: Mapped[str] = mapped_column(Text, nullable=False)  # JSON object — full feature vector
    is_synthetic_input: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provenance: Mapped[str] = mapped_column(Text, nullable=False)  # JSON

    road_segment: Mapped["RoadSegment"] = relationship(back_populates="risk_predictions")

    __table_args__ = (
        Index("ix_risk_predictions_road_segment_id", "road_segment_id"),
        Index("ix_risk_predictions_prediction_timestamp", "prediction_timestamp"),
        Index("ix_risk_predictions_risk_category", "risk_category"),
        Index("ix_risk_predictions_model_version", "model_version"),
    )
```

### 3.8 InfrastructureStressIndex (PISI)

```python
class InfrastructureStressIndex(Base):
    __tablename__ = "infrastructure_stress_indices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    road_segment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("road_segments.id", ondelete="RESTRICT"), nullable=False
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    index_value: Mapped[float] = mapped_column(Float, nullable=False)
    index_category: Mapped[IndexCategory] = mapped_column(SAEnum(IndexCategory), nullable=False)
    component_excavation_count: Mapped[float] = mapped_column(Float, nullable=False)
    component_utility_diversity: Mapped[float] = mapped_column(Float, nullable=False)
    component_recency: Mapped[float] = mapped_column(Float, nullable=False)
    component_resurfacing_gap: Mapped[float] = mapped_column(Float, nullable=False)
    component_conflict_count: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(50), nullable=False)
    provenance: Mapped[str] = mapped_column(Text, nullable=False)  # JSON

    road_segment: Mapped["RoadSegment"] = relationship(back_populates="stress_indices")

    __table_args__ = (
        Index("ix_isi_road_segment_id", "road_segment_id"),
        Index("ix_isi_calculated_at", "calculated_at"),
        Index("ix_isi_index_category", "index_category"),
    )
```

### 3.9 CoordinationRecommendation

```python
class CoordinationRecommendation(Base, TimestampMixin):
    __tablename__ = "coordination_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    affected_projects: Mapped[str] = mapped_column(Text, nullable=False)   # JSON array of UUIDs
    affected_segment_ids: Mapped[str] = mapped_column(Text, nullable=False) # JSON array of UUIDs
    recommendation_type: Mapped[RecommendationType] = mapped_column(SAEnum(RecommendationType), nullable=False)
    priority: Mapped[RecommendationPriority] = mapped_column(SAEnum(RecommendationPriority), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)   # JSON with provenance
    estimated_avoided_excavations: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[RecommendationStatus] = mapped_column(SAEnum(RecommendationStatus), nullable=False, default="PENDING")
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance: Mapped[str] = mapped_column(Text, nullable=False)  # JSON

    __table_args__ = (
        Index("ix_recommendations_status", "status"),
        Index("ix_recommendations_priority", "priority"),
        Index("ix_recommendations_type", "recommendation_type"),
        Index("ix_recommendations_generated_at", "generated_at"),
    )
```

### 3.10 ModelMetadata (Supporting Table)

Tracks trained model artifacts — version, training parameters, feature group, training date, and evaluation report path.

```python
class ModelMetadata(Base, TimestampMixin):
    __tablename__ = "model_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_group: Mapped[str] = mapped_column(String(50), nullable=False)  # A, B, C, FULL
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    training_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    training_data_version: Mapped[str] = mapped_column(String(100), nullable=False)
    evaluation_report_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    training_seed: Mapped[int] = mapped_column(nullable=False)
    parameters: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: hyperparameters

    __table_args__ = (
        Index("ix_model_metadata_model_version", "model_version"),
        Index("ix_model_metadata_is_active", "is_active"),
    )
```

### 3.11 Foreign Key Cascade Strategy

| Relationship | On Delete Behavior | Rationale |
|---|---|---|
| ExcavationEvent → RoadSegment | RESTRICT | Never lose excavation history if a segment is somehow removed |
| ExcavationEvent → UtilityProject | RESTRICT | Excavation event cannot exist without its project |
| ResurfacingEvent → RoadSegment | RESTRICT | Same principle |
| ResurfacingEvent → UtilityProject | SET NULL | A resurfacing may be standalone (not tied to a project) |
| ConflictRecord → RoadSegment | RESTRICT | Conflicts are part of the infrastructure record |
| ConflictRecord → UtilityProject | RESTRICT | Cannot lose project context for a conflict |
| RiskPrediction → RoadSegment | RESTRICT | Predictions are immutable historical records |
| InfrastructureStressIndex → RoadSegment | RESTRICT | Historical record |
| project_segments → UtilityProject | CASCADE | Deleting a project cleans up its segment associations |
| project_segments → RoadSegment | CASCADE | Deleting a segment cleans up its project associations |

### 3.12 Soft Delete Pattern

Projects use `SoftDeleteMixin`. All repository queries on `UtilityProject` must include `WHERE deleted_at IS NULL` unless the caller explicitly passes `include_deleted=True`. A `BaseRepository.delete()` method sets `deleted_at = datetime.now(UTC)` rather than issuing a SQL DELETE.

---

## 4. Geospatial Design

### 4.1 Geometry Representation

Road segment geometries are stored as **GeoJSON LineString strings** in the `geometry_geojson` column (TEXT). This approach works identically on SQLite and PostgreSQL without requiring PostGIS extensions at the storage layer.

Coordinate system: **WGS84 (EPSG:4326)** — longitude, latitude. This is the native format for MapLibre GL JS and GeoJSON.

When the system migrates to PostgreSQL/PostGIS, `geometry_geojson` can be replaced with a native `GEOMETRY(LineString, 4326)` column. The `SpatialAdapter` interface (Section 4.3) ensures this migration is entirely internal to the geospatial module.

### 4.2 Length Calculation

Segment length is computed once at seed/import time and stored in `length_meters`. The calculation uses Shapely's `transform` to project from WGS84 to UTM Zone 44N (EPSG:32644, which covers Dehradun) before measuring length in metres.

```python
# backend/app/geospatial/utils.py

from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj

WGS84 = pyproj.CRS("EPSG:4326")
UTM_44N = pyproj.CRS("EPSG:32644")  # UTM Zone 44N — covers Dehradun

def compute_length_meters(geojson_linestring: dict) -> float:
    """
    Project a GeoJSON LineString to UTM 44N and return length in metres.
    Input: GeoJSON geometry dict (type: LineString)
    """
    geom = shape(geojson_linestring)
    project = pyproj.Transformer.from_crs(WGS84, UTM_44N, always_xy=True).transform
    projected = transform(project, geom)
    return projected.length
```

### 4.3 SpatialAdapter Interface

The `SpatialAdapter` abstract class isolates all geometric operations. v1.0 uses a `ShapelyAdapter` implementation. A future `PostGISAdapter` will implement the same interface using PostGIS ST_ functions.

```python
# backend/app/geospatial/adapter.py

from abc import ABC, abstractmethod

class SpatialAdapter(ABC):

    @abstractmethod
    def segments_share_geometry(
        self,
        geom_a: str,   # GeoJSON string
        geom_b: str,
    ) -> bool:
        """
        v1.0 rule: two segments share geometry if they are the same segment_id.
        Future: return True if geometries intersect or are within buffer_meters.
        """
        ...

    @abstractmethod
    def compute_length_meters(self, geojson_linestring: dict) -> float:
        ...

    @abstractmethod
    def geojson_to_feature(self, segment) -> dict:
        """Convert a RoadSegment ORM object to a GeoJSON Feature dict."""
        ...

    @abstractmethod
    def segments_to_feature_collection(self, segments: list) -> dict:
        """Convert a list of RoadSegment objects to a GeoJSON FeatureCollection."""
        ...
```

```python
# backend/app/geospatial/shapely_adapter.py

class ShapelyAdapter(SpatialAdapter):

    def segments_share_geometry(self, geom_a: str, geom_b: str) -> bool:
        """
        v1.0: Spatial overlap is determined entirely by shared segment_id,
        NOT by geometry intersection. This method is provided for future use
        and currently raises NotImplementedError if called with different
        geometries that are not identical strings.
        The conflict engine uses segment_id matching directly in v1.0.
        """
        return geom_a == geom_b  # placeholder for v1.0

    def compute_length_meters(self, geojson_linestring: dict) -> float:
        return compute_length_meters(geojson_linestring)

    def geojson_to_feature(self, segment, latest_risk=None, latest_pisi=None) -> dict:
        """
        Convert a RoadSegment to a GeoJSON Feature.
        `latest_risk` and `latest_pisi` are optional pre-fetched records.
        They must be included when serving the /segments/geojson endpoint
        so that MapLibre layer paint expressions can color segments by
        risk_category and pisi_category without a separate API call.
        """
        import json
        properties = {
            "name": segment.name,
            "road_class": segment.road_class.value,
            "ward": segment.ward,
            "zone": segment.zone,
            "length_meters": segment.length_meters,
            "is_synthetic": segment.is_synthetic,
            # Overlay data — null if no prediction/PISI exists yet
            "risk_category": latest_risk.risk_category.value if latest_risk else None,
            "pisi_category": latest_pisi.index_category.value if latest_pisi else None,
            "pisi_value": latest_pisi.index_value if latest_pisi else None,
        }
        return {
            "type": "Feature",
            "id": segment.id,
            "geometry": json.loads(segment.geometry_geojson),
            "properties": properties,
        }

    def segments_to_feature_collection(self, segments: list) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [self.geojson_to_feature(s) for s in segments]
        }
```

### 4.4 Pluggable Spatial Rule Interface (Future-Ready)

The conflict engine in v1.0 uses `segment_id` matching. Future proximity-based rules will need geometric operations. The design already supports this via the `SpatialAdapter` injection point:

```python
# In ConflictEngine.__init__:
self.spatial_adapter: SpatialAdapter = spatial_adapter  # injected

# Future rule PROXIMITY_BUFFER_05 will call:
# self.spatial_adapter.segments_within_distance(geom_a, geom_b, buffer_meters)
# This method does not exist yet — it will be added to the interface when implemented.
```

---

## 5. Conflict Engine

### 5.1 Architecture: Registered Rule Pipeline

The conflict engine is a **pipeline of independently registered rules**. Each rule is a class that implements `AbstractConflictRule`. The `ConflictRuleRegistry` manages the active set of rules and routes project pairs through them.

```python
# backend/app/conflict_rules/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ConflictResult:
    """
    Returned by a rule's evaluate() method.
    None means no conflict detected by this rule.
    """
    rule_id: str
    conflict_type: str           # SPATIAL_OVERLAP | TEMPORAL_OVERLAP | SPATIAL_TEMPORAL
    severity: str                # HIGH | MEDIUM | LOW
    spatial_reason: str
    temporal_reason: Optional[str]
    excavation_involvement: str
    overlap_days: Optional[int]
    spatial_overlap_meters: Optional[float]
    affected_corridor: Optional[str]
    detection_method: str        # RULE_BASED | ML_ASSISTED


class AbstractConflictRule(ABC):
    """
    Every conflict detection rule must implement this interface.
    A rule is responsible for exactly one type of conflict detection.
    Rules must be stateless — no instance variables mutated between calls.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier e.g. 'SPATIAL_TEMPORAL_EXCAVATION_01'"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this rule detects."""
        ...

    @abstractmethod
    def is_applicable(
        self,
        project_a,          # UtilityProject ORM object
        project_b,          # UtilityProject ORM object
        shared_segments,    # list of segment_ids shared by both projects
        temporal_buffer_days: int,
    ) -> bool:
        """
        Fast pre-check. If False, evaluate() will not be called.
        Use this to short-circuit rules that clearly don't apply
        (e.g., if neither project requires excavation, skip excavation rules).
        """
        ...

    @abstractmethod
    def evaluate(
        self,
        project_a,
        project_b,
        shared_segments,
        segment_map: dict,  # segment_id -> RoadSegment
        temporal_buffer_days: int,
    ) -> Optional[ConflictResult]:
        """
        Evaluate the rule. Return ConflictResult if conflict detected, None otherwise.
        Must be idempotent: same inputs → same output.
        Must not perform any database writes.
        """
        ...
```

### 5.2 Rule Registry

```python
# backend/app/conflict_rules/registry.py

class ConflictRuleRegistry:
    """
    Maintains the ordered list of active conflict rules.
    Rules are evaluated in registration order.
    A project pair may produce at most one ConflictResult per rule_id per shared segment.
    """

    def __init__(self):
        self._rules: list[AbstractConflictRule] = []

    def register(self, rule: AbstractConflictRule) -> None:
        if any(r.rule_id == rule.rule_id for r in self._rules):
            raise ValueError(f"Rule '{rule.rule_id}' is already registered.")
        self._rules.append(rule)

    def get_rules(self) -> list[AbstractConflictRule]:
        return list(self._rules)

    def get_rule(self, rule_id: str) -> AbstractConflictRule:
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return rule
        raise KeyError(f"Rule '{rule_id}' not registered.")


# Default registry — instantiated at application startup
def build_default_registry() -> ConflictRuleRegistry:
    from app.conflict_rules.spatial_only import SpatialOnlyRule
    from app.conflict_rules.temporal_proximity import TemporalProximityRule
    from app.conflict_rules.spatial_temporal_excavation import SpatialTemporalExcavationRule
    from app.conflict_rules.spatial_temporal_mixed import SpatialTemporalMixedRule

    registry = ConflictRuleRegistry()
    registry.register(SpatialTemporalExcavationRule())  # Highest priority first
    registry.register(SpatialTemporalMixedRule())
    registry.register(SpatialOnlyRule())
    registry.register(TemporalProximityRule())
    return registry
```

### 5.3 V1.0 Rule Implementations

#### SPATIAL_TEMPORAL_EXCAVATION_01 (HIGH)

```python
# backend/app/conflict_rules/spatial_temporal_excavation.py

class SpatialTemporalExcavationRule(AbstractConflictRule):
    rule_id = "SPATIAL_TEMPORAL_EXCAVATION_01"
    description = (
        "Both projects share at least one road segment, their planned date ranges "
        "overlap or fall within the temporal buffer window, and BOTH require excavation."
    )

    def is_applicable(self, project_a, project_b, shared_segments, temporal_buffer_days):
        return (
            len(shared_segments) > 0
            and project_a.requires_excavation
            and project_b.requires_excavation
        )

    def evaluate(self, project_a, project_b, shared_segments, segment_map, temporal_buffer_days):
        overlap_days = _compute_overlap_days(
            project_a.planned_start_date, project_a.planned_end_date,
            project_b.planned_start_date, project_b.planned_end_date,
            buffer_days=temporal_buffer_days
        )
        if overlap_days is None:
            return None  # No temporal overlap even with buffer

        segment = segment_map[shared_segments[0]]
        return ConflictResult(
            rule_id=self.rule_id,
            conflict_type="SPATIAL_TEMPORAL",
            severity="HIGH",
            spatial_reason=(
                f"Project '{project_a.name}' ({project_a.utility_type.value}) and "
                f"Project '{project_b.name}' ({project_b.utility_type.value}) "
                f"both affect {segment.name} (zone: {segment.zone}, {segment.road_class.value})."
            ),
            temporal_reason=(
                f"Project A runs {project_a.planned_start_date}–{project_a.planned_end_date}; "
                f"Project B runs {project_b.planned_start_date}–{project_b.planned_end_date}. "
                f"Excavation windows overlap by {overlap_days} day(s)."
            ),
            excavation_involvement="Both projects require excavation.",
            overlap_days=overlap_days,
            spatial_overlap_meters=segment.length_meters,
            affected_corridor=f"{segment.name} ({segment.zone})",
            detection_method="RULE_BASED",
        )
```

#### Overlap Calculation Helper

```python
def _compute_overlap_days(
    start_a, end_a, start_b, end_b, buffer_days: int
) -> int | None:
    """
    Returns the number of days of overlap between two date ranges,
    extended by buffer_days on each side.
    Returns None if no overlap even with buffer.
    A return value of 0 means the ranges are within the buffer window
    but do not literally overlap.
    """
    buffered_start_a = start_a - timedelta(days=buffer_days)
    buffered_end_a = end_a + timedelta(days=buffer_days)

    latest_start = max(start_b, buffered_start_a)
    earliest_end = min(end_b, buffered_end_a)

    if latest_start > earliest_end:
        return None  # No overlap

    # Count actual (non-buffered) literal overlap
    actual_latest_start = max(start_a, start_b)
    actual_earliest_end = min(end_a, end_b)
    if actual_latest_start <= actual_earliest_end:
        return (actual_earliest_end - actual_latest_start).days
    return 0  # Within buffer but no literal overlap
```

#### SPATIAL_TEMPORAL_MIXED_02 (MEDIUM), SPATIAL_ONLY_03 (LOW), TEMPORAL_PROXIMITY_04 (LOW)

These follow the same pattern as above, with appropriate `is_applicable` guards and `ConflictResult` construction. They are not shown in full here to avoid repetition, but each lives in its own file.

### 5.4 ConflictEngine Service

```python
# backend/app/services/conflict_engine.py

class ConflictEngine:
    """
    Orchestrates conflict detection across all registered rules.
    Idempotent: running on the same data twice produces the same set of conflicts.
    """

    def __init__(
        self,
        registry: ConflictRuleRegistry,
        conflict_repo: ConflictRepository,
        project_repo: ProjectRepository,
        segment_repo: SegmentRepository,
        temporal_buffer_days: int = 30,
    ):
        self.registry = registry
        self.conflict_repo = conflict_repo
        self.project_repo = project_repo
        self.segment_repo = segment_repo
        self.temporal_buffer_days = temporal_buffer_days

    async def detect_all(self, db: AsyncSession) -> list[ConflictRecord]:
        """
        Run all rules against all non-deleted project pairs.
        Returns newly created ConflictRecord objects.
        Idempotency: before inserting, check if a record with the same
        (canonical project pair, segment_id, rule_id) already exists.
        """
        projects = await self.project_repo.get_all_active(db)
        segments_map = await self.segment_repo.get_all_as_map(db)
        results = []

        for i, proj_a in enumerate(projects):
            for proj_b in projects[i+1:]:
                shared_segment_ids = self._find_shared_segments(proj_a, proj_b)
                if not shared_segment_ids:
                    continue

                for rule in self.registry.get_rules():
                    if not rule.is_applicable(
                        proj_a, proj_b, shared_segment_ids, self.temporal_buffer_days
                    ):
                        continue

                    conflict_result = rule.evaluate(
                        proj_a, proj_b, shared_segment_ids,
                        segments_map, self.temporal_buffer_days
                    )
                    if conflict_result is None:
                        continue

                    # Canonical ordering: always store lower UUID first
                    canon_a, canon_b = sorted([proj_a.id, proj_b.id])

                    existing = await self.conflict_repo.find_by_canonical(
                        db, canon_a, canon_b,
                        shared_segment_ids[0],
                        conflict_result.rule_id
                    )
                    if existing:
                        continue  # Already recorded — idempotency

                    record = await self.conflict_repo.create(
                        db,
                        project_a_id=canon_a,
                        project_b_id=canon_b,
                        road_segment_id=shared_segment_ids[0],
                        **conflict_result.__dict__,
                        detected_at=datetime.now(UTC),
                        status="OPEN",
                    )
                    results.append(record)

        return results

    def _find_shared_segments(self, proj_a, proj_b) -> list[str]:
        seg_ids_a = {s.id for s in proj_a.road_segments}
        seg_ids_b = {s.id for s in proj_b.road_segments}
        return list(seg_ids_a & seg_ids_b)

    async def detect_for_project(
        self, db: AsyncSession, project_id: str
    ) -> list[ConflictRecord]:
        """Run detection for a specific project's affected segments only."""
        ...
```

### 5.5 Idempotency Guarantee

Idempotency is achieved through three mechanisms:

1. **Canonical project ordering**: `project_a_id` is always the lexicographically smaller UUID. This ensures that (A, B) and (B, A) are treated as identical.
2. **Unique index**: `(project_a_id, project_b_id, road_segment_id, rule_id)` has a UNIQUE constraint.
3. **Pre-insert check**: `conflict_repo.find_by_canonical()` checks for existing OPEN records before inserting. If found, the insert is skipped.

---

## 6. Project Collision Simulation

### 6.1 Design Principle

The collision simulator reuses the exact same `ConflictRuleRegistry` and rule implementations as the `ConflictEngine`. It is not a separate conflict system. The only difference is that the hypothetical project is never written to the database.

### 6.2 HypotheticalProject Schema

```python
# backend/app/schemas/conflict.py

class HypotheticalProjectRequest(BaseModel):
    """
    Represents a project that does not yet exist in the database.
    Used for collision simulation only. No ID is assigned.
    """
    name: str
    utility_type: UtilityType
    agency: str
    planned_start_date: date
    planned_end_date: date
    requires_excavation: bool
    requires_resurfacing: bool
    affected_segment_ids: list[str]  # Must be valid existing segment IDs

    @model_validator(mode="after")
    def end_after_start(self) -> "HypotheticalProjectRequest":
        if self.planned_end_date <= self.planned_start_date:
            raise ValueError("planned_end_date must be after planned_start_date")
        return self
```

### 6.3 Collision Simulator Flow

```python
# backend/app/services/collision_simulator.py

class CollisionSimulator:
    """
    Runs the conflict rule pipeline against a hypothetical (unsaved) project.
    ZERO database writes. All operations are read + compute.
    """

    def __init__(
        self,
        registry: ConflictRuleRegistry,
        project_repo: ProjectRepository,
        segment_repo: SegmentRepository,
        prediction_repo: PredictionRepository,
        stress_index_repo: StressIndexRepository,
        temporal_buffer_days: int = 30,
    ):
        ...

    async def simulate(
        self,
        db: AsyncSession,
        hypothetical: HypotheticalProjectRequest,
    ) -> CollisionSimulationResult:
        """
        1. Build a transient UtilityProject-like object (not an ORM model,
           just a dataclass) from HypotheticalProjectRequest.
        2. Load all existing non-deleted projects that share any of the
           hypothetical project's segment IDs.
        3. Run every applicable rule from the registry against each
           (existing_project, hypothetical_project) pair.
        4. For each affected segment, attach current PISI and risk prediction.
        5. Return CollisionSimulationResult — no DB writes at any point.
        """
        segments = await self.segment_repo.get_by_ids(
            db, hypothetical.affected_segment_ids
        )
        existing_projects = await self.project_repo.get_projects_for_segments(
            db, hypothetical.affected_segment_ids
        )

        # Build transient project object
        hyp_project = _build_transient_project(hypothetical)
        segment_map = {s.id: s for s in segments}

        collision_items = []
        for existing in existing_projects:
            shared = list(
                set(hypothetical.affected_segment_ids)
                & {s.id for s in existing.road_segments}
            )
            if not shared:
                continue

            for rule in self.registry.get_rules():
                if not rule.is_applicable(
                    existing, hyp_project, shared, self.temporal_buffer_days
                ):
                    continue
                result = rule.evaluate(
                    existing, hyp_project, shared, segment_map,
                    self.temporal_buffer_days
                )
                if result:
                    # Attach PISI + risk for affected segment
                    seg_id = shared[0]
                    pisi = await self.stress_index_repo.get_latest(db, seg_id)
                    risk = await self.prediction_repo.get_latest(db, seg_id)
                    collision_items.append(CollisionItem(
                        conflicting_project=existing,
                        affected_segment_id=seg_id,
                        conflict_result=result,
                        segment_pisi=pisi,
                        segment_risk=risk,
                    ))

        return CollisionSimulationResult(
            hypothetical_project=hypothetical,
            collisions=collision_items,
            simulation_label="Simulation — Not a Confirmed Conflict. The hypothetical project has not been saved.",
            provenance=ProvenanceService.build(
                evidence_sources=["SIMULATION"],
                calculation_method="conflict_rule_pipeline_v1",
                is_synthetic=True,
            ),
        )
```

### 6.4 Zero-Write Guarantee

The `CollisionSimulator.simulate()` method:
- Never calls `db.add()`, `db.flush()`, `db.commit()`, or any repository write method.
- Uses only `SELECT` queries through read-only repository methods.
- Returns a Pydantic response model, not a SQLAlchemy ORM object.
- The API endpoint `POST /api/v1/conflicts/simulate` does not call `db.commit()`.

A test invariant (TEST-UNIT-07) verifies this by counting database rows before and after the simulation call.

---

## 7. Road Memory

### 7.1 Purpose

Road Memory is a chronological, unified view of everything that has happened to a road segment: excavations, resurfacings, and project lifecycle milestones. It is not a separate database table — it is a **query-time assembly** of records from `excavation_events`, `resurfacing_events`, and `utility_projects`.

### 7.2 Event Normalization

All event types are normalized into a single `TimelineEvent` schema before being returned. This prevents the frontend from needing to understand three different data shapes.

```python
# backend/app/services/road_memory.py

from dataclasses import dataclass
from datetime import date
from typing import Literal

@dataclass
class TimelineEvent:
    event_type: Literal["EXCAVATION", "RESURFACING", "PROJECT_START", "PROJECT_END"]
    start_date: date
    end_date: date | None
    project_id: str | None
    project_name: str | None
    utility_type: str | None
    agency: str | None
    notes: str
    is_synthetic: bool
    data_source: str
    provenance_category: str  # "SYNTHETIC_HISTORICAL_EVENT" | "SYNTHETIC_PROJECT"
    # Warning flags — computed during assembly
    is_warranty_breach: bool = False
    is_frequent_excavation_window: bool = False
    is_premature_excavation: bool = False
```

### 7.3 Query Strategy

```python
class RoadMemoryService:
    """
    Assembles the Road Memory timeline for a given road segment.
    All data is fetched in three queries, then merged and sorted in Python.
    No JOIN spanning all three tables — too many nullable columns make
    a single SQL JOIN harder to read and maintain.
    """

    def __init__(
        self,
        excavation_repo: ExcavationRepository,
        resurfacing_repo: ResurfacingRepository,
        project_repo: ProjectRepository,
    ):
        ...

    async def get_timeline(
        self,
        db: AsyncSession,
        segment_id: str,
        event_type_filter: list[str] | None = None,
        start_date_filter: date | None = None,
        end_date_filter: date | None = None,
    ) -> list[TimelineEvent]:
        """
        1. Fetch all ExcavationEvents for segment_id.
        2. Fetch all ResurfacingEvents for segment_id.
        3. Fetch all UtilityProjects associated with segment_id
           (via project_segments association table).
        4. Normalize each to TimelineEvent.
        5. Merge and sort by start_date ascending.
        6. Apply warning flags (see Section 7.4).
        7. Apply optional filters.
        """
        excavations = await self.excavation_repo.get_by_segment(db, segment_id)
        resurfacings = await self.resurfacing_repo.get_by_segment(db, segment_id)
        projects = await self.project_repo.get_by_segment(db, segment_id)

        events: list[TimelineEvent] = []

        for exc in excavations:
            events.append(TimelineEvent(
                event_type="EXCAVATION",
                start_date=exc.start_date,
                end_date=exc.end_date,
                project_id=exc.project_id,
                project_name=exc.project.name if exc.project else None,
                utility_type=exc.utility_type.value,
                agency=exc.project.agency if exc.project else None,
                notes=exc.notes,
                is_synthetic=exc.is_synthetic,
                data_source=exc.data_source,
                provenance_category="SYNTHETIC_HISTORICAL_EVENT",
            ))

        for res in resurfacings:
            events.append(TimelineEvent(
                event_type="RESURFACING",
                start_date=res.start_date,
                end_date=res.end_date,
                project_id=res.project_id,
                project_name=res.project.name if res.project else None,
                utility_type=None,
                agency=res.project.agency if res.project else None,
                notes=f"{res.resurfacing_type.value}, warranty={res.warranty_months}mo",
                is_synthetic=res.is_synthetic,
                data_source="synthetic_resurfacing",
                provenance_category="SYNTHETIC_HISTORICAL_EVENT",
            ))

        for proj in projects:
            events.append(TimelineEvent(
                event_type="PROJECT_START",
                start_date=proj.planned_start_date,
                end_date=None,
                project_id=proj.id,
                project_name=proj.name,
                utility_type=proj.utility_type.value,
                agency=proj.agency,
                notes=proj.description,
                is_synthetic=proj.is_synthetic,
                data_source="synthetic_project",
                provenance_category="SYNTHETIC_PROJECT",
            ))
            events.append(TimelineEvent(
                event_type="PROJECT_END",
                start_date=proj.planned_end_date,
                end_date=None,
                project_id=proj.id,
                project_name=proj.name,
                utility_type=proj.utility_type.value,
                agency=proj.agency,
                notes="",
                is_synthetic=proj.is_synthetic,
                data_source="synthetic_project",
                provenance_category="SYNTHETIC_PROJECT",
            ))

        events.sort(key=lambda e: e.start_date)
        events = self._apply_warning_flags(events)

        # Apply filters
        if event_type_filter:
            events = [e for e in events if e.event_type in event_type_filter]
        if start_date_filter:
            events = [e for e in events if e.start_date >= start_date_filter]
        if end_date_filter:
            events = [e for e in events if e.start_date <= end_date_filter]

        return events
```

### 7.4 Warning Flag Logic

Warning flags are computed in a single pass over the sorted event list.

```python
    def _apply_warning_flags(self, events: list[TimelineEvent]) -> list[TimelineEvent]:
        """
        Rules applied in order after events are sorted chronologically:

        1. WARRANTY_BREACH: An EXCAVATION event whose start_date falls within
           the warranty period of the most recent preceding RESURFACING event.
           warranty_expiry = resurfacing.end_date + timedelta(days=warranty_months * 30)

        2. FREQUENT_EXCAVATION: Any EXCAVATION event that is part of a window
           where 3+ excavations fall within any rolling 24-month window.
           Mark ALL excavations in such a window with is_frequent_excavation_window=True.

        3. PREMATURE_EXCAVATION: An EXCAVATION event whose start_date is less
           than 90 days after the end_date of the most recent preceding RESURFACING.
        """
        # Track last resurfacing for warranty/premature checks
        last_resurfacing_end: date | None = None
        last_warranty_months: int | None = None

        excavation_dates = [
            e.start_date for e in events if e.event_type == "EXCAVATION"
        ]

        for event in events:
            if event.event_type == "RESURFACING" and event.end_date:
                last_resurfacing_end = event.end_date
                # Extract warranty_months from notes (stored as "FULL, warranty=12mo")
                last_warranty_months = _parse_warranty_months(event.notes)

            if event.event_type == "EXCAVATION":
                # Warranty breach check
                if last_resurfacing_end and last_warranty_months:
                    warranty_expiry = last_resurfacing_end + timedelta(
                        days=last_warranty_months * 30
                    )
                    if event.start_date <= warranty_expiry:
                        event.is_warranty_breach = True

                # Premature excavation check
                if last_resurfacing_end:
                    gap_days = (event.start_date - last_resurfacing_end).days
                    if 0 < gap_days < 90:
                        event.is_premature_excavation = True

        # Frequent excavation: rolling 24-month window
        for i, event in enumerate(events):
            if event.event_type != "EXCAVATION":
                continue
            window_count = sum(
                1 for d in excavation_dates
                if 0 <= (event.start_date - d).days <= 730
            )
            if window_count >= 3:
                event.is_frequent_excavation_window = True

        return events
```

### 7.5 JSON Export Format

The API endpoint `GET /api/v1/segments/{id}/memory` returns the full timeline. The export format:

```json
{
  "segment": {
    "id": "...",
    "name": "Rajpur Road – Segment 3",
    "road_class": "ARTERIAL",
    "ward": "...",
    "zone": "Rajpur",
    "is_synthetic": true
  },
  "events": [
    {
      "event_type": "EXCAVATION",
      "start_date": "2022-03-01",
      "end_date": "2022-03-20",
      "project_name": "Water Main Phase 2",
      "utility_type": "WATER",
      "agency": "Jal Sansthan",
      "notes": "",
      "is_synthetic": true,
      "data_source": "synthetic_v1",
      "provenance_category": "SYNTHETIC_HISTORICAL_EVENT",
      "is_warranty_breach": false,
      "is_frequent_excavation_window": true,
      "is_premature_excavation": false
    }
  ],
  "summary": {
    "total_excavations": 4,
    "total_resurfacings": 2,
    "excavations_last_24m": 2,
    "warranty_breaches": 1,
    "frequent_excavation_windows": 1
  },
  "provenance": { ... }
}
```

---

## 8. PipeWatch Infrastructure Stress Index (PISI)

### 8.1 Calculator Design

The PISI calculator is a pure-function service — given the inputs, it deterministically produces the same output. It has no database access; it receives pre-fetched data.

```python
# backend/app/services/pisi_calculator.py

from dataclasses import dataclass

FORMULA_VERSION = "v1.0"

WEIGHTS = {
    "excavation_count": 0.30,
    "utility_diversity": 0.20,
    "recency": 0.20,
    "resurfacing_gap": 0.15,
    "conflict_count": 0.15,
}
# Assertion at module load time:
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "PISI weights must sum to 1.0"

@dataclass
class PISIComponents:
    excavation_count_norm: float   # [0, 100]
    utility_diversity_norm: float  # [0, 100]
    recency_penalty: float         # [0, 100]
    resurfacing_gap_penalty: float # [0, 100]
    conflict_count_norm: float     # [0, 100]

@dataclass
class PISIResult:
    index_value: float             # [0, 100]
    index_category: str            # CRITICAL | HIGH | MEDIUM | LOW
    components: PISIComponents
    formula_version: str

class PISICalculator:
    """
    Deterministic. No I/O. All inputs are passed explicitly.
    """

    def calculate(
        self,
        excavation_count_24m: int,
        distinct_utility_count: int,
        days_since_last_excavation: float,   # float; may be large if no recent event
        days_since_last_resurfacing: float,
        historical_conflict_count: int,
        warranty_breach: bool,
    ) -> PISIResult:

        components = PISIComponents(
            excavation_count_norm=self._excavation_count_norm(excavation_count_24m),
            utility_diversity_norm=self._utility_diversity_norm(distinct_utility_count),
            recency_penalty=self._recency_penalty(days_since_last_excavation),
            resurfacing_gap_penalty=self._resurfacing_gap_penalty(
                days_since_last_resurfacing, warranty_breach
            ),
            conflict_count_norm=self._conflict_count_norm(historical_conflict_count),
        )

        index_value = (
            WEIGHTS["excavation_count"]  * components.excavation_count_norm
            + WEIGHTS["utility_diversity"] * components.utility_diversity_norm
            + WEIGHTS["recency"]           * components.recency_penalty
            + WEIGHTS["resurfacing_gap"]   * components.resurfacing_gap_penalty
            + WEIGHTS["conflict_count"]    * components.conflict_count_norm
        )
        # Clamp to [0, 100] — floating-point safety
        index_value = max(0.0, min(100.0, index_value))

        return PISIResult(
            index_value=round(index_value, 4),
            index_category=self._categorize(index_value),
            components=components,
            formula_version=FORMULA_VERSION,
        )

    # --- Component functions (each returns float in [0, 100]) ---

    def _excavation_count_norm(self, count: int) -> float:
        return min(count / 5.0, 1.0) * 100.0

    def _utility_diversity_norm(self, count: int) -> float:
        return min(count / 4.0, 1.0) * 100.0

    def _recency_penalty(self, days: float) -> float:
        return max(0.0, 100.0 - (days / 2.0))

    def _resurfacing_gap_penalty(self, days: float, warranty_breach: bool) -> float:
        if warranty_breach:
            return 100.0
        return 100.0 - min(days / 365.0, 1.0) * 100.0

    def _conflict_count_norm(self, count: int) -> float:
        return min(count / 3.0, 1.0) * 100.0

    def _categorize(self, value: float) -> str:
        if value >= 75.0:
            return "CRITICAL"
        elif value >= 50.0:
            return "HIGH"
        elif value >= 25.0:
            return "MEDIUM"
        return "LOW"
```

### 8.2 PISI Service (Orchestration)

```python
# Used by the API and batch recalculation endpoint

class PISIService:
    def __init__(
        self,
        calculator: PISICalculator,
        segment_repo: SegmentRepository,
        excavation_repo: ExcavationRepository,
        resurfacing_repo: ResurfacingRepository,
        conflict_repo: ConflictRepository,
        stress_index_repo: StressIndexRepository,
        provenance_service: ProvenanceService,
    ):
        ...

    async def calculate_for_segment(
        self, db: AsyncSession, segment_id: str
    ) -> InfrastructureStressIndex:
        """
        1. Gather required input statistics from repositories.
        2. Call PISICalculator.calculate() — pure function, no I/O.
        3. Persist the result as a new InfrastructureStressIndex record.
        4. Return the record.
        """
        now = datetime.now(UTC)

        excavation_count_24m = await self.excavation_repo.count_in_window(
            db, segment_id, days=730
        )
        distinct_utility_count = await self.excavation_repo.count_distinct_utilities(
            db, segment_id
        )
        days_since_exc = await self.excavation_repo.days_since_last(db, segment_id, now)
        days_since_res, warranty_breach = await self.resurfacing_repo.days_since_last_and_warranty(
            db, segment_id, now
        )
        conflict_count = await self.conflict_repo.count_for_segment(db, segment_id)

        result = self.calculator.calculate(
            excavation_count_24m=excavation_count_24m,
            distinct_utility_count=distinct_utility_count,
            days_since_last_excavation=days_since_exc,
            days_since_last_resurfacing=days_since_res,
            historical_conflict_count=conflict_count,
            warranty_breach=warranty_breach,
        )

        provenance = self.provenance_service.build(
            evidence_sources=["DETERMINISTIC_CALCULATION"],
            calculation_method=f"PISI-{FORMULA_VERSION}",
            input_data_timestamps={"calculated_at": now.isoformat()},
            is_synthetic=True,
        )

        record = await self.stress_index_repo.create(
            db,
            road_segment_id=segment_id,
            calculated_at=now,
            index_value=result.index_value,
            index_category=result.index_category,
            component_excavation_count=result.components.excavation_count_norm,
            component_utility_diversity=result.components.utility_diversity_norm,
            component_recency=result.components.recency_penalty,
            component_resurfacing_gap=result.components.resurfacing_gap_penalty,
            component_conflict_count=result.components.conflict_count_norm,
            formula_version=result.formula_version,
            provenance=provenance.model_dump_json(),
        )
        return record
```

### 8.3 Formula Versioning

`FORMULA_VERSION = "v1.0"` is a module-level constant. If the formula changes, bump this string. Old records retain their `formula_version` for auditability. The UI "How is this calculated?" section reads `formula_version` from the API response and renders the corresponding formula documentation.

---

## 9. ML Data Pipeline

### 9.1 Pipeline Overview

The ML pipeline is entirely **offline** — it runs as standalone scripts before the API starts. The API's `PredictionService` loads the trained artifact at startup and serves predictions on demand.

```
generate_synthetic_data.py
        │
        ▼
[SQLite DB: road_segments, utility_projects,
 excavation_events, resurfacing_events]
        │
        ▼
build_feature_store.py
        │  Point-in-time feature construction (leakage-safe)
        ▼
[data/feature_store/features_v1.parquet]
        │
        ▼
train_model.py
        │  Temporal split → fit → serialize
        ▼
[models/rf_v1.0_20261001.joblib]
[ml/evaluation/eval_report_rf_v1.0.json]
        │
        ▼
evaluate_model.py
        │  Backtesting folds, ablation, calibration
        ▼
[ml/evaluation/backtest_report_rf_v1.0.json]
[ml/evaluation/ablation_report_rf_v1.0.json]
```

### 9.2 Point-in-Time Feature Construction

The critical design: for each (segment, snapshot_date) pair, features are computed using **only data with timestamps strictly before snapshot_date**, and the target is whether any `ExcavationEvent.start_date > snapshot_date` and `≤ snapshot_date + horizon_days`.

```python
# ml/features/builder.py

class PointInTimeFeatureBuilder:
    """
    Constructs a feature vector for a road segment at a given snapshot timestamp.
    Enforces the leakage contract: no feature may use data from >= snapshot_ts.
    """

    def __init__(self, validator: "LeakageValidator"):
        self.validator = validator

    def build(
        self,
        segment_id: str,
        snapshot_ts: datetime,
        excavations: pd.DataFrame,      # all excavations for this segment
        resurfacings: pd.DataFrame,     # all resurfacings for this segment
        projects: pd.DataFrame,         # all projects associated with this segment
        conflicts: pd.DataFrame,        # all conflicts for this segment
        segment_meta: dict,             # road_class, length_meters
        prediction_horizon_days: int = 180,
    ) -> dict:
        """
        Returns a dict of feature_name -> value.
        Raises LeakageError if any data row has timestamp >= snapshot_ts.
        """
        # Filter to only pre-snapshot data
        exc_pre = excavations[excavations["start_date"] < snapshot_ts.date()]
        res_pre = resurfacings[resurfacings["end_date"] < snapshot_ts.date()]
        # Projects: only those created (or started) before snapshot_ts
        proj_pre = projects[projects["created_at"] < snapshot_ts]
        conf_pre = conflicts[conflicts["detected_at"] < snapshot_ts]

        # Run leakage validation
        self.validator.assert_no_future_data(exc_pre, snapshot_ts, "start_date")
        self.validator.assert_no_future_data(res_pre, snapshot_ts, "end_date")

        features = {}

        # excavation_count_all_time
        # Timestamp basis: start_date < snapshot_ts
        features["excavation_count_all_time"] = len(exc_pre)

        # excavation_count_24m
        # Timestamp basis: start_date in [snapshot_ts - 730d, snapshot_ts)
        window_24m = snapshot_ts.date() - timedelta(days=730)
        features["excavation_count_24m"] = len(
            exc_pre[exc_pre["start_date"] >= window_24m]
        )

        # excavation_count_12m
        window_12m = snapshot_ts.date() - timedelta(days=365)
        features["excavation_count_12m"] = len(
            exc_pre[exc_pre["start_date"] >= window_12m]
        )

        # days_since_last_excavation
        # Timestamp basis: most recent start_date < snapshot_ts
        if len(exc_pre) > 0:
            last_exc_date = exc_pre["start_date"].max()
            features["days_since_last_excavation"] = (
                snapshot_ts.date() - last_exc_date
            ).days
        else:
            features["days_since_last_excavation"] = 9999  # sentinel: never excavated

        # days_since_last_resurfacing
        if len(res_pre) > 0:
            last_res_date = res_pre["end_date"].max()
            features["days_since_last_resurfacing"] = (
                snapshot_ts.date() - last_res_date
            ).days
        else:
            features["days_since_last_resurfacing"] = 9999

        # distinct_utility_count
        features["distinct_utility_count"] = exc_pre["utility_type"].nunique()

        # active_project_count
        # Projects active AT snapshot_ts, created BEFORE snapshot_ts
        # Timestamp basis: planned_start_date <= snapshot_ts.date() <= planned_end_date
        #                  AND created_at < snapshot_ts
        active = proj_pre[
            (proj_pre["planned_start_date"] <= snapshot_ts.date())
            & (proj_pre["planned_end_date"] >= snapshot_ts.date())
        ]
        features["active_project_count"] = len(active)

        # historical_conflict_count
        # Timestamp basis: detected_at < snapshot_ts
        features["historical_conflict_count"] = len(conf_pre)

        # road_class_encoded
        road_class_map = {"ARTERIAL": 2, "COLLECTOR": 1, "LOCAL": 0}
        features["road_class_encoded"] = road_class_map.get(
            segment_meta["road_class"], 0
        )

        # segment_length_normalized
        # Normalize by max segment length in dataset (computed globally before calling)
        features["segment_length_normalized"] = segment_meta["length_normalized"]

        # project_density_per_km
        proj_24m = proj_pre[
            proj_pre["planned_start_date"] >= window_24m
        ]
        km = segment_meta["length_meters"] / 1000.0
        features["project_density_per_km"] = (
            len(proj_24m) / km if km > 0 else 0.0
        )

        # resurfacing_within_warranty
        features["resurfacing_within_warranty"] = self._check_warranty(
            res_pre, snapshot_ts
        )

        return features

    def _check_warranty(self, res_pre: pd.DataFrame, snapshot_ts: datetime) -> int:
        """Returns 1 if the most recent resurfacing's warranty is still active at snapshot_ts."""
        if len(res_pre) == 0:
            return 0
        latest = res_pre.loc[res_pre["end_date"].idxmax()]
        if pd.isna(latest["warranty_months"]) or latest["warranty_months"] is None:
            return 0
        expiry = latest["end_date"] + timedelta(days=int(latest["warranty_months"]) * 30)
        return 1 if snapshot_ts.date() <= expiry else 0
```

### 9.3 Target Generation

```python
def build_target(
    excavations: pd.DataFrame,
    snapshot_ts: datetime,
    prediction_horizon_days: int = 180,
) -> int:
    """
    Target = 1 if any excavation has start_date > snapshot_ts.date()
                              AND start_date <= snapshot_ts.date() + horizon
    Target = 0 otherwise.

    Note: uses start_date STRICTLY AFTER snapshot_ts.date() — no same-day events.
    """
    horizon_end = snapshot_ts.date() + timedelta(days=prediction_horizon_days)
    future_exc = excavations[
        (excavations["start_date"] > snapshot_ts.date())
        & (excavations["start_date"] <= horizon_end)
    ]
    return 1 if len(future_exc) > 0 else 0
```

### 9.4 Snapshot Date Generation Strategy

For each road segment, the feature store builder generates multiple training examples by iterating over a set of snapshot dates. This creates temporal diversity without data leakage.

```python
def generate_snapshot_dates(
    earliest_event_date: date,
    latest_event_date: date,
    step_days: int = 90,
) -> list[date]:
    """
    Generate snapshot dates from earliest_event_date + 6 months to
    latest_event_date - prediction_horizon_days.
    Step every `step_days` days.

    Minimum 6 months of history required before a snapshot date is usable.
    """
    start = earliest_event_date + timedelta(days=180)
    end = latest_event_date - timedelta(days=180)
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=step_days)
    return dates
```

---

## 10. Feature Store

### 10.1 Schema

The feature store is a **Parquet file** at `data/feature_store/features_v1.parquet`. Each row is one training example: one (segment, snapshot_date) pair.

| Column | Type | Description |
|---|---|---|
| `segment_id` | string | Road segment UUID |
| `feature_snapshot_timestamp` | datetime[UTC] | Point-in-time for this example |
| `prediction_horizon_days` | int | 180 (configurable) |
| `data_version` | string | e.g., `"synthetic_v1_seed42"` |
| `target` | int | 0 or 1 |
| `excavation_count_all_time` | float | |
| `excavation_count_24m` | float | |
| `excavation_count_12m` | float | |
| `days_since_last_excavation` | float | |
| `days_since_last_resurfacing` | float | |
| `distinct_utility_count` | float | |
| `active_project_count` | float | |
| `historical_conflict_count` | float | |
| `road_class_encoded` | float | |
| `segment_length_normalized` | float | |
| `project_density_per_km` | float | |
| `resurfacing_within_warranty` | float | 0.0 or 1.0 |

### 10.2 Feature Definitions File

```python
# ml/features/definitions.py

FEATURE_DEFINITIONS = {
    "excavation_count_all_time": {
        "description": "Total excavations recorded before snapshot_ts",
        "timestamp_basis": "ExcavationEvent.start_date < snapshot_ts",
        "group": "A",  # A = Historical, B = +Activity, C = +Structural
    },
    "excavation_count_24m": {
        "description": "Excavations in [snapshot_ts - 730d, snapshot_ts)",
        "timestamp_basis": "ExcavationEvent.start_date in [snapshot_ts-730d, snapshot_ts)",
        "group": "A",
    },
    "excavation_count_12m": {
        "description": "Excavations in [snapshot_ts - 365d, snapshot_ts)",
        "timestamp_basis": "ExcavationEvent.start_date in [snapshot_ts-365d, snapshot_ts)",
        "group": "A",
    },
    "days_since_last_excavation": {
        "description": "Days between snapshot_ts and most recent excavation before it",
        "timestamp_basis": "snapshot_ts - max(ExcavationEvent.start_date < snapshot_ts)",
        "group": "A",
    },
    "days_since_last_resurfacing": {
        "description": "Days between snapshot_ts and most recent resurfacing end before it",
        "timestamp_basis": "snapshot_ts - max(ResurfacingEvent.end_date < snapshot_ts)",
        "group": "A",
    },
    "distinct_utility_count": {
        "description": "Distinct utility types that have excavated before snapshot_ts",
        "timestamp_basis": "ExcavationEvent.start_date < snapshot_ts",
        "group": "A",
    },
    "resurfacing_within_warranty": {
        "description": "1 if most recent resurfacing warranty is active at snapshot_ts",
        "timestamp_basis": "ResurfacingEvent.end_date < snapshot_ts; warranty active at snapshot_ts",
        "group": "A",
    },
    "active_project_count": {
        "description": "Projects active at snapshot_ts, created before snapshot_ts",
        "timestamp_basis": "UtilityProject.created_at < snapshot_ts AND planned_start<=snapshot_ts<=planned_end",
        "group": "B",
    },
    "historical_conflict_count": {
        "description": "Conflict records with detected_at < snapshot_ts",
        "timestamp_basis": "ConflictRecord.detected_at < snapshot_ts",
        "group": "B",
    },
    "project_density_per_km": {
        "description": "Projects started in [snapshot_ts-730d, snapshot_ts) per km of segment",
        "timestamp_basis": "UtilityProject.planned_start_date in [snapshot_ts-730d, snapshot_ts)",
        "group": "B",
    },
    "road_class_encoded": {
        "description": "Road class as ordinal: ARTERIAL=2, COLLECTOR=1, LOCAL=0",
        "timestamp_basis": "static (road segment attribute)",
        "group": "C",
    },
    "segment_length_normalized": {
        "description": "Segment length normalized by max segment length in dataset",
        "timestamp_basis": "static (road segment attribute)",
        "group": "C",
    },
}

# Feature groups for ablation experiment
FEATURE_GROUPS = {
    "A": [k for k, v in FEATURE_DEFINITIONS.items() if v["group"] == "A"],
    "B": [k for k, v in FEATURE_DEFINITIONS.items() if v["group"] in ("A", "B")],
    "C": [k for k in FEATURE_DEFINITIONS.keys()],  # All features
}
```

### 10.3 Leakage Validator

```python
# ml/features/validator.py

class LeakageError(Exception):
    pass

class LeakageValidator:
    """
    Asserts that no data row in a DataFrame has a timestamp >= snapshot_ts.
    Called by PointInTimeFeatureBuilder before computing each feature.
    """

    def assert_no_future_data(
        self,
        df: pd.DataFrame,
        snapshot_ts: datetime,
        date_column: str,
    ) -> None:
        """
        Raises LeakageError if any row in df[date_column] >= snapshot_ts.date().
        This is a hard error — not a warning.
        """
        if df.empty:
            return
        col = pd.to_datetime(df[date_column]).dt.date
        violations = df[col >= snapshot_ts.date()]
        if not violations.empty:
            raise LeakageError(
                f"Data leakage detected: {len(violations)} row(s) in column "
                f"'{date_column}' have date >= snapshot_ts ({snapshot_ts.date()}). "
                f"Earliest violation: {col[violations.index[0]]}"
            )

    def assert_target_is_future(
        self,
        target_date: date,
        snapshot_ts: datetime,
    ) -> None:
        if target_date <= snapshot_ts.date():
            raise LeakageError(
                f"Target event date {target_date} is not strictly after "
                f"snapshot_ts {snapshot_ts.date()}."
            )
```

---

## 11. Synthetic Data Generator

### 11.1 Design Philosophy

The generator must not hard-code which segments become "high risk." Instead, it implements a **causal model** where characteristics of a road segment influence the probability of excavation in each time period. High-activity segments emerge naturally from this process.

### 11.2 Configuration Object

All parameters are controlled through a single `GeneratorConfig` object, not hard-coded constants. This makes the generator testable and allows parameter sensitivity analysis.

```python
# scripts/generate_synthetic_data.py (configuration section)

@dataclass
class GeneratorConfig:
    seed: int = 42
    num_segments: int = 80
    num_arterial: int = 10
    num_collector: int = 20
    # num_local = num_segments - num_arterial - num_collector

    # Base annual excavation probability by road class
    base_excavation_prob_arterial: float = 0.55
    base_excavation_prob_collector: float = 0.35
    base_excavation_prob_local: float = 0.18

    # Multipliers for causal factors
    # Each additional distinct utility that has excavated previously
    utility_diversity_multiplier: float = 1.15
    # Each prior excavation in last 24 months (capped at 3x)
    recent_excavation_multiplier: float = 1.20
    # Days since last excavation damping: probability decays for first 90 days
    excavation_fatigue_days: int = 90
    excavation_fatigue_factor: float = 0.5  # probability multiplied by this during fatigue window

    # Resurfacing attraction: fresh resurfacing increases probability slightly
    # (agencies know there is a clean surface to cut)
    resurfacing_attraction_days: int = 180  # window after resurfacing completion
    resurfacing_attraction_multiplier: float = 1.25

    # Temporal clustering: probability of a new project starting in
    # the same 60-day window as an existing project on an adjacent segment
    temporal_cluster_prob: float = 0.40
    temporal_cluster_window_days: int = 60

    # Spatial clustering: probability that a project on segment X also
    # affects a neighboring segment in the same zone
    spatial_cluster_prob: float = 0.30

    # Project duration distributions (days) by utility type
    duration_params: dict = field(default_factory=lambda: {
        "WATER":       {"min": 15, "max": 60, "mode": 30},
        "SEWERAGE":    {"min": 20, "max": 60, "mode": 35},
        "DRAINAGE":    {"min": 10, "max": 45, "mode": 25},
        "ELECTRICITY": {"min": 7,  "max": 30, "mode": 15},
        "TELECOM":     {"min": 10, "max": 45, "mode": 20},
        "GAS":         {"min": 15, "max": 50, "mode": 30},
        "OTHER":       {"min": 7,  "max": 40, "mode": 20},
    })

    # Agency assignment by utility type
    agency_map: dict = field(default_factory=lambda: {
        "WATER":       ["Jal Sansthan Dehradun"],
        "SEWERAGE":    ["Jal Sansthan Dehradun", "UJS"],
        "DRAINAGE":    ["Nagar Nigam", "PWD"],
        "ELECTRICITY": ["UPCL"],
        "TELECOM":     ["BSNL", "Jio Infrastructure", "Airtel"],
        "GAS":         ["GAIL"],
        "OTHER":       ["Nagar Nigam"],
    })

    # Date range for synthetic history
    history_start_year: int = 2020
    history_end_year: int = 2025

    # Warranty periods by resurfacing type (months)
    warranty_months: dict = field(default_factory=lambda: {
        "FULL": 24,
        "OVERLAY": 18,
        "PATCH": 6,
    })
```

### 11.3 Causal Generation Process

```
Step 1: Generate road network
    → assign road_class, zone, name, synthetic geometry (LineString)
    → compute base excavation probability from road_class

Step 2: For each year in [history_start, history_end]:
    → For each segment:
        → compute adjusted_prob = base_prob
                                  × utility_multiplier(past_utils)
                                  × recent_excavation_multiplier(exc_24m)
                                  × fatigue_factor(days_since_last_exc)
                                  × resurfacing_factor(days_since_last_res)
        → Bernoulli draw: excavation_this_year ~ Bernoulli(min(adjusted_prob, 0.95))
        → If True: generate a UtilityProject with dates, utility_type drawn from
                   distribution weighted by road_class

Step 3: Apply temporal clustering
    → For each generated project, with probability temporal_cluster_prob:
        → Find projects on other segments in the same zone that started
          within temporal_cluster_window_days
        → Offset this project's start date to create overlap within the window

Step 4: Apply spatial clustering
    → For each generated project, with probability spatial_cluster_prob:
        → Extend the project to also affect a neighboring segment in the zone

Step 5: Generate resurfacing events
    → After each FULL excavation event, generate a ResurfacingEvent
      with end_date = excavation.end_date + uniform(7, 30) days
    → warranty_months drawn from warranty_months config for the resurfacing_type

Step 6: Write all records to SQLite
    → Insert in chronological order
    → Compute and store all derived fields (length_meters, etc.)
```

### 11.4 Reproducibility

```python
import numpy as np

class SyntheticDataGenerator:
    def __init__(self, config: GeneratorConfig):
        self.config = config
        # Single RNG instance; all random draws go through this
        self.rng = np.random.default_rng(config.seed)

    def _bernoulli(self, p: float) -> bool:
        return bool(self.rng.random() < p)

    def _triangular(self, low: int, high: int, mode: int) -> int:
        return int(self.rng.triangular(low, mode, high))

    def _choice(self, items: list, p: list | None = None):
        return self.rng.choice(items, p=p)
```

All randomness flows through `self.rng`. No calls to `random.random()` or `numpy.random.*` global functions. This guarantees that `--seed 42` produces identical output on every run.

### 11.5 `--describe-model` Flag

```
$ python scripts/generate_synthetic_data.py --describe-model

PipeWatch Synthetic Data Generator — Causal Model Description
=============================================================
IMPORTANT: These are simulated assumptions for generating plausible synthetic
data. They are NOT empirical claims about Dehradun's infrastructure patterns.

Base excavation probabilities:
  ARTERIAL:  0.55 per year
  COLLECTOR: 0.35 per year
  LOCAL:     0.18 per year

Multipliers:
  Each additional utility type (historical): × 1.15
  Each excavation in last 24 months (cap 3): × 1.20
  Excavation fatigue (first 90 days):        × 0.50
  Post-resurfacing attraction (180 days):    × 1.25

Clustering:
  Temporal cluster probability: 0.40 (60-day window)
  Spatial cluster probability:  0.30 (same zone, adjacent segment)
```

---

## 12. ML Models

### 12.1 Abstract Model Interface

```python
# ml/models/base.py

from abc import ABC, abstractmethod
import numpy as np

class AbstractPipeWatchModel(ABC):
    """
    All PipeWatch prediction models implement this interface.
    This allows the PredictionService to use any model without
    knowing its internal structure.
    """

    @property
    @abstractmethod
    def model_type(self) -> str:
        """e.g., 'RandomForestClassifier', 'LogisticRegression', 'RuleBaseline'"""
        ...

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the model. X is the feature matrix, y is binary target."""
        ...

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Return probability of class 1 (repeat excavation within horizon).
        Shape: (n_samples,) — only the positive class probability.
        For the RuleBaseline, this returns 0.0 or 1.0.
        """
        ...

    @abstractmethod
    def get_feature_importances(
        self, feature_names: list[str]
    ) -> list[dict]:
        """
        Return list of dicts: [{name, importance, direction}]
        Sorted descending by |importance|.
        """
        ...

    def predict_risk_category(self, probability: float) -> str:
        if probability >= 0.75:
            return "CRITICAL"
        elif probability >= 0.50:
            return "HIGH"
        elif probability >= 0.25:
            return "MEDIUM"
        return "LOW"
```

### 12.2 Rule Baseline

```python
# ml/models/rule_baseline.py

class RuleBaseline(AbstractPipeWatchModel):
    """
    Simple threshold rule: excavation_count_24m >= 2 → risk 1, else 0.
    Returns 0.0 or 1.0 (not a calibrated probability).
    Used as the performance floor for ML model comparison.
    """

    model_type = "RuleBaseline"
    THRESHOLD_FEATURE = "excavation_count_24m"
    THRESHOLD_VALUE = 2

    def fit(self, X, y):
        pass  # No training required

    def predict_proba(self, X):
        # X is a DataFrame; extract the threshold feature
        col = X[self.THRESHOLD_FEATURE] if hasattr(X, "__getitem__") else X[:, 0]
        return np.where(col >= self.THRESHOLD_VALUE, 1.0, 0.0)

    def get_feature_importances(self, feature_names):
        return [{"name": self.THRESHOLD_FEATURE, "importance": 1.0, "direction": "increases_risk"}]
```

### 12.3 Logistic Regression

```python
# ml/models/logistic_regression.py

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression as SKLogReg
from sklearn.calibration import CalibratedClassifierCV
import numpy as np

class PipeWatchLogisticRegression(AbstractPipeWatchModel):
    """
    Logistic Regression with StandardScaler and probability calibration.
    Interpretable via coefficients.
    """

    model_type = "LogisticRegression"

    def __init__(self, C: float = 1.0, max_iter: int = 500, random_state: int = 42):
        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SKLogReg(C=C, max_iter=max_iter,
                             class_weight="balanced",
                             random_state=random_state)),
        ])
        self._feature_names: list[str] = []

    def fit(self, X, y):
        self._feature_names = list(X.columns) if hasattr(X, "columns") else []
        self._pipeline.fit(X, y)

    def predict_proba(self, X):
        return self._pipeline.predict_proba(X)[:, 1]

    def get_feature_importances(self, feature_names):
        coefs = self._pipeline.named_steps["clf"].coef_[0]
        results = []
        for name, coef in zip(feature_names, coefs):
            results.append({
                "name": name,
                "importance": float(abs(coef)),
                "raw_coefficient": float(coef),
                "direction": "increases_risk" if coef > 0 else "decreases_risk",
            })
        return sorted(results, key=lambda x: -x["importance"])
```

### 12.4 Random Forest

```python
# ml/models/random_forest.py

from sklearn.ensemble import RandomForestClassifier
import shap

class PipeWatchRandomForest(AbstractPipeWatchModel):
    """
    Random Forest with class_weight='balanced'.
    Feature attribution via SHAP TreeExplainer.
    """

    model_type = "RandomForestClassifier"

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int | None = None,
        random_state: int = 42,
    ):
        self._model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight="balanced",
            random_state=random_state,
        )
        self._feature_names: list[str] = []
        self._shap_explainer = None

    def fit(self, X, y):
        self._feature_names = list(X.columns) if hasattr(X, "columns") else []
        self._model.fit(X, y)
        # Build SHAP explainer after fitting
        self._shap_explainer = shap.TreeExplainer(self._model)

    def predict_proba(self, X):
        return self._model.predict_proba(X)[:, 1]

    def get_feature_importances(self, feature_names):
        importances = self._model.feature_importances_
        results = []
        for name, imp in zip(feature_names, importances):
            results.append({
                "name": name,
                "importance": float(imp),
                "direction": "varies",  # RF importance is magnitude only
            })
        return sorted(results, key=lambda x: -x["importance"])

    def get_shap_values(self, X_single: pd.DataFrame) -> list[dict]:
        """
        Returns per-feature SHAP values for a single prediction instance.
        Used by the explainability module (Section 15).
        """
        if self._shap_explainer is None:
            raise RuntimeError("Model not fitted.")
        shap_vals = self._shap_explainer.shap_values(X_single)
        # shap_vals[1] = class 1 (repeat excavation) SHAP values
        class1_shap = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]
        feature_names = list(X_single.columns)
        results = []
        for name, sv, fv in zip(feature_names, class1_shap, X_single.iloc[0]):
            results.append({
                "name": name,
                "shap_value": float(sv),
                "feature_value": float(fv),
                "direction": "increases_risk" if sv > 0 else "decreases_risk",
            })
        return sorted(results, key=lambda x: -abs(x["shap_value"]))
```

### 12.5 Prediction Service (Runtime)

```python
# ml/prediction/predictor.py

class PredictionService:
    """
    Loaded at FastAPI startup. Holds the active model in memory.
    Serves on-demand predictions for the API.
    """

    def __init__(self, model: AbstractPipeWatchModel, model_version: str, feature_group: str):
        self.model = model
        self.model_version = model_version
        self.feature_group = feature_group
        self.feature_builder = PointInTimeFeatureBuilder(LeakageValidator())
        self.feature_names = FEATURE_GROUPS[feature_group]

    def predict(
        self,
        segment_id: str,
        snapshot_ts: datetime,
        raw_data: dict,   # Pre-fetched DataFrames for this segment
        prediction_horizon_days: int = 180,
    ) -> PredictionOutput:
        """
        1. Build feature vector at snapshot_ts using PointInTimeFeatureBuilder.
        2. Run model.predict_proba().
        3. Get top 5 feature explanations.
        4. Return PredictionOutput (not yet persisted — caller persists it).
        """
        feature_dict = self.feature_builder.build(
            segment_id=segment_id,
            snapshot_ts=snapshot_ts,
            **raw_data,
            prediction_horizon_days=prediction_horizon_days,
        )
        # Restrict to the model's feature group
        X = pd.DataFrame([{k: feature_dict[k] for k in self.feature_names}])
        probability = float(self.model.predict_proba(X)[0])

        if isinstance(self.model, PipeWatchRandomForest):
            top_features = self.model.get_shap_values(X)[:5]
        else:
            top_features = self.model.get_feature_importances(self.feature_names)[:5]

        # Attach timestamp_basis from FEATURE_DEFINITIONS
        for f in top_features:
            f["timestamp_basis"] = FEATURE_DEFINITIONS[f["name"]]["timestamp_basis"]

        return PredictionOutput(
            probability=round(probability, 4),
            risk_category=self.model.predict_risk_category(probability),
            prediction_timestamp=datetime.now(UTC),
            feature_snapshot_timestamp=snapshot_ts,
            prediction_horizon_days=prediction_horizon_days,
            model_version=self.model_version,
            model_type=self.model.model_type,
            feature_group=self.feature_group,
            top_features=top_features,
            feature_snapshot=feature_dict,
        )
```

### 12.6 Model Serialization

Models are serialized with `joblib`:

```python
import joblib
from pathlib import Path

def save_model(model: AbstractPipeWatchModel, version: str, models_dir: Path) -> Path:
    filename = f"{model.model_type.lower()}_{version}.joblib"
    path = models_dir / filename
    joblib.dump(model, path)
    return path

def load_model(path: Path) -> AbstractPipeWatchModel:
    return joblib.load(path)
```

Filename convention: `{model_type}_{version}_{yyyymmdd}.joblib`
Example: `randomforestclassifier_v1.0_20261001.joblib`

---

## 13. Temporal Backtesting

### 13.1 Protocol Definition

Temporal backtesting simulates how the model would have performed when deployed at successive points in time. It prevents evaluation data from leaking into training.

```
Fold 1:  Train on [2020-01-01, 2022-12-31]  →  Validate on 2023
Fold 2:  Train on [2020-01-01, 2023-12-31]  →  Validate on 2024
Final:   Train on [2020-01-01, 2024-12-31]  →  Test on 2025
```

The **2025 test set is touched exactly once** — after all hyperparameter decisions are finalized using the validation folds. Any hyperparameter selection that peeks at the 2025 metrics is a violation of the protocol.

### 13.2 Data Slicing

```python
# ml/training/splitter.py

from dataclasses import dataclass
import pandas as pd

@dataclass
class TemporalSplit:
    train: pd.DataFrame
    eval_: pd.DataFrame   # validation or test
    label: str            # e.g., "fold_1_train2022_val2023"

class TemporalSplitter:
    """
    Slices the feature store DataFrame by feature_snapshot_timestamp.
    No random shuffling. Examples are assigned to folds based solely
    on their snapshot year.
    """

    FOLDS = [
        # (train_end_year, eval_year, label)
        (2022, 2023, "fold_1"),
        (2023, 2024, "fold_2"),
        (2024, 2025, "final_test"),
    ]

    def split(self, df: pd.DataFrame) -> list[TemporalSplit]:
        """
        df must have a 'feature_snapshot_timestamp' column (datetime).
        Returns one TemporalSplit per fold, plus the final test split.
        """
        df = df.copy()
        df["_year"] = pd.to_datetime(df["feature_snapshot_timestamp"]).dt.year

        splits = []
        for train_end_year, eval_year, label in self.FOLDS:
            train = df[df["_year"] <= train_end_year].drop(columns=["_year"])
            eval_ = df[df["_year"] == eval_year].drop(columns=["_year"])
            splits.append(TemporalSplit(
                train=train,
                eval_=eval_,
                label=f"{label}_train{train_end_year}_eval{eval_year}"
            ))
        return splits
```

### 13.3 Hyperparameter Selection

Hyperparameter tuning is performed **only on validation folds (2023, 2024)**, never on the 2025 test set. The search uses `TimeSeriesSplit` within each fold's training data:

```python
# ml/training/hyperparameters.py

from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

RF_PARAM_GRID = {
    "n_estimators": [100, 200, 300],
    "max_depth": [None, 10, 20],
    "min_samples_split": [2, 5],
}

LR_PARAM_GRID = {
    "C": [0.01, 0.1, 1.0, 10.0],
    "max_iter": [500],
}

def tune_hyperparameters(
    model_class,
    param_grid: dict,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_splits: int = 3,
    random_state: int = 42,
) -> dict:
    """
    Uses TimeSeriesSplit CV within the training fold.
    Returns best_params dict.
    The CV split respects temporal ordering within the training window.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    search = GridSearchCV(
        model_class(random_state=random_state),
        param_grid,
        cv=tscv,
        scoring="roc_auc",
        n_jobs=-1,
        refit=True,
    )
    search.fit(X_train, y_train)
    return search.best_params_
```

### 13.4 Training and Evaluation Loop

```python
# ml/evaluation/backtesting.py

class BacktestRunner:
    """
    Runs the full temporal backtesting protocol for a given model class.
    Stores per-fold metrics and final test metrics.
    The final test split (2025) is evaluated LAST, after all fold tuning is done.
    """

    def run(
        self,
        feature_df: pd.DataFrame,
        feature_cols: list[str],
        model_class,
        param_grid: dict,
        seed: int = 42,
    ) -> dict:
        """
        Returns a results dict:
        {
          "fold_results": [...],       # per validation-fold metrics
          "best_params": {...},        # hyperparams from fold tuning
          "final_test_metrics": {...}, # 2025 test metrics (computed once)
          "model_version": "...",
        }
        """
        splitter = TemporalSplitter()
        splits = splitter.split(feature_df)

        # Separate validation folds from final test
        val_folds = [s for s in splits if "final_test" not in s.label]
        test_split = next(s for s in splits if "final_test" in s.label)

        # --- Phase 1: Tune on validation folds ---
        all_best_params = []
        fold_results = []

        for fold in val_folds:
            X_train = fold.train[feature_cols]
            y_train = fold.train["target"]
            X_val = fold.eval_[feature_cols]
            y_val = fold.eval_["target"]

            if len(X_val) == 0:
                continue

            best_params = tune_hyperparameters(
                model_class, param_grid, X_train, y_train, random_state=seed
            )
            all_best_params.append(best_params)

            # Fit with best params and score on val
            model = model_class(**best_params, random_state=seed)
            model.fit(X_train, y_train)
            metrics = compute_metrics(model, X_val, y_val)
            fold_results.append({
                "label": fold.label,
                "best_params": best_params,
                "metrics": metrics,
                "train_size": len(X_train),
                "val_size": len(X_val),
            })

        # --- Phase 2: Select consensus best params from val folds ---
        # Use params from the fold with highest val ROC-AUC
        best_fold = max(fold_results, key=lambda r: r["metrics"]["roc_auc"])
        consensus_params = best_fold["best_params"]

        # --- Phase 3: Final test on 2025 — exactly once ---
        X_train_full = test_split.train[feature_cols]
        y_train_full = test_split.train["target"]
        X_test = test_split.eval_[feature_cols]
        y_test = test_split.eval_["target"]

        final_model = model_class(**consensus_params, random_state=seed)
        final_model.fit(X_train_full, y_train_full)
        final_metrics = compute_metrics(final_model, X_test, y_test)

        return {
            "fold_results": fold_results,
            "best_params": consensus_params,
            "final_test_metrics": final_metrics,
            "test_size": len(X_test),
            "model_class": model_class.__name__,
        }
```

### 13.5 Metric Computation

```python
# ml/evaluation/metrics.py

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score
)

def compute_metrics(model, X, y) -> dict:
    proba = model.predict_proba(X)
    preds = (proba >= 0.5).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y, preds)), 4),
        "precision": round(float(precision_score(y, preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y, preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y, preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y, proba)), 4),
        "n_positive": int(y.sum()),
        "n_total": int(len(y)),
    }
```

### 13.6 Metric Storage

All results are written to `ml/evaluation/backtest_report_{model_version}.json`:

```json
{
  "model_version": "rf_v1.0_20261001",
  "model_class": "RandomForestClassifier",
  "feature_group": "C",
  "seed": 42,
  "fold_results": [
    {
      "label": "fold_1_train2022_eval2023",
      "best_params": {"n_estimators": 200, "max_depth": null},
      "metrics": {"accuracy": 0.74, "roc_auc": 0.79, ...},
      "train_size": 1240,
      "val_size": 430
    }
  ],
  "best_params": {"n_estimators": 200, "max_depth": null},
  "final_test_metrics": {"accuracy": 0.71, "roc_auc": 0.77, ...},
  "test_size": 410,
  "baseline_comparison": {
    "baseline_roc_auc": 0.63,
    "delta_roc_auc": 0.14,
    "interpretation": "Random Forest improves ROC-AUC by 0.14 over rule baseline on 2025 test set."
  },
  "limitations": [
    "All data is synthetic. Relationships are simulated assumptions.",
    "Performance on real Dehradun data is unknown.",
    "Class imbalance handled via class_weight=balanced."
  ]
}
```

---

## 14. Feature Ablation

### 14.1 Experiment Design

The ablation experiment answers: **which feature group contributes genuine predictive signal?** It holds the model type (Random Forest) and evaluation protocol (temporal backtesting) constant across all three groups.

```python
# ml/evaluation/ablation.py

ABLATION_GROUPS = {
    "A": FEATURE_GROUPS["A"],   # Historical only
    "B": FEATURE_GROUPS["B"],   # Historical + project activity
    "C": FEATURE_GROUPS["C"],   # Full feature set
}

class AblationRunner:
    """
    Runs BacktestRunner for each feature group and collects results.
    All groups use identical: model class, hyperparameter grid, seed, splits.
    """

    def run_all(
        self,
        feature_df: pd.DataFrame,
        seed: int = 42,
    ) -> dict:
        results = {}
        for group_name, feature_cols in ABLATION_GROUPS.items():
            runner = BacktestRunner()
            group_result = runner.run(
                feature_df=feature_df,
                feature_cols=feature_cols,
                model_class=RandomForestClassifier,
                param_grid=RF_PARAM_GRID,
                seed=seed,
            )
            results[group_name] = {
                "feature_cols": feature_cols,
                "num_features": len(feature_cols),
                "final_test_metrics": group_result["final_test_metrics"],
                "fold_avg_roc_auc": _avg_fold_metric(
                    group_result["fold_results"], "roc_auc"
                ),
            }

        return self._build_report(results)

    def _build_report(self, results: dict) -> dict:
        """
        Computes deltas between groups and writes interpretation.
        If delta(B vs A) < 0.02 in ROC-AUC: notes that project activity
        features may not contribute signal — possibly because the synthetic
        causal model does not generate the intended relationships.
        """
        roc_a = results["A"]["final_test_metrics"]["roc_auc"]
        roc_b = results["B"]["final_test_metrics"]["roc_auc"]
        roc_c = results["C"]["final_test_metrics"]["roc_auc"]

        interpretation = []
        if (roc_b - roc_a) < 0.02:
            interpretation.append(
                "Group B (+ project activity) does not meaningfully improve over "
                "Group A (historical only). Project activity features may not add "
                "signal, possibly because the synthetic causal model does not generate "
                "the intended relationships between project activity and excavation outcomes."
            )
        if (roc_c - roc_b) < 0.02:
            interpretation.append(
                "Adding structural features (road class, segment length) in Group C "
                "does not meaningfully improve over Group B."
            )

        return {
            "group_results": results,
            "deltas": {
                "B_vs_A": round(roc_b - roc_a, 4),
                "C_vs_B": round(roc_c - roc_b, 4),
                "C_vs_A": round(roc_c - roc_a, 4),
            },
            "interpretation": interpretation,
            "recommendation": _select_best_group(results),
        }
```

### 14.2 Output Format

Written to `ml/evaluation/ablation_report_{model_version}.json`:

```json
{
  "group_results": {
    "A": {
      "feature_cols": ["excavation_count_all_time", ...],
      "num_features": 7,
      "final_test_metrics": {"roc_auc": 0.72, "f1": 0.68, ...},
      "fold_avg_roc_auc": 0.74
    },
    "B": { ... },
    "C": { ... }
  },
  "deltas": {
    "B_vs_A": 0.04,
    "C_vs_B": 0.01,
    "C_vs_A": 0.05
  },
  "interpretation": [
    "Adding structural features (Group C vs B) adds minimal signal (delta ROC-AUC = 0.01)."
  ],
  "recommendation": "Use Group B features for production model."
}
```

---

## 15. Explainability

### 15.1 Per-Prediction Explanation Pipeline

Every prediction returned by the API includes a `top_features` list. This list is assembled as follows:

```
For Logistic Regression:
    → Use coefficients × feature value as attribution
    → Direction: positive coefficient = increases_risk

For Random Forest:
    → Use SHAP TreeExplainer on the single prediction instance
    → shap_values[1][0] = class-1 SHAP values for this row
    → Direction: positive SHAP = increases_risk

For RuleBaseline:
    → Single feature: "excavation_count_24m"
    → Direction: "excavation_count_24m >= 2 → increases_risk"
```

### 15.2 Explanation Schema

Each item in `top_features` must conform to:

```python
@dataclass
class FeatureExplanation:
    name: str                  # Feature key from FEATURE_DEFINITIONS
    value: float               # Actual feature value at snapshot_ts
    importance: float          # |SHAP value| or |coefficient × value|
    direction: str             # "increases_risk" | "decreases_risk"
    timestamp_basis: str       # From FEATURE_DEFINITIONS[name]["timestamp_basis"]
    plain_language: str        # Human-readable explanation (see Section 15.3)
```

### 15.3 Plain-Language Explanation Generation

Plain language is generated from templates, not hard-coded strings:

```python
# ml/explainability/explainer.py

PLAIN_LANGUAGE_TEMPLATES = {
    "excavation_count_24m": (
        "This segment has had {value:.0f} excavation(s) in the last 24 months, "
        "which {direction_verb} repeat excavation risk."
    ),
    "days_since_last_excavation": (
        "The last excavation was {value:.0f} days ago, "
        "which {direction_verb} risk (recent excavations indicate active segments)."
    ),
    "days_since_last_resurfacing": (
        "The last resurfacing was {value:.0f} days ago, "
        "which {direction_verb} repeat excavation risk."
    ),
    "distinct_utility_count": (
        "{value:.0f} distinct utility type(s) have previously excavated this segment, "
        "which {direction_verb} risk."
    ),
    "active_project_count": (
        "There are {value:.0f} active project(s) on this segment at the prediction date, "
        "which {direction_verb} risk."
    ),
    "resurfacing_within_warranty": (
        "The segment {'is' if value else 'is not'} within a resurfacing warranty period, "
        "which {direction_verb} risk."
    ),
    "historical_conflict_count": (
        "This segment has had {value:.0f} recorded conflict(s) historically, "
        "which {direction_verb} risk."
    ),
    "road_class_encoded": (
        "Road class ({value:.0f} = {'ARTERIAL' if value==2 else 'COLLECTOR' if value==1 else 'LOCAL'}) "
        "{direction_verb} risk (arterial roads attract more activity)."
    ),
}

def build_plain_language(feature_name: str, value: float, direction: str) -> str:
    direction_verb = "increases" if direction == "increases_risk" else "decreases"
    template = PLAIN_LANGUAGE_TEMPLATES.get(feature_name)
    if template is None:
        return f"Feature '{feature_name}' (value={value:.3f}) {direction_verb} risk."
    return template.format(value=value, direction_verb=direction_verb)
```

### 15.4 Calibration Curve

The calibration curve compares predicted probabilities to observed frequencies:

```python
# ml/evaluation/calibration.py

from sklearn.calibration import calibration_curve

def compute_calibration(
    probas: np.ndarray, y_true: np.ndarray, n_bins: int = 10
) -> dict:
    """
    Returns fraction_of_positives and mean_predicted_value arrays
    for plotting. Well-calibrated models have these arrays close to
    the identity line (y = x).
    """
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, probas, n_bins=n_bins, strategy="uniform"
    )
    return {
        "fraction_of_positives": fraction_of_positives.tolist(),
        "mean_predicted_value": mean_predicted_value.tolist(),
        "n_bins": n_bins,
    }
```

Stored in the evaluation report; rendered on the "Model Info" panel in the frontend.

---

## 16. What-If Simulator

### 16.1 Scenario Representation

```python
# backend/app/schemas/simulator.py

class ScenarioEvent(BaseModel):
    utility_type: UtilityType
    start_date: date
    end_date: date
    requires_excavation: bool
    requires_resurfacing: bool

    @model_validator(mode="after")
    def end_after_start(self) -> "ScenarioEvent":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class Scenario(BaseModel):
    name: str
    segment_id: str
    events: list[ScenarioEvent]

    @field_validator("events")
    @classmethod
    def at_least_two_events(cls, v):
        if len(v) < 2:
            raise ValueError("A scenario must contain at least 2 events.")
        return v

class WhatIfRequest(BaseModel):
    scenario_a: Scenario
    scenario_b: Scenario
```

### 16.2 Metric Computation Engine

```python
# backend/app/services/whatif_simulator.py

REPEAT_EXCAVATION_WINDOW_DAYS = 180

@dataclass
class ScenarioMetrics:
    total_excavation_count: int
    repeat_excavation_count: int
    conflict_count: int
    total_road_disturbance_days: int
    coordination_opportunities: int
    resurfacing_count: int
    estimated_avoided_excavations: int   # populated only in comparison

class WhatIfSimulator:
    """
    Deterministic. No I/O. All inputs are the scenario events.
    """

    def compute_metrics(self, scenario: Scenario) -> ScenarioMetrics:
        events = sorted(scenario.events, key=lambda e: e.start_date)
        excavation_events = [e for e in events if e.requires_excavation]

        # total_excavation_count
        total_excavation_count = len(excavation_events)

        # repeat_excavation_count
        # An excavation is a "repeat" if there was a prior excavation on
        # the same segment within REPEAT_EXCAVATION_WINDOW_DAYS before it.
        repeat_excavation_count = 0
        for i, exc in enumerate(excavation_events):
            for prior in excavation_events[:i]:
                gap = (exc.start_date - prior.start_date).days
                if 0 < gap <= REPEAT_EXCAVATION_WINDOW_DAYS:
                    repeat_excavation_count += 1
                    break

        # conflict_count
        # A conflict exists when two events overlap in time on the same segment
        conflict_count = 0
        for i, e1 in enumerate(excavation_events):
            for e2 in excavation_events[i+1:]:
                if e1.start_date <= e2.end_date and e2.start_date <= e1.end_date:
                    conflict_count += 1

        # total_road_disturbance_days
        total_road_disturbance_days = sum(
            (e.end_date - e.start_date).days
            for e in excavation_events
        )

        # coordination_opportunities
        # Pairs of excavation events that could be merged:
        # their date ranges overlap or are within 30 days of each other.
        coordination_opportunities = 0
        for i, e1 in enumerate(excavation_events):
            for e2 in excavation_events[i+1:]:
                gap = (e2.start_date - e1.end_date).days
                if gap <= 30:
                    coordination_opportunities += 1

        # resurfacing_count
        resurfacing_count = sum(1 for e in events if e.requires_resurfacing)

        return ScenarioMetrics(
            total_excavation_count=total_excavation_count,
            repeat_excavation_count=repeat_excavation_count,
            conflict_count=conflict_count,
            total_road_disturbance_days=total_road_disturbance_days,
            coordination_opportunities=coordination_opportunities,
            resurfacing_count=resurfacing_count,
            estimated_avoided_excavations=0,   # set during comparison
        )

    def compare(
        self, scenario_a: Scenario, scenario_b: Scenario
    ) -> "WhatIfComparisonResult":
        metrics_a = self.compute_metrics(scenario_a)
        metrics_b = self.compute_metrics(scenario_b)

        avoided = metrics_a.repeat_excavation_count - metrics_b.repeat_excavation_count
        metrics_b.estimated_avoided_excavations = max(0, avoided)

        narrative = self._generate_narrative(scenario_a, scenario_b, metrics_a, metrics_b)

        return WhatIfComparisonResult(
            scenario_a_name=scenario_a.name,
            scenario_b_name=scenario_b.name,
            metrics_a=metrics_a,
            metrics_b=metrics_b,
            narrative=narrative,
            simulation_label="Simulation — Not a Committed Schedule.",
            provenance=ProvenanceService.build(
                evidence_sources=["SIMULATION"],
                calculation_method="whatif_simulator_v1",
                is_synthetic=True,
            ),
        )
```

### 16.3 Narrative Generation

The narrative is constructed programmatically from the computed metric deltas. It is never hard-coded.

```python
    def _generate_narrative(self, scenario_a, scenario_b, m_a, m_b) -> str:
        lines = []
        avoided = max(0, m_a.repeat_excavation_count - m_b.repeat_excavation_count)

        if avoided > 0:
            lines.append(
                f"Scenario '{scenario_b.name}' avoids {avoided} repeat excavation(s) "
                f"compared to '{scenario_a.name}' by coordinating work into fewer "
                f"excavation windows."
            )
        elif m_a.repeat_excavation_count == m_b.repeat_excavation_count:
            lines.append(
                f"Both scenarios result in the same number of repeat excavations "
                f"({m_a.repeat_excavation_count})."
            )

        disturbance_delta = m_a.total_road_disturbance_days - m_b.total_road_disturbance_days
        if disturbance_delta > 0:
            lines.append(
                f"'{scenario_b.name}' reduces total road disturbance by "
                f"{disturbance_delta} days."
            )

        if m_b.coordination_opportunities > m_a.coordination_opportunities:
            lines.append(
                f"'{scenario_b.name}' has {m_b.coordination_opportunities} "
                f"coordination opportunity/opportunities (project pairs that could "
                f"share a single excavation)."
            )

        if not lines:
            lines.append(
                f"No significant difference in coordination efficiency between "
                f"'{scenario_a.name}' and '{scenario_b.name}' based on calculated metrics."
            )

        lines.append("Note: No monetary figures are estimated.")
        return " ".join(lines)
```

---

## 17. Recommendation Engine

### 17.1 Design Principle

The recommendation engine is **deterministic and rule-based**. It consumes outputs from the conflict engine, road memory, PISI, and ML predictions, but it does not contain its own ML model. ML evidence is inputs to the rules — the rules themselves are deterministic.

```
ConflictRecords  ──┐
RoadMemory       ──┤──► RecommendationEngine ──► CoordinationRecommendation[]
PISIScore        ──┤
RiskPrediction   ──┘
```

### 17.2 Recommendation Rule Interface

```python
# backend/app/services/recommendation_engine.py

from abc import ABC, abstractmethod

@dataclass
class RecommendationInput:
    """
    Pre-assembled inputs for a single road segment.
    All data is already fetched; the rule does not query the DB.
    """
    segment_id: str
    segment_name: str
    open_conflicts: list   # ConflictRecord objects
    timeline_events: list  # TimelineEvent objects (last 24 months)
    pisi: object           # InfrastructureStressIndex
    risk: object           # RiskPrediction | None
    active_projects: list  # UtilityProject objects
    planned_projects: list

class AbstractRecommendationRule(ABC):
    recommendation_type: str   # class variable

    @abstractmethod
    def is_applicable(self, inp: RecommendationInput) -> bool: ...

    @abstractmethod
    def generate(self, inp: RecommendationInput) -> "RecommendationDraft | None": ...
```

### 17.3 Four Recommendation Rules

#### MERGE_WINDOW

```python
class MergeWindowRule(AbstractRecommendationRule):
    """
    Trigger: Two HIGH-severity OPEN conflicts exist on the same segment,
    both involving ACTIVE or PLANNED projects within 30 days of each other.
    Suggestion: Schedule both projects to excavate simultaneously.
    Evidence: Both conflict records, project dates.
    """
    recommendation_type = "MERGE_WINDOW"

    def is_applicable(self, inp):
        high_conflicts = [
            c for c in inp.open_conflicts
            if c.severity == "HIGH" and c.rule_id == "SPATIAL_TEMPORAL_EXCAVATION_01"
        ]
        return len(high_conflicts) >= 1

    def generate(self, inp):
        high_conflicts = [
            c for c in inp.open_conflicts
            if c.severity == "HIGH" and c.rule_id == "SPATIAL_TEMPORAL_EXCAVATION_01"
        ]
        c = high_conflicts[0]
        return RecommendationDraft(
            recommendation_type=self.recommendation_type,
            priority="HIGH",
            title=f"Merge excavation windows on {inp.segment_name}",
            rationale=(
                f"Projects '{c.project_a_id}' and '{c.project_b_id}' are both planned "
                f"to excavate {inp.segment_name} within {c.overlap_days or 0} days of "
                f"each other. Coordinating them into a single excavation window would "
                f"avoid a repeat excavation."
            ),
            evidence={
                "conflict_id": c.id,
                "rule_id": c.rule_id,
                "overlap_days": c.overlap_days,
                "source_categories": ["DETERMINISTIC_CALCULATION"],
            },
            estimated_avoided_excavations=1,
        )
```

#### SEQUENCE_REORDER

```python
class SequenceReorderRule(AbstractRecommendationRule):
    """
    Trigger: A ResurfacingEvent is planned before all utility projects
    associated with the segment are complete (a PLANNED utility project
    starts after the planned resurfacing end_date, within 90 days).
    Suggestion: Complete all utility work before resurfacing.
    """
    recommendation_type = "SEQUENCE_REORDER"

    def is_applicable(self, inp):
        resurfacing_events = [
            e for e in inp.timeline_events if e.event_type == "RESURFACING"
            and e.start_date > date.today()
        ]
        if not resurfacing_events:
            return False
        # Check if any planned project starts after the resurfacing
        for res in resurfacing_events:
            for proj in inp.planned_projects:
                if proj.planned_start_date > res.end_date:
                    days_after = (proj.planned_start_date - res.end_date).days
                    if days_after <= 90:
                        return True
        return False

    def generate(self, inp) -> "RecommendationDraft | None":
        # Build rationale from evidence
        ...
```

#### DEFER_PROJECT

```python
class DeferProjectRule(AbstractRecommendationRule):
    """
    Trigger: A new PLANNED project is on a segment where the most recent
    resurfacing warranty is currently active.
    Suggestion: Defer the project or reroute it.
    Evidence: Active warranty dates, project planned dates.
    """
    recommendation_type = "DEFER_PROJECT"

    def is_applicable(self, inp):
        warranty_breach_events = [
            e for e in inp.timeline_events
            if e.is_warranty_breach or (
                inp.pisi and inp.pisi.component_resurfacing_gap >= 90.0
            )
        ]
        return len(warranty_breach_events) > 0 and len(inp.planned_projects) > 0
```

#### INSPECT_BEFORE_RESURFACE

```python
class InspectBeforeResurfaceRule(AbstractRecommendationRule):
    """
    Trigger: A segment has had 2+ excavations in the last 12 months.
    Suggestion: Conduct a structural inspection before committing to resurfacing.
    Evidence: excavation_count_12m, PISI component values.
    """
    recommendation_type = "INSPECT_BEFORE_RESURFACE"

    def is_applicable(self, inp):
        exc_12m = sum(
            1 for e in inp.timeline_events
            if e.event_type == "EXCAVATION"
            and (date.today() - e.start_date).days <= 365
        )
        return exc_12m >= 2

    def generate(self, inp):
        exc_12m = sum(
            1 for e in inp.timeline_events
            if e.event_type == "EXCAVATION"
            and (date.today() - e.start_date).days <= 365
        )
        risk_note = ""
        if inp.risk and inp.risk.risk_category in ("CRITICAL", "HIGH"):
            risk_note = (
                f" The ML model also predicts {inp.risk.risk_category} repeat "
                f"excavation risk (probability: {inp.risk.probability:.1%}). "
                f"Note: This is an ML prediction, not a confirmed event."
            )
        return RecommendationDraft(
            recommendation_type=self.recommendation_type,
            priority="MEDIUM",
            title=f"Inspect {inp.segment_name} before resurfacing",
            rationale=(
                f"{inp.segment_name} has had {exc_12m} excavation(s) in the last "
                f"12 months. Resurfacing before a structural inspection risks "
                f"premature damage.{risk_note}"
            ),
            evidence={
                "excavation_count_12m": exc_12m,
                "pisi_value": inp.pisi.index_value if inp.pisi else None,
                "ml_risk_category": inp.risk.risk_category if inp.risk else None,
                "source_categories": [
                    "DETERMINISTIC_CALCULATION",
                    "ML_PREDICTION" if inp.risk else None,
                ],
            },
            estimated_avoided_excavations=None,
        )
```

### 17.4 Recommendation Engine Orchestrator

```python
class RecommendationEngine:
    RULES = [
        MergeWindowRule(),
        SequenceReorderRule(),
        DeferProjectRule(),
        InspectBeforeResurfaceRule(),
    ]

    def __init__(self, repo: RecommendationRepository, ...):
        ...

    async def generate_for_segment(
        self, db: AsyncSession, segment_id: str
    ) -> list[CoordinationRecommendation]:
        """
        1. Assemble RecommendationInput from repositories.
        2. Apply each rule.
        3. For each draft, persist as CoordinationRecommendation.
        4. Return new records.
        Note: ML evidence is labeled as such in the evidence dict.
        The recommendation logic itself is deterministic.
        """
        inp = await self._assemble_input(db, segment_id)
        records = []
        for rule in self.RULES:
            if rule.is_applicable(inp):
                draft = rule.generate(inp)
                if draft:
                    record = await self.repo.create(db, segment_id, draft)
                    records.append(record)
        return records
```

---

## 18. API Design

### 18.1 Application Setup

```python
# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML model at startup — once, not per request
    from ml.prediction.predictor import PredictionService
    from app.config import settings
    app.state.prediction_service = PredictionService.from_artifact(
        settings.ml_model_path
    )
    yield
    # Cleanup on shutdown (if needed)

app = FastAPI(
    title="PipeWatch API",
    version="1.0.0",
    description="Predictive Utility Coordination & Road Excavation Intelligence",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import (
    segments, projects, excavations, resurfacing,
    conflicts, ml, stress, simulator, recommendations,
    dashboard, data_quality
)
app.include_router(segments.router,        prefix="/api/v1/segments",         tags=["segments"])
app.include_router(projects.router,        prefix="/api/v1/projects",          tags=["projects"])
app.include_router(excavations.router,     prefix="/api/v1/excavations",       tags=["excavations"])
app.include_router(resurfacing.router,     prefix="/api/v1/resurfacing",       tags=["resurfacing"])
app.include_router(conflicts.router,       prefix="/api/v1/conflicts",         tags=["conflicts"])
app.include_router(ml.router,              prefix="/api/v1/ml",                tags=["ml"])
app.include_router(stress.router,          prefix="/api/v1/stress",            tags=["stress"])
app.include_router(simulator.router,       prefix="/api/v1/simulator",         tags=["simulator"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations",   tags=["recommendations"])
app.include_router(dashboard.router,       prefix="/api/v1/dashboard",         tags=["dashboard"])
app.include_router(data_quality.router,    prefix="/api/v1/data-quality",      tags=["data-quality"])
```

### 18.2 Common Schemas

```python
# backend/app/schemas/common.py

from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 50

    @field_validator("page_size")
    @classmethod
    def cap_page_size(cls, v):
        return min(v, 200)

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

class ProvenanceSchema(BaseModel):
    evidence_sources: list[str]        # ["SYNTHETIC_HISTORICAL_EVENT", ...]
    calculation_method: str
    input_data_timestamps: dict
    is_synthetic: bool

class ErrorResponse(BaseModel):
    detail: str
    error_code: str                    # e.g., "SEGMENT_NOT_FOUND", "LEAKAGE_DETECTED"
```

### 18.3 Segment Endpoints

```python
# backend/app/routers/segments.py

router = APIRouter()

@router.get("", response_model=PaginatedResponse[SegmentSummary])
async def list_segments(
    road_class: RoadClass | None = Query(None),
    zone: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all road segments with optional filters."""
    ...

@router.get("/geojson", response_model=GeoJSONFeatureCollection)
async def segments_geojson(db: AsyncSession = Depends(get_db)):
    """
    GeoJSON FeatureCollection of all segments.
    Used by MapLibre to render the road network layer.
    Properties include: name, road_class, zone, ward,
    latest risk_category, latest pisi_category.
    """
    ...

@router.get("/{segment_id}", response_model=SegmentDetail)
async def get_segment(segment_id: str, db: AsyncSession = Depends(get_db)):
    """Full segment detail including latest PISI and risk prediction."""
    ...

@router.get("/{segment_id}/memory", response_model=RoadMemoryResponse)
async def get_road_memory(
    segment_id: str,
    event_type: list[str] | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    ...

@router.get("/{segment_id}/stress", response_model=PISIResponse)
async def get_stress_index(segment_id: str, db: AsyncSession = Depends(get_db)):
    """Latest PISI record for a segment."""
    ...

@router.get("/{segment_id}/risk", response_model=RiskPredictionResponse)
async def get_risk_prediction(segment_id: str, db: AsyncSession = Depends(get_db)):
    """Latest RiskPrediction for a segment."""
    ...

@router.post("/{segment_id}/risk/refresh", response_model=RiskPredictionResponse)
async def refresh_risk_prediction(segment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger a fresh ML prediction. Creates a new immutable RiskPrediction record.
    Uses datetime.now(UTC) as the feature_snapshot_timestamp.
    """
    ...
```

### 18.4 Conflict Endpoints

```python
# backend/app/routers/conflicts.py

@router.get("", response_model=PaginatedResponse[ConflictSummary])
async def list_conflicts(
    status: ConflictStatus | None = Query(None),
    severity: ConflictSeverity | None = Query(None),
    rule_id: str | None = Query(None),
    segment_id: str | None = Query(None),
    page: int = Query(1), page_size: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    ...

@router.get("/{conflict_id}", response_model=ConflictDetail)
async def get_conflict(conflict_id: str, db: AsyncSession = Depends(get_db)):
    """Full conflict detail including all explanation fields."""
    ...

@router.post("/detect", response_model=ConflictDetectionResult)
async def run_conflict_detection(
    segment_ids: list[str] | None = Body(None),
    db: AsyncSession = Depends(get_db),
    conflict_engine: ConflictEngine = Depends(get_conflict_engine),
):
    """
    Run conflict detection. If segment_ids provided, only for those segments.
    Otherwise runs for all segments. Idempotent.
    """
    ...

@router.patch("/{conflict_id}/status", response_model=ConflictDetail)
async def update_conflict_status(
    conflict_id: str,
    body: ConflictStatusUpdate,   # {status, resolution_note}
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge or resolve a conflict. resolution_note required for RESOLVED."""
    ...

@router.post("/simulate", response_model=CollisionSimulationResponse)
async def simulate_collision(
    body: HypotheticalProjectRequest,
    db: AsyncSession = Depends(get_db),
    simulator: CollisionSimulator = Depends(get_collision_simulator),
):
    """
    Project Collision Simulation. No DB writes.
    Returns conflicts the hypothetical project would create.
    """
    ...
```

### 18.5 ML Endpoints

```python
# backend/app/routers/ml.py

@router.get("/predict/{segment_id}", response_model=RiskPredictionResponse)
async def get_prediction(segment_id: str, db: AsyncSession = Depends(get_db)):
    """Return the latest stored RiskPrediction. Does not create a new one."""
    ...

@router.post("/predict/{segment_id}/refresh", response_model=RiskPredictionResponse)
async def refresh_prediction(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    prediction_service: PredictionService = Depends(get_prediction_service),
):
    """Create a fresh RiskPrediction record using the active model."""
    ...

@router.post("/batch-predict", response_model=BatchPredictResult)
async def batch_predict(
    db: AsyncSession = Depends(get_db),
    prediction_service: PredictionService = Depends(get_prediction_service),
):
    """Refresh predictions for all segments. Returns count of new records created."""
    ...

@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Model metadata, evaluation metrics, ablation results, backtesting folds.
    Reads from ml/evaluation/*.json — does not query the DB.
    """
    ...
```

### 18.6 Simulator Endpoint

```python
# backend/app/routers/simulator.py

@router.post("/compare", response_model=WhatIfComparisonResponse)
async def compare_scenarios(
    body: WhatIfRequest,
    db: AsyncSession = Depends(get_db),
    simulator: WhatIfSimulator = Depends(get_whatif_simulator),
):
    """
    Compare two scenarios. Returns metrics + narrative + provenance.
    No DB writes. Response includes simulation_label and provenance.
    """
    ...
```

### 18.7 Response Schema: RiskPredictionResponse

Full schema for the risk prediction API response, showing all required fields from FR-RISK-09:

```python
class FeatureExplanationSchema(BaseModel):
    name: str
    value: float
    importance: float
    direction: str            # "increases_risk" | "decreases_risk"
    timestamp_basis: str
    plain_language: str

class RiskPredictionResponse(BaseModel):
    id: str
    road_segment_id: str
    probability: float                          # 4 decimal places
    risk_category: str                          # CRITICAL|HIGH|MEDIUM|LOW
    prediction_timestamp: datetime              # ISO 8601
    feature_snapshot_timestamp: datetime        # ISO 8601
    prediction_horizon_days: int
    model_version: str
    model_type: str
    feature_group: str
    top_features: list[FeatureExplanationSchema]
    feature_snapshot: dict                      # full feature vector
    is_synthetic_input: bool
    provenance: ProvenanceSchema
    prediction_label: str = "ML Prediction — Not a confirmed event."
```

### 18.8 Validation and Error Handling (API Layer)

All validation is performed by Pydantic v2 at the request boundary. FastAPI automatically returns 422 Unprocessable Entity for validation failures.

Custom HTTP exceptions use a centralized exception handler:

```python
# backend/app/main.py

from fastapi import Request
from fastapi.responses import JSONResponse

class PipeWatchException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code

@app.exception_handler(PipeWatchException)
async def pipewatch_exception_handler(request: Request, exc: PipeWatchException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )
```

### 18.9 Pagination Pattern

All list endpoints use cursor-free page/page_size pagination. Repository methods accept `offset = (page-1) * page_size` and `limit = page_size`:

```python
class BaseRepository:
    async def paginate(self, db, stmt, page: int, page_size: int):
        total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
        items = (await db.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": math.ceil(total / page_size),
        }
```

### 18.10 Dependency Injection

Services and repositories are injected via FastAPI's `Depends` mechanism. A single `get_db` dependency provides the async session. Services are instantiated once per request through factory functions:

```python
# backend/app/dependencies.py

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

def get_conflict_engine(db: AsyncSession = Depends(get_db)) -> ConflictEngine:
    return ConflictEngine(
        registry=build_default_registry(),
        conflict_repo=ConflictRepository(),
        project_repo=ProjectRepository(),
        segment_repo=SegmentRepository(),
        temporal_buffer_days=settings.conflict_buffer_days,
    )
```

---

## 19. Frontend Design

### 19.1 Design Language

PipeWatch targets **infrastructure planners**, not consumers. The UI must feel like an operations control centre — not a generic admin template, a citizen portal, or a social product.

**Visual principles:**
- Dark base: `slate-900` / `slate-800` backgrounds. Maps and data panels sit on dark surfaces.
- High-contrast data: White and `slate-100` for primary data text. Color is reserved for status (risk levels, severity).
- Color vocabulary is consistent and never decorative:
  - CRITICAL → `red-500`
  - HIGH → `orange-400`
  - MEDIUM → `yellow-400`
  - LOW → `green-400`
  - SYNTHETIC DATA → `amber-400` accent (banner color)
  - ML PREDICTION → `violet-400` pill/badge
  - ADVISORY → `sky-400` pill/badge
  - DETERMINISTIC → `teal-400` pill/badge
- Typography: mono or tabular numerals for counts and scores. Proportional for labels.
- Dense but readable: compact row heights, clear section dividers. No excessive whitespace.

### 19.2 Application Shell

```
┌─────────────────────────────────────────────────────────────┐
│  SYNTHETIC DATA BANNER (amber, full-width, always visible)  │
│  "DEMO — Synthetic Infrastructure Records — Not Real Data"  │
├──────────┬──────────────────────────────────────────────────┤
│          │  Page Header: title + breadcrumb + refresh btn   │
│ Sidebar  ├──────────────────────────────────────────────────┤
│  (fixed) │                                                  │
│          │           Page Content                           │
│  Nav     │                                                  │
│  items:  │                                                  │
│  ·Dashboard                                                 │
│  ·Map                                                       │
│  ·Conflicts                                                 │
│  ·Projects                                                  │
│  ·Gantt                                                     │
│  ·Simulator                                                 │
│  ·Recommendations                                           │
│  ·Model Info                                                │
│  ·Data Quality                                              │
└──────────┴──────────────────────────────────────────────────┘
```

The `SyntheticDataBanner` component renders at the root layout level and cannot be dismissed. It renders above the sidebar/header on every page.

### 19.3 Page: Dashboard (`/dashboard`)

**Layout:** 2-column responsive grid. Left column: KPI widgets (stacked). Right column: charts (stacked).

**KPI widget row (top):**
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Open         │ │ Active       │ │ High-Risk    │ │ Pending      │ │ Data         │
│ Conflicts    │ │ Projects     │ │ Segments     │ │ Recommends   │ │ Freshness    │
│              │ │              │ │              │ │              │ │              │
│  [12]        │ │  [8]         │ │  [5]         │ │  [3]         │ │ 2h ago       │
│  HIGH:4      │ │              │ │  CRIT:2      │ │  HIGH:1      │ │              │
│  MED:6       │ │              │ │  HIGH:3      │ │              │ │              │
│  LOW:2       │ │              │ │              │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```
Each KPI widget is a link to the relevant filtered view.

**Charts row:**
- Left: Excavation frequency by utility type (vertical bar chart, Recharts `BarChart`)
- Centre: Conflicts detected per month, last 12 months (line chart, Recharts `LineChart`)
- Right: Risk distribution across all segments (donut, Recharts `PieChart`)

**Tables row:**
- Top 10 High-PISI Segments (ranked table, clicking a segment navigates to map with segment selected)
- Open Conflicts summary (sortable table, clicking a row opens conflict detail)

**Data fetch:** Single `GET /api/v1/dashboard/summary` call. React Query with manual refetch on "Refresh All" button.

### 19.4 Page: Map (`/map`)

```
┌────────────────────────────────────────────────────────────┐
│  Overlay selector: [Default] [Risk] [PISI] [Conflicts]     │
│                    [Excavation Frequency]                   │
│  ┌────────────────────────────────────┐ ┌─────────────────┐│
│  │                                    │ │ Segment Detail  ││
│  │         MapLibre GL Map            │ │ Panel           ││
│  │    (road segments colored by       │ │                 ││
│  │     active overlay mode)           │ │ [Shown on click]││
│  │                                    │ │                 ││
│  │  [Legend bottom-left]              │ │                 ││
│  └────────────────────────────────────┘ └─────────────────┘│
│  Filter bar: utility_type | status | date range            │
└────────────────────────────────────────────────────────────┘
```

**MapLibre configuration:**
- Base style: `https://demotiles.maplibre.org/style.json` (open, no API key) or a self-hosted simple style
- Road segment layer: GeoJSON source from `GET /api/v1/segments/geojson`
- Layer paint: `line-color` expression reads `risk_category` or `pisi_category` from feature properties, mapped to color constants
- On segment click: `map.on('click', 'segments-layer', handler)` → sets `selectedSegmentId` in Zustand store → `SegmentDetailPanel` fetches full detail

**SegmentDetailPanel sub-components (rendered on segment click):**
```
SegmentDetailPanel
├── SegmentHeader (name, road_class badge, ward, zone)
├── PISIPanel (index_value, category badge, component bar chart, disclaimer, formula disclosure)
├── RiskPredictionPanel (probability %, category badge, "ML Prediction" label, top features list)
├── ExcavationSummary (counts: all-time, 24m)
├── ActiveProjectsList (compact list)
└── ViewRoadMemoryLink → /segments/{id}/memory
```

**Overlay switching:** Changes a Zustand `activeOverlay` atom. The `SegmentLayer` component reacts to this atom and repaints the MapLibre layer style expression accordingly.

**Risk overlay invariant:** When risk overlay is active, a `MLPredictionDisclaimer` component is absolutely positioned over the map bottom-center: "ML Predictions — Not Confirmed Events."

### 19.5 Page: Conflict Radar (`/conflicts`)

**Layout:** Summary stats bar → filter bar → sortable table → detail slide-over panel.

**Summary stats bar:**
```
Total Open: 12   HIGH: 4 (red)   MEDIUM: 6 (orange)   LOW: 2 (yellow)
```

**Table columns:** Severity badge | Rule ID | Project A | Project B | Segment | Overlap Days | Detected | Status

**Sort:** Default: severity DESC, detected DESC. User can change.

**ConflictExplanationPanel (slide-over on row click):**
```
ConflictExplanationPanel
├── SeverityBadge + RuleIdBadge
├── Explanation block (spatial_reason, temporal_reason, excavation_involvement)
├── Affected corridor
├── Project A detail (link)
├── Project B detail (link)
├── Segment link (navigates to map)
├── "Run What-If Simulation" button → /simulator?projectA=...&projectB=...
└── StatusActions (Acknowledge / Mark Resolved + note input)
```

**"Check Hypothetical Project" button** opens the Collision Simulator form pre-populated with the segment ID.

### 19.6 Page: Projects (`/projects`)

Standard filterable data table of all projects. Columns: Name | Utility type | Agency | Status | Planned dates | Requires excavation | Segments. Filter bar: utility_type, status, date range, segment, agency.

Clicking a row opens project detail (read-only in v1.0 — full CRUD is API-accessible but not required in the UI for all fields).

### 19.7 Page: Gantt (`/gantt`)

```
Timeline axis: months ◄──────────────────────────────►
               Jan   Feb   Mar   Apr   May   Jun ...
Water main     ██████████████░░░░░░░░░████████
Fiber laying          ████████████████████████
                          ⚠ conflict (red border)
Resurfacing                              ████████
```

- Implemented with Recharts `BarChart` in horizontal mode, or a custom SVG Gantt with React.
- Bars are colored by utility type (7 colors, consistent with the map legend).
- Conflict indicator: a red/striped overlay on overlapping bars for the same segment.
- Tooltip on hover shows: project name, agency, dates, affected segments, conflict rule ID if applicable.
- Controls: zoom (month / quarter / year buttons), filter by utility type / segment / status / agency, planned vs actual toggle.

### 19.8 Page: Road Memory (`/segments/[id]/memory`)

```
Segment: Rajpur Road – Segment 3 (ARTERIAL, Rajpur zone)
[Filter: All types | Excavation | Resurfacing | Project] [Date range picker]

━━━━ 2022 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 EXCAVATION  ⚠ FREQUENT EXCAVATION WINDOW
Mar 1 – Mar 20, 2022
Water Main Phase 2 · WATER · Jal Sansthan
[SYNTHETIC] [SYNTHETIC_HISTORICAL_EVENT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟩 RESURFACING
Mar 27 – Apr 3, 2022
Full resurfacing, warranty=24mo · PWD
[SYNTHETIC]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 EXCAVATION  ⚠ WARRANTY BREACH
Jun 10 – Jun 25, 2022
Fiber Laying Phase 1 · TELECOM · BSNL
[SYNTHETIC] [SYNTHETIC_HISTORICAL_EVENT]
```

Each `TimelineEvent` renders as a `TimelineEvent` component with: icon, type label, date badge, project info, provenance badges, and warning badges.

**Download button:** `GET /api/v1/segments/{id}/memory` with `Accept: application/json` → file download as JSON.

### 19.9 Page: What-If Simulator (`/simulator`)

**Step 1:** Select a road segment (searchable dropdown).

**Step 2:** Define Scenario A — add 2+ events (utility type, start/end dates, excavation/resurfacing toggles).

**Step 3:** Define Scenario B — same form.

**Step 4:** Click "Compare Scenarios" → `POST /api/v1/simulator/compare`.

**Result panel:**
```
Scenario A: "Separate Work"        Scenario B: "Coordinated"
──────────────────────────────────────────────────────────────
Excavations:        4              2   ✓ better
Repeat excavations: 1              0   ✓ better
Conflicts:          2              0   ✓ better
Disturbance days:   65             35  ✓ better
Coord. opportunities: 1            2   ✓ better
──────────────────────────────────────────────────────────────
Narrative:
"Scenario B avoids 1 repeat excavation by coordinating the water
and telecom work into a single excavation window. Scenario B
reduces total road disturbance by 30 days."

⚠  Simulation — Not a Committed Schedule.
    No monetary figures are estimated.
    provenance: SIMULATION
```

The `ScenarioComparisonTable` highlights the winning scenario for each metric with a checkmark and color.

### 19.10 Page: Collision Simulator (`/collision`)

**Form:** Enter hypothetical project details (same fields as `HypotheticalProjectRequest`). The form has a clear header: "Check Hypothetical Project — Results are not saved."

**Result panel:** List of detected collisions, each showing: conflicting project name, severity badge, rule ID, overlap dates, affected segment name, current PISI and risk category for that segment.

Persistent label: "Simulation — Not a Confirmed Conflict. The hypothetical project has not been saved."

### 19.11 Page: PISI Detail (embedded in Segment Detail)

The `PISIPanel` component renders:
- Large numeric value with category color
- Horizontal stacked bar chart (5 components, each weighted)
- Expandable "How is this calculated?" section showing the formula
- Disclaimer: "This is a derived index, not a physical measurement of road condition."
- `calculated_at` and `formula_version` in small text

### 19.12 Page: Model Information (`/model-info`)

```
Active Model: RandomForestClassifier v1.0 (trained 2026-10-01)
Feature Group: C (Full feature set, 12 features)
Training data: synthetic_v1_seed42

Final Test Metrics (2025 held-out):
  ROC-AUC: 0.77    F1: 0.72    Precision: 0.74    Recall: 0.70

vs. Rule Baseline (2025):
  ROC-AUC: 0.63   (Δ +0.14)

Calibration Curve: [chart]

Backtesting Folds:
  Fold 1 (train→2022, val:2023): ROC-AUC 0.76
  Fold 2 (train→2023, val:2024): ROC-AUC 0.78

Ablation Results:
  Group A (historical only):    ROC-AUC 0.72
  Group B (+ project activity): ROC-AUC 0.76  (Δ +0.04)
  Group C (full):               ROC-AUC 0.77  (Δ +0.01)

⚠ Trained on synthetic data. Relationships are simulated assumptions.
  Performance on real Dehradun data is unknown.

[Download evaluation report (JSON)]
```

### 19.13 State Management

| State | Location | Reason |
|---|---|---|
| Selected segment ID | Zustand `mapStore` | Shared between map canvas and detail panel |
| Active overlay mode | Zustand `mapStore` | Drives MapLibre paint expression |
| Server data (segments, projects, conflicts, etc.) | React Query | Caching, refetch, loading/error states |
| Form state (simulator, collision, project creation) | React Hook Form | Local form state, validation |
| UI open/close (panels, modals) | React local state | No cross-component sharing needed |

### 19.14 API Client Pattern

```typescript
// frontend/src/lib/api/client.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new APIError(res.status, body.detail ?? "Unknown error", body.error_code);
  }
  return res.json() as Promise<T>;
}

// Domain-specific clients wrap apiFetch with typed return types:
// frontend/src/lib/api/segments.ts
export const getSegmentsGeoJSON = () =>
  apiFetch<GeoJSONFeatureCollection>("/api/v1/segments/geojson");

export const getSegmentDetail = (id: string) =>
  apiFetch<SegmentDetail>(`/api/v1/segments/${id}`);
```

### 19.15 Loading, Error, and Empty States

Every data-fetching component must handle three states beyond the happy path:

| State | Component | Behavior |
|---|---|---|
| Loading | `LoadingState` | Skeleton cards matching the layout of the loaded content |
| Error | `ErrorState` | Error message + error_code from API + retry button |
| Empty | `EmptyState` | Descriptive message explaining why there is no data (e.g., "No conflicts detected for this segment.") |

---

## 20. Main User Flow

### 20.1 End-to-End Scenario: Planner Investigating a Conflict

This sequence traces the full user journey described in FR-REC through the system layers.

```
ACTOR: Priya (Municipal Infrastructure Planner)

Step 1: Open PipeWatch → Dashboard
────────────────────────────────────
Browser → GET /api/v1/dashboard/summary
       ← {open_conflicts: 12, high_risk_segments: 5, ...}
Dashboard renders. Priya sees: 4 HIGH conflicts, 5 high-risk segments.

Step 2: Navigate to Map → select segment
────────────────────────────────────────
Browser → GET /api/v1/segments/geojson
       ← GeoJSON FeatureCollection (risk_category, pisi_category in properties)
Map renders. Risk overlay active. Priya sees a RED segment on Rajpur Road.
Clicks the segment.

Browser → GET /api/v1/segments/{seg_id}
       ← SegmentDetail {name, pisi, risk_prediction, excavation_counts, projects}
SegmentDetailPanel opens.
  · PISI: 78.2 (CRITICAL) — "Derived index, not a physical measurement"
  · Risk: 74% (HIGH) — "ML Prediction — Not a confirmed event"
  · Top feature: "excavation_count_24m=3 → increases risk"

Step 3: View Road Memory
────────────────────────
Priya clicks "View Road Memory".
Browser → GET /api/v1/segments/{seg_id}/memory
       ← {events: [...], summary: {warranty_breaches: 1, ...}}
RoadMemoryTimeline renders.
Priya sees: 3 excavations in 2022–2024, 1 WARRANTY BREACH flag in 2023.

Step 4: Open Conflict Radar
────────────────────────────
Priya navigates to /conflicts.
Browser → GET /api/v1/conflicts?status=OPEN&severity=HIGH
       ← PaginatedResponse [{...SPATIAL_TEMPORAL_EXCAVATION_01...}]
Conflict table shows a HIGH conflict between Water Main and Fiber Laying
on the same segment.

Step 5: Inspect Conflict Detail
────────────────────────────────
Priya clicks the conflict row.
ConflictExplanationPanel opens (no API call — data already in the list response).
  · Rule: SPATIAL_TEMPORAL_EXCAVATION_01
  · Spatial reason: "Both affect Rajpur Road – Seg 3"
  · Temporal reason: "Overlap by 5 days (15–20 Jan)"
  · Excavation: "Both projects require excavation"

Step 6: Launch What-If Simulator
──────────────────────────────────
Priya clicks "Run What-If Simulation".
Browser navigates to /simulator?segmentId={seg_id}&projectA={id}&projectB={id}
WhatIfScenarioForm pre-populated with the two conflicting projects.
Priya defines:
  Scenario A: Water (1 Jan–20 Jan) then Fiber (15 Jan–10 Feb) — separate
  Scenario B: Water + Fiber combined (1 Jan–10 Feb) — coordinated

Browser → POST /api/v1/simulator/compare
       ← {metrics_a, metrics_b, narrative, provenance}

ScenarioComparisonTable renders:
  Repeat excavations: A=1, B=0 ✓
  Disturbance days:   A=50, B=40 ✓
  Narrative: "Scenario B avoids 1 repeat excavation..."
  Label: "Simulation — Not a Committed Schedule."

Step 7: Run Collision Simulation for a new hypothetical project
───────────────────────────────────────────────────────────────
Priya wants to add a drainage project. Opens /collision.
Fills form: utility_type=DRAINAGE, start=Feb 15, end=Mar 10, segment={seg_id}.

Browser → POST /api/v1/conflicts/simulate
       ← {collisions: [{conflicting_project: Fiber Laying, severity: MEDIUM, ...}]}

CollisionResultPanel renders:
  · MEDIUM conflict with "Fiber Laying (BSNL)"
  · Affected segment: Rajpur Road – Seg 3
  · Current PISI: 78.2 (CRITICAL)
  · Risk: 74% HIGH (ML Prediction)
Label: "Simulation — Not a Confirmed Conflict. The hypothetical project has not been saved."

Step 8: Review Recommendation
───────────────────────────────
Priya navigates to /recommendations.
Browser → GET /api/v1/recommendations?status=PENDING
       ← [{type: MERGE_WINDOW, priority: HIGH, title: "Merge excavation windows..."}]

RecommendationCard renders for the MERGE_WINDOW recommendation:
  · Rationale: "Water Main and Fiber Laying both excavate Rajpur Road – Seg 3..."
  · Evidence: conflict ID, overlap_days=5
  · Label: "Advisory — Requires Planner Review."

Step 9: Accept recommendation
──────────────────────────────
Priya clicks ACCEPT.
Browser → PATCH /api/v1/recommendations/{id}/decision
       ← {status: ACCEPTED, decided_at: ...}
Recommendation moves to History.
```

### 20.2 Sequence Diagram — Conflict Detection Trigger

```
Frontend         API              ConflictEngine        DB
   │              │                     │                │
   │ POST /projects│                     │                │
   ├─────────────►│                     │                │
   │              │ project_repo.create()                 │
   │              ├───────────────────────────────────────►│
   │              │◄───────────────────────────────────────┤
   │              │                     │                │
   │              │ conflict_engine.detect_for_project()  │
   │              ├────────────────────►│                │
   │              │                     │ fetch projects │
   │              │                     ├───────────────►│
   │              │                     │◄───────────────┤
   │              │                     │ apply 4 rules  │
   │              │                     │ idempotency    │
   │              │                     │ check          │
   │              │                     ├───────────────►│
   │              │                     │◄───────────────┤
   │              │                     │ insert new     │
   │              │                     │ conflicts      │
   │              │                     ├───────────────►│
   │              │◄────────────────────┤                │
   │ 201 Created  │                     │                │
   │◄─────────────┤                     │                │
```

---

## 21. Data Provenance

### 21.1 ProvenanceService

```python
# backend/app/services/provenance.py

from dataclasses import dataclass
from typing import Literal

ProvenanceCategory = Literal[
    "SYNTHETIC_HISTORICAL_EVENT",
    "SYNTHETIC_PROJECT",
    "DETERMINISTIC_CALCULATION",
    "ML_PREDICTION",
    "SIMULATION",
]

@dataclass
class Provenance:
    evidence_sources: list[ProvenanceCategory]
    calculation_method: str      # rule_id, formula version, model version, or "whatif_simulator_v1"
    input_data_timestamps: dict  # {"feature_snapshot_timestamp": "...", "calculated_at": "..."}
    is_synthetic: bool

class ProvenanceService:
    """
    Stateless. All methods are static/class-level.
    """

    @staticmethod
    def build(
        evidence_sources: list[ProvenanceCategory],
        calculation_method: str,
        input_data_timestamps: dict | None = None,
        is_synthetic: bool = True,
    ) -> Provenance:
        return Provenance(
            evidence_sources=evidence_sources,
            calculation_method=calculation_method,
            input_data_timestamps=input_data_timestamps or {},
            is_synthetic=is_synthetic,
        )

    @staticmethod
    def for_pisi(formula_version: str, calculated_at: str) -> Provenance:
        return ProvenanceService.build(
            evidence_sources=["DETERMINISTIC_CALCULATION"],
            calculation_method=f"PISI-{formula_version}",
            input_data_timestamps={"calculated_at": calculated_at},
        )

    @staticmethod
    def for_ml_prediction(
        model_version: str, feature_snapshot_ts: str
    ) -> Provenance:
        return ProvenanceService.build(
            evidence_sources=["ML_PREDICTION"],
            calculation_method=f"model-{model_version}",
            input_data_timestamps={"feature_snapshot_timestamp": feature_snapshot_ts},
        )

    @staticmethod
    def for_conflict(rule_id: str, detected_at: str) -> Provenance:
        return ProvenanceService.build(
            evidence_sources=["DETERMINISTIC_CALCULATION"],
            calculation_method=rule_id,
            input_data_timestamps={"detected_at": detected_at},
        )

    @staticmethod
    def for_simulation() -> Provenance:
        return ProvenanceService.build(
            evidence_sources=["SIMULATION"],
            calculation_method="whatif_simulator_v1",
        )
```

### 21.2 Provenance Propagation Map

| Output | Evidence Sources | Calculation Method |
|---|---|---|
| ExcavationEvent (API response) | `SYNTHETIC_HISTORICAL_EVENT` | `data_source` field |
| ResurfacingEvent (API response) | `SYNTHETIC_HISTORICAL_EVENT` | `data_source` field |
| UtilityProject (API response) | `SYNTHETIC_PROJECT` | n/a |
| ConflictRecord | `DETERMINISTIC_CALCULATION` | rule_id |
| RiskPrediction | `ML_PREDICTION` | `model-{version}` |
| InfrastructureStressIndex | `DETERMINISTIC_CALCULATION` | `PISI-{formula_version}` |
| CoordinationRecommendation | `DETERMINISTIC_CALCULATION` + optionally `ML_PREDICTION` | recommendation rule type |
| WhatIfComparisonResult | `SIMULATION` | `whatif_simulator_v1` |
| CollisionSimulationResult | `SIMULATION` | `conflict_rule_pipeline_v1` |
| RoadMemory event | inherited from source record | inherited |

### 21.3 Frontend Provenance Display

```typescript
// frontend/src/components/shared/ProvenanceBadge.tsx

const PROVENANCE_STYLES: Record<string, {label: string; className: string}> = {
  SYNTHETIC_HISTORICAL_EVENT: { label: "SYNTHETIC",    className: "bg-amber-900 text-amber-300" },
  SYNTHETIC_PROJECT:          { label: "SYNTHETIC",    className: "bg-amber-900 text-amber-300" },
  DETERMINISTIC_CALCULATION:  { label: "CALCULATED",   className: "bg-teal-900 text-teal-300" },
  ML_PREDICTION:              { label: "ML PREDICTION",className: "bg-violet-900 text-violet-300" },
  SIMULATION:                 { label: "SIMULATION",   className: "bg-sky-900 text-sky-300" },
};
```

Every data item in the Road Memory timeline, prediction panels, conflict detail panels, and recommendation cards renders a `ProvenanceBadge` indicating its source category.

---

## 22. Testing Architecture

### 22.1 Backend Unit Tests

Location: `backend/tests/unit/`

**Key invariants tested:**

| Test File | Invariants |
|---|---|
| `test_conflict_rules.py` | Each rule returns expected severity/rule_id; spatial_reason and temporal_reason are non-null when applicable; idempotency (same inputs = same output); boundary conditions (exactly 30-day gap) |
| `test_pisi_calculator.py` | Zero-event segment scores 0; max-input segment approaches 100; each component in isolation; weights sum to 1.0; formula_version is set |
| `test_road_memory.py` | Warranty breach flagged correctly; frequent excavation window flagged at 3+ in 24m; premature excavation flagged under 90 days; chronological sort preserved |
| `test_whatif_simulator.py` | Each metric computed correctly with known fixture inputs; narrative generated from data (not empty); simulation label present |
| `test_collision_simulator.py` | Zero DB writes confirmed via record count assertions; SIMULATION provenance set; same rule logic as stored conflict engine |
| `test_provenance.py` | Each provenance builder returns correct evidence_sources; is_synthetic=True for all synthetic inputs |

### 22.2 Data Leakage Tests

Location: `backend/tests/leakage/`

These tests must run as part of the standard `pytest` suite, not as separate scripts.

```python
# backend/tests/leakage/test_feature_leakage.py

def test_future_excavation_excluded_from_features():
    """
    Given: A snapshot_ts of 2023-06-01
    And: An excavation event with start_date = 2023-07-01 (future)
    When: PointInTimeFeatureBuilder.build() is called
    Then: LeakageError is raised
    """
    ...

def test_active_project_count_excludes_future_projects():
    """
    Given: A project created_at=2023-08-01 (after snapshot_ts)
    When: active_project_count is computed at snapshot_ts=2023-06-01
    Then: The project is NOT counted
    """
    ...

def test_target_is_strictly_future():
    """
    Given: An excavation event with start_date = snapshot_ts (same day)
    When: build_target() is called
    Then: target = 0 (same-day events are NOT in the prediction window)
    """
    ...

def test_historical_conflict_count_excludes_future_detections():
    """
    Given: A conflict with detected_at after snapshot_ts
    When: historical_conflict_count is computed
    Then: The conflict is NOT counted
    """
    ...
```

### 22.3 API Integration Tests

Location: `backend/tests/integration/`

Uses `pytest-asyncio` + `httpx.AsyncClient` against a test SQLite database populated from fixtures.

```python
# backend/tests/conftest.py

@pytest.fixture(scope="session")
async def test_db():
    """In-memory SQLite for tests. Schema created from Alembic migrations."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def client(test_db):
    app.dependency_overrides[get_db] = override_get_db(test_db)
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
```

**Key integration tests:**

```python
# test_conflicts_api.py

async def test_high_conflict_detected_on_project_creation(client):
    """
    Given: Project A (water, segment S1, 1 Jan–20 Jan, excavation=True)
    When: Project B (telecom, segment S1, 15 Jan–10 Feb, excavation=True) is POSTed
    Then: GET /conflicts returns 1 record with severity=HIGH,
          rule_id=SPATIAL_TEMPORAL_EXCAVATION_01,
          overlap_days=5, spatial_reason non-null, temporal_reason non-null
    """
    ...

async def test_conflict_detection_is_idempotent(client):
    """
    Given: Two conflicting projects already in DB
    When: POST /conflicts/detect is called twice
    Then: Second call creates 0 new records; total count unchanged
    """
    ...

async def test_collision_simulation_creates_no_db_records(client):
    """
    Given: An existing project in DB
    When: POST /conflicts/simulate is called with a hypothetical project
    Then: All DB record counts are unchanged after the call
    And: Response contains collisions list and SIMULATION provenance
    """
    ...
```

### 22.4 ML Tests

```python
# backend/tests/leakage/test_feature_leakage.py + scripts tests

def test_training_script_produces_model_and_report():
    """Run scripts/train_model.py --seed 42 --dry-run; assert model file exists."""
    ...

def test_evaluation_report_complete():
    """Load eval_report_*.json; assert all required keys present."""
    required_keys = [
        "fold_results", "best_params", "final_test_metrics",
        "baseline_comparison", "limitations"
    ]
    ...

def test_prediction_schema_valid():
    """
    Call prediction service with known feature vector.
    Assert: probability in [0,1], risk_category in enum,
            top_features non-empty, feature_snapshot_timestamp present,
            feature_snapshot_timestamp < prediction_timestamp.
    """
    ...

def test_synthetic_seed_reproducibility():
    """Run generator twice with seed=42; assert output is byte-identical."""
    ...

def test_risk_prediction_immutability():
    """
    Create a RiskPrediction record. Attempt to update it.
    Assert: The repository raises an error or the record is unchanged.
    """
    ...
```

### 22.5 Frontend Tests

Location: `frontend/tests/`

```typescript
// components/PISIPanel.test.tsx

test("renders PISI disclaimer text", () => {
  render(<PISIPanel data={mockPISI} />);
  expect(screen.getByText(
    /This is a derived index, not a physical measurement of road condition/i
  )).toBeInTheDocument();
});

// components/RiskBadge.test.tsx
test("renders ML Prediction label when prediction data present", () => {
  render(<RiskPredictionPanel data={mockPrediction} />);
  expect(screen.getByText(/ML Prediction — Not a confirmed event/i)).toBeInTheDocument();
});

// app/layout.test.tsx
test("synthetic data banner renders on every page", () => {
  render(<RootLayout><div /></RootLayout>);
  expect(screen.getByText(/DEMO — Synthetic Infrastructure Records/i)).toBeInTheDocument();
});

// utils/colors.test.ts
test("risk category maps to correct color", () => {
  expect(riskCategoryToColor("CRITICAL")).toBe("red-500");
  expect(riskCategoryToColor("HIGH")).toBe("orange-400");
  expect(riskCategoryToColor("MEDIUM")).toBe("yellow-400");
  expect(riskCategoryToColor("LOW")).toBe("green-400");
});
```

### 22.6 Property-Based Tests

For the PISI calculator, property-based tests using `hypothesis` verify algebraic properties:

```python
from hypothesis import given, strategies as st

@given(
    exc_count=st.integers(min_value=0, max_value=50),
    util_count=st.integers(min_value=0, max_value=7),
    days_exc=st.floats(min_value=0, max_value=3650),
    days_res=st.floats(min_value=0, max_value=3650),
    conflicts=st.integers(min_value=0, max_value=20),
    warranty=st.booleans(),
)
def test_pisi_always_in_range(exc_count, util_count, days_exc, days_res, conflicts, warranty):
    calc = PISICalculator()
    result = calc.calculate(exc_count, util_count, days_exc, days_res, conflicts, warranty)
    assert 0.0 <= result.index_value <= 100.0
    assert result.index_category in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
```

---

## 23. Error Handling

### 23.1 Error Code Registry

All application errors use a documented `error_code` string. HTTP status follows standard semantics.

| Error Code | HTTP Status | Trigger |
|---|---|---|
| `SEGMENT_NOT_FOUND` | 404 | `segment_id` does not exist in DB |
| `PROJECT_NOT_FOUND` | 404 | `project_id` does not exist |
| `CONFLICT_NOT_FOUND` | 404 | `conflict_id` does not exist |
| `PREDICTION_NOT_FOUND` | 404 | No prediction exists for this segment |
| `INVALID_DATE_RANGE` | 422 | `end_date <= start_date` |
| `INVALID_GEOMETRY` | 422 | GeoJSON geometry is malformed or not a LineString |
| `ML_MODEL_NOT_LOADED` | 503 | Model artifact missing or failed to load at startup |
| `LEAKAGE_DETECTED` | 500 | Feature builder detected future data in input (programming error) |
| `INVALID_FEATURE_SNAPSHOT` | 422 | feature_snapshot JSON is malformed |
| `SIMULATION_FAILURE` | 500 | Unexpected error in simulator computation |
| `DB_WRITE_IN_SIMULATION` | 500 | Invariant violation: DB write attempted during simulation |
| `RESOLUTION_NOTE_REQUIRED` | 422 | Conflict marked RESOLVED without resolution_note |
| `DECISION_NOTE_REQUIRED` | 422 | Recommendation REJECTED without decision_note |
| `CONFLICT_ALREADY_RESOLVED` | 409 | Attempt to modify a RESOLVED conflict |
| `RECOMMENDATION_NOT_PENDING` | 409 | Attempt to decide on a non-PENDING recommendation |

### 23.2 Service Layer Error Handling Pattern

```python
# Services raise domain exceptions; API layer catches and converts.

class PipeWatchNotFoundError(PipeWatchException):
    def __init__(self, entity: str, id: str):
        super().__init__(
            status_code=404,
            detail=f"{entity} with id '{id}' not found.",
            error_code=f"{entity.upper()}_NOT_FOUND",
        )

class PipeWatchValidationError(PipeWatchException):
    def __init__(self, detail: str, error_code: str):
        super().__init__(status_code=422, detail=detail, error_code=error_code)

class PipeWatchInvariantError(PipeWatchException):
    """For programming errors / violated invariants (e.g., leakage detected)."""
    def __init__(self, detail: str, error_code: str):
        super().__init__(status_code=500, detail=detail, error_code=error_code)
```

### 23.3 ML Fallback

If the ML model artifact is missing at startup, the `PredictionService` initializes in **fallback mode** using `RuleBaseline`. All predictions will be labeled `"Rule-Based Estimate — Not an ML Prediction."` and `model_type = "RuleBaseline"`. The API does not return a 503; it returns predictions with the fallback label.

If the artifact path is configured but the file does not exist, the application **logs a warning** and enters fallback mode. It does not crash.

### 23.4 Frontend Error Handling

```typescript
// All API calls go through apiFetch which throws APIError on non-2xx.
// React Query's onError callback renders <ErrorState />.

class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public errorCode: string,
  ) { super(detail); }
}

// Component usage:
const { data, isLoading, isError, error } = useQuery({
  queryKey: ["segment", segmentId],
  queryFn: () => getSegmentDetail(segmentId),
});

if (isLoading) return <LoadingState />;
if (isError) return <ErrorState error={error} />;
```

---

## 24. Configuration

### 24.1 Backend Settings

```python
# backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./pipewatch.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # ML
    ml_model_path: str = "models/randomforestclassifier_v1.0_20261001.joblib"
    ml_prediction_horizon_days: int = 180
    ml_feature_group: str = "C"

    # Conflict engine
    conflict_buffer_days: int = 30

    # Synthetic data
    synthetic_seed: int = 42
    synthetic_data_version: str = "v1"

    # Feature store
    feature_store_path: str = "data/feature_store/features_v1.parquet"

    # PISI
    pisi_formula_version: str = "v1.0"

settings = Settings()
```

### 24.2 `.env.example`

```
# Copy to .env and adjust values. Never commit .env.

# Database
DATABASE_URL=sqlite+aiosqlite:///./pipewatch.db

# API server
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000

# ML
ML_MODEL_PATH=models/randomforestclassifier_v1.0_20261001.joblib
ML_PREDICTION_HORIZON_DAYS=180
ML_FEATURE_GROUP=C

# Conflict engine
CONFLICT_BUFFER_DAYS=30

# Synthetic data
SYNTHETIC_SEED=42
SYNTHETIC_DATA_VERSION=v1

# Feature store
FEATURE_STORE_PATH=data/feature_store/features_v1.parquet
```

### 24.3 Frontend Environment

```
# frontend/.env.local.example
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 24.4 No Hard-Coded Values Checklist

| Value | Location | How configured |
|---|---|---|
| Database URL | `Settings.database_url` | `DATABASE_URL` env var |
| ML model path | `Settings.ml_model_path` | `ML_MODEL_PATH` env var |
| Prediction horizon | `Settings.ml_prediction_horizon_days` | `ML_PREDICTION_HORIZON_DAYS` env var |
| Conflict buffer | `Settings.conflict_buffer_days` | `CONFLICT_BUFFER_DAYS` env var |
| Synthetic seed | `Settings.synthetic_seed` | `SYNTHETIC_SEED` env var; also `--seed` CLI arg |
| CORS origin | `Settings.frontend_url` | `FRONTEND_URL` env var |
| PISI weights | `WEIGHTS` dict in `pisi_calculator.py` | Module constant (formula-defined); not env var |
| API base URL (frontend) | `process.env.NEXT_PUBLIC_API_URL` | `.env.local` |

> **Note on PISI weights:** The formula weights are part of the documented formula specification (`PISI-v1.0`), not runtime configuration. Changing them constitutes a formula version bump, not a config change.

---

## 25. Development Strategy

### 25.1 Phase Overview

Each phase must result in a **runnable, testable increment**. No phase leaves the system in a broken or untestable state.

| Phase | Name | Deliverable | Runnable After? |
|---|---|---|---|
| 1 | Foundation | Repo structure, linting, CI config, env setup | ✓ (empty app starts) |
| 2 | Database & Migrations | All ORM models, Alembic migrations, seed loader | ✓ (DB populated) |
| 3 | Synthetic Data Engine | `generate_synthetic_data.py`, reproducibility test | ✓ (DB has data) |
| 4 | Core Backend APIs | CRUD endpoints for segments, projects, excavations, resurfacing | ✓ (API returns data) |
| 5 | Map Frontend | Next.js shell, MapLibre map, segment layer, detail panel | ✓ (map loads) |
| 6 | Conflict Engine | 4 rules, detection API, idempotency | ✓ (conflicts detected) |
| 7 | Collision Simulation | `POST /conflicts/simulate`, zero-write guarantee | ✓ |
| 8 | Road Memory | Timeline assembly, warning flags, JSON export | ✓ |
| 9 | PISI | Calculator, service, recalculate API, map overlay | ✓ |
| 10 | ML Feature Store | `build_feature_store.py`, leakage validator, all tests | ✓ (Parquet built) |
| 11 | ML Models & Backtesting | Train/eval scripts, backtest protocol, model artifacts | ✓ (model in /models) |
| 12 | Explainability | SHAP integration, top_features in prediction response | ✓ |
| 13 | What-If Simulator | Scenario form, metrics engine, narrative, API | ✓ |
| 14 | Recommendation Engine | 4 rules, recommendation API, decision workflow | ✓ |
| 15 | Dashboard Integration | Dashboard API, all widgets, charts | ✓ |
| 16 | Testing & Hardening | Full test suite, error states, edge cases | ✓ |
| 17 | Real-Data Adapters | Pluggable ingestion interface (stub only) | ✓ |
| 18 | Deployment Prep | Docker config, README, environment docs | ✓ |

### 25.2 Phase Dependencies

```
Phase 1 (Foundation)
    │
    ▼
Phase 2 (Database) ──────────────────────────────────────────┐
    │                                                         │
    ▼                                                         │
Phase 3 (Synthetic Data) ─────────────────────────────────── │ ─────────────────┐
    │                                                         │                  │
    ▼                                                         │                  │
Phase 4 (Core APIs) ──────────────────────────────────────── │ ──────────────── │ ──────────┐
    │                                                         │                  │           │
    ▼                                ▼                        ▼                  ▼           │
Phase 5 (Map)              Phase 6 (Conflict Engine)   Phase 10 (Feature Store)             │
    │                             │                           │                              │
    │                      Phase 7 (Collision Sim)     Phase 11 (ML Models)                │
    │                             │                           │                              │
    ▼                             ▼                     Phase 12 (Explainability)           │
Phase 8 (Road Memory)      Phase 14 (Recommendations)        │                              │
    │                                                         ▼                              │
Phase 9 (PISI) ──────────────────────────────────────► Phase 13 (What-If)                  │
                                                              │                              │
                                                              └──────────────────────────────┘
                                                                           │
                                                                     Phase 15 (Dashboard)
                                                                           │
                                                                     Phase 16 (Hardening)
```

### 25.3 Testing Strategy per Phase

Each phase must ship with tests before the next phase begins:

| Phase | Required Tests Before Proceeding |
|---|---|
| 2 | ORM model unit tests, migration reversibility |
| 3 | Seed reproducibility test |
| 4 | API happy-path + 404 + 422 tests for all CRUD endpoints |
| 6 | All 4 conflict rule unit tests + idempotency test |
| 7 | Zero-write invariant test |
| 10 | All 4 leakage prevention tests |
| 11 | Backtesting reproducibility test + eval report completeness |
| 13 | What-If metric tests with known fixture inputs |

---

## 26. Implementation Task Plan

Each task is independently testable and has a clear acceptance check. Tasks are ordered within each phase. Dependencies are noted.

---

### Phase 1 — Foundation

**T-01: Initialize repository structure**
- Objective: Create all directories and placeholder files per Section 2
- Files: all directories, `.gitignore`, `.env.example`, `README.md`
- Dependencies: none
- Acceptance: `git status` shows clean structure; `ruff check backend/` passes on empty files

**T-02: Configure backend tooling**
- Objective: Set up pyproject.toml, ruff, pytest, requirements.txt (pinned versions)
- Files: `backend/pyproject.toml`, `backend/requirements.txt`
- Dependencies: T-01
- Acceptance: `pip install -r requirements.txt` succeeds; `ruff check .` passes

**T-03: Configure frontend tooling**
- Objective: `next create` + TypeScript strict mode + Tailwind + ESLint + Prettier
- Files: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`
- Dependencies: T-01
- Acceptance: `npm run build` succeeds on empty Next.js app; `npm run lint` passes

**T-04: Configure pydantic-settings and Settings class**
- Objective: `Settings` class with all config fields from Section 24
- Files: `backend/app/config.py`, `.env.example`
- Dependencies: T-02
- Acceptance: `from app.config import settings` imports without error; all fields have defaults

---

### Phase 2 — Database & Migrations

**T-05: Create SQLAlchemy base, mixins, and engine**
- Objective: `Base`, `TimestampMixin`, `SoftDeleteMixin`, async engine, session factory
- Files: `backend/app/models/base.py`, `backend/app/database.py`
- Dependencies: T-04
- Acceptance: `Base.metadata` contains no tables (mixins only); session factory returns `AsyncSession`

**T-06: Create RoadSegment ORM model**
- Objective: Full model per Section 3.2 with all fields and indexes
- Files: `backend/app/models/road_segment.py`
- Dependencies: T-05
- Acceptance: Unit test: model instantiates with all required fields; `__tablename__` = `"road_segments"`

**T-07: Create UtilityProject ORM model and association table**
- Objective: Model + `project_segment_association` table per Section 3.3
- Files: `backend/app/models/utility_project.py`
- Dependencies: T-05
- Acceptance: Many-to-many relationship navigable in both directions; soft-delete mixin applied

**T-08: Create ExcavationEvent and ResurfacingEvent ORM models**
- Objective: Both models per Sections 3.4 and 3.5
- Files: `backend/app/models/excavation_event.py`, `backend/app/models/resurfacing_event.py`
- Dependencies: T-06, T-07
- Acceptance: FK references valid; cascade behavior matches Section 3.11

**T-09: Create ConflictRecord ORM model**
- Objective: Full model per Section 3.6 including all explanation fields and unique index
- Files: `backend/app/models/conflict_record.py`
- Dependencies: T-07
- Acceptance: Unique constraint on `(project_a_id, project_b_id, road_segment_id, rule_id)` present

**T-10: Create RiskPrediction ORM model**
- Objective: Immutable model per Section 3.7 with `feature_snapshot` and `feature_snapshot_timestamp`
- Files: `backend/app/models/risk_prediction.py`
- Dependencies: T-06
- Acceptance: No `updated_at` column (immutable); all required fields per FR-RISK-09 present

**T-11: Create InfrastructureStressIndex and CoordinationRecommendation ORM models**
- Objective: Both models per Sections 3.8 and 3.9
- Files: `backend/app/models/infrastructure_stress_index.py`, `backend/app/models/coordination_recommendation.py`
- Dependencies: T-06
- Acceptance: `index_value` field exists (not `score`); PISI category enum present

**T-12: Create ModelMetadata ORM model**
- Objective: Model per Section 3.10
- Files: `backend/app/models/model_metadata.py` (add to `__init__.py`)
- Dependencies: T-05
- Acceptance: `model_version` has unique constraint; `is_active` field present

**T-13: Create and run initial Alembic migration**
- Objective: `alembic revision --autogenerate` + `alembic upgrade head`
- Files: `backend/alembic/versions/001_initial_schema.py`
- Dependencies: T-06 through T-12
- Acceptance: `alembic upgrade head` succeeds; `alembic downgrade -1` succeeds (reversible)

**T-14: Write SegmentRepository**
- Objective: `get_all`, `get_by_id`, `get_all_as_map`, `get_by_ids` with soft-delete filtering
- Files: `backend/app/repositories/segment_repo.py`
- Dependencies: T-06, T-05
- Acceptance: Unit tests: `get_by_id` raises `PipeWatchNotFoundError` for unknown ID; soft-deleted records excluded

**T-15: Write ProjectRepository**
- Objective: `get_all_active`, `get_by_id`, `create`, `update`, `soft_delete`, `get_projects_for_segments`
- Files: `backend/app/repositories/project_repo.py`
- Dependencies: T-07
- Acceptance: `soft_delete` sets `deleted_at`; `get_all_active` excludes deleted records

**T-16: Write remaining repositories**
- Objective: ExcavationRepository, ResurfacingRepository, ConflictRepository, PredictionRepository, StressIndexRepository, RecommendationRepository
- Files: `backend/app/repositories/*.py`
- Dependencies: T-08 through T-11
- Acceptance: Each repository has at minimum: `get_by_segment`, `create`, `get_latest` (where applicable)

**T-17: Write GeoJSON seed loader**
- Objective: Script that reads `data/seed/dehradun_segments.geojson` and inserts `RoadSegment` rows
- Files: `scripts/load_seed_data.py`
- Dependencies: T-06, T-14
- Acceptance: Running twice does not duplicate records (upsert on `id`); `length_meters` computed from geometry

---

### Phase 3 — Synthetic Data Engine

**T-18: Create `GeneratorConfig` dataclass**
- Objective: Full config per Section 11.2 with all causal parameters as typed fields
- Files: `scripts/generate_synthetic_data.py` (config section)
- Dependencies: T-01
- Acceptance: `--describe-model` prints all parameters; defaults produce plausible values

**T-19: Implement road network generation**
- Objective: Generate N segments with road_class, zone, name, synthetic LineString geometry
- Files: `scripts/generate_synthetic_data.py`
- Dependencies: T-18
- Acceptance: Correct counts per road class; geometry is valid GeoJSON LineString; `length_meters` > 0

**T-20: Implement causal project/excavation generator**
- Objective: Bernoulli draws per segment per year using causal multipliers; generate projects + excavation events
- Files: `scripts/generate_synthetic_data.py`
- Dependencies: T-19
- Acceptance: Base probability for ARTERIAL > LOCAL; temporal clustering produces overlapping projects; 20–30% of segments have repeat excavations

**T-21: Implement resurfacing event generation**
- Objective: Generate ResurfacingEvent after each FULL excavation with warranty
- Files: `scripts/generate_synthetic_data.py`
- Dependencies: T-20
- Acceptance: All resurfacings have `warranty_months` set; `start_date > excavation.end_date`

**T-22: Implement reproducibility and write to DB**
- Objective: All randomness through `np.default_rng(seed)`; write all records to SQLite
- Files: `scripts/generate_synthetic_data.py`
- Dependencies: T-21, T-17
- Acceptance: Two runs with `--seed 42` produce byte-identical SQLite DB hashes; DB populated with ~80–120 projects, 50–100 segments; **post-generation assert: if project count is outside [80, 120], script logs a warning with actual count and suggests adjusting `base_excavation_prob_*` parameters (does not force-inject projects)**

**T-23: Write synthetic data reproducibility test**
- Objective: `test_synthetic_seed_reproducibility` per Section 22.4
- Files: `backend/tests/unit/test_synthetic_data.py`
- Dependencies: T-22
- Acceptance: Test passes; test is part of `pytest` run

---

### Phase 4 — Core Backend APIs

**T-24: Implement `GET /segments` and `GET /segments/geojson`**
- Objective: List endpoint with pagination and GeoJSON export
- Files: `backend/app/routers/segments.py`, `backend/app/schemas/road_segment.py`
- Dependencies: T-14, T-04
- Acceptance: 200 with paginated list; GeoJSON is valid FeatureCollection; `is_synthetic` in properties; **GeoJSON feature properties include `risk_category` (or `null`) and `pisi_category` (or `null`) and `pisi_value` (or `null`) per segment** — these are joined from the latest RiskPrediction and InfrastructureStressIndex records so MapLibre paint expressions can color segments by overlay mode without a second API call

**T-25: Implement `GET /segments/{id}`, `/memory`, `/stress`, `/risk`**
- Objective: Segment detail + sub-resource endpoints (stubs for memory/stress/risk until Phases 8/9/11)
- Files: `backend/app/routers/segments.py`
- Dependencies: T-24
- Acceptance: 404 for unknown ID with `SEGMENT_NOT_FOUND` error code; 200 with correct schema

**T-26: Implement project CRUD endpoints**
- Objective: `GET/POST/PUT/DELETE /projects` with validation
- Files: `backend/app/routers/projects.py`, `backend/app/schemas/utility_project.py`
- Dependencies: T-15
- Acceptance: `end_date <= start_date` returns 422 `INVALID_DATE_RANGE`; soft-delete sets `deleted_at`; conflict detection triggered on create/update (stub until Phase 6)

**T-27: Implement excavation and resurfacing CRUD endpoints**
- Objective: CRUD for both event types
- Files: `backend/app/routers/excavations.py`, `backend/app/routers/resurfacing.py`
- Dependencies: T-16
- Acceptance: Filterable by `road_segment_id`; `is_synthetic` returned in all responses

**T-28: Write API integration tests for Phase 4 endpoints**
- Objective: Happy path + 404 + 422 for all Phase 4 endpoints
- Files: `backend/tests/integration/test_segments_api.py`, `test_projects_api.py`
- Dependencies: T-24 through T-27
- Acceptance: All tests pass; no test creates real side effects outside the test DB

---

### Phase 5 — Map Frontend

**T-29: Create AppShell with sidebar and synthetic data banner**
- Objective: Root layout with `SyntheticDataBanner` always visible
- Files: `frontend/src/app/layout.tsx`, `frontend/src/components/layout/AppShell.tsx`, `SyntheticDataBanner.tsx`
- Dependencies: T-03
- Acceptance: Banner renders on every page; `SyntheticDataBanner` test passes

**T-30: Implement MapLibre map with segment layer**
- Objective: `PipeWatchMap` component loading GeoJSON from API; segments rendered as colored lines
- Files: `frontend/src/components/map/PipeWatchMap.tsx`, `SegmentLayer.tsx`
- Dependencies: T-29, T-24
- Acceptance: Map loads; segments visible; click on segment logs segment ID to console

**T-31: Implement overlay selector and map legend**
- Objective: Overlay toggle (Default / Risk / PISI / Conflicts / Excavation Freq); legend updates per overlay
- Files: `frontend/src/components/map/OverlaySelector.tsx`, `MapLegend.tsx`, `frontend/src/store/mapStore.ts`
- Dependencies: T-30
- Acceptance: Switching overlay changes segment colors; legend label matches active overlay; risk overlay shows ML disclaimer

**T-32: Implement SegmentDetailPanel**
- Objective: Panel that opens on segment click with all sub-components (PISI, risk, excavation counts, projects)
- Files: `frontend/src/components/map/SegmentDetailPanel.tsx`
- Dependencies: T-31, T-25
- Acceptance: Panel renders with correct data; PISI disclaimer present; ML Prediction label present; "View Road Memory" link present

---

### Phase 6 — Conflict Engine

**T-33: Implement `AbstractConflictRule` and `ConflictRuleRegistry`**
- Objective: Base class + registry per Section 5.1 and 5.2
- Files: `backend/app/conflict_rules/base.py`, `backend/app/conflict_rules/registry.py`
- Dependencies: T-05
- Acceptance: `register()` raises ValueError on duplicate `rule_id`; `get_rules()` returns ordered list

**T-34: Implement `SPATIAL_TEMPORAL_EXCAVATION_01` rule**
- Objective: HIGH severity rule per Section 5.3
- Files: `backend/app/conflict_rules/spatial_temporal_excavation.py`
- Dependencies: T-33
- Acceptance: Unit test: correct overlap_days; spatial_reason and temporal_reason non-null; returns None when no temporal overlap

**T-35: Implement remaining 3 conflict rules**
- Objective: `SPATIAL_TEMPORAL_MIXED_02`, `SPATIAL_ONLY_03`, `TEMPORAL_PROXIMITY_04`
- Files: `backend/app/conflict_rules/spatial_temporal_mixed.py`, `spatial_only.py`, `temporal_proximity.py`
- Dependencies: T-33
- Acceptance: Unit tests for each rule covering applicable and non-applicable inputs; severity correct per FR-CONF-06

**T-36: Implement `ConflictEngine` service**
- Objective: `detect_all()` and `detect_for_project()` with canonical ordering and idempotency
- Files: `backend/app/services/conflict_engine.py`
- Dependencies: T-34, T-35, T-16
- Acceptance: Idempotency test passes; canonical ordering test passes; correct rule_id in DB records

**T-37: Implement conflict detection API endpoints**
- Objective: `GET/PATCH /conflicts`, `POST /conflicts/detect`
- Files: `backend/app/routers/conflicts.py`
- Dependencies: T-36
- Acceptance: Integration test: two conflicting projects → HIGH conflict with correct rule_id, spatial_reason, overlap_days; PATCH with no resolution_note on RESOLVED → 422

---

### Phase 7 — Collision Simulation

**T-38: Implement `CollisionSimulator` service**
- Objective: `simulate()` per Section 6.3; zero-write guarantee
- Files: `backend/app/services/collision_simulator.py`, `backend/app/schemas/conflict.py` (HypotheticalProjectRequest)
- Dependencies: T-36
- Acceptance: Zero-write invariant test passes; SIMULATION provenance set; same rule logic as stored detection

**T-39: Implement `POST /conflicts/simulate` endpoint**
- Objective: API endpoint calling `CollisionSimulator.simulate()`
- Files: `backend/app/routers/conflicts.py`
- Dependencies: T-38
- Acceptance: API integration test: no DB records created; response contains collisions and simulation_label

---

### Phase 8 — Road Memory

**T-40: Implement `RoadMemoryService`**
- Objective: Timeline assembly, warning flags, filtering per Section 7
- Files: `backend/app/services/road_memory.py`
- Dependencies: T-16
- Acceptance: Unit tests: warranty breach flagged; frequent excavation flagged at 3+; premature excavation flagged at < 90 days; chronological sort preserved

**T-41: Implement `GET /segments/{id}/memory` endpoint**
- Objective: Returns full timeline with provenance per event
- Files: `backend/app/routers/segments.py` (update stub)
- Dependencies: T-40
- Acceptance: Response includes `provenance_category` on each event; download as JSON endpoint works

**T-42: Implement Road Memory frontend page**
- Objective: `RoadMemoryTimeline` component with all event types and warning badges
- Files: `frontend/src/app/segments/[id]/memory/page.tsx`, `frontend/src/components/memory/`
- Dependencies: T-41, T-29
- Acceptance: WARRANTY BREACH badge renders in red when flag set; all events have provenance badges

---

### Phase 9 — PISI

**T-43: Implement `PISICalculator`**
- Objective: Pure function per Section 8.1 with exact formula
- Files: `backend/app/services/pisi_calculator.py`
- Dependencies: T-05
- Acceptance: Property-based test: output always in [0,100]; zero-event input = 0; weights sum assertion at module load

**T-44: Implement `PISIService` and `POST /stress/recalculate`**
- Objective: Service orchestration + batch recalculation endpoint
- Files: `backend/app/services/pisi_service.py`, `backend/app/routers/stress.py`
- Dependencies: T-43, T-16
- Acceptance: Recalculate endpoint creates new PISI records; `GET /stress/top` returns top N by `index_value`

**T-45: Implement PISI frontend components**
- Objective: `PISIPanel`, `PISIComponentChart`, `PISIFormulaDisclosure`
- Files: `frontend/src/components/pisi/`
- Dependencies: T-44
- Acceptance: Disclaimer text test passes; component chart shows all 5 sub-scores; formula disclosure contains formula text

---

### Phase 10 — ML Feature Store

**T-46: Implement `FeatureDefinitions` and `FEATURE_GROUPS`**
- Objective: `ml/features/definitions.py` per Section 10.2
- Files: `ml/features/definitions.py`
- Dependencies: T-01
- Acceptance: All 12 features have `timestamp_basis`; Group A ⊂ B ⊂ C

**T-47: Implement `LeakageValidator`**
- Objective: `assert_no_future_data` and `assert_target_is_future` per Section 10.3
- Files: `ml/features/validator.py`
- Dependencies: T-46
- Acceptance: All 4 leakage tests pass

**T-48: Implement `PointInTimeFeatureBuilder`**
- Objective: Full builder per Section 9.2 for all 12 approved features
- Files: `ml/features/builder.py`
- Dependencies: T-47
- Acceptance: Each feature matches its documented timestamp_basis; `days_since_last_excavation` returns 9999 for no-history segment

**T-49: Implement `build_feature_store.py` script**
- Objective: Reads DB → generates (segment, snapshot_date) pairs → builds Parquet feature store
- Files: `scripts/build_feature_store.py`
- Dependencies: T-48, T-23
- Acceptance: Parquet has all required columns per Section 10.1; no row has `feature_snapshot_timestamp` in the future relative to `target` event dates

---

### Phase 11 — ML Models & Backtesting

**T-50: Implement `AbstractPipeWatchModel`, `RuleBaseline`, `PipeWatchLogisticRegression`**
- Objective: Interface + two models per Section 12
- Files: `ml/models/base.py`, `ml/models/rule_baseline.py`, `ml/models/logistic_regression.py`
- Dependencies: T-01
- Acceptance: All implement `predict_proba` returning array in [0,1]; `get_feature_importances` returns sorted list

**T-51: Implement `PipeWatchRandomForest` with SHAP**
- Objective: RF model + `get_shap_values()` per Section 12.4
- Files: `ml/models/random_forest.py`
- Dependencies: T-50
- Acceptance: `get_shap_values()` returns list with `shap_value`, `feature_value`, `direction`; SHAP explainer built after `fit()`

**T-52: Implement `TemporalSplitter` and `BacktestRunner`**
- Objective: Full backtesting protocol per Section 13
- Files: `ml/training/splitter.py`, `ml/evaluation/backtesting.py`
- Dependencies: T-49, T-50
- Acceptance: Final test split (2025) only evaluated once; fold results stored; test never seen during hyperparameter selection

**T-53: Implement `train_model.py` and `evaluate_model.py` scripts**
- Objective: End-to-end training + evaluation producing `.joblib` artifact and JSON reports
- Files: `scripts/train_model.py`, `scripts/evaluate_model.py`
- Dependencies: T-52, T-51
- Acceptance: `python scripts/train_model.py --seed 42` produces model file and eval report; running twice produces identical reports

**T-54: Implement `PredictionService` runtime predictor**
- Objective: Loads model at startup, serves on-demand predictions with full output schema
- Files: `ml/prediction/predictor.py`
- Dependencies: T-53, T-48
- Acceptance: Prediction schema test passes (probability ∈ [0,1], all required fields present, `feature_snapshot_timestamp < prediction_timestamp`)

**T-55: Wire prediction service into FastAPI and implement prediction endpoints**
- Objective: `GET /ml/predict/{id}`, `POST /ml/predict/{id}/refresh`, `POST /ml/batch-predict`, `GET /ml/model-info`
- Files: `backend/app/routers/ml.py`
- Dependencies: T-54
- Acceptance: API returns `prediction_label = "ML Prediction — Not a confirmed event."`; fallback to RuleBaseline if model artifact missing

---

### Phase 12 — Explainability

**T-56: Implement plain-language explanation generator**
- Objective: Template-based `build_plain_language()` per Section 15.3
- Files: `ml/explainability/explainer.py`
- Dependencies: T-54
- Acceptance: All 12 features have a template; output is human-readable string; no raw numbers without context

**T-57: Implement calibration curve computation**
- Objective: `compute_calibration()` per Section 15.4; stored in eval report
- Files: `ml/evaluation/calibration.py`
- Dependencies: T-53
- Acceptance: Returns `fraction_of_positives` and `mean_predicted_value` arrays; rendered in Model Info frontend page

**T-58: Implement `TopFeaturesPanel` and `ModelInfoPanel` frontend components**
- Objective: Frontend panels per Section 19.12
- Files: `frontend/src/components/prediction/TopFeaturesPanel.tsx`, `ModelInfoPanel.tsx`
- Dependencies: T-55, T-57
- Acceptance: `timestamp_basis` shown per feature; calibration curve chart renders; ablation results table present

---

### Phase 13 — What-If Simulator

**T-59: Implement `WhatIfSimulator` service**
- Objective: Deterministic metrics + narrative per Section 16
- Files: `backend/app/services/whatif_simulator.py`, `backend/app/schemas/simulator.py`
- Dependencies: T-05
- Acceptance: Unit tests with fixture inputs (repeat_excavation_count, coordination_opportunities, etc.) all pass; narrative generated from data

**T-60: Implement `POST /simulator/compare` endpoint and frontend page**
- Objective: API + `WhatIfScenarioForm` + `ScenarioComparisonTable` + `ScenarioNarrative`
- Files: `backend/app/routers/simulator.py`, `frontend/src/app/simulator/page.tsx`, `frontend/src/components/simulator/`
- Dependencies: T-59
- Acceptance: "Simulation — Not a Committed Schedule" label renders; no monetary figures; `provenance.evidence_sources = ["SIMULATION"]`

---

### Phase 14 — Recommendation Engine

**T-61: Implement `AbstractRecommendationRule` and all 4 recommendation rules**
- Objective: Interface + `MergeWindowRule`, `SequenceReorderRule`, `DeferProjectRule`, `InspectBeforeResurfaceRule`
- Files: `backend/app/services/recommendation_engine.py`
- Dependencies: T-36, T-40, T-44, T-54
- Acceptance: ML evidence labeled in evidence dict; rationale generated from data; "Advisory — Requires Planner Review" label in response

**T-62: Implement recommendation API endpoints and frontend page**
- Objective: `GET/POST /recommendations`, `PATCH /recommendations/{id}/decision`
- Files: `backend/app/routers/recommendations.py`, `frontend/src/app/recommendations/page.tsx`
- Dependencies: T-61
- Acceptance: ACCEPT/REJECT with note; rejected records retained; decision_note required for REJECTED (422 otherwise)

---

### Phase 15 — Dashboard Integration

**T-63: Implement `GET /dashboard/summary` endpoint**
- Objective: Single endpoint returning all dashboard widget data
- Files: `backend/app/routers/dashboard.py`, `backend/app/services/dashboard_service.py`
- Dependencies: T-36, T-44, T-54, T-61
- Acceptance: Returns all fields per FR-DASH-02; response time < 3 seconds for synthetic dataset

**T-64: Implement all dashboard widgets and charts**
- Objective: All 9 dashboard components per Section 19.3
- Files: `frontend/src/app/dashboard/page.tsx`, `frontend/src/components/dashboard/`
- Dependencies: T-63
- Acceptance: Each KPI widget navigates to filtered detail view on click; all 3 charts render with axes and tooltips; **Conflict Summary table includes a `rule_id` column or badge for each conflict row** (per FR-DASH-03); Data Quality widget accessible from dashboard

---

### Phase 16 — Testing & Hardening

**T-65: Achieve ≥ 80% backend service layer coverage**
- Objective: Review coverage report; add missing unit tests
- Files: `backend/tests/unit/*`
- Dependencies: T-64
- Acceptance: `pytest --cov=app/services --cov-report=term-missing` shows ≥ 80%

**T-66: Implement all data leakage tests**
- Objective: All 4 tests from TEST-LEAK-01 through TEST-LEAK-04
- Files: `backend/tests/leakage/`
- Dependencies: T-48
- Acceptance: All 4 tests pass; tests run in standard `pytest` suite (not separately)

**T-67: Implement property-based PISI tests**
- Objective: `hypothesis` tests per Section 22.6
- Files: `backend/tests/unit/test_pisi_calculator.py`
- Dependencies: T-43
- Acceptance: 100 hypothesis examples pass without assertion errors

**T-68: Implement all frontend component tests**
- Objective: All tests from Section 22.5 including disclaimer, ML label, banner, color mapping
- Files: `frontend/tests/components/`
- Dependencies: T-29 through T-64
- Acceptance: `npm run test` passes all component tests

**T-69: Audit and fix all empty/error/loading states**
- Objective: Verify every data-fetching component has `LoadingState`, `ErrorState`, `EmptyState`
- Files: All frontend components
- Dependencies: T-68
- Acceptance: Manual review confirms no blank screens on empty data or API errors

---

### Phase 17 — Real-Data Adapters (Stub)

**T-70: Define `DataIngestionAdapter` interface**
- Objective: Abstract base class with `load_road_network()`, `load_projects()`, `load_events()` methods
- Files: `backend/app/ingestion/base.py`, `backend/app/ingestion/synthetic_adapter.py`
- Dependencies: T-22
- Acceptance: `SyntheticAdapter` implements the interface; interface documented in `docs/`

---

### Phase 18 — Deployment Preparation

**T-71: Write comprehensive README**
- Objective: Setup instructions, quickstart, architecture summary, synthetic data disclaimer
- Files: `README.md`
- Dependencies: all prior phases
- Acceptance: A new developer can set up and run the system following the README without additional guidance

**T-72: Create `docker-compose.yml` for PostgreSQL migration path**
- Objective: Optional compose file running the API + a PostgreSQL instance (for future use)
- Files: `docker-compose.yml`, `backend/app/config.py` (ensure PostgreSQL URL supported)
- Dependencies: T-71
- Acceptance: `docker compose up` starts without errors; API connects to PostgreSQL; all migrations run

---

*End of PipeWatch Technical Design Document v1.0*
*Requirements source: REQUIREMENTS.md v1.1*
*Next step: Review DESIGN.md against REQUIREMENTS.md for contradictions (Section below).*
