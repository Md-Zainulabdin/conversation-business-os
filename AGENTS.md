# Conversational Business OS (CBO)

> A production-ready side project built to learn modern software engineering while solving a real-world problem for small retailers.

---

# Project Vision

This project aims to build a **Conversational Business Operating System** where retailers can manage their business through **WhatsApp** instead of traditional ERP software.

Instead of opening a dashboard and filling forms, users should be able to send messages like:

> Sold 20 packs of rice.

> Bought 10 cartons of Coke.

> Customer Ali paid 5,000.

The system will understand the message, validate it, convert it into structured data, and store it in the database.

The long-term goal is that users can perform most daily business operations through conversation while still having a dashboard available for reports and management.

---

# Primary Objectives

This project has two goals.

## 1. Learn

Learn modern software engineering including:

- FastAPI
- Next.js
- TurboRepo
- PostgreSQL
- Redis
- Docker
- GitHub Actions
- CI/CD
- WhatsApp Cloud API
- OpenAI APIs
- Speech-to-Text
- Prompt Engineering
- Production Deployment

## 2. Build

Build a portfolio-quality application that feels like a real product rather than a tutorial project.

---

# Core Principles

## Keep everything simple.

We are a single developer.

Avoid unnecessary abstraction.

Avoid overengineering.

Refactor only when needed.

---

## AI only understands language.

The LLM should never directly modify the database.

Correct flow:

```
User Message
      ↓
Intent Extraction
      ↓
Validation
      ↓
Business Logic
      ↓
Database
```

---

## Business logic belongs in the backend.

The AI is responsible for understanding user input.

FastAPI is responsible for deciding what should happen.

---

## Build one feature at a time.

Complete each phase before starting the next.

Do not build future features early.

---

# Tech Stack

## Monorepo

- TurboRepo

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- FastAPI
- Python 3.13+
- SQLAlchemy
- Alembic
- Pydantic

## Database

- PostgreSQL (Neon)

## Cache

- Redis (Upstash)

## AI

- OpenAI

## Messaging

- WhatsApp Business Cloud API

## Speech

- OpenAI Whisper

## Deployment

Frontend

- Vercel

Backend

- Railway

Database

- Neon

Redis

- Upstash

---

# Project Structure

```
conversation-business-os/

apps/
│
├── api/
│
└── web/

packages/
│
├── shared/
│
└── config/

docs/

.github/

docker-compose.yml

README.md

turbo.json
```

---

# Backend Structure

```
apps/api/

app/

├── main.py

├── core/
│   ├── config.py
│   ├── database.py
│   └── security.py

├── models/

├── schemas/

├── services/

├── routes/

├── integrations/
│   ├── openai.py
│   ├── whatsapp.py
│   └── speech.py

└── utils/
```

---

# Frontend Structure

```
apps/web/

app/

components/

hooks/

lib/

types/

public/
```

---

# Development Roadmap

## Phase 0 — Foundation

Goal

Set up the project.

Tasks

- TurboRepo
- FastAPI
- Next.js
- PostgreSQL
- Docker
- GitHub
- GitHub Actions
- Local development environment

Deliverable

A running application with frontend and backend connected.

---

## Phase 1 — Inventory System

Goal

Build a traditional web application first.

Features

- Authentication
- Products
- Categories
- Inventory
- Basic Dashboard

Deliverable

Users can manage inventory through the web interface.

---

## Phase 2 — Sales

Features

- Record sales
- Record purchases
- Record expenses

Deliverable

Basic business management system.

---

## Phase 3 — AI

Goal

Allow natural language interaction.

Examples

> Sold 20 Coke

↓

```json
{
  "intent": "sale",
  "product": "Coke",
  "quantity": 20
}
```

The AI should only return structured JSON.

The backend validates and performs the action.

---

## Phase 4 — WhatsApp

Features

- Receive WhatsApp messages
- Process messages
- Reply with confirmations

Example

User

> Sold 20 Coke

System

> Recorded the sale of 20 Coke bottles.

---

## Phase 5 — Voice

Features

- Receive voice notes
- Speech-to-text
- Send transcript to AI
- Execute business logic

---

## Phase 6 — Reports

Features

- Daily summary
- Revenue
- Inventory status
- Low stock alerts

---

# Coding Guidelines

- Keep code readable.
- Prefer simple solutions.
- Use meaningful names.
- Avoid premature optimization.
- Keep functions small.
- Write reusable code only when duplication becomes a real problem.
- Add comments only when the code is not self-explanatory.

---

# Git Workflow

Use feature branches.

Example

```
main

feature/setup

feature/products

feature/inventory

feature/openai

feature/whatsapp
```

Merge into `main` only after the feature is complete.

---

# Commit Convention

Use Conventional Commits.

Examples

```
feat: add product CRUD

feat: integrate OpenAI

fix: inventory calculation

docs: update roadmap

refactor: simplify services
```

---

# CI/CD

Every pull request should automatically:

- Install dependencies
- Lint
- Build the frontend
- Run backend tests (when available)

Every merge to `main` should automatically deploy:

- Frontend → Vercel
- Backend → Railway

---

# Rules for the Coding Agent

When generating code:

1. Follow the current phase only.
2. Do not implement future phases unless requested.
3. Keep the architecture simple and easy to understand.
4. Prefer clarity over cleverness.
5. Explain important decisions briefly when introducing new patterns.
6. Use production-ready practices, but avoid unnecessary complexity.
7. Keep files organized and reasonably small.
8. Do not introduce new libraries unless they solve a clear problem.
9. Ask before making major architectural changes.
10. Prioritize maintainability over abstraction.

---

# End Goal

