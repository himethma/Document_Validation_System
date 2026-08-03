

import os
import re
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from text_extractor import extract_text

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------------------------------------------------------------------
# Reference documents (gold standards).
#
# Templates are AUTO-DISCOVERED from the references/ folder - no code changes
# are needed to add a new document category. Just drop a file in references/
# named exactly:
#
#       <CATEGORY_CODE>_Template.pdf     (or .docx)
#
# where <CATEGORY_CODE> matches the category value the frontend sends
# (e.g. "FRD", "PRD", "HLD", "R&D", "Release Notes"). On the next server
# restart it will show up as a supported category automatically.
#
# Example current files: FRD_Template.pdf, HLD_Template.pdf, LLD_Template.pdf,
# PRD_Template.pdf, SRS_Template.pdf, STD_Template.pdf
# ---------------------------------------------------------------------------
REFERENCE_DIR = "references"
TEMPLATE_FILENAME_PATTERN = re.compile(r"^(.+)_Template\.(pdf|docx)$", re.IGNORECASE)

# category -> filename inside REFERENCE_DIR, rebuilt by discover_references()
REFERENCE_FILES = {}

# Cache of extracted reference text, populated once at startup.
_reference_cache = {}


def discover_references():
    """Scan references/ and build the category -> filename map from filenames."""
    REFERENCE_FILES.clear()

    if not os.path.isdir(REFERENCE_DIR):
        print(f"[reference] WARNING: reference directory not found: {REFERENCE_DIR}")
        return

    for filename in sorted(os.listdir(REFERENCE_DIR)):
        match = TEMPLATE_FILENAME_PATTERN.match(filename)
        if not match:
            continue
        category = match.group(1)
        REFERENCE_FILES[category] = filename


def load_references():
    """Discover template files, then extract + cache their text once at startup."""
    discover_references()
    _reference_cache.clear()

    for category, filename in REFERENCE_FILES.items():
        path = os.path.join(REFERENCE_DIR, filename)
        text = extract_text(path, filename.lower())
        if text:
            _reference_cache[category] = text
            print(f"[reference] Loaded {category} reference ({filename}): {len(text)} chars")
        else:
            print(f"[reference] WARNING: could not extract text for {category} ({filename})")

    loaded = ", ".join(sorted(_reference_cache.keys())) or "none"
    print(f"[reference] {len(_reference_cache)} template(s) ready: {loaded}")


def get_reference_text(category: str) -> str:
    return _reference_cache.get(category, "")


def is_supported(category: str) -> bool:
    return category in _reference_cache


def supported_categories():
    """Categories that currently have a loaded reference template."""
    return sorted(_reference_cache.keys())


