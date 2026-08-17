from .. import hd_constants

def get_inc_cross(date_to_gate_dict):
    ''' 
    get incarnation cross from open gates 
        Args:
            date_to_gate_dict(dict):output of hd_feature class 
                                    keys->[planets,label,longitude,gate,line,color,tone,base]
        Return:
            incarnation cross(str): gates + angle type string
                                    format e.g. "((1,2),(3,4))-RAC"
    '''
    df = date_to_gate_dict
    idx = int(len(df["planets"])/2) #start idx of design values 
    inc_cross = (
        (df["gate"][0],df["gate"][1]),#sun&earth gate at birth
        (df["gate"][idx],df["gate"][idx+1])#sun&earth gate at design
                )          
    profile = df["line"][0],df["line"][idx]
    cr_typ = hd_constants.IC_CROSS_TYP[profile]
    inc_cross = str(inc_cross)+"-"+cr_typ
    return inc_cross

def get_quarter(date_to_gate_dict):
    '''
    Determine the Quarter based on the Personality Sun Gate position.
    The Personality Sun Gate is the first gate in date_to_gate_dict (index 0, label "prs").
    
    Args:
        date_to_gate_dict(dict): output of hd_feature class
    Return:
        quarter_info(dict): {"number": 1-4, "name": "Quarter of ...", "theme": "Purpose through ..."}
    '''
    p_sun_gate = date_to_gate_dict["gate"][0]  # Personality Sun gate
    quarter_num = hd_constants.QUARTER_MAP.get(p_sun_gate, 0)
    quarter_name = hd_constants.QUARTER_NAMES.get(quarter_num, "Unknown")
    
    return {
        "number": quarter_num,
        "name": quarter_name
    }

def get_cross_name(date_to_gate_dict):
    '''
    Get the full descriptive name of the Incarnation Cross from CROSS_DB.
    Uses Personality Sun Gate + angle type (RAC/JXP/LAC).
    
    Args:
        date_to_gate_dict(dict): output of hd_feature class
    Return:
        cross_name(str): e.g. "The Right Angle Cross of the Vessel of Love (1)"
    '''
    df = date_to_gate_dict
    idx = int(len(df["planets"])/2)
    p_sun_gate = df["gate"][0]
    profile = (df["line"][0], df["line"][idx])
    cr_typ = hd_constants.IC_CROSS_TYP.get(profile, "RAC")
    
    # Map angle abbreviation to CROSS_DB key format
    angle_key_map = {"RAC": "RAC", "JXP": "JC", "LAC": "LAC"}
    db_key = angle_key_map.get(cr_typ, "RAC")
    
    cross_info = hd_constants.CROSS_DB.get(p_sun_gate)
    if cross_info:
        return cross_info.get(db_key, f"Unknown Cross for Gate {p_sun_gate}")
    return f"Unknown Cross for Gate {p_sun_gate}"

def get_profile(date_to_gate_dict):
    ''' 
    profile is calculated from sun line of birth and design date
    Args:
        date_to_gate_dict(dict):output of hd_feature class 
                                    keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        profile(tuple): format e.g. (1,4)
    '''
    df = date_to_gate_dict
    idx = int(len(df["line"])/2) #start idx of design values
    profile = (df["line"][0],df["line"][idx]) #sun gate at birth and design
    #sort lines to known format
    if profile not in hd_constants.IC_CROSS_TYP.keys():
        profile = profile[::-1]
    
    return profile

