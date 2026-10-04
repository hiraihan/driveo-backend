# Developer A Implementation Plan (DriveO Backend)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Core Marketplace & Rental Operations domains (Auth, User, Rental, Vehicle, Availability, Listing, Search, Booking, Review, Admin) for the DriveO Modular Monolith backend.

**Architecture:** Modular Monolith. Strict domain boundaries: Domain A cannot import Domain B's SQLAlchemy models. Cross-domain communication is strictly via Protocol interfaces in `app/contracts/ports.py`. Developer A implements `BookingPort` and `RentalReadPort`, and consumes mock ports for domains owned by B (Payment, Escrow, Verification, Refund, Notification, Audit).

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, PostgreSQL, Alembic, Pytest.

**Spec:** `scratch/srs.txt` and `scratch/devplan.txt`.

## Global Constraints

- **DB Keys:** UUIDv7 for all Primary Keys (NFR-DB-001).
- **Timezone:** UTC for database storage, WIB (UTC+7) for presentation/notification.
- **Append-Only:** Ledger, Audit Log, and Payment Events are append-only.
- **Data Deletion:** Soft delete for User, Rental, Vehicle (NFR-PDP-003).
- **Security:** Passwords use bcrypt/argon2. JWT access/refresh tokens. Role-Based Access Control (RBAC) enforced per endpoint.

## Open Questions & Assumptions (To Be Resolved by Product/Business)

- `OQ-001`: DP Percentage (Assumed 20-30%, DO NOT HARDCODE).
- `OQ-002`: DP link expiry minutes (X) (DO NOT HARDCODE, use config).
- `OQ-003`: SLA Rental Confirmation (Assumed 2 hours, use config).
- `OQ-007`: X hours to report unmatched unit.
- `OQ-017`: T&C digital agreement (Assume boolean click-to-accept flag + timestamp + IP).

## Review Focus

1. **State Machine Inconsistencies:** Confirming a booking before `EscrowState=DITAHAN_ESCROW`. Ensure tests verify `BookingState` transitions strictly enforce preconditions.
2. **Double Booking (Race Condition):** Concurrent requests locking the same `VehicleAvailability`. Ensure tests use database row-level locking (`SELECT FOR UPDATE`).
3. **Refund Overdraw:** Refunding more than the held escrow amount. Tests must enforce `refund <= escrow_balance`.
4. **Data Leakage via Ports:** Returning ORM objects through Contracts instead of Pydantic DTOs.
5. **Missed Audit Trails:** Critical state changes (e.g., Booking cancel, Rental verification) missing `AuditPort.log()` calls.

---

## Interfaces (Contracts)

**Consumes (Mocked in Sprint 0-2):**
- `PaymentReadPort`: Reads payment status.
- `EscrowReadPort`: Reads escrow state (`DITAHAN_ESCROW`, `LUNAS`).
- `VerificationReadPort`: Reads eKYC status.
- `RefundPort`: Triggers refund.
- `NotificationPort`: Sends push/WA.
- `AuditPort`: Appends audit logs.

**Produces (Exposed to Developer B):**
- `BookingPort`: For B to query booking details.
- `RentalReadPort`: For B to query rental verification/status.

---

### Sprint 0: Scaffolding & Core Foundations

**Files:**
- Create: `app/contracts/ports.py`
- Create: `app/mocks/ports.py`
- Create: `app/modules/auth/`
- Create: `app/modules/user/`

- [ ] **Task 0.1: Define Contracts (`app/contracts/ports.py`)**
  Define `Protocol` classes for `BookingPort`, `RentalReadPort`, `PaymentReadPort`, `EscrowReadPort`, `VerificationReadPort`, `RefundPort`, `NotificationPort`, `AuditPort` using Pydantic DTOs (no SQLAlchemy models).

- [ ] **Task 0.2: Implement Mocks (`app/mocks/ports.py`)**
  Implement dummy classes for B's ports (e.g., `MockPaymentReadPort` returns `BERHASIL`, `MockAuditPort` prints to stdout).

- [ ] **Task 0.3: Database Setup & Alembic**
  Configure async SQLAlchemy session, `Base` model, and initialize Alembic. Create initial migration for `users` and `roles` tables.

- [ ] **Task 0.4: Auth & RBAC (FR-AUTH)**
  Implement JWT generation, validation middleware, and `depends_on_role` FastAPI dependency. Implement `/auth/login`, `/auth/register`. Write integration tests for RBAC.

