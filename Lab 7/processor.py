import math
from datetime import date


def parse_season_pass_validity(date_str):
    """Parse a 'YYYY/MM/DD' expiry date and report whether the pass is still valid.

    Returns a message string. Malformed or impossible dates return an
    'INVALID' message instead of raising.
    """
    if not isinstance(date_str, str):
        return "Invalid input: expected a date string in YYYY/MM/DD format"

    parts = date_str.strip().split('/')
    if len(parts) != 3:
        return "Invalid input: expected a date string in YYYY/MM/DD format"

    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        expiry = date(year, month, day)  # rejects impossible dates (e.g. Feb 30)
    except (ValueError, OverflowError):
        return "Invalid input: expected a real calendar date in YYYY/MM/DD format"

    valid = expiry >= date.today()
    return f"Pass Expiry: {expiry.isoformat()} ({'VALID' if valid else 'EXPIRED'})"


def compute_trail_gradient(elevation_str):
    """Compute gradient % from a 'drop:distance' string.

    Returns the gradient rounded to 2 decimals, or None for invalid input.
    """
    if not isinstance(elevation_str, str):
        return None

    parts = elevation_str.split(':')
    if len(parts) != 2:
        return None

    try:
        drop = float(parts[0])
        distance = float(parts[1])
    except ValueError:
        return None

    if not (math.isfinite(drop) and math.isfinite(distance)):
        return None
    if distance <= 0:
        return None

    try:
        gradient_pct = (drop / distance) * 100.0
    except (ZeroDivisionError, OverflowError):
        return None

    if not math.isfinite(gradient_pct):
        return None
    return round(gradient_pct, 2)


def calculate_lift_access_tier(zone_code):
    """Return the lift pass price for a zone code (BEG, INT, ADV, ALL).

    Returns None for missing, non-string, or unknown zone codes.
    """
    if not isinstance(zone_code, str):
        return None

    prefix = zone_code.strip().upper()[:3]
    zone_rates = {
        "BEG": 35.0,
        "INT": 60.0,
        "ADV": 85.0,
        "ALL": 110.0
    }
    return zone_rates.get(prefix)


def main():
    print("==== Running parse_season_pass_validity ====")
    d_input = input("Enter pass expiry (YYYY/MM/DD): ")
    print(parse_season_pass_validity(d_input))

    print("\n==== Running compute_trail_gradient ====")
    e_input = input("Enter drop:distance (e.g. 250:1000): ")
    gradient = compute_trail_gradient(e_input)
    if gradient is None:
        print("Invalid input: expected drop:distance with a positive distance, e.g. 250:1000")
    else:
        print("Gradient %:", gradient)

    print("\n==== Running calculate_lift_access_tier ====")
    z_input = input("Enter zone code (e.g. BEG, INT, ALL): ")
    price = calculate_lift_access_tier(z_input)
    if price is None:
        print("Invalid zone code: use BEG, INT, ADV or ALL")
    else:
        print("Lift Pass Price: $", price)


if __name__ == "__main__":
    main()