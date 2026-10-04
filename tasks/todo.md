# Developer A (Marketplace & Rental Operations) Tasks

## Sprint 0: Scaffolding & Core Foundations
- [ ] 0.1 Define Contracts (app/contracts/ports.py)
- [ ] 0.2 Implement Mocks for Developer B's domains (Payment, Escrow, Verification, Refund, Notification, Audit)
- [ ] 0.3 Database Setup & Alembic Init
- [ ] 0.4 Auth & RBAC (JWT, users, roles)

## Sprint 1: User & Merchant Onboarding
- [ ] 1.1 User Profile & Consent endpoints
- [ ] 1.2 Rental Model & Onboarding (rentals, rental_payout_accounts, rental_staff)
- [ ] 1.3 Rental Verification by Admin (rental_verifications)

## Sprint 2: Vehicle Management & Catalog
- [ ] 2.1 Vehicle CRUD (vehicles, documents, photos)
- [ ] 2.2 Availability Calendar (Atomic slot lock, SELECT FOR UPDATE)
- [ ] 2.3 Listing Management (All-in price calculation, freshness)

## Sprint 3: Discovery & Core Booking (State Machine)
- [ ] 3.1 Search & Comparison (Filter by availability, location, price, freshness)
- [ ] 3.2 Booking Creation & Lock (State: MENUNGGU_DP)
- [ ] 3.3 DP Link Expiry cron & Mock Payment Webhook

## Sprint 4: Booking Lifecycle
- [ ] 4.1 Rental Confirmation (SLA auto-cancel to mock RefundPort)
- [ ] 4.2 User & Rental Cancellation (Tiered refund logic)
- [ ] 4.3 Handover Checklist (Locked until EscrowState=LUNAS)

## Sprint 5: Post-Trip & Port Integration
- [ ] 5.1 Review System (Only when BookingState=SELESAI)
- [ ] 5.2 Rental Dashboard & Customer History
- [ ] 5.3 Expose BookingPort and RentalReadPort to Developer B
