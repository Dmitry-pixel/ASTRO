from datetime import datetime, timedelta

# Helper to convert HD timestamp (Y,M,D,H,M,S,Offset) to ISO UTC
def to_iso_utc(ts_tuple):
    try:
        # ts_tuple is (Y, M, D, H, M, S, Offset)
        local_dt = datetime(ts_tuple[0], ts_tuple[1], ts_tuple[2], 
                          ts_tuple[3], ts_tuple[4], ts_tuple[5])
        # Offset is in hours (float or int). Subtract to get UTC.
        offset_hours = ts_tuple[6]
        utc_dt = local_dt - timedelta(hours=offset_hours)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return str(ts_tuple)

# Helper to clean birth_date string which might be "(1990, 1, 1, 12, 0)"
def clean_birth_date_to_iso(b_date_str, offset):
    try:
        if isinstance(b_date_str, tuple):
             # If it's a tuple, format string then parse or just use parts
             parts = list(b_date_str)
        else:
             # If it's string tuple representation
             parts = [int(x) for x in b_date_str.strip('()').split(', ')]
             
        # Pad with 0 for seconds if missing
        while len(parts) < 6:
            parts.append(0)
        local_dt = datetime(*parts[:6])
        utc_dt = local_dt - timedelta(hours=offset)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return str(b_date_str)

# Helper for create_date which is typically already UTC (from swe) but might be tuple/string
def clean_create_date_to_iso(c_date_input):
    try:
        if isinstance(c_date_input, str):
             parts = [float(x) for x in c_date_input.strip('()').split(', ')]
        elif isinstance(c_date_input, (list, tuple)):
             parts = list(c_date_input)
        else:
             return str(c_date_input)
             
        # Create date is from swe.jdut1_to_utc so it is ALREADY UTC.
        # We just need to format it.
        # It's likely (Y, M, D, H, M, S)
        parts = [int(p) for p in parts] # Ensure ints
        while len(parts) < 6:
            parts.append(0)
            
        utc_dt = datetime(*parts[:6])
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return str(c_date_input)

# Helper to calculate age from birth date tuple (Y, M, D, H, M, S)
def calculate_age(birth_time_tuple):
    try:
        birth_date = datetime(birth_time_tuple[0], birth_time_tuple[1], birth_time_tuple[2])
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except Exception:
        return None