By the end of this project we should have a production-ready application where a retailer can:

- Manage inventory
- Record sales
- Record purchases
- Record expenses
- Interact using WhatsApp
- Send voice notes
- View reports from a web dashboard

while the codebase remains simple, clean, and easy for a single developer to understand and maintain.

---

# Database Schema (MVP)

> This document defines the initial database schema for the **Conversational Business OS**. The schema is intentionally kept simple to support the current project scope. Additional entities will be introduced only when required by future features.

---

# General Rules

- Every table uses **UUID** as its primary key.
- Every table includes `created_at`.
- Tables that can be modified also include `updated_at`.
- Relationships should use foreign keys.
- Keep the schema simple and avoid premature optimization.

---

# 1. Product

Represents an item that can be purchased and sold.

| Field | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String | Product name |
| sku | String | Unique stock keeping unit |
| category | String | Product category |
| unit | String | Unit of measurement (Piece, Pack, KG, Litre, etc.) |
| purchase_price | Decimal | Buying price |
| selling_price | Decimal | Selling price |
| stock_quantity | Integer | Current available stock |
| minimum_stock | Integer | Low stock threshold |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

---

# 2. Customer

Represents customers who purchase products.

| Field | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String | Customer name |
| phone | String | Phone number |
| address | String | Customer address (Optional) |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

---

# 3. Sale

Represents a single sales transaction.

> **MVP Assumption:** One sale contains one product. If multiple products per sale are needed in the future, this entity will be refactored into `Sale` and `SaleItem`.

| Field | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| customer_id | UUID (Nullable) | Reference to Customer |
| product_id | UUID | Reference to Product |
| quantity | Integer | Quantity sold |
| unit_price | Decimal | Selling price at the time of sale |
| total_amount | Decimal | Total sale amount |
| sale_date | Timestamp | Date and time of sale |
| notes | Text | Optional remarks |
| created_at | Timestamp | Record creation time |

Relationship

```
Customer (1)
      │
      │
      ▼
Sale (Many)

Product (1)
      │
      ▼
Sale (Many)
```

---

# 4. Purchase

Represents purchasing inventory from suppliers.

> **MVP Assumption:** Supplier information is stored as plain text. A dedicated Supplier table can be added later.

| Field | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| product_id | UUID | Reference to Product |
| supplier_name | String | Supplier name |
| quantity | Integer | Quantity purchased |
| purchase_price | Decimal | Purchase price per unit |
| total_amount | Decimal | Total purchase amount |
| purchase_date | Timestamp | Purchase date |
| notes | Text | Optional remarks |
| created_at | Timestamp | Record creation time |

Relationship

```
Product (1)
      │
      ▼
Purchase (Many)
```

---

# 5. Expense

Represents business expenses.

| Field | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | String | Expense title |
| category | String | Expense category |
| amount | Decimal | Expense amount |
| expense_date | Timestamp | Date of expense |
| notes | Text | Optional remarks |
| created_at | Timestamp | Record creation time |

Example Categories

- Electricity
- Internet
- Transport
- Salary
- Miscellaneous

---

# Inventory Rules

Inventory is **not** stored in a separate table during the MVP.

Instead:

- Every Product contains a `stock_quantity`.
- Creating a Purchase **increases** stock.
- Creating a Sale **decreases** stock.
- Editing or deleting a Sale/Purchase must update stock accordingly.

Example

```
Rice Stock = 100

Purchase 20

↓

Stock = 120

Sale 15

↓

Stock = 105
```

---

# Current Entity Relationships

```
                +-------------+
                |  Customer   |
                +-------------+
                       |
                       |
                       ▼
                   +--------+
                   |  Sale  |
                   +--------+
                       ▲
                       |
                       |
+-----------+     +---------+
| Purchase  | --> | Product |
+-----------+     +---------+
                       ▲
                       |
                       |
                  +----------+
                  | Expense  |
                  +----------+
```

---

# Future Entities (Not Part of MVP)

These entities will only be introduced when their corresponding features are implemented.

### Phase 3
- User (Authentication)

### Phase 4
- Conversation
- Message

### Phase 5
- AIRequest

### Phase 6+
- Supplier
- Organization
- InventoryTransaction
- Notifications
- Audit Logs

---

# Final MVP Scope

The first version of the application will consist of only **five business entities**:

- Product
- Customer
- Sale
- Purchase
- Expense

The goal is to keep the database small, understandable, and easy to extend as the project evolves.

---

# Coding Agent Guardrails

Act as a senior software engineer and software architect on every task. Prioritize simplicity, correctness, readability, maintainability, and long-term scalability over clever or overly abstract solutions. Follow the current project phase only and never implement future features unless explicitly requested. Do not make assumptions—if requirements are ambiguous or a design decision could affect the architecture, stop and ask for clarification. Write production-quality code using established best practices, keep files organized and reasonably small, remove dead code and stale files, avoid duplication, and refactor only when there is clear value. Handle errors comprehensively on both the frontend and backend with proper validation, structured error responses, meaningful user feedback, logging, and graceful failure handling. Consider edge cases, security, performance, and maintainability as part of every implementation, and ensure that new changes do not introduce regressions.

Treat the repository as the source of truth and make only the changes required for the requested task. Never commit, push, merge, create pull requests, or perform any GitHub operations without explicit user approval. Never delete or modify existing functionality unless it is necessary for the requested change, and always explain any architectural decisions that significantly affect the codebase. Before completing a task, verify that the project builds successfully, code is formatted and linted where applicable, imports are clean, unused code has been removed, and the implementation is consistent with the project's architecture and conventions. The goal is to produce production-ready, understandable code that a single developer can confidently maintain and extend.
