def process_payment_success(booking):
    if booking.booking_state == "MENUNGGU_DP":
        booking.booking_state = "MENUNGGU_KONFIRMASI_RENTAL"
        booking.escrow_state = "DITAHAN_ESCROW"
