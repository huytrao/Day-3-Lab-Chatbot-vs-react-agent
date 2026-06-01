def calculate_price(adults: int = 1, children: int = 0) -> str:
    """Calculate demo VinWonders ticket price.

    Args:
        adults: Number of adult visitors. Negative or invalid values are treated
            as 0.
        children: Number of child visitors. Negative or invalid values are
            treated as 0.

    Returns:
        Vietnamese text with adult subtotal, child subtotal, total price, and a
        note that this is demo pricing and must be confirmed officially.
    """
    try:
        adult_count = max(0, int(adults))
    except Exception:
        adult_count = 0

    try:
        child_count = max(0, int(children))
    except Exception:
        child_count = 0

    adult_price = 250_000
    child_price = 150_000
    adult_total = adult_count * adult_price
    child_total = child_count * child_price
    total = adult_total + child_total

    return (
        "Gia ve demo VinWonders: "
        f"{adult_count} nguoi lon x {adult_price:,} VND = {adult_total:,} VND; "
        f"{child_count} tre em x {child_price:,} VND = {child_total:,} VND; "
        f"tong cong {total:,} VND. Day la gia demo, can xac nhan gia chinh thuc."
    )
