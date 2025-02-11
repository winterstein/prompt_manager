# This file is open-source under the MIT License (c) Daniel Winterstein. This does not apply to other files in this repository.
import sys
import os

# # Add the project root directory to the PYTHONPATH. Fixes ModuleNotFoundError: No module 
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_manager.prompt_manager import get_prompt, render_prompt, parse_json

def test_render_prompt_simple():
	p = render_prompt("Test keys {k1} and {k2}", {"k1":"v1","k2":"v two"})
	print(p)
	assert p == "Test keys v1 and v two"
 

 
def test_render_prompt_include_file():
	p = render_prompt("Use this {file:test-prompt.md}", {})
	print(p)
	assert "assistant" in p
 