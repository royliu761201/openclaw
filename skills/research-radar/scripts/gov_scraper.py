#!/usr/bin/env python3
"""
Gov.cn Policy Page Scraper — Zero-cost supplement to Tavily for Chinese government sites.
Scrapes announcement listing pages from nsfc.gov.cn, most.gov.cn, etc.
Outputs standardized markdown compatible with radar_collector.py pipeline.

Usage:
    python gov_scraper.py                    # Scrape all configured sources
    python gov_scraper.py --sources NSFC     # Scrape specific source
"""
import os
import sys
import re
import json
import time
import datetime
import argparse
import traceback
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Missing dependencies. Run: pip install requests beautifulsoup4")
    sys.exit(1)

# === Configuration: Gov.cn Announcement Pages ===
# Each source defines: name, base_url, list_page, CSS selectors for list items
GOV_SOURCES = {
    "NSFC": {
        "name": "国家自然科学基金委员会",
        "list_url": "https://www.nsfc.gov.cn/publish/portal0/tab434/",
        "base_url": "https://www.nsfc.gov.cn",
        "item_selector": "li a",
        "date_selector": "span",
        "keywords_filter": ["项目指南", "申报", "通知", "申请", "基金", "指南", "受理", "评审"],
    },
    "MOST": {
        "name": "科学技术部",
        "list_url": f"https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/fgzc/gfxwj/gfxwj{datetime.datetime.now().year}/",
        "base_url": "https://www.most.gov.cn",
        "item_selector": "li a",
        "date_selector": "span",
        "keywords_filter": ["重点研发", "重大专项", "申报", "指南", "项目", "计划", "颠覆"],
    },
    "MOST_KJBG": {
        "name": "科技部-科技报告",
        "list_url": "https://www.most.gov.cn/kjbgz/",
        "base_url": "https://www.most.gov.cn",
        "item_selector": "li a",
        "date_selector": "span",
        "keywords_filter": ["重点研发", "申报", "指南", "项目"],
    },
    "NHC": {
        "name": "国家卫生健康委员会",
        "list_url": "https://www.nhc.gov.cn/kjxx/s7785/new_list.shtml",
        "base_url": "https://www.nhc.gov.cn",
        "item_selector": "li a",
        "date_selector": "span.pubtimedate",
        "keywords_filter": ["课题", "申报", "科研", "项目", "通知", "重大专项"],
    },
    "MOE": {
        "name": "教育部",
        "list_url": "https://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/",
        "base_url": "https://www.moe.gov.cn",
        "item_selector": "li a",
        "date_selector": "span",
        "keywords_filter": ["课题", "申报", "人文社科", "科研", "重点实验室", "项目"],
    },
    "NOPSS": {
        "name": "全国哲学社会科学工作办公室",
        "list_url": "http://www.nopss.gov.cn/n1/c10132070/list.html",
        "base_url": "http://www.nopss.gov.cn",
        "item_selector": "li a",
        "date_selector": "span",
        "keywords_filter": ["社科基金", "项目申报", "申报公告", "年度项目", "重大项目"],
    },
    "ZJ_KJT": {
        "name": "浙江省科学技术厅",
        "list_url": "https://kjt.zj.gov.cn/col/col1229123966/index.html",
        "base_url": "https://kjt.zj.gov.cn",
        "item_selector": "li a",
        "date_selector": "span",
        "keywords_filter": ["自然科学基金", "尖兵领雁", "重点研发", "申报", "项目", "通知"],
    },
    "HB_KJT": {
        "name": "湖北省科学技术厅",
        "list_url": "https://kjt.hubei.gov.cn/kjdt/tzgg/",
        "base_url": "https://kjt.hubei.gov.cn",
        "item_selector": "li a",
        "date_selector": "span",
        "keywords_filter": ["自然科学基金", "重大科技", "重点研发", "申报", "项目", "通知"],
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

WORKSPACE_DIR = Path(os.path.expanduser("~/workspace"))
RAW_DATA_DIR = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_raw_data"
SEEN_GOV_PATH = RAW_DATA_DIR / "seen_gov_urls.json"


def load_seen_urls():
    """Load seen URLs as dict {url: iso_timestamp}. 90-day rolling purge."""
    if SEEN_GOV_PATH.exists():
        try:
            with open(SEEN_GOV_PATH, "r") as f:
                data = json.load(f)
            # Backward compat: convert list to dict
            if isinstance(data, list):
                now_str = datetime.datetime.now().isoformat()
                data = {url: now_str for url in data}
            # Purge entries older than 90 days
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=90)).isoformat()
            data = {url: ts for url, ts in data.items() if ts > cutoff}
            return data
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def save_seen_urls(seen_dict):
    """Save seen URLs dict {url: iso_timestamp}."""
    with open(SEEN_GOV_PATH, "w") as f:
        json.dump(seen_dict, f, ensure_ascii=False, indent=2)


