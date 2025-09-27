# This file is open-source under the MIT License (c) Daniel Winterstein. This does not apply to other files in this repository.
from datetime import datetime
import json
import os
import re

try:
    from py_mini_racer import MiniRacer
except Exception:
    print("py_mini_racer not installed. JS in prompts will not work.")
    MiniRacer = None

import requests
import time
import logging
from prompt_manager.parse_json import parse_json

DEFAULT_PROMPT = os.getenv(
    "DEFAULT_PROMPT",
    "You are a helpful assistant. You give short answers, 1 or 2 sentences.",
)
INTERPRET_JS_IN_PROMPTS = os.getenv("INTERPRET_JS_IN_PROMPTS", True)

# Prompts MUST be in the prompts directory, unless PROMPTS_DIR_SECURITY is set to False
PROMPTS_DIR = os.getenv("PROMPTS_DIR") or "prompts"
PROMPTS_DIR_SECURITY = os.getenv("PROMPTS_DIR_SECURITY", "True")
# number format can be set. By default, 4 decimal places
# For scientific notation: use e.g. "8e"
NUMBER_FORMAT = os.getenv("NUMBER_FORMAT", ".4f")
ALLOW_REMOTE_PROMPTS = os.getenv("ALLOW_REMOTE_PROMPTS", "False")
REMOTE_PROMPT_CACHE_SECONDS = int(os.getenv("REMOTE_PROMPT_CACHE_SECONDS", "3600"))

# Dictionary to store custom prompt handlers [(regex_pattern, handler)]
_prompt_handlers = []

def register_prompt_handler(pattern: str, handler: callable):
    """
    Register a global custom handler for specific prompt filenames or patterns.
    Note: call-specific custom handlers can be set using get_prompt() with a custom_handler parameter.
    """
    global _prompt_handlers
    regex_pattern = re.compile(pattern)
    _prompt_handlers.append((regex_pattern, handler))

def get_prompt(prompt_filename, custom_handler:callable=None) -> str:
    """
    Read a file from the prompts directory.
    Can be a local file (in the PROMPTS_DIR directory), or a url.
    Can be a list of prompts, which will be joined with newlines.
    Params:
        prompt_filename: str or list[str] a filename, url, or a list of filenames.
                        files are loaded from the PROMPTS_DIR ("prompts" by default).
        custom_handler: Optional callable that takes a prompt_filename and returns a prompt or None (in which case normal handlers are used).
						Note: Global custom handlers can also be set using register_prompt_handler().
    Returns:
        str The prompt text. No variables inserted - the next step is to use render_prompt()
    """
    # print(f"get_prompt: {prompt_filename}")
    # support prompt as str or list[]
    if isinstance(prompt_filename, list):
        # join prompts with newlines
        return "\n\n".join([get_prompt(x, custom_handler=custom_handler) for x in prompt_filename])    
    if prompt_filename is None:
        return DEFAULT_PROMPT
    # custom handlers
    if custom_handler:
        prompt = custom_handler(prompt_filename)
        if prompt:
            return prompt
    for regex_pattern, handler in _prompt_handlers:
        if regex_pattern.match(prompt_filename):
            return handler(prompt_filename)
    # url?
    if prompt_filename.startswith("http://") or prompt_filename.startswith("https://"):
        if ALLOW_REMOTE_PROMPTS == "False":
            raise ValueError("Remote prompts not allowed: " + prompt_filename)
        cache_file = os.path.join(PROMPTS_DIR, "_cache_", prompt_filename)
        if os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < REMOTE_PROMPT_CACHE_SECONDS:
            with open(cache_file, "r") as f:    
                return f.read()
        # fetch the url
        response = requests.get(prompt_filename)
        prompt = response.text
        with open(cache_file, "w") as f:
            f.write(prompt)
        return prompt
    # Security guard
    if PROMPTS_DIR_SECURITY == "True":
        if re.search(r"[<>:;\"/\\|?*]", prompt_filename) or ".." in prompt_filename:
            raise ValueError("PROMPTS_DIR Security fail: " + prompt_filename)
    if PROMPTS_DIR:
        file = PROMPTS_DIR + "/" + prompt_filename
    else:
        file = prompt_filename
    if not os.path.exists(file) and os.path.exists(file + ".md"):
        print(f"(please use full filenames eg myprompt.txt) Prompt file {file} not found, trying {file}.md")
        file += ".md"
    # print(f"get_prompt file: {file}")
    with open(file, "r") as f:
        prompt = f.read()
        return prompt


