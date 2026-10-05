# Implementation Plan: Backend DriveO (Developer B)

**Context & Scope**
Developer B owns the following domains according to the SRS:
1. **Payment & Settlement:** DP, Full Payment, Escrow release, Midtrans integration.
2. **Verification (eKYC):** KTP, Selfie checks (mocked via dummy service).
3. **Refunds:** Cancellation refund tiers calculation (BR-023, BR-024).
4. **Notifications:** Mock implementations of Email/WhatsApp ports.
5. **Audit & Logging:** Secure append-only logs for administrative and critical actions (SEC-008, Section 15.1).

This plan assumes Developer A has already provided the mock implementations in `app/mocks/ports.py` and the base models in `app/contracts/ports.py`. Developer B will implement the actual services behind these ports (though for payment gateways we will mock the external HTTP calls but build the internal core logic).

## Sprint 1: Setup & Notifications
### Task 1: Setup Dev B Contracts & Mocks for Dev A Domains
Developer B needs to provide mock implementations for `BookingPort` and `RentalReadPort` so B's modules can compile without depending directly on A's code.

### Task 2: Notification Service (FR-NOTIF)
Implement `NotificationService` that implements `NotificationPort`.
- Models: `notifications` table for tracking sent statuses.
- Methods: `send_email`, `send_push`, `send_whatsapp`.

## Sprint 2: Verification & Audit
### Task 3: Verification Service (eKYC)
Implement `VerificationService` implementing `VerificationReadPort`.
- Models: `verifications` table (KTP, Selfie).
- Methods: `submit_verification`, `get_status`.

### Task 4: Audit & Logging (SEC-008, Section 15)
Implement `AuditService` implementing `AuditPort`.
- Models: `audit_logs` table (append-only).
- Methods: `log_event`.

## Sprint 3: Payments & Escrow
### Task 5: Payment Core (FR-PAYMENT)
Implement `PaymentService` integrating with dummy Midtrans.
- Models: `payments` table (total, status, payment_method, external_id).
- Endpoints: Webhook listener `/payments/webhook`.

### Task 6: Escrow Management (BR-015)
Implement `EscrowService`.
- Models: `escrow_ledgers` tracking funds held vs released.
- Methods: `hold_funds`, `release_funds`.

## Sprint 4: Refund Engine
### Task 7: Refund Logic & Tiers (BR-023, BR-024)
Implement `RefundService`.
- Models: `refunds` table.
- Calculate refund amount based on SLA (H-2 = 100%, H-1 = 50%, dll).