def scrape_source(source_key, source_config):
    """Scrape a single gov.cn announcement listing page."""
    name = source_config["name"]
    list_url = source_config["list_url"]
    base_url = source_config["base_url"]
    item_sel = source_config["item_selector"]
    kw_filter = source_config["keywords_filter"]

    print(f"  -> [Gov Scraper] Fetching: {name} ({list_url})")

    try:
        resp = requests.get(list_url, headers=HEADERS, timeout=15, verify=False)
        resp.encoding = resp.apparent_encoding or "utf-8"

        if resp.status_code != 200:
            return f"> ⚠️ HTTP {resp.status_code} from {name}\n"

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(item_sel)

        if not items:
            return f"> ⚠️ No items found on {name} (selector: `{item_sel}`)\n"

        results = []
        for item in items[:30]:  # Limit to latest 30
            title = item.get_text(strip=True)
            href = item.get("href", "")

            if not title or not href:
                continue

            # Resolve relative URLs
            if href.startswith("/"):
                href = urljoin(base_url, href)
            elif not href.startswith("http"):
                href = urljoin(list_url, href)

            # Keyword relevance filter
            if not any(kw in title for kw in kw_filter):
                continue

            results.append({"title": title, "url": href})

        return results

    except requests.exceptions.Timeout:
        return f"> ⚠️ Timeout fetching {name}\n"
    except (requests.RequestException, ValueError, AttributeError) as e:
        traceback.print_exc()
        return f"> ⚠️ Error scraping {name}: {e}\n"


def run_gov_scraper(sources_filter=None):
    """Main entry point: scrape all configured gov.cn sources."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    seen_urls = load_seen_urls()
    output_lines = [
        f"## 🏛️ Gov.cn Policy Scraper Results: {today_str}",
        "> **Auto-scraped by gov_scraper.py (Zero-cost HTML extraction)**\n",
    ]

    sources_to_scan = GOV_SOURCES
    if sources_filter:
        sources_to_scan = {
            k: v
            for k, v in GOV_SOURCES.items()
            if any(s.upper() in k.upper() for s in sources_filter)
        }
        if not sources_to_scan:
            print(f"⚠️ No matching sources for: {sources_filter}")
            sources_to_scan = GOV_SOURCES

    new_count = 0
    now_str = datetime.datetime.now().isoformat()
    for src_key, src_config in sources_to_scan.items():
        results = scrape_source(src_key, src_config)

        if isinstance(results, str):
            # Error message
            output_lines.append(f"### 🎯 {src_config['name']} ({src_key})")
            output_lines.append(results)
            # Rate limit between sources
            time.sleep(3)
            continue

        new_items = []
        for item in results:
            if item["url"] not in seen_urls:
                seen_urls[item["url"]] = now_str
                new_items.append(item)
                new_count += 1

        if new_items:
            output_lines.append(f"### 🎯 {src_config['name']} ({src_key}) — {len(new_items)} 条新通知")
            for item in new_items:
                output_lines.append(f"- **[{item['title']}]({item['url']})**")
            output_lines.append("")
        else:
            output_lines.append(f"### 🎯 {src_config['name']} ({src_key}) — 无新通知")
            output_lines.append("")

        # Rate limit between sources (anti-ban)
        time.sleep(3)

    save_seen_urls(seen_urls)

    output_text = "\n".join(output_lines)
    print(f"✅ Gov scraper done. {new_count} new announcements found.")
    return output_text


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    parser = argparse.ArgumentParser(description="Gov.cn Policy Page Scraper")
    parser.add_argument("--sources", nargs="+", help="Specific sources to scrape", default=[])
    args = parser.parse_args()

    result = run_gov_scraper(sources_filter=args.sources if args.sources else None)
    print("\n" + result)