### Sprint 1: User & Merchant Onboarding

**Files:**
- Create: `app/modules/rental/models.py`, `schemas.py`, `services.py`, `routers.py`
- Modify: `app/modules/user/routers.py`

- [ ] **Task 1.1: User Profile & Consent**
  Implement `/users/me`, update profile, and recording `user_consents` (BR-040). 

- [ ] **Task 1.2: Rental Model & Onboarding (FR-RENTAL)**
  Implement `rentals`, `rental_payout_accounts` (encrypted), `rental_staff` tables. Implement `/rentals/onboard`.

- [ ] **Task 1.3: Rental Verification (Admin/Verification Team)**
  Implement `rental_verifications` table (BR-036). Endpoints for admin to approve/reject rental (updates Rental status). Must emit mock audit log.

### Sprint 2: Vehicle Management & Catalog

**Files:**
- Create: `app/modules/vehicle/models.py`, `routers.py`, `services.py`
- Create: `app/modules/listing/models.py`, `routers.py`
- Create: `app/modules/availability/models.py`, `routers.py`

- [ ] **Task 2.1: Vehicle CRUD (FR-VEHICLE)**
  Implement `vehicles`, `vehicle_documents`, `vehicle_photos`. Endpoints for rental to add vehicles. Ensure RBAC (Rental can only edit their own).

- [ ] **Task 2.2: Availability Calendar (BR-028)**
  Implement `vehicle_availability`. Endpoints to block/unblock dates. Must use explicit `SELECT FOR UPDATE` when locking slots.

- [ ] **Task 2.3: Listing Management (FR-LISTING)**
  Implement `listings` table. Sync vehicle data to listing. Implement logic for freshness/stale threshold (BR-027) and all-in price calculation (BR-026).

### Sprint 3: Discovery & Core Booking (State Machine)

**Files:**
- Create: `app/modules/search/routers.py`, `services.py`
- Create: `app/modules/booking/models.py`, `routers.py`, `state.py`

- [ ] **Task 3.1: Search & Comparison (FR-SEARCH)**
  Implement `/search` endpoint. Filter by availability (joins `vehicle_availability`), location, price. Sort by freshness (BR-025).

- [ ] **Task 3.2: Booking Creation & Lock**
  Implement `/bookings`. Calculate total price. Lock `vehicle_availability` transactionally. Create `Booking` and `BookingItem`. Initial state: `MENUNGGU_DP`.

- [ ] **Task 3.3: DP Link Expiry & Mock Payment Webhook**
  Implement background task/cron to auto-cancel bookings if DP not paid in X minutes (BR-005). Implement a test endpoint to simulate B's payment webhook completing the DP payment, moving state to `MENUNGGU_KONFIRMASI_RENTAL`.

### Sprint 4: Booking Lifecycle (Confirmation, Handover, Cancellation)

**Files:**
- Modify: `app/modules/booking/routers.py`, `services.py`

- [ ] **Task 4.1: Rental Confirmation (BR-006)**
  Endpoint for rental to confirm booking. State transitions to `TERKONFIRMASI`. Implement background task to auto-cancel if SLA breached (triggering mock `RefundPort`).

- [ ] **Task 4.2: User & Rental Cancellation (BR-011, BR-012)**
  Implement `/bookings/{id}/cancel`. Calculate refund tier based on H-x days. Call `RefundPort`. 

- [ ] **Task 4.3: Handover Checklist (BR-007, BR-018)**
  Implement `handover_checklists` and `return_checklists`. Enforce BR-007: Checklist UI locked until `EscrowReadPort.get_state() == LUNAS`.

### Sprint 5: Post-Trip, Reviews, & Port Integration

**Files:**
- Create: `app/modules/review/models.py`, `routers.py`
- Create: `app/modules/dashboard/routers.py`

- [ ] **Task 5.1: Review System (BR-013)**
  Implement `reviews` table. Enforce rules: Only for `BookingState=SELESAI`, two-way, one per party. 

- [ ] **Task 5.2: Rental Dashboard & History**
  Implement aggregated endpoints for rental dashboard (total bookings, revenue stats using mock ledger, upcoming handovers).

- [ ] **Task 5.3: Expose Developer A's Ports**
  Finalize and wire up `BookingPort` (allowing B to query booking state/escrow reference) and `RentalReadPort` (allowing B to check payout account info).

