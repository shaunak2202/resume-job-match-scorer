import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

PROMPT_TEMPLATE = """You are a resume screening expert. Analyze the resume against the job description and return ONLY a JSON object with no extra text.

Job Description:
{job_description}

Resume:
{resume}

Return this exact JSON structure:
{{
  "score": <integer 0-100 representing match percentage>,
  "missing_keywords": [<list of important keywords/skills from the job description missing from the resume>],
  "matched_keywords": [<list of important keywords/skills found in both>],
  "summary": "<2-3 sentence explanation of the score>"
}}"""


def score_resume(resume: str, job_description: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        job_description=job_description.strip(),
        resume=resume.strip(),
    )

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.1},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Cannot connect to Ollama. Make sure it's running: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama took too long to respond. Try again.")

    raw = response.json()["message"]["content"].strip()
    return _parse_json(raw)


def _close_json(text: str) -> str:
    # Walk the string and append any missing closing braces/brackets.
    stack = []
    in_string = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch in "{[":
                stack.append("}" if ch == "{" else "]")
            elif ch in "}]" and stack and stack[-1] == ch:
                stack.pop()

    return text + "".join(reversed(stack))


def _parse_json(raw: str) -> dict:
    # Normalize curly/smart quotes to straight ASCII quotes
    raw = (
        raw.replace("“", '"').replace("”", '"')
           .replace("‘", "'").replace("’", "'")
    )

    # Strip markdown code fences
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    # Drop any prose before the opening brace
    start = raw.find("{")
    if start != -1:
        raw = raw[start:]

    for candidate in (raw, _close_json(raw)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Model returned non-JSON output:\n{raw}")
