
# Prompt Manager

A small simple prompt manager for LLM prompts.

## Usage	

```python
from prompt_manager.prompt_manager import get_prompt, render_prompt

prompt = get_prompt("my-prompt.md")
print(prompt)

prompt = render_prompt(prompt, {"name": "John"})
print(prompt)
```

## Features

- Flexible variable substitution with render_prompt()

- Include files from the prompts directory, or from a url with get_prompt()

- Combine files, e.g. roleplay-prompt.txt + output-format-prompt.js

- Handle not-quite-json output from LLMs with parse_json()

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any bugs or feature requests.

## License

This project is licensed under the MIT License.

## Contact

For questions or comments, please contact the project maintainer, Daniel Winterstein.
