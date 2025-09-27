import json
import re
import json_repair

def parse_json(json_text:str) -> dict:
    """Utility function: Parse a (potentially badly formatted) json string. Because LLMs sometimes output not-quite-json
    Parameters:
        json_text: str E.g. the output content of an LLM.
    Returns:
        dict a parsed json object
    """
    if not json_text:
        return None
    jobj = parse_json_repair(json_text)
    # recurse on jobj, and replace any "undefined" with "null"
    jobj = replace_undefined(jobj, depth=0)
    return jobj

MAX_DEPTH = 20 # safety guard against non-json inputs with self-referencing loops

def replace_undefined(jobj:dict, depth:int) -> dict:
    if depth > MAX_DEPTH:
        return jobj
    depth += 1
    if isinstance(jobj, str):
        if jobj == "undefined":
            return None
        return jobj
    if isinstance(jobj, dict):
        for key, value in jobj.items():
            jobj[key] = replace_undefined(value, depth)
    if isinstance(jobj, list): # seen on one test with "blah {json} blah" -- json-repair returned ['', {json}]
        for i, item in enumerate(jobj):
            clean_item = replace_undefined(item, depth)
            if clean_item != item:
                jobj[i] = clean_item
    return jobj

def parse_json_repair(json_text:str) -> dict:
    jobj = json_repair.loads(json_text)
    if isinstance(jobj, list):
        # pluck one obvious dict?
        largest_dict = None
        for item in jobj:
            if isinstance(item, dict):
                if largest_dict is None or len(item) > len(largest_dict):
                    largest_dict = item
        if largest_dict is not None:
            return largest_dict
    if isinstance(jobj, dict):
        return jobj
    raise Exception("Failed to parse json: "+json_text+"\nGot: "+str(jobj))
