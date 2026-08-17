def get_zodiac_sign(sun_longitude: float) -> str:
    """
    Determine the Western astrological sign based on the Sun's tropical longitude.
    
    Args:
        sun_longitude (float): Longitude of the Sun in degrees (0-360).
        
    Returns:
        str: The name of the zodiac sign.
    """
    signs = [
        ("Aries", 0, 30),
        ("Taurus", 30, 60),
        ("Gemini", 60, 90),
        ("Cancer", 90, 120),
        ("Leo", 120, 150),
        ("Virgo", 150, 180),
        ("Libra", 180, 210),
        ("Scorpio", 210, 240),
        ("Sagittarius", 240, 270),
        ("Capricorn", 270, 300),
        ("Aquarius", 300, 330),
        ("Pisces", 330, 360)
    ]
    
    # Ensure longitude is within 0-360
    lon = sun_longitude % 360
    
    for name, start, end in signs:
        if start <= lon < end:
            return name
            
    return signs[0][0] # Fallback to Aries
