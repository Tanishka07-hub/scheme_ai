"""
GovSchemeAssistant — Final Scheme Batch Scraper
Scrapes 9 confirmed working schemes and saves to one combined JSON file.
"""

import asyncio
import json
import re
import time
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import OpenAI
from bs4 import BeautifulSoup

# ── Ollama client ─────────────────────────────────────────────────────────────
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

SESSION_ID = "scheme_session"

# ── 9 confirmed working scheme URLs ──────────────────────────────────────────
SCHEME_URLS = [
    "https://www.myscheme.gov.in/schemes/famdpwog",
    "https://www.myscheme.gov.in/schemes/pmvs",
    "https://www.myscheme.gov.in/schemes/pm-daksh",
    "https://www.myscheme.gov.in/schemes/ip-mea",
    "https://www.myscheme.gov.in/schemes/kvps",
    "https://www.myscheme.gov.in/schemes/sjpfsgc",
    "https://www.myscheme.gov.in/schemes/pmajay-ag",
    "https://www.myscheme.gov.in/schemes/pm-vikas",
    "https://www.myscheme.gov.in/schemes/pgspcscstc",
]

# ── Crawler configs ───────────────────────────────────────────────────────────
def make_phase1_config():
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="networkidle",
        delay_before_return_html=3.0,
        session_id=SESSION_ID,
        scan_full_page=True,
        scroll_delay=0.3,
    )

WAIT_FOR_PANEL = """js:() => {
    const selectors = [
        '[role="tabpanel"]:not([hidden])',
        '[role="tabpanel"][aria-hidden="false"]',
        '[class*="tabpanel"]:not([hidden])',
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.offsetParent !== null && el.innerText.trim().length > 50) return true;
    }
    return false;
}"""

def make_tab_click_js(tab_index: int) -> str:
    return f"""
const tabSelectors = ['[role="tab"]','button[class*="tab"]','.MuiTab-root','[class*="Tab_tab"]','li[class*="tab"] button','nav button'];
let tabs = [];
for (const sel of tabSelectors) {{ tabs = Array.from(document.querySelectorAll(sel)); if (tabs.length > 0) break; }}
const tab = tabs[{tab_index}];
if (tab) tab.click();
"""

def make_phase2_config(tab_index: int) -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        session_id=SESSION_ID,
        js_only=True,
        js_code=make_tab_click_js(tab_index),
        wait_for=WAIT_FOR_PANEL,
        delay_before_return_html=1.5,
    )

# ── Helpers ───────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def extract_tab_labels(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    for sel in ['[role="tab"]', 'button[class*="tab"]', '.MuiTab-root']:
        tabs = soup.select(sel)
        if tabs:
            return [t.get_text(strip=True) for t in tabs if t.get_text(strip=True)]
    return []

def extract_panel_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for p in soup.find_all(attrs={"role": "tabpanel"}):
        hidden = p.get("hidden") or p.get("aria-hidden") == "true"
        if not hidden and len(p.get_text(strip=True)) > 50:
            return clean_text(p.get_text(separator="\n"))
    main = soup.find("main") or soup.body
    for tag in main(["nav", "footer", "header", "script", "style"]):
        tag.decompose()
    return clean_text(main.get_text(separator="\n"))

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
                "content": f"""Extract these fields STRICTLY from the content below.
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

# ── Per-scheme scraper ────────────────────────────────────────────────────────
async def scrape_scheme(url: str, crawler, model: str = "deepseek-r1:7b") -> dict:
    result = await crawler.arun(url=url, config=make_phase1_config())
    if hasattr(result, '_results'):
        result = result._results[0]

    phase1_html = result.html
    soup = BeautifulSoup(phase1_html, "html.parser")

    h1 = soup.find("h1")
    name_hint = h1.get_text(strip=True) if h1 else ""
    tab_labels = extract_tab_labels(phase1_html)
    sections = {}

    if not tab_labels:
        sections = heuristic_split(clean_text((soup.find("main") or soup.body).get_text(separator="\n")))
    else:
        for i, label in enumerate(tab_labels):
            try:
                tab_result = await crawler.arun(url=url, config=make_phase2_config(i))
                if hasattr(tab_result, '_results'):
                    tab_result = tab_result._results[0]
                panel_text = extract_panel_text(tab_result.html)
                if panel_text:
                    sections[label] = panel_text
            except Exception:
                pass

    if name_hint:
        sections["_name_hint"] = name_hint

    extracted = extract_with_llm(sections, model=model)

    if not extracted.get("scheme_name") and name_hint:
        extracted["scheme_name"] = name_hint

    extracted["source_url"] = url
    return extracted

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        viewport_width=1280,
        viewport_height=900,
    )

    all_schemes = []
    total = len(SCHEME_URLS)
    start = time.time()

    print(f"🚀 Scraping {total} schemes...\n{'='*55}")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i, url in enumerate(SCHEME_URLS, 1):
            slug = url.split("/schemes/")[-1]
            print(f"\n[{i:02d}/{total}] {slug}")
            t0 = time.time()
            try:
                data = await scrape_scheme(url, crawler)
                elapsed = round(time.time() - t0, 1)
                print(f"  ✅ '{data.get('scheme_name', '?')}' ({elapsed}s)")
                print(f"     benefits={len(data.get('benefits',[]))}  "
                      f"eligibility={len(data.get('eligibility',[]))}  "
                      f"docs={len(data.get('documents_required',[]))}  "
                      f"steps={len(data.get('application_process',[]))}")
                all_schemes.append(data)
            except Exception as e:
                elapsed = round(time.time() - t0, 1)
                print(f"  ❌ Failed: {e} ({elapsed}s)")
                all_schemes.append({"source_url": url, "error": str(e)})

    # ── Wrap in final output structure ────────────────────────
    output = {
        "metadata": {
            "total_schemes": len(all_schemes),
            "successful": sum(1 for s in all_schemes if "error" not in s),
            "failed": sum(1 for s in all_schemes if "error" in s),
            "scrape_time_seconds": round(time.time() - start, 1),
            "source": "myscheme.gov.in",
        },
        "schemes": all_schemes
    }

    with open("gov_schemes_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*55}")
    print(f"✅ Done! {output['metadata']['successful']}/{total} schemes extracted successfully")
    print(f"⏱  Total time: {output['metadata']['scrape_time_seconds']}s")
    print(f"💾 Saved → gov_schemes_data.json")

if __name__ == "__main__":
    asyncio.run(main())