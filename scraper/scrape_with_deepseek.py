# import asyncio
# import json
# from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
# from openai import OpenAI
# from bs4 import BeautifulSoup


# # Connect to local Ollama
# client = OpenAI(
#     base_url="http://localhost:11434/v1",
#     api_key="ollama"
# )


# async def main():

#     browser_config = BrowserConfig(
#         headless=True,
#         browser_type="chromium"
#     )

#     crawler_config = CrawlerRunConfig(
#         cache_mode="BYPASS",
#         wait_until="networkidle"
#     )

#     target_url = "https://www.myscheme.gov.in/schemes/pradhan-mantri-vidyalaxmi-yojana/pmvs"

#     async with AsyncWebCrawler(config=browser_config) as crawler:

#         result = await crawler.arun(
#             url=target_url,
#             config=crawler_config
#         )

#         # --- Extract clean visible content from HTML ---
#         html_content = result.html
#         soup = BeautifulSoup(html_content, "html.parser")

#         main_tag = soup.find("main")

#         if main_tag:
#             page_content = main_tag.get_text(separator="\n")
#         else:
#             page_content = soup.get_text(separator="\n")

#         page_content = page_content[:20000]

#         print("Page Crawled Successfully\n")
#         print("------------ RAW CONTENT SAMPLE ------------")
#         print(page_content[:2000])
#         print("------------ END SAMPLE ------------")
#         # DEBUG PREVIEW
#         print("----- CLEAN CONTENT PREVIEW -----")
#         print(page_content[:1500])
#         print("----- END PREVIEW -----\n")

#         response = client.chat.completions.create(
#             model="deepseek-r1:7b",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a strict government scheme data extractor. "
#                         "Extract ONLY information explicitly present in the given text. "
#                         "Do NOT assume, infer, or fabricate anything. "
#                         "If a section is not clearly mentioned, return an empty list. "
#                         "Return ONLY valid JSON."
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": f"""
# Extract the following details strictly from the provided webpage content.

# - Scheme Name (exact official name as written)
# - Description (summary only from text)
# - Benefits (only explicitly mentioned)
# - Eligibility Criteria (only explicitly mentioned)
# - Documents Required (only if clearly listed)
# - Application Process (only if clearly described)

# If any section is missing in the text, return an empty list.

# Return JSON in this format:

# {{
#   "scheme_name": "",
#   "description": "",
#   "benefits": [],
#   "eligibility": [],
#   "documents_required": [],
#   "application_process": []
# }}

# Webpage Content:
# {page_content}
# """
#                 }
#             ],
#             temperature=0,
#             response_format={"type": "json_object"},
#             max_tokens=800
#         )

#         try:
#             extracted_data = json.loads(response.choices[0].message.content)

#             print("\nExtracted JSON:\n")
#             print(json.dumps(extracted_data, indent=2))

#         except json.JSONDecodeError:
#             print("\n⚠️ Model did not return valid JSON.\n")
#             print(response.choices[0].message.content)


# if __name__ == "__main__":
#     asyncio.run(main())
"""
GovSchemeAssistant — Scheme Data Scraper
Compatible with: crawl4ai 0.8.0
Approach: Two-phase session crawl
  Phase 1 — Load page, wait for React hydration
  Phase 2 — Per-tab: click tab → wait for panel → capture HTML (js_only=True)
  Then BeautifulSoup parses each panel and sends to Ollama for JSON extraction.
"""

import asyncio
import json
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import OpenAI
from bs4 import BeautifulSoup
from database_layer.cleaner import clean_scheme, add_to_database
from database_layer.validator import validate_scheme
from datetime import datetime


# ── Ollama client ─────────────────────────────────────────────────────────────
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

SESSION_ID = "scheme_session"

# ── Phase 1: Just load the page and wait for React ────────────────────────────
PHASE1_CONFIG = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    wait_until="networkidle",
    delay_before_return_html=3.0,
    session_id=SESSION_ID,
    # Scroll to trigger lazy-load of tab nav
    scan_full_page=True,
    scroll_delay=0.3,
)

