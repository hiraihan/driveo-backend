def process_payment_success(booking):
    if booking.booking_state == "MENUNGGU_DP":
        booking.booking_state = "MENUNGGU_KONFIRMASI_RENTAL"
        booking.escrow_state = "DITAHAN_ESCROW"

def process_cancellation(booking, alasan: str):
    if booking.booking_state in ["MENUNGGU_DP", "MENUNGGU_KONFIRMASI_RENTAL"]:
        booking.booking_state = "DIBATALKAN"
        if booking.escrow_state == "DITAHAN_ESCROW":
            booking.escrow_state = "DIKEMBALIKAN"
