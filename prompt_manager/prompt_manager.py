# This file is open-source under the MIT License (c) Daniel Winterstein. This does not apply to other files in this repository.
from datetime import datetime
import json
import os
import re
import requests
import time
DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT",
	"You are a helpful assistant. You give short answers, 1 or 2 sentences."
)

# Prompts MUST be in the prompts directory, unless PROMPTS_DIR_SECURITY is set to False
PROMPTS_DIR = os.getenv("PROMPTS_DIR") or "prompts"
PROMPTS_DIR_SECURITY = os.getenv("PROMPTS_DIR_SECURITY", "True")
# number format can be set. By default, 4 decimal places
# For scientific notation: use e.g. "8e"
NUMBER_FORMAT = os.getenv("NUMBER_FORMAT", ".4f")
ALLOW_REMOTE_PROMPTS = os.getenv("ALLOW_REMOTE_PROMPTS", "False")
REMOTE_PROMPT_CACHE_SECONDS = int(os.getenv("REMOTE_PROMPT_CACHE_SECONDS", "3600"))

def get_prompt(prompt_filename) -> str:
	"""
	Read a file from the prompts directory.
	Can be a local file (in the PROMPTS_DIR directory), or a url.
	Can be a list of prompts, which will be joined with newlines.
	Params:
		prompt_filename: str or list[str] a filename, url, or a list of filenames.
						files are loaded from the PROMPTS_DIR ("prompts" by default).
	Returns:
		str The prompt text. No variables inserted - the next step is to use render_prompt()
	"""
	print(f"get_prompt: {prompt_filename}")
	# support prompt as str or list[]
	if isinstance(prompt_filename, list):
		# join prompts with newlines
		return "\n\n".join([get_prompt(x) for x in prompt_filename])	
	if prompt_filename is None:
		return DEFAULT_PROMPT
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
	print(f"get_prompt file: {file}")
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
	if (type(x) == datetime):
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


def render_prompt(prompt, vars):
	"""
 	Insert variables. Follows jinja / mustache: {var} {{escaped braces}}.
	The variable `context` is a special case for "all the context!".
	There is also a special case for `file:X` to include another prompt file -- this will fetch the file using get_prompt()
	with the PROMPTS_DIR and security setup of get_prompt().
	"""
	if vars is None:
		return prompt
	# variables
	vpattern = "{([a-zA-Z0-9_:/.-]+)}"
	# print(vpattern)
	p = re.compile(vpattern)
	rendered = p.sub(lambda match: _render_prompt_sub(match, vars), prompt)
	# convert {{ }} into { }
	rendered = rendered.replace("{{", "{").replace("}}", "}")
	return rendered


def _render_prompt_sub(match, vars):    
	"""
 Convert {var} Supports special cases: `context`, `prompt:X`, 
	"""
	key = match.group(1)
	print(f"render_prompt_sub: key: {key}")
	if key == "context":
		return _to_str(vars)
	if key[0:5] == "file:":
		print("INSERT "+key[5:])
		v = get_prompt(key[5:])
		print(f"INSERT got {key[5:]} = {v}")
	else:
		v = vars.get(key)
	if v is None:
		return ""
	return _to_str(v)

def parse_json(json:str) -> dict:
	"""Utility function: Parse a (potentially badly formatted) json string. Because LLMs sometimes output not-quite-json
	"""
	try:
		return json.loads(json)
	except json.JSONDecodeError:
		# remove leading non-json characters
		mod_json = re.sub(r"^[\{\[]+", "", json)
		# remove trailing non-json characters
		mod_json = re.sub(r"[\}\]]+$", "", mod_json)
		return json.loads(mod_json)