# ── Phase 2 JS: click one tab by index, inject result into DOM ────────────────
# Must be a plain sync script (no top-level await).
# crawl4ai wraps js_code in an async context internally, but the script itself
# must NOT use top-level await — use .then() chains instead.
def make_tab_click_js(tab_index: int) -> str:
    return f"""
const tabSelectors = [
    '[role="tab"]',
    'button[class*="tab"]',
    '.MuiTab-root',
    '[class*="Tab_tab"]',
    'li[class*="tab"] button',
    'nav button'
];

let tabs = [];
for (const sel of tabSelectors) {{
    tabs = Array.from(document.querySelectorAll(sel));
    if (tabs.length > 0) break;
}}

const tab = tabs[{tab_index}];
if (tab) {{
    tab.click();
}}
"""

# ── Phase 2 wait: wait until a tab panel becomes visible ─────────────────────
WAIT_FOR_PANEL = """js:() => {
    const selectors = [
        '[role="tabpanel"]:not([hidden])',
        '[role="tabpanel"][aria-hidden="false"]',
        '[class*="tabpanel"]:not([hidden])',
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.offsetParent !== null && el.innerText.trim().length > 50) {
            return true;
        }
    }
    return false;
}"""


def make_phase2_config(tab_index: int) -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        session_id=SESSION_ID,
        js_only=True,                          # continue in same tab, no reload
        js_code=make_tab_click_js(tab_index),
        wait_for=WAIT_FOR_PANEL,
        delay_before_return_html=1.5,
    )


# ── Extract visible tab panel text from HTML ──────────────────────────────────
def extract_panel_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    panel_selectors = [
        {'attrs': {'role': 'tabpanel'}},
    ]
    for sel in panel_selectors:
        panels = soup.find_all(**sel)
        for p in panels:
            # Pick the one that isn't hidden
            hidden = p.get('hidden') or p.get('aria-hidden') == 'true'
            if not hidden and len(p.get_text(strip=True)) > 50:
                return clean_text(p.get_text(separator='\n'))
    # Fallback: main content
    main = soup.find('main') or soup.body
    for tag in main(['nav', 'footer', 'header', 'script', 'style']):
        tag.decompose()
    return clean_text(main.get_text(separator='\n'))


def extract_tab_labels(html: str) -> list:
    """Read tab button labels from the page to name each section."""
    soup = BeautifulSoup(html, "html.parser")
    for sel in ['[role="tab"]', 'button[class*="tab"]', '.MuiTab-root']:
        tabs = soup.select(sel)
        if tabs:
            return [t.get_text(strip=True) for t in tabs if t.get_text(strip=True)]
    return []


def clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


