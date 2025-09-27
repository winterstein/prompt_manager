# This file is open-source under the MIT License (c) Daniel Winterstein. This does not apply to other files in this repository.
import sys
import os

# Add the project root directory to the PYTHONPATH. Fixes ModuleNotFoundError: No module 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_manager.parse_json import parse_json

def test_parse_json_with_unescaped_quotes():
    content = '{"key": "value with "quoted" bit"}'
    result = parse_json(content)
    assert result == {"key": "value with \"quoted\" bit"}
    
    content = r'{"key": "value with properly \"quoted\" text"}'
    result = parse_json(content)
    assert result == {"key": "value with properly \"quoted\" text"}

    content = '{"key": null}'
    result = parse_json(content)
    assert result == {"key": None}
    content = '{"key": true}'
    result = parse_json(content)
    assert result == {"key": True}
    content = '{"key": false}'
    result = parse_json(content)
    assert result == {"key": False}


def test_parse_json_with_unescaped_quotes_multiline():
    content = """{"key": "a few lines
    and a "quoted" bit or "two even" oh dear,
    in the middle"}"""
    result = parse_json(content)
    print(str(result))
    assert result == {"key": 'a few lines\n    and a "quoted" bit or "two even" oh dear,\n    in the middle'}
    
def test_parse_json_with_linebreaks_nice():
    content = '{"key": "value\n\nwith breaks"}'
    result = parse_json(content)
    assert result == {"key": "value\n\nwith breaks"}

def test_parse_json_with_linebreaks_ugly():
    content = """{"key": 
    "value

with breaks"}"""
    result = parse_json(content)
    print(str(result))
    assert result == {"key": "value\n\nwith breaks"}
 
 
def test_parse_json_with_undefined():
    content = """{"key": undefined}"""
    result = parse_json(content)
    print(str(result))
    assert result == {"key": None}
 
 
def test_parse_json():
    # Test with valid JSON string
    content = '{"key": "value"}'
    result = parse_json(content)
    assert result == {"key": "value"}

    # Test with JSON string having markdown wrapping
    content = '```json\n{"key": "value"}\n```'
    result = parse_json(content)
    assert result == {"key": "value"}

    # Test with malformed JSON string
    content = 'Some text before {"key": "value"} and some text after'
    result = parse_json(content)
    assert result == {"key": "value"}
 
 
def test_parse_json_with_compact_fluff():
    content = """
type Answer = {"type": "answer", "answer": "Morgan Stanley's ESG documents detail their initiatives and practices focusing on environmental, social, and governance aspects. They include information on the Code of Conduct and Ethics, professional integrity, and remuneration policies with variable compensation structures for Material Risk Takers. The company has ESG and climate risk management strategies in place, which are guided by frameworks like SASB and TCFD. Diversity and inclusion are a core part of their culture, with specific programs aimed at supporting various demographic groups within the firm. Morgan Stanley also emphasizes its commitment to community development through loans and investments, highlighting their efforts to support small businesses and personal development. The documents reflect a strong commitment to transparency and consistent improvement in their ESG approaches.","sources": ["6838cd82-1a9c-3ccc-a85d-e401be984014", "03f5ebcf-b602-31ac-8360-f2a3cadc6266", "58fb3317-af00-3034-98bb-30bdbaf6f6f2", "c090c8b5-19d9-3f19-95fe-92bfd3d3d8ed", "b3a75dd4-fcf6-3e95-8891-3d381e83f8f0"],"confidence": "HIGH","completeness": "HIGH"}
    """
    result = parse_json(content)
    print(str(result))
    assert result["type"] == "answer"
    assert result["answer"] is not None
    assert result["sources"] is not None
    assert result["confidence"] == "HIGH"
    assert result["completeness"] == "HIGH"

 
 