def validate_document(selected_category: str, extracted_text: str):
    # Only categories with a loaded reference template are supported right now.
    if not is_supported(selected_category):
        return {
            "predicted_category": "N/A",
            "confidence": 0,
            "structure_score": 0,
            "content_score": 0,
            "decision": "NOT_SUPPORTED",
            "reason": (
                f"The '{selected_category}' category is not supported yet. "
                f"Reference-based comparison is currently available for: "
                f"{', '.join(supported_categories())}."
            ),
            "missing_sections": [],
            "is_spam_or_irrelevant": False,
        }

    reference_text = get_reference_text(selected_category)

    if not reference_text:
        return {
            "predicted_category": "N/A",
            "confidence": 0,
            "structure_score": 0,
            "content_score": 0,
            "decision": "REJECT",
            "reason": (
                f"No reference document is loaded for '{selected_category}'. "
                f"Please contact the administrator."
            ),
            "missing_sections": [],
            "is_spam_or_irrelevant": False,
        }

    prompt = f"""
You are a strict, deterministic document Quality-Assurance auditor for a
software project submission platform. You behave like a rules-based
checklist evaluator, NOT a creative writer. Given the SAME two documents,
you MUST always return the SAME output - no randomness, no guessing, no
rounding differences between runs.

============================================================
REFERENCE {selected_category} TEMPLATE (GOLD STANDARD)
============================================================
{reference_text[:14000]}

============================================================
USER'S UPLOADED DOCUMENT
============================================================
{extracted_text[:14000]}

============================================================
STEP 0 - BOILERPLATE / UNFILLED TEMPLATE CHECK (HARD GATE)
============================================================
Before doing anything else, check whether the USER'S document is itself an
unfilled template, instruction sheet, or boilerplate shell rather than a
real, completed document. Signs of this include (non-exhaustive):
    - Section bodies are instructional/imperative sentences telling the
      reader what to write (e.g. "Describe the purpose of this document",
      "List the main functions of the system", "Explain the scope...").
    - Generic placeholder markers: "[Insert ...]", "TBD", "TODO", "Lorem
      ipsum", "<Project Name>", "XXX", empty tables with only header rows.
    - The document reads as a set of instructions FOR filling something
      out, not an actual filled-out account of a real project.
    - The content is near-identical in wording to a generic template
      structure with no project-specific facts, names, numbers, or details
      substituted in.

If the USER'S document is substantially an unfilled template or boilerplate
shell (even if headings match the checklist perfectly), you MUST immediately
return:
    decision = "REJECT"
    is_spam_or_irrelevant = true
    structure_score = 0
    content_score = 0
    confidence = 0
    reason = a one-sentence explanation that this is an unfilled
             template/placeholder document, not a completed submission.
Do NOT proceed to Steps 1-6 in that case - skip straight to STEP 7 (output)
with the above values. A document that merely LOOKS structurally complete
because its headings match the reference is not sufficient for ACCEPT if
the content under those headings is placeholder/instructional text rather
than real project-specific writing.

If the document is a genuine, substantively completed document, continue
to STEP 1 as normal.

============================================================
STEP 1 - IDENTIFY THE ACTUAL DOCUMENT TYPE
============================================================
Independently of what category was selected in the upload form, read the
USER'S document and determine what kind of document it actually is, based
purely on its content and structure (e.g. "SRS", "Proposal", "Meeting
Minutes", "Resume", "Unknown"). This is your genuine, unbiased judgment -
do NOT simply assume it matches {selected_category} just because that is
what was selected. Put this value in "predicted_category".

============================================================
STEP 2 - BUILD THE REQUIRED SECTION CHECKLIST
============================================================
Read the "Validation Rules" / "Required Sections" part of the REFERENCE
template above and extract the exact list of required top-level sections
for a {selected_category} document. This checklist is fixed - use it
exactly as written in the reference. Do not invent, rename, merge, or
omit any item from it.

============================================================
STEP 3 - MATCH SECTIONS (STRUCTURE)
============================================================
For every item in the checklist, decide if the USER'S document contains an
equivalent section. Two sections match if they cover the same topic, even
if worded differently (e.g. "Overview" can match "Introduction" if the
content covers the same ground). A section counts as PRESENT only if it
exists AND contains real content - not just a heading with nothing under
it, and not unedited placeholder/template text.

Compute:
    structure_score = round( (number of PRESENT checklist sections /
                               total checklist sections) * 100 )

This must be the exact ratio above - do not adjust it subjectively.

============================================================
STEP 4 - SCORE CONTENT QUALITY
============================================================
For each PRESENT section, rate its content quality using this fixed rubric:
    0-20   Empty, placeholder-only, or template text left unedited
    21-40  Extremely shallow - one line, generic, no specifics
    41-60  Basic but underdeveloped - missing key details a real
           {selected_category} of this type would include
    61-80  Solid, specific, mostly complete content
    81-100 Comprehensive, detailed, professional-quality content
           comparable to the reference

    content_score = round(average of all PRESENT sections' ratings)

If ZERO sections are present, content_score = 0.

============================================================
STEP 5 - OVERALL CONFIDENCE
============================================================
    confidence = round( (structure_score * 0.5) + (content_score * 0.5) )

Do not weight these differently and do not apply any bonus or penalty
outside this formula.

============================================================
STEP 6 - DECISION
============================================================
This system uses a strict two-outcome decision - there is NO middle
"needs review" option. Every document is either good enough to accept
or it is not. Apply these rules in order:
    - If the document is empty, spam, unrelated to {selected_category},
      or the extracted text is gibberish -> decision = "REJECT",
      is_spam_or_irrelevant = true, confidence = 0.
    - Else if confidence >= 75 -> decision = "ACCEPT"
    - Else -> decision = "REJECT"

There is no "MANUAL_REVIEW" or any other decision value. Only "ACCEPT"
or "REJECT" are valid.

============================================================
STEP 7 - OUTPUT
============================================================
Return ONLY the following JSON object. No markdown, no code fences, no
commentary before or after it, and no extra keys:

{{
  "predicted_category": "Your genuine best guess at the document's real type, independent of {selected_category}",
  "confidence": 0,
  "structure_score": 0,
  "content_score": 0,
  "decision": "ACCEPT | REJECT",
  "reason": "One or two sentences explaining the decision, referencing structure_score and content_score.",
  "missing_sections": ["List of checklist sections that were NOT present"],
  "is_spam_or_irrelevant": false
}}

Be exact and consistent. If you were given this exact same pair of
documents again, you must produce this exact same JSON output.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,        # no randomness in sampling
            top_p=1,
            top_k=1,              # always pick the single most likely token
            seed=42,              # fixed seed for extra reproducibility
            response_mime_type="application/json",  # guarantees clean JSON, no ```json fences
        ),
    )

    result_text = response.text.strip()

    if result_text.startswith("```json"):
        result_text = result_text.replace("```json", "").replace("```", "").strip()
    elif result_text.startswith("```"):
        result_text = result_text.replace("```", "").strip()

    result = json.loads(result_text)

    # Safety net: the system is strictly binary now. If the model ever
    # slips and returns something other than ACCEPT/REJECT, force REJECT
    # rather than let an unexpected value through.
    if result.get("decision") not in ("ACCEPT", "REJECT"):
        result["decision"] = "REJECT"

    return result