# ── LLM extraction ────────────────────────────────────────────────────────────
def extract_with_llm(sections: dict, model: str = "deepseek-r1:7b") -> dict:
    labelled = ""
    for label, content in sections.items():
        if content and content.strip():
            labelled += f"\n\n### {label.upper()} ###\n{content[:3000]}"
    labelled = labelled[:18000]

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict government scheme data extractor. "
                    "Extract ONLY information explicitly present in the text. "
                    "Return ONLY valid JSON with no preamble, explanation, or markdown fences."
                )
            },
            {
                "role": "user",
                "content": f"""Extract these fields STRICTLY from the webpage content below.
Return empty string/list if a section is absent. Do NOT invent anything.

Return ONLY this JSON:
{{
  "scheme_name": "string",
  "description": "string (2-4 sentence summary)",
  "benefits": ["string", ...],
  "eligibility": ["string", ...],
  "documents_required": ["string", ...],
  "application_process": ["string", ...]
}}

Content:
{labelled}"""
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=1200
    )

    raw = response.choices[0].message.content
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
    raw = re.sub(r'^```json|^```|```$', '', raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


# ── Main scrape function ───────────────────────────────────────────────────────
# ── Main scrape function ───────────────────────────────────────────────────────
async def scrape_scheme(url: str, model: str = "deepseek-r1:7b") -> dict:
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        viewport_width=1280,
        viewport_height=900,
    )

    print(f"\n🔍 Crawling: {url}")

    async with AsyncWebCrawler(config=browser_config) as crawler:

        # ── Phase 1: Load page ────────────────────────────────────────────────
        print("  📡 Phase 1: Loading page...")
        result = await crawler.arun(url=url, config=PHASE1_CONFIG)

        if hasattr(result, '_results'):
            result = result._results[0]

        phase1_html = result.html
        soup = BeautifulSoup(phase1_html, "html.parser")

        h1 = soup.find("h1")
        name_hint = h1.get_text(strip=True) if h1 else ""
        print(f"Scheme name hint: {name_hint}")

        tab_labels = extract_tab_labels(phase1_html)
        print(f"Tabs detected: {tab_labels}")

        sections = {}

        if not tab_labels:
            print("No tabs found — using full page content")
            sections = heuristic_split(
                clean_text((soup.find("main") or soup.body).get_text(separator="\n"))
            )
        else:
            for i, label in enumerate(tab_labels):
                print(f"Phase 2 [{i+1}/{len(tab_labels)}]: clicking '{label}'...")
                try:
                    tab_result = await crawler.arun(
                        url=url,
                        config=make_phase2_config(i)
                    )

                    if hasattr(tab_result, '_results'):
                        tab_result = tab_result._results[0]

                    panel_text = extract_panel_text(tab_result.html)
                    if panel_text:
                        sections[label] = panel_text
                        print(f"Got {len(panel_text)} chars")
                    else:
                        print(f"Empty panel")
                except Exception as e:
                    print(f"Tab {i} failed: {e}")

        if name_hint:
            sections["_name_hint"] = name_hint

        print(f"\nSections ready: {[k for k in sections if not k.startswith('_')]}")
        print("Sending to LLM...")

        extracted = extract_with_llm(sections, model=model)

        if not extracted.get("scheme_name") and name_hint:
            extracted["scheme_name"] = name_hint

        extracted["source_url"] = url
        return extracted


# ── Heuristic fallback ────────────────────────────────────────────────────────
SECTION_KEYWORDS = {
    "description":         ["about", "overview", "detail", "description", "scheme details"],
    "benefits":            ["benefit", "what you get", "financial assistance", "subsidy"],
    "eligibility":         ["eligibility", "who can apply", "criteria", "eligible"],
    "documents_required":  ["document", "required doc", "paperwork", "certificate"],
    "application_process": ["how to apply", "application process", "steps to apply", "apply online"],
}

def heuristic_split(text: str) -> dict:
    sections = {k: [] for k in SECTION_KEYWORDS}
    current = "description"
    for line in text.splitlines():
        lower = line.lower().strip()
        if not lower:
            continue
        for section, keywords in SECTION_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                current = section
                break
        sections[current].append(line.strip())
    return {k: "\n".join(v) for k, v in sections.items()}


# ── Batch support ─────────────────────────────────────────────────────────────
async def scrape_multiple(urls: list, model: str = "deepseek-r1:7b") -> list:
    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*55}\n[{i}/{len(urls)}]")
        try:
            data = await scrape_scheme(url, model=model)
            results.append(data)
            print(f"{data.get('scheme_name', 'Unknown')}")
        except Exception as e:
            print(f"Failed: {e}")
            results.append({"source_url": url, "error": str(e)})
    return results


# ── Entry point ───────────────────────────────────────────────────────────────
async def main():
    url =  "https://www.myscheme.gov.in/schemes/fesmwpnie"

    data = await scrape_scheme(url)

    print("\n" + "=" * 55)
    print("EXTRACTED SCHEME DATA")
    print("=" * 55)
    print(json.dumps(data, indent=2, ensure_ascii=False))

    with open("extracted_schemes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\nSaved → extracted_schemes.json")


if __name__ == "__main__":
    asyncio.run(main())