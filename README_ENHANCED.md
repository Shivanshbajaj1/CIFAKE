# PipeWatch

PipeWatch is a geospatial intelligence platform designed to solve infrastructure coordination challenges in urban environments. By predicting repeat excavation risks and identifying potential conflicts between utility projects, PipeWatch enables data-driven decision making for municipal planners, utility companies, and infrastructure agencies.

> **Synthetic data notice:** the included system uses synthetic records only. They are not Dehradun municipal measurements or confirmed event history. Risk output is a prediction, never a confirmed event. The PipeWatch Infrastructure Stress Index (PISI) is a derived index, not a physical measurement of road condition.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [API Reference](#api-reference)
- [Project Status](#project-status)
- [Troubleshooting](#troubleshooting)
- [Contributing Guidelines](#contributing-guidelines)
- [License](#license)

## Overview

Infrastructure projects in urban areas are frequently planned and executed in isolation by separate agencies — water boards, telecom operators, road authorities, municipal corporations, and electricity departments. This siloed approach results in a well-documented and costly failure pattern:

1. A road corridor is excavated for water work and restored.
2. Within months, the same corridor is excavated again for fiber optic laying.
3. The freshly restored road surface is broken again, often within its warranty period.
4. Each cycle incurs duplicated excavation costs, restoration costs, traffic disruption, and accelerated road deterioration.
5. There is no shared institutional memory of what has happened to a road corridor, when, and by whom.

PipeWatch addresses this challenge by providing:
- **Predictive Analytics**: ML-powered forecasting of repeat excavation risk
- **Conflict Detection**: Rule-based identification of scheduling conflicts
- **Historical Memory**: Complete timeline of all infrastructure activities
- **Decision Support**: Simulation and recommendation tools for optimal coordination
- **Visual Analytics**: Interactive maps and dashboards for situational awareness

## Key Features

### 🔮 Predictive Risk Modeling
- Machine learning models forecast probability of repeat excavation
- Feature importance analysis explains model decisions
- Temporal backtesting validates model performance over time
- Synthetic data generation creates realistic training scenarios

### ⚔️ Intelligent Conflict Engine
- Four deterministic rules detect spatiotemporal conflicts
- Idempotent detection prevents duplicate database entries
- Collision simulation tests hypothetical scenarios without side effects
- Conflict severity scoring (HIGH, MEDIUM, LOW) prioritizes response

### 🗺️ Comprehensive Road Memory
- Chronological timeline of all infrastructure events
- Automatic warning flag detection (warranty breaches, frequent excavation, premature work)
- Event filtering by type, date range, and data source
- Provenance tracking tracks data origins and calculation methods
- JSON export enables external analysis and reporting

### 📊 Infrastructure Stress Index (PISI)
- Deterministic index quantifies excavation vulnerability
- Five-component model: excavation count, utility diversity, recency, resurfacing gap, conflict history
- Formula versioning ensures reproducibility and auditability
- Map overlay visualization shows spatial risk distribution
- Component breakdown aids in root cause analysis

### 🎯 What-If Simulation & Optimization
- Scenario-based comparison of project schedules
- Quantitative metrics: repeat excavations, disturbance days, coordination opportunities
- Plain-language narratives explain simulation results
- Zero-write guarantee ensures no unintended database modifications

### 💡 Intelligent Recommendation System
- Four rule-based recommendation types:
  1. Merge Window: Simultaneous excavation of coordinated projects
  2. Sequence Reorder: Optimal project sequencing to prevent conflicts
  3. Defer Project: Postponement during active warranty periods
  4. Inspect Before Resurface: Structural assessment recommendation
- Evidence-based rationale supports each recommendation
- Priority scoring (HIGH, MEDIUM, LOW) guides decision making
- Accept/reject workflow with required justification for rejections

### 📈 Interactive Dashboard & Visualization
- Real-time overview of system health and key performance indicators
- Interactive MapLibre map with multiple overlay modes:
  - Default: Road network visualization
  - Risk: ML-based excavation probability
  - PISI: Infrastructure stress index
  - Conflicts: Active conflict locations
  - Excavation Frequency: Historical digging patterns
- Sortable, filterable tables for detailed data exploration
- Download capabilities for offline analysis and reporting
- **Recently Enhanced**: Actual chart visualizations using Recharts library (BarChart, LineChart, PieChart)
- **Recently Enhanced**: Real data fetching for dashboard widgets including KPIs, charts, and tables
- **Recently Enhanced**: Top 10 High-PISI Segments table with actual PISI data from GeoJSON endpoint
- **Recently Enhanced**: Open Conflicts Summary table with enriched conflict data including project and segment names

## System Architecture

PipeWatch follows a clean, layered architecture that separates concerns while maintaining operational simplicity:

```
┌─────────────────────────────────────────────────────────────┐
│                     BROWSER CLIENT                           │
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
│  │                                                     │   │
│  └──────────────────────────┬───────────────────────-──┘   │
│                             │ SQLAlchemy 2 async            │
└─────────────────────────────┼────────────────────────────-─┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     DATA LAYER                               │
│                                                             │
│  SQLite (dev)  ──►  PostgreSQL + PostGIS (prod migration)  │
│  GeoJSON seed files  ·  Parquet feature store              │
│  Joblib model artifacts                                     │
└─────────────────────────────────────────────────────────────┘
```

### ML Pipeline (Completely Offline)

To prevent data leakage and ensure reproducibility, PipeWatch's ML pipeline operates entirely offline:

```bash
# 1. Generate reproducible synthetic data
python scripts/generate_synthetic_data.py --seed 42

# 2. Load data into development database
python scripts/load_seed_data.py

# 3. Construct leakage-safe feature store
python scripts/build_feature_store.py

# 4. Train model with temporal backtesting
python scripts/train_model.py --seed 42

# 5. Evaluate model performance
python scripts/evaluate_model.py --seed 42
```

This approach guarantees:
- No data leakage between training and testing periods
- Reproducible results with fixed seeds
- Clear separation between model training and inference
- Auditability of all data transformations

## Technology Stack

### Backend (Python 3.12)
- **Web Framework**: FastAPI with Uvicorn ASGI server
- **ORM**: SQLAlchemy 2.0 with async support
- **Database Migrations**: Alembic
- **Data Processing**: Pandas 2.x, NumPy 2.x
- **Geospatial Operations**: Shapely 2.x, GeoPandas 1.x, PyProj 3.x
- **Machine Learning**: Scikit-learn 1.x, SHAP for explainability
- **API Validation**: Pydantic 2.x
- **Testing**: Pytest 8.x, pytest-asyncio, Hypothesis
- **Code Quality**: Ruff linter, type hints throughout
- **Environment Management**: Pydantic-settings

### Frontend (Next.js 14)
- **Framework**: Next.js 14 with App Router, React 19, TypeScript 5.x
- **Mapping**: MapLibre GL JS via react-map-gl
- **Data Fetching**: React Query for caching and synchronization
- **State Management**: Zustand for UI state (sidebar, overlax, etc.)
- **Visualization**: Recharts for interactive charts and graphs
- **\Form Handling**: React Hook Form with Zod validation
- **Testing**: Jest, React Testing Library
- **Build**: SWC compiler for fast refresh

### DevOps & Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for local development
- **Production Database**: PostgreSQL 16 + PostGIS extension
- **API Documentation**: Swagger/OpenAPI via FastAPI docs
- **Environment Variables**: .env files with pydantic-settings
- **Package Management**: pip (Python), npm (Node.js)

## Getting Started

### Prerequisites
- Python 3.12 or higher
- Node.js 18 or higher
- npm (comes with Node.js)
- Git (for version control)

### Installation Steps

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/PipeWatch.git
cd PipeWatch
```

#### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Unix/macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
copy ..\env.example .env
```

#### 3. Generate and Load Sample Data
```bash
# Generate synthetic road network and infrastructure data
# Using seed 42 ensures reproducible results
python ..\scripts\generate_synthetic_data.py --seed 42

# Load generated data into SQLite database
python ..\scripts\load_seed_data.py
```

#### 4. Start the API Server
```bash
# Start FastAPI with auto-reload for development
python -m uvicorn app.main:app --reload
```
The API will be available at http://localhost:8000
Access interactive API documentation at http://localhost:8000/docs

#### 5. Frontend Setup (in a new terminal window)
```bash
# Navigate to frontend directory
cd ../frontend

# Install JavaScript dependencies
npm install

# Copy environment example
copy .env.local.example .env.local

# Start development server
npm run dev
```
The frontend will be available at http://localhost:3000

### Verification

#### Backend Tests
```bash
# Run all backend tests
pytest

# Run tests with coverage reporting
pytest --cov=app --cov-report=term-missing

# Check code quality
ruff check .
```

#### Frontend Tests
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Run unit tests
npm run test

# Build for production
npm run build
```

## Development Workflow

### Making Changes
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes following existing code patterns
3. Add or update tests as appropriate
4. Ensure all tests pass: `pytest` (backend) and `npm run test` (frontend)
5. Commit changes with descriptive messages
6. Push to your fork and open a pull request

### Backend Development Guidelines
- Follow existing patterns in service组件, repositories, and API endpoints
- Include proper error handling with documented error codes
- Write unit tests for new functionality
- Maintain backward compatibility where possible
- Document complex algorithms with comments and docstrings

### Frontend Development Guidelines
- Follow existing component patterns and file organization
- Ensure responsive design works on mobile and desktop
- Include proper loading, error, and empty states
- Write unit tests for complex components
- Follow accessibility guidelines (WCAG 2.1 AA)
- Use existing color schemes and typography

### Database Migrations
When modifying the data model:
1. Make changes to SQLAlchemy models in `/backend/app/models/`
2. Generate migration: `python -m alembic revision --autogenerate -m "description"`
3. Review generated migration in `/backend/alembic/versions/`
4. Apply migration: `python -m alembic upgrade head`
5. Test migration reversibility: `python -m alembic downgrade -1`

## API Reference

PipeWatch provides a comprehensive REST API for all functionality. The complete interactive documentation is available at http://localhost:8000/docs when the API is running.

### Core Resources

#### Segments (`/api/v1/segments*`)
- List, retrieve, and visualize road segments
- Access infrastructure timeline (Road Memory)
- Query current PISI scores and risk predictions

#### Projects (`/api/v1/projects*`)
- Full CRUD operations for utility projects
- Automatic conflict detection on create/update
- Project lifecycle tracking

#### Excavations & Resurfacing (`/api/v1/excavations*`, `/api/v1/resurfacing*`)
- Track individual infrastructure work events
- Temporal querying and filtering
- Synthetic data provenance tracking

#### Conflicts (`/api/v1/conflicts*`)
- Detect and manage scheduling conflicts
- Update conflict status (acknowledge/resolve)
- Simulate hypothetical projects (zero-write)
- Retrieve detailed conflict explanations

#### Machine Learning (`/api/v1/ml*`)
- Generate and retrieve risk predictions
- Access model metadata and performance metrics
- Batch prediction operations
- Explain model decisions with feature importance

#### Simulation (`/api/v1/simulator*`)
- Compare project scenarios for optimal scheduling
- Export simulation results for planning
- Zero-write guarantee protects production data

#### Recommendations (`/api/v1/recommendations*`)
- Generate data-driven coordination suggestions
- Accept/reject recommendations with justification
- Track decision history and outcomes

#### Dashboard (`/api/v1/dashboard*`)
- Retrieve aggregated KPIs for dashboard widgets
- Real-time system health overview

## Project Status

The current implementation represents Release 1.0 "Foundation Complete" with core functionality implemented and tested. For detailed progress tracking, refer to:

- [BUILD_STATUS.md](BUILD_STATUS.md) - Detailed task completion matrix
- [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) - Narrative progress summary

### ✅ Completed Milestones

**Foundation (Phases 1-5)**
- Repository structure and development tooling
- Async SQLAlchemy ORM models and database migrations
- Synthetic data generation with causal modeling
- Core REST API for segments, projects, excavations, resurfacing
- Next.js frontend shell with MapLibre integration

**Core Functionality (Phases 6-11)**
- Four-rule conflict detection engine with idempotency
- Road Memory service with timeline assembly and warning flags
- PISI calculation service and API endpoints
- ML feature store with leakage prevention
- Baseline logistic regression model with training/evaluation
- Explainability integration (SHAP values, feature importance)
- What-If simulator for scenario comparison

**Decision Support (Phases 12-14)**
- Recommendation engine with four rule-based rules
- Dashboard API endpoint with KPI aggregation
- Model information panels and feature explanations

**Presentation Layer (Phases 15-16)**
- Interactive dashboard with KPI widgets, charts, and tables (**Recently Enhanced**)
- Map-based visualization with multiple overlay modes
- Loading, error, and empty states for all components
- Synthetic data disclaimers and provenance tracking

### 🔧 In Progress / Planned

**ML Enhancements**
- [ ] Random Forest model with SHAP explanations (T-51)
- [ ] Temporal backtesting pipeline implementation (T-52, T-53)
- [ ] Complete prediction service wiring (T-54, T-55)
- [ ] Feature explanation panels UI (T-58)

**Frontend Completion**
- [ ] Road Memory frontend page (T-42)
- [ ] Dashboard widgets and charts implementation (T-64) **Partially Complete**
- [ ] Backend service layer test coverage ≥80% (T-65)
- [ ] Data leakage test suite completion (T-66)
- [ ] Property-based PISI tests (T-67)
- [ ] Frontend component test suite (T-68)

**Infrastructure & Quality**
- [ ] Data ingestion adapter interface (T-70)
- [ ] docker-compose.yml for PostgreSQL deployment (T-72)
- [ ] API integration tests for Phase 4 endpoints (T-28)
- [ ] Production deployment documentation and scripts
- [ ] Performance optimization and load testing

## Troubleshooting

### Common Issues and Solutions

#### Backend Connection Problems
**Symptom**: Frontend shows network errors or API connection failures
**Solutions**:
1. Verify backend is running: `ps aux | grep uvicorn` (Unix) or Check Task Manager (Windows)
2. Check that API is accessible: `curl http://localhost:8000/health`
3. Verify virtual environment is activated and using Python 3.12+
- Confirm correct directory: must be in `backend/` folder when running commands
4. Check firewall settings blocking port 8000
5. Verify `.env` file contains correct `API_HOST` and `API_PORT` values

#### Data Loading Issues
**Symptom**: Missing data after running synthetic data generation
**Solutions**:
1. Check generation completed successfully (look for "Generated X segments, Y projects" message)
2. Verify data loading step executed after generation
3. Confirm SQLite database file exists: `backend/pipewatch.db`
4. Check for permission issues on Windows temp directories during generation
5. Try running with explicit seed: `python scripts/generate_synthetic_data.py --seed 42`

#### Test Failures Due to Permissions
**Symptom**: Pytest fails with "PermissionError" accessing temp directories
**Solutions**:
1. Set explicit pytest cache directory:
   ```cmd
   set PYTEST_CACHE_DIR=C:\temp\pytest_cache
   pytest
   ```
2. Use cache clearing to avoid permission conflicts:
   ```cmd
   pytest --cache-clear
   ```
3. Run tests from a directory with full write permissions
4. Temporarily disable antivirus software that might interfere with temp file access

#### Missing ML Model Artifacts
**Symptom**: Warnings about missing model files or fallback to rule-based predictions
**Solutions**:
1. Train a model if none exists:
   ```bash
   python scripts/train_model.py --seed 42
   ```
2. Verify model file was created: `models/randomforestclassifier_v1.0_20261001.joblib`
3. Check `.env` file for correct `ML_MODEL_PATH` setting
4. Confirm the model artifact is accessible from the application working directory

#### Database Locked Errors
**Symptom**: "Database is locked" errors during concurrent access
**Solutions**:
1. Ensure only one process is accessing the SQLite database at a time
2. For development, consider deleting and recreating the database:
   ```bash
   del backend\pipewatch.db
   python ..\scripts\generate_synthetic_data.py --seed 42
   python ..\scripts\load_seed_data.py
   ```
3. For production, migrate to PostgreSQL using the provided docker-compose.yml
4. Check for long-running transactions or uncommitted changes

### Debugging Tips

#### Enabling Detailed Logging
Modify `backend/app/config.py` to increase log level:
```python
import logging
# Add to Settings class:
log_level: str = "DEBUG"
```

#### Inspecting Database Contents
Use SQLite CLI to examine data:
```bash
sqlite3 backend/pipewatch.db
.schema  # Show table structure
SELECT COUNT(*) FROM road_segments;  # Count records
```

#### API Debugging
1. Use the interactive API docs at http://localhost:8000/docs
2. Try endpoints directly with curl:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/health"
   ```
3. Enable debug mode in FastAPI by setting `debug: true` in config (development only)

#### Frontend Debugging
1. Open browser developer tools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for failed API requests
4. Use React DevTools extension for component inspection
5. Check Application tab for localStorage and sessionStorage issues

## Contributing Guidelines

We welcome contributions from the community to improve PipeWatch! Please follow these guidelines to ensure your contributions can be effectively reviewed and integrated.

### How to Contribute

1. **Fork the Repository**
   - Create your own fork of the PipeWatch repository on GitHub

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-descriptive-feature-name
   ```

3. **Make Your Changes**
   - Follow the existing code style and conventions
   - Add comprehensive tests for new functionality
   - Update documentation as needed
   - Keep changes focused and atomic

4. **Run Tests**
   ```bash
   # Backend tests
   pytest
   
   # Frontend tests
   npm run test
   
   # Type checking
   npm run type-check
   
   # Linting
   npm run lint
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: descriptive message following conventional commits"
   ```

6. **Push and Open Pull Request**
   ```bash
   git push origin feature/your-descriptive-feature-name
   ```
   - Open a pull request against the `main` branch
   - Include clear description of changes and motivation
   - Reference any related issues

### Code Style and Conventions

#### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Document complex algorithms with docstrings
- Handle exceptions gracefully with meaningful error messages
- Follow existing patterns for service组件, repositories, and routers
- Include unit tests for all new functionality
- Keep functions focused and single-responsibility

#### Frontend (TypeScript/React)
- Follow existing component organization patterns
- Use functional components with hooks
- Include proper TypeScript typing for props and state
- Handle loading, error, and empty states for all data-fetching components
- Follow existing styling conventions and color usage
- Write unit tests for non-trivial components
- Ensure responsive design works across device sizes
- Follow accessibility guidelines (WCAG 2.1 AA)

#### Documentation
- Update README.md for significant changes
- Add inline comments for complex logic
- Document public APIs and interfaces
- Keep synthetic data disclaimers prominent in user-facing outputs
- Maintain architectural decision records for major changes

### Reporting Issues
When reporting bugs or suggesting features:
1. Check if the issue already exists in the issue tracker
2. Provide clear, reproducible steps for bugs
3. Include relevant error messages and screenshots
4. Specify expected vs. actual behavior
5. For feature requests, describe the use case and benefits

### Licensing
By contributing to PipeWatch, you agree that your contributions will be licensed under the MIT License.

## License

MIT License

Copyright (c) 2026 PipeWatch Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

---

*Documentation last updated: October 4, 2026*
*PipeWatch v1.0.0 - Foundation Complete Release*
*Dashboard enhanced with actual chart visualizations and real data fetching*