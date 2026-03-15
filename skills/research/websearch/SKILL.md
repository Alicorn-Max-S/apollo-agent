---
name: websearch
description: Student-focused web search using the built-in web_search tool (Firecrawl). Results are safe-search filtered, prioritised from trusted educational sources, and include APA citations. Use webscraping skill to analyze full page content from results.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [search, web-search, firecrawl, education, student, research, safe-search]
    related_skills: [webscraping, arxiv, parallel-cli]
    fallback_for_toolsets: []
prerequisites:
  env_vars: [FIRECRAWL_API_KEY]
---

# Web Search

Student-focused web search powered by the built-in `web_search` tool. **Requires `FIRECRAWL_API_KEY`.**

## Student Safety Features

The `web_search` tool has built-in protections for students:

- **Safe-search filtering** — results from blocked/inappropriate domains (reddit, 4chan, tiktok, etc.) are automatically removed
- **Trusted source prioritisation** — educational sources (.edu, .gov, scholarly publishers like arxiv.org, nature.com, khanacademy.org, britannica.com, wikipedia.org) are sorted to the top
- **APA-style citations** — every result includes a ready-to-use `citation` field for schoolwork

## Basic Usage

Use the `web_search` tool directly:

```
web_search(query="photosynthesis process", topic="science")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *(required)* | The search query |
| `topic` | string | `"general"` | Academic subject area to prioritise relevant sources |

### Supported Topics

| Topic | Effect |
|-------|--------|
| `math` | Prioritises math-focused educational content |
| `science` | Surfaces scholarly/research sources |
| `history` | Prioritises historical archives and educational sites |
| `literature` | Focuses on literary analysis and educational sources |
| `geography` | Prioritises geographic/environmental sources |
| `art` | Focuses on art history and educational content |
| `technology` | Surfaces tech documentation and educational resources |
| `health` | Prioritises health/medical educational sources |
| `general` | Default — no topic-specific prioritisation |

### Result Format

Each result contains:

```json
{
  "title": "Page title",
  "url": "https://example.edu/article",
  "description": "Brief snippet...",
  "citation": "example.edu. Page title. Retrieved from https://example.edu/article"
}
```

## Workflow: Search then Scrape

`web_search` returns titles, URLs, snippets, and citations — **not full page content**. To get the full content of promising results, use the webscraping skill's tiered approach:

### Step 1: Search

```
web_search(query="causes of world war 1", topic="history")
```

### Step 2: Analyze top results with webscraping

After getting search results, extract full content from the most relevant URLs using the tiered scraping approach from the **webscraping** skill:

**Tier 1 (Free) — Try first:**

```python
import trafilatura

url = "https://www.britannica.com/event/World-War-I"
downloaded = trafilatura.fetch_url(url)
text = trafilatura.extract(downloaded, include_tables=True, include_links=True)
print(text[:5000])
```

**Tier 2 (Free) — If Tier 1 fails:**

```python
import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
resp = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")

for tag in soup(["script", "style", "nav", "footer", "aside"]):
    tag.decompose()

main = soup.find("main") or soup.find("article") or soup.body
text = main.get_text(separator="\n", strip=True)
print(text[:5000])
```

**Tier 3 (Paid) — Only if free methods fail:**

```
web_extract(urls=["https://www.britannica.com/event/World-War-I"])
```

### Complete Search-then-Scrape Example

```python
import json, trafilatura

# Step 1: Search (use web_search tool, results come back as JSON)
# search_results = web_search(query="renewable energy sources", topic="science")

# Step 2: Parse the top URLs from results
# results = json.loads(search_results)
# urls = [r["url"] for r in results["data"]["web"][:3]]

# Step 3: Scrape each URL (free first)
for url in urls:
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        text = trafilatura.extract(downloaded, include_tables=True)
        if text and len(text.strip()) > 100:
            print(f"--- {url} ---")
            print(text[:3000])
            continue
    # Tier 1 failed — fall back to web_extract (paid)
    # web_extract(urls=[url])
```

## Trusted Educational Domains

The following domains are automatically prioritised in search results:

| Category | Domains |
|----------|---------|
| **Academic** | .edu, scholar.google.com, arxiv.org, pubmed.ncbi.nlm.nih.gov, jstor.org, ieee.org, nature.com, sciencedirect.com |
| **Government** | .gov |
| **Educational** | .org, khanacademy.org, britannica.com, wikipedia.org, pbs.org, worldhistory.org |
| **Science/Media** | nationalgeographic.com, smithsonianmag.com, bbc.co.uk/bitesize, howstuffworks.com |

## Blocked Domains

Results from these domains are automatically removed:

- reddit.com, 4chan.org, tiktok.com, onlyfans.com, buzzfeed.com, tmz.com

## Using Citations in Schoolwork

Every search result includes a `citation` field with an APA-style citation. Copy it directly into your bibliography:

```
khanacademy.org. Photosynthesis overview. Retrieved from https://www.khanacademy.org/science/biology/photosynthesis
```

For more formal citations, expand with the date:

```
Khan Academy. (2026). Photosynthesis overview. Retrieved March 15, 2026, from https://www.khanacademy.org/science/biology/photosynthesis
```

## Tips

- **Set the topic** when searching for school subjects — it helps surface academic sources
- **Use specific queries** — "causes of French Revolution 1789" works better than "French Revolution"
- **Check multiple results** — don't rely on a single source for research papers
- **Always cite your sources** — use the provided `citation` field
- **Scrape for depth** — search results give you an overview; use the webscraping skill to get full content from the best results

## Limitations

- **Requires `FIRECRAWL_API_KEY`** — the web_search tool needs this environment variable
- **Results are snippets** — full page content requires follow-up scraping with webscraping skill or `web_extract`
- **Rate limits** — Firecrawl has API rate limits; avoid rapid repeated searches
- **Not all content is free** — some academic sources may be behind paywalls

## Cross-Skill Chaining

- **Auto-use chaining**: After searching, automatically scrape the top 2-3 most relevant results using the webscraping skill's tiered approach (try free methods first, then `web_extract` as fallback). If scraping fails, fall back to `browser_navigate`.
- **Propose to user**: After finding useful results, propose: "Would you like me to save these sources to memory for your project?" Use the clarify tool to offer this.
- **Citation export**: When the user is working on an assignment, offer to compile all citations into a bibliography section.
