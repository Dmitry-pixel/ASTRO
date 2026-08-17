from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
import json

from .. import features as hd
from .. import hd_constants
from ..utils import serialization as cj
from ..services.geolocation import get_latitude_longitude, tf
from ..dependencies import verify_token
from ..utils.date_utils import clean_birth_date_to_iso, clean_create_date_to_iso
from ..schemas.general import HealthResponse
from ..utils.health_utils import check_swisseph_health
from datetime import datetime

router = APIRouter(tags=["general"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Operational status and system info."""
    from ..api import __version__
    from ..auth import _get_db

    # Auth/logging database (api_auth.db) — writable runtime state
    db_status = "error"
    try:
        conn = _get_db()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ready"
    except Exception:
        db_status = "error"

    # Reference database (hd_data.sqlite) — required by /v2/calculate enrichment.
    # Checked separately: without it the calculation endpoints fail while the
    # auth database stays perfectly healthy.
    reference_db_status = "error"
    try:
        from ..services.sqlite_repository import SQLiteRepository

        SQLiteRepository().connect().execute("SELECT 1 FROM public_gates LIMIT 1")
        reference_db_status = "ready"
    except Exception:
        reference_db_status = "error"

    ephemeris_status = check_swisseph_health()

    healthy = db_status == "ready" and reference_db_status == "ready"

    return {
        "status": "ok" if healthy else "degraded",
        "version": __version__,
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "pysweph": ephemeris_status,
            "sqlite": db_status,
            "hd_data": reference_db_status
        }
    }

@router.get("/calculate")
def calculate_hd(
    year: int = Query(..., description="Birth year"),
    month: int = Query(..., description="Birth month"),
    day: int = Query(..., description="Birth day"),
    hour: int = Query(..., description="Birth hour"),
    minute: int = Query(..., description="Birth minute"),
    second: int = Query(0, description="Birth second"),
    place: Optional[str] = Query(None, description="Birth place (city, country) or IANA timezone. Required unless latitude and longitude are both supplied."),
    gender: Optional[str] = Query(None, description="Gender"),
    islive: bool = Query(True, description="Whether the person is still alive (True) or deceased (False)"),
    latitude: Optional[float] = Query(None, description="Latitude for the birth place; bypasses geocoding when given with longitude"),
    longitude: Optional[float] = Query(None, description="Longitude for the birth place; bypasses geocoding when given with latitude"),
    authorized: bool = Depends(verify_token)
):
    # 1. Validate and collect input
    if place is None and (latitude is None or longitude is None):
        raise HTTPException(
            status_code=422,
            detail="Provide 'place', or both 'latitude' and 'longitude'."
        )

    birth_time = (year, month, day, hour, minute, second)

    # 2. Geocode and timezone
    try:
        # Use provided coordinates if available, otherwise geocode
        if latitude is None or longitude is None:
            latitude, longitude = get_latitude_longitude(place)
            
        if latitude is not None and longitude is not None:
            if place and "/" in place:
                zone = place
            else:
                # Use singleton
                zone = tf.timezone_at(lat=latitude, lng=longitude) or 'Etc/UTC'
        else:
            raise HTTPException(status_code=400, detail=f"Geocoding failed for place: '{place}'. Please check the place name or try a different format.")
        hours = hd.get_utc_offset_from_tz(birth_time, zone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error determining timezone or offset: {str(e)}")

    # 3. Prepare timestamp
    timestamp = tuple(list(birth_time) + [float(hours)])

    # 4. Calculate Human Design Features
    try:
        single_result = hd.calc_single_hd_features(timestamp, report=False, channel_meaning=False, day_chart_only=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating Human Design features: {str(e)}")

    # 5. Additional Calculations (Age, Zodiac)
    from ..utils import astrology
    from ..utils import date_utils
    
    age = date_utils.calculate_age(birth_time)
    # Personality Sun longitude is at index 0 of the 'lon' list in date_to_gate_dict (index 6 of result)
    sun_lon = single_result[6]['lon'][0]
    zodiac_sign = astrology.get_zodiac_sign(sun_lon)

    # 6. Format Data for JSON Output
    try:
        data = {
            "birth_date": clean_birth_date_to_iso(single_result[9], hours),
            "create_date": clean_create_date_to_iso(single_result[10]),
            "birth_place": place,
            "energy_type": single_result[0],
            "inner_authority": single_result[1],
            "inc_cross": single_result[2],
            "profile": single_result[4], # Pass tuple directly for serialization helper
            "active_chakras": list(single_result[7]),
            "inactive_chakras": list(set(hd_constants.CHAKRA_LIST) - set(single_result[7])),
            "definition": "{}".format(single_result[5]),
            "variables": single_result[11],
            "quarter": single_result[12],
            "cross_name": single_result[13],
            "line_counts": single_result[14],
            "sun_roles": single_result[15],
            "yin_yang_balance": single_result[16],
            "contour": single_result[17],
            "age": age,
            "zodiac_sign": zodiac_sign,
            "gender": gender,
            "islive": islive
        }
        
        # Serialize parts
        general_json_str = cj.general(data)
        gates_json_str = cj.gatesJSON(single_result[6])
        channels_json_str = cj.channelsJSON(single_result[8], False)
        
        general_output = json.loads(general_json_str)
        gates_output = json.loads(gates_json_str)
        channels_output = json.loads(channels_json_str)
        
        final_result = {
            "general": general_output,
            "channels": channels_output,
            "gates": gates_output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing results: {str(e)}")

    return JSONResponse(content=final_result)
