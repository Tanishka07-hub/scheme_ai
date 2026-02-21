import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from openai import OpenAI
from content_filter import extract_scheme_content


# Connect to local Ollama (OpenAI-compatible API)
client = OpenAI(
    base_url="http://10.174.207.131:11434/v1",
    api_key="ollama"
)

async def main():

    # -------------------------
    # Configure Browser
    # -------------------------
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium"
    )

    crawler_config = CrawlerRunConfig(
        cache_mode="BYPASS"
    )

    # -------------------------
    # Target Scheme URL
    # -------------------------
    target_url = "https://pmkisan.gov.in/"

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=target_url,
            config=crawler_config
        )
        raw_content = result.markdown
        
        page_content = extract_scheme_content(raw_content)


        # Focus on actual scheme section if possible
        if "PM-KISAN Scheme" in page_content:
            page_content = page_content[page_content.find("PM-KISAN Scheme"):]

        # Limit size for model
        page_content = page_content[:20000]

        print("Page Crawled Successfully\n")

        # -------------------------
        # Send to Local DeepSeek 7B
        # -------------------------
        response = client.chat.completions.create(
            model="deepseek-r1:7b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict JSON API. "
                        "You must return ONLY valid JSON. "
                        "Do not explain. Do not summarize. "
                        "Do not add text outside JSON."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
Extract structured scheme data from the content below.

Return EXACTLY in this JSON format:

{{
  "scheme_name": "",
  "description": "",
  "benefits": [],
  "eligibility": [],
  "documents_required": [],
  "application_process": ""
}}

Content:
{page_content}
"""
                }
            ],
            temperature=0,
            response_format={"type": "json_object"},
            max_tokens=800
        )

        # Parse JSON safely
        try:
            extracted_data = json.loads(response.choices[0].message.content)
            print("\nExtracted JSON:\n")
            print(json.dumps(extracted_data, indent=2))
        except json.JSONDecodeError:
            print("\n⚠️ Model did not return valid JSON.\n")
            print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
