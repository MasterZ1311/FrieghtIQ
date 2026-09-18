# 📚 FreightIQ — Master AI Agent & Engineering Specification Suite
## Problem SIH26006 | Smart India Hackathon 2026 | Thoothukudi & Chennai Centric

This directory contains the **6 foundational software specification documents** required to prompt, guide, and instruct any AI agent (Claude, ChatGPT, Antigravity, GitHub Copilot) or human developer to build, understand, or extend the FreightIQ platform without guesswork:

---

### 📑 Document Index & Quick Reference

| # | Document | Purpose & Contents | Primary File Link |
|---|---|---|---|
| **1** | **PRD (Product Requirements Document)** | Executive vision, SAIL bulk freight problem statement, 4 user personas, 10 core functional feature modules with acceptance criteria, non-functional requirements, and hackathon evaluation KPIs. | [01_PRD](file:///e:/SIH21006/SYSTEM_SPEC/01_PRODUCT_REQUIREMENTS_DOCUMENT_PRD.md) |
| **2** | **TRD (Technical Requirements Document)** | System topology, technology stack decision rationale (Next.js 16 + FastAPI), 12 REST API specifications, mathematical formulas (Black-Scholes, 4-state HMM, Admiralty cubic fuel burn, IMO CII AER), and offline demo architecture. | [02_TRD](file:///e:/SIH21006/SYSTEM_SPEC/02_TECHNICAL_REQUIREMENTS_DOCUMENT_TRD.md) |
| **3** | **App Flow & User Journey Map** | Complete 16-route navigation tree, button click triggers, inputs, page transitions, and end-to-end user journeys (Australia-Thoothukudi coal import, Paradip Virtual Arrival congestion mitigation). | [03_App_Flow](file:///e:/SIH21006/SYSTEM_SPEC/03_APP_FLOW_AND_USER_JOURNEY.md) |
| **4** | **UI/UX Design Brief** | Visual identity (Industrial Cyber-Maritime Command Center), dark mode palette (`#030712`), regime badge tokens, IMO CII color scale, typography system, component standards (`CiiRing`, `StatCard`, Skeletons), and ASCII screen wireframes. | [04_UI_UX](file:///e:/SIH21006/SYSTEM_SPEC/04_UI_UX_DESIGN_BRIEF.md) |
| **5** | **Backend Schema & Auth Flow** | JWT token architecture (access + refresh), Role-Based Access Control (RBAC) matrix, complete Mermaid Entity-Relationship diagram (ERD), and exhaustive definitions for all 11 database tables with indexing strategies. | [05_Schema_Auth](file:///e:/SIH21006/SYSTEM_SPEC/05_BACKEND_SCHEMA_AND_AUTH_FLOW.md) |
| **6** | **Step-by-Step Implementation Plan** | 6-phase sequential build roadmap, task dependencies, automated verification commands (`verify_all.py` 12/12 pass condition, `npm run build` 16/16 static routes), and copy-paste prompt templates for AI agents. | [06_Implementation_Plan](file:///e:/SIH21006/SYSTEM_SPEC/06_STEP_BY_STEP_IMPLEMENTATION_PLAN.md) |

---

### 🤖 How an AI Agent Uses This Suite

1. **Context Initialization:** Feed **PRD** and **TRD** to establish domain understanding (bulk shipping, SAIL raw materials, draft/tides, and maritime physics).
2. **UI Development:** Feed **App Flow** and **UI/UX Design Brief** to build or restyle any screen with guaranteed design consistency.
3. **Database & API Integration:** Feed **Backend Schema** and **TRD** to generate migrations, Pydantic schemas, and endpoints.
4. **Execution & Auditing:** Follow the **Step-by-Step Implementation Plan** sequentially to build and verify components with 0 errors.