def get_variables(date_to_gate_dict):
    '''
    variables are calculated based on tones of sun(birth,design) and 
    Nodes(birth,design), respectively
    If tone 1,2,3-> left arrow, else right arrow
    Args:
        date_to_gate_dict(dict):output of hd_feature class 
                                    keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        variables(dict): keys-> ["top_right","bottom_right","top_left","bottom_left"]
    '''
    df = date_to_gate_dict
    idx = int(len(df["tone"])/2) #start idx of design values 
    tones = (
            (df["tone"][0]),#sun at birth
            (df["tone"][3]),#Node at birth
            (df["tone"][idx]),#sun at design
            (df["tone"][idx+3]),#node at design
                ) 
    keys = ["top_right","bottom_right","top_left","bottom_left"] #arrows,variables
    
    variables = {}
    for i, key in enumerate(keys):
        tone = tones[i]
        val = "left" if tone <= 3 else "right"
        
        # Get metadata from constants
        meta = hd_constants.VARIABLES_METADATA.get(key, {})
        def_type = meta.get("definitions", {}).get(val, {}).get("type", "Unknown")
        
        variables[key] = {
            "value": val,
            "name": meta.get("name", "Unknown"),
            "aspect": meta.get("aspect", "Unknown"),
            "def_type": def_type
        }

    # Calculate Standard Shorthand (e.g., "PRL DRR")
    # Tones: 0:Motivation(P-Top), 1:Perspective(P-Bottom), 2:Digestion(D-Top), 3:Environment(D-Bottom)
    p_top = "R" if tones[0] > 3 else "L"
    p_bot = "R" if tones[1] > 3 else "L"
    d_top = "R" if tones[2] > 3 else "L"
    d_bot = "R" if tones[3] > 3 else "L"
    
    variables["short_code"] = f"P{p_top}{p_bot} D{d_top}{d_bot}"

    return variables 

def get_line_counts(date_to_gate_dict):
    '''
    Count how many times each line (1-6) appears across all planets,
    separately for Personality ("prs") and Design ("des"), plus total.
    
    Args:
        date_to_gate_dict(dict): output of hd_feature class
                                 keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        line_counts(dict): {"prs": {1:n,...,6:n}, "des": {1:n,...,6:n}, "total": {1:n,...,6:n}}
    '''
    prs_counts = {i: 0 for i in range(1, 7)}
    des_counts = {i: 0 for i in range(1, 7)}
    
    labels = date_to_gate_dict["label"]
    lines = date_to_gate_dict["line"]
    
    for label, line in zip(labels, lines):
        if label == "prs":
            prs_counts[line] = prs_counts.get(line, 0) + 1
        elif label == "des":
            des_counts[line] = des_counts.get(line, 0) + 1
    
    total_counts = {i: prs_counts[i] + des_counts[i] for i in range(1, 7)}
    
    return {
        "prs": prs_counts,
        "des": des_counts,
        "total": total_counts
    }

def _classify_gates(date_to_gate_dict, gate_map):
    '''
    Generic helper: classify all activated gates by a given map,
    group by class with planet labels, and calculate percentages.
    '''
    df = date_to_gate_dict
    total = len(df["gate"])
    
    # Collect unique class names from the map
    classes = sorted(set(gate_map.values()))
    result = {cls: {"values": {}, "share_pct": 0, "total": total} for cls in classes}
    
    for i in range(total):
        gate = df["gate"][i]
        line = df["line"][i]
        label = df["label"][i]
        planet = df["planets"][i]
        
        cls = gate_map.get(gate, "Unknown")
        if cls not in result:
            continue
        
        key = f"({label}) {planet}"
        value = f"{gate}.{line}"
        result[cls]["values"][key] = value
    
    for cls in result:
        count = len(result[cls]["values"])
        result[cls]["share_pct"] = round(count / total * 100) if total > 0 else 0
    
    return result


def get_contour_real_mind_decis_bigO(date_to_gate_dict):
    '''
    Classify all activated gates (all planets, prs + des) by 4 systems:
      - Realization: Individual / Collective / Communal
      - Mind: Individ / Logical / Abstract
      - Decision: Practical / Mental / Empathic
      - BigO: Competition / Strategy / Management / Interaction / Innovation / Direction
    
    Args:
        date_to_gate_dict(dict): output of hd_feature class
    Return:
        dict with 4 keys, each containing class breakdown with percentages
    '''
    return {
        "realization": _classify_gates(date_to_gate_dict, hd_constants.GATE_REALIZATION_MAP),
        "mind": _classify_gates(date_to_gate_dict, hd_constants.GATE_MIND_MAP),
        "decision": _classify_gates(date_to_gate_dict, hd_constants.GATE_DECISION_MAP),
        "big_o": _classify_gates(date_to_gate_dict, hd_constants.GATE_BIGO_MAP),
    }