def test_parse_json_with_fluff():
    content = """
type Answer = {
    "type": "answer",
    "answer": "Morgan Stanley's ESG documents detail their initiatives and practices focusing on environmental, social, and governance aspects. They include information on the Code of Conduct and Ethics, professional integrity, and remuneration policies with variable compensation structures for Material Risk Takers. The company has ESG and climate risk management strategies in place, which are guided by frameworks like SASB and TCFD. Diversity and inclusion are a core part of their culture, with specific programs aimed at supporting various demographic groups within the firm. Morgan Stanley also emphasizes its commitment to community development through loans and investments, highlighting their efforts to support small businesses and personal development. The documents reflect a strong commitment to transparency and consistent improvement in their ESG approaches.",
    "sources": ["6838cd82-1a9c-3ccc-a85d-e401be984014", "03f5ebcf-b602-31ac-8360-f2a3cadc6266", "58fb3317-af00-3034-98bb-30bdbaf6f6f2", "c090c8b5-19d9-3f19-95fe-92bfd3d3d8ed", "b3a75dd4-fcf6-3e95-8891-3d381e83f8f0"],
    "confidence": "HIGH",
    "completeness": "HIGH",
}
    """
    result = parse_json(content)
    print(str(result))
    assert result["type"] == "answer"
    assert result["answer"] is not None
    assert result["sources"] is not None
    assert result["confidence"] == "HIGH"
    assert result["completeness"] == "HIGH"


def test_parse_json_unquoted_keys():
    content = """
type Answer = {
    type: "answer",
    answer: "Morgan Stanley's ESG documents detail their initiatives: practices focusing on environmental, social, and governance aspects",
    sources: ["6838cd82-1a9c-3ccc-a85d-e401be984014", "03f5ebcf-b602-31ac-8360-f2a3cadc6266", "58fb3317-af00-3034-98bb-30bdbaf6f6f2", "c090c8b5-19d9-3f19-95fe-92bfd3d3d8ed", "b3a75dd4-fcf6-3e95-8891-3d381e83f8f0"],
    confidence: "HIGH",
    completeness: "HIGH",
}
    """
    result = parse_json(content)
    print(str(result))
    assert result["type"] == "answer"
    assert result["answer"] is not None
    assert result["answer"] == "Morgan Stanley's ESG documents detail their initiatives: practices focusing on environmental, social, and governance aspects"
    assert result["sources"] is not None
    assert result["confidence"] == "HIGH"
    assert result["completeness"] == "HIGH"

def test_parse_json_unquoted_keys2():
    content = """ChatMessage: { message: "Morgan Stanley has made significant strides in assessing the lifecycle impacts of their products and meeting the demand for sustainable products." }
    """
    result = parse_json(content)
    print(str(result))
    assert result["message"] is not None
    assert result["message"] == "Morgan Stanley has made significant strides in assessing the lifecycle impacts of their products and meeting the demand for sustainable products."
 
def test_parse_json_big():
    mystery_blah = """
Sure! Let's create a Sherlock Holmes murder mystery featuring a lost gem.

### Step 1: Create characters:

**VICTIM:**
- **Name:** Lord Alfred Pennington
- **Description:** A wealthy aristocrat known for his extensive collection of rare and valuable gemstones.

**SUSPECT1:**
- **Name:** Lady Penelope Trewbridge
- **Description:** A cousin of Lord Alfred, constantly in need of money due to her lavish lifestyle.

### Step 2: Output a complete MurderMystery JSON object

```json
{
    "victim": {
        "name": "Lord Alfred Pennington",
        "description": "A wealthy aristocrat known for his extensive collection of rare and valuable gemstones."
    },
    "suspects": [
        {
            "name": "Lady Penelope Trewbridge",
            "description": "A distant cousin of Lord Alfred, constantly in need of money due to her lavish lifestyle.",
            "relationship_to_victim": "Distant cousin",
            "motive": "Lady Penelope was in dire financial straits and stood to gain a significant inheritance from Lord Alfred.",
            "motive_clue": "Her recent lavish purchases despite financial issues are well-documented.",
            "place": "Drawing Room"
        }
    ],
    "places": [
        {
            "name": "Library",
            "description": "A large, opulent room filled with shelves of books and a display case for Lord Alfred's gem collection."
        }
    ],
    "place_of_death": "Library",
    "place_of_body": "Library"
}
```

This JSON provides a detailed murder mystery setting for a Sherlock Holmes story.
    """
    p = parse_json(mystery_blah)
    assert p is not None
    print(str(p))
    assert p["victim"] is not None
