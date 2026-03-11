CAMELOT_MAP = {
    (0,1):"8B",(1,1):"3B",(2,1):"10B",(3,1):"5B",(4,1):"12B",(5,1):"7B",
    (6,1):"2B",(7,1):"9B",(8,1):"4B",(9,1):"11B",(10,1):"6B",(11,1):"1B",
    (0,0):"5A",(1,0):"12A",(2,0):"7A",(3,0):"2A",(4,0):"9A",(5,0):"4A",
    (6,0):"11A",(7,0):"6A",(8,0):"1A",(9,0):"8A",(10,0):"3A",(11,0):"10A",
}
KEY_NAMES = {
    (0,1):"C maj",(1,1):"C# maj",(2,1):"D maj",(3,1):"Eb maj",(4,1):"E maj",(5,1):"F maj",
    (6,1):"F# maj",(7,1):"G maj",(8,1):"Ab maj",(9,1):"A maj",(10,1):"Bb maj",(11,1):"B maj",
    (0,0):"C min",(1,0):"C# min",(2,0):"D min",(3,0):"Eb min",(4,0):"E min",(5,0):"F min",
    (6,0):"F# min",(7,0):"G min",(8,0):"Ab min",(9,0):"A min",(10,0):"Bb min",(11,0):"B min",
}

def get_camelot(key, mode):
    return CAMELOT_MAP.get((key, mode), "Unknown")

def get_key_name(key, mode):
    return KEY_NAMES.get((key, mode), "Unknown")

def get_compatible_keys(camelot_position):
    if camelot_position == "Unknown":
        return []
    number = int(camelot_position[:-1])
    letter = camelot_position[-1]
    opposite = "B" if letter == "A" else "A"
    return [camelot_position, f"{(number % 12) + 1}{letter}", f"{((number - 2) % 12) + 1}{letter}", f"{number}{opposite}"]

def compatibility_score(key1, mode1, key2, mode2):
    cam1 = get_camelot(key1, mode1)
    cam2 = get_camelot(key2, mode2)
    if cam1 == "Unknown" or cam2 == "Unknown":
        return 0.0
    compatible = get_compatible_keys(cam1)
    if cam2 == cam1:
        return 1.0
    elif cam2 in compatible:
        return 0.8
    return 0.0