def _to_str(x):
    """Convert common types to strings, for insertion into a prompt"""
    if type(x) == str:
        return x
    if type(x) == int or type(x) == bool:
        return str(x)
    if type(x) == float:
        if abs(x) < 1e-8:
            return "0"
        # number format can be set. By default, 4 decimal places (i.e. give the AI some detail).
        number_format = os.getenv("NUMBER_FORMAT", ".4f")
        return f"{x:{number_format}}"
    if type(x) == datetime:
        return x.isoformat()
    if type(x) == list:
        return ", ".join([_to_str(y) for y in x])
    if type(x) == dict:
        return ", ".join([f"{k}: {_to_str(v)}" for k, v in x.items()])
    # attempt a json dump
    try:
        return json.dumps(x)
    except:
        # fallback to string
        return str(x)


def render_prompt(prompt:str, vars:dict, custom_handler:callable=None):
    """
     Insert variables. Follows jinja / mustache: {var} {{escaped braces}}.
    The variable `context` is a special case for "all the context!".
    There is also a special case for `file:X` to include another prompt file -- this will fetch the file using get_prompt()
    with the PROMPTS_DIR and security setup of get_prompt().
    Lines beginning with //// are meta-comments and are not part of the prompt (// you might want in the prompt, but //// is a 2nd order comment on a comment - exclude it).
    """
    # strip //// comments
    prompt = re.sub(r"^////.*$\n?", "", prompt, flags=re.MULTILINE)
    if vars is None and custom_handler is None:
        return prompt # no-op as no replacement options
    if vars is None: vars = {}
    # variables
    # A variable name must start with a letter (this avoids matching JSON), and can contain letters, numbers, and some special characters.
    vpattern = "{([a-zA-Z][a-zA-Z0-9_:/. &|?\"'+-]*?)}"
    p = re.compile(vpattern)
    rendered = p.sub(lambda match: _render_prompt_sub(match.group(1), vars, custom_handler=custom_handler), prompt)
    # convert {{ }} into { }
    rendered = rendered.replace("{{", "{").replace("}}", "}")
    return rendered


def _render_prompt_sub(key:str, vars:dict, custom_handler:callable=None):    
    """
    Convert {var} Supports special cases: `context`, `prompt:X`,
    """
    # simple or-fallback? (without any more complex js logic)
    if "||" in key and not ("&&" in key or "?" in key or "!" in key):
        key_bits = key.split("||")
        for key_bit in key_bits:
            if key_bit[0] == "'" or key_bit[0] == '"':
                # literal string
                return key_bit[1:-1]
            vs = _render_prompt_sub(key_bit, vars, custom_handler=custom_handler)
            if vs != "":
                return vs
        return ""
    # code-guarded snippets: e.g. "test and value" -> if test is true, render value
    if "&&" in key or "?" in key:        
        if INTERPRET_JS_IN_PROMPTS:
            return eval_js_expression(key, vars)
        else:
            logging.warning(f"JS in prompts is disabled: {key}")
    # guarded_match = re.match(guarded_pattern, key)
    # if guarded_match:
    #     # interpret the key as a python expression??
    #     try:
    #         result = eval(key, vars)
    #     except:
    #         result = False
    #     if result:
    #         return _to_str(result)
    if key == "context":
        return _to_str(vars)
    if key[0:5] == "file:":
        # include another prompt file
        included_prompt = get_prompt(key[5:], custom_handler=custom_handler)
        rendered = render_prompt(included_prompt, vars, custom_handler=custom_handler)
        return rendered
    else:
        v = vars.get(key)
    if v is None:
        return ""
    return _to_str(v)


def eval_js_expression(expression: str, vars: dict) -> any:
    """
    Evaluates a JavaScript expression with given variables.
    Does NOT yet do nested "{}" expressions.
    """
    if not MiniRacer:
        raise ImportError("py_mini_racer not installed. JS in prompts will not work.")
    # Create JavaScript context
    ctx = MiniRacer()
    # Set variables in JavaScript context
    for var_name, value in vars.items():
        # security note: keys should be safe
        if re.search(r"[^a-zA-Z0-9_]", var_name):
            raise ValueError(f"Invalid variable name: {var_name}")
        if isinstance(value, str):
            # Strings need to be quoted -- and protect against quotes in the string
            safe_value = value.replace('"', '\\"')
            ctx.eval(f'let {var_name} = "{safe_value}";')
        if isinstance(value, bool):
            ctx.eval(f"let {var_name} = {str(value).lower()};")
        else:
            ctx.eval(f"let {var_name} = {value};")
    # spot variables in expression, e.g. "foo" in "foo && 1"
    all_vars = re.findall(r"[a-zA-Z0-9_]+", expression)
    # and add them to the context as undefined
    for var in all_vars:
        if var not in vars:
            ctx.eval(f"let {var};")
    # Evaluate the expression
    try:
        result = ctx.eval(expression)
        # print(f"eval_js_expression: {expression} -> {result}")
        return result
    except Exception as e:
        print(f"Error evaluating JavaScript expression: {e}")
        return None