def get_yin_yang_balance(date_to_gate_dict):
    '''
    Classify all activated gates (all planets, prs + des) into Yang/Yin/Balance
    and calculate percentage share of each class.
    
    Args:
        date_to_gate_dict(dict): output of hd_feature class
                                 keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        yin_yang_balance(dict): {
            "Yang": {"values": {"(prs) Sun": "25.6", ...}, "share_pct": 39, "total": 26},
            "Yin":  {"values": {...}, "share_pct": 42, "total": 26},
            "Balance": {"values": {...}, "share_pct": 19, "total": 26}
        }
    '''
    df = date_to_gate_dict
    
    result = {
        "Yang":    {"values": {}, "share_pct": 0, "total": 0},
        "Yin":     {"values": {}, "share_pct": 0, "total": 0},
        "Balance": {"values": {}, "share_pct": 0, "total": 0},
    }
    
    total_count = len(df["gate"])
    
    for i in range(total_count):
        gate = df["gate"][i]
        line = df["line"][i]
        label = df["label"][i]       # "prs" or "des"
        planet = df["planets"][i]
        
        cls = hd_constants.GATE_YIN_YANG_MAP.get(gate, "Unknown")
        if cls not in result:
            continue
        
        key = f"({label}) {planet}"
        value = f"{gate}.{line}"
        result[cls]["values"][key] = value
    
    # Calculate counts and percentages
    for cls in result:
        count = len(result[cls]["values"])
        result[cls]["total"] = total_count
        result[cls]["share_pct"] = round(count / total_count * 100) if total_count > 0 else 0
    
    return result

def get_sun_roles(date_to_gate_dict):
    '''
    Get the archetypal role for Personality Sun and Design Sun.
    Role is determined by the gate number (8 roles × 8 gates = 64 gates).
    
    Args:
        date_to_gate_dict(dict): output of hd_feature class
                                 keys->[planets,label,longitude,gate,line,color,tone,base]
    Return:
        sun_roles(dict): {
            "prs_sun": {"hexagram": "25.6", "role": "MASTERMIND"},
            "des_sun": {"hexagram": "47.3", "role": "REALIZER"}
        }
    '''
    df = date_to_gate_dict
    idx = int(len(df["gate"]) / 2)  # start index of design values
    
    # Personality Sun = index 0, Design Sun = index idx
    prs_sun_gate = df["gate"][0]
    prs_sun_line = df["line"][0]
    des_sun_gate = df["gate"][idx]
    des_sun_line = df["line"][idx]
    
    prs_role = hd_constants.GATE_ROLE_MAP.get(prs_sun_gate, "Unknown")
    des_role = hd_constants.GATE_ROLE_MAP.get(des_sun_gate, "Unknown")
    
    return {
        "prs_sun": {
            "hexagram": f"{prs_sun_gate}.{prs_sun_line}",
            "role": prs_role
        },
        "des_sun": {
            "hexagram": f"{des_sun_gate}.{des_sun_line}",
            "role": des_role
        }
    }

def get_lunar_phase(date_to_gate_dict):
    """
    Calculate Lunar Phase from Sun/Moon longitude.
    Phase = (Moon - Sun) % 360
    """
    try:
        planets = date_to_gate_dict.get("planets", [])
        lons = date_to_gate_dict.get("lon", [])
        
        if "Sun" not in planets or "Moon" not in planets:
             return "Unknown"
             
        sun_idx = planets.index("Sun")
        moon_idx = planets.index("Moon")
        
        sun = lons[sun_idx]
        moon = lons[moon_idx]
        
        diff = (moon - sun) % 360
        
        # 8 Phases (approx 45 deg each)
        if diff < 45:
            return "New Moon"
        if diff < 90:
            return "Waxing Crescent"
        if diff < 135:
            return "First Quarter"
        if diff < 180:
            return "Waxing Gibbous"
        if diff < 225:
            return "Full Moon"
        if diff < 270:
            return "Waning Gibbous"
        if diff < 315:
            return "Last Quarter"
        return "Waning Crescent"
        
    except Exception:
        return "Unknown"

