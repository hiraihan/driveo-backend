from enum import StrEnum

class UserRole(StrEnum):
    ADMIN = "Admin"
    RENTAL = "Rental"
    PENYEWA = "Penyewa"
    # Role operasional DriveO (frontend)
    STAFF_OPERASIONAL = "STAFF_OPERASIONAL"
    STAFF_KEUANGAN = "STAFF_KEUANGAN"
    TIM_VERIFIKASI = "TIM_VERIFIKASI"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    TIM_MEDIASI = "TIM_MEDIASI"

class BookingState(StrEnum):
    MENUNGGU_DP = "MENUNGGU_DP"
    MENUNGGU_KONFIRMASI_RENTAL = "MENUNGGU_KONFIRMASI_RENTAL"
    TERKONFIRMASI = "TERKONFIRMASI"
    BERJALAN = "BERJALAN"
    SELESAI = "SELESAI"
    DIBATALKAN = "DIBATALKAN"
    DITOLAK = "DITOLAK"

class BookingEvent(StrEnum):
    DP_PAID = "DP_PAID"
    CONFIRM = "CONFIRM"
    REJECT = "REJECT"
    CANCEL = "CANCEL"
    EXPIRE = "EXPIRE"
    SLA_BREACH = "SLA_BREACH"
    HANDOVER = "HANDOVER"
    RETURN = "RETURN"

class EscrowState(StrEnum):
    NONE = "NONE"
    DITAHAN_ESCROW = "DITAHAN_ESCROW"
    LUNAS = "LUNAS"
    DICAIRKAN = "DICAIRKAN"
    DIKEMBALIKAN = "DIKEMBALIKAN"

class LedgerEntryType(StrEnum):
    HOLD = "HOLD"
    RELEASE = "RELEASE"
    REFUND = "REFUND"

class SlotStatus(StrEnum):
    DIPESAN = "DIPESAN"
    DIBLOKIR = "DIBLOKIR"

class RentalStatus(StrEnum):
    MENUNGGU = "MENUNGGU"
    LOLOS = "LOLOS"
    DITOLAK = "DITOLAK"

class VerificationStatus(StrEnum):
    MENUNGGU = "MENUNGGU"
    TERVERIFIKASI = "TERVERIFIKASI"
    DITOLAK = "DITOLAK"

class PaymentType(StrEnum):
    DP = "DP"
    PELUNASAN = "PELUNASAN"

class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    BERHASIL = "BERHASIL"
    GAGAL = "GAGAL"

class ListingStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class VehicleStatus(StrEnum):
    AKTIF = "AKTIF"
    NONAKTIF = "NONAKTIF"

class ChecklistType(StrEnum):
    HANDOVER = "HANDOVER"
    RETURN = "RETURN"
