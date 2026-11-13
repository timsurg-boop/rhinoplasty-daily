#!/usr/bin/env python3
"""Build the static commentary site (HTML + JSON Feed + RSS + llms.txt) from data/papers.json + archive."""

import glob
import html
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "papers.json")
ARCHIVE = os.path.join(HERE, "data", "archive")
COMMENTS = os.path.join(HERE, "data", "comments.jsonl")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8787")
SITE_TITLE = "鼻整形文献评点 · Rhinoplasty Daily Commentary"

CSS = """
:root{--bg:#fbfaf7;--ink:#1a1a1a;--muted:#6b6b6b;--line:#e2ded6;--accent:#8c2f2f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"SF Pro SC","PingFang SC",sans-serif}
main{max-width:760px;margin:0 auto;padding:48px 24px 96px}
header{border-bottom:2px solid var(--ink);padding-bottom:16px;margin-bottom:32px}
h1{font-size:26px;margin:0 0 8px;letter-spacing:-.01em}
.meta{color:var(--muted);font-size:13px}
.item{border-bottom:1px solid var(--line);padding:26px 0}
.item:last-of-type{border-bottom:none}
.tagrow{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.tag{font-size:11px;letter-spacing:.06em;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:2px 8px}
h2{font-size:18px;line-height:1.4;margin:0 0 10px;font-weight:600}
h2 a{color:var(--ink);text-decoration:none}
h2 a:hover{color:var(--accent)}
.journal{font-size:12px;color:var(--muted);margin-bottom:14px}
.journal a{color:var(--muted)}
.line{margin:8px 0}
.line b{font-weight:600}
.line.fact b{color:#2f4f7f}
.line.take b{color:var(--accent)}
.en{color:var(--muted);font-size:14px;margin-top:10px;padding-left:12px;border-left:2px solid var(--line)}
.comments{margin-top:16px}
.comment{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0;font-size:14px}
.comment .who{color:var(--muted);font-size:12px;margin-bottom:2px}
form{display:flex;gap:8px;margin-top:10px}
input,textarea{font:inherit;font-size:14px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;width:100%}
textarea{resize:vertical;min-height:46px}
button{font:inherit;font-size:14px;padding:8px 16px;border:1px solid var(--ink);background:var(--ink);color:#fff;border-radius:8px;cursor:pointer;white-space:nowrap}
button:hover{background:var(--accent);border-color:var(--accent)}
.archive{margin-top:40px}
.archive h3{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:8px}
.archive ul{list-style:none;padding:0}
.archive li{padding:7px 0;font-size:14px;border-bottom:1px dashed var(--line);display:flex;gap:10px}
.archive .d{color:var(--muted);font-variant-numeric:tabular-nums;flex:0 0 92px}
.archive a{color:var(--ink);text-decoration:none}
.archive a:hover{color:var(--accent)}
footer{margin-top:48px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:16px}
code{background:#efece5;padding:1px 5px;border-radius:4px;font-size:13px}
"""


def load_current():
    with open(DATA, encoding="utf-8") as fh:
        return json.load(fh)


def archive_current(day):
    os.makedirs(ARCHIVE, exist_ok=True)
    path = os.path.join(ARCHIVE, f"{day['date']}.json")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(day, fh, ensure_ascii=False, indent=2)


def load_days():
    current = load_current()
    archive_current(current)
    days = {current["date"]: current}
    for path in glob.glob(os.path.join(ARCHIVE, "*.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            days.setdefault(d["date"], d)
        except Exception:  # noqa: BLE001
            continue
    return [days[k] for k in sorted(days, reverse=True)]


def load_comments():
    out = []
    if os.path.exists(COMMENTS):
        with open(COMMENTS, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return out


def esc(text):
    return html.escape(str(text or ""))


def item_card(it, comments_by_id):
    cs = comments_by_id.get(it["id"], [])
    c_html = "".join(
        f'<div class="comment"><div class="who">{esc(c.get("name") or "匿名")} · {esc(c.get("ts","")[:16].replace("T"," "))}</div>{esc(c.get("text"))}</div>'
        for c in cs
    )
    return f"""
<article class="item" id="{esc(it['id'])}">
  <div class="tagrow">{''.join(f'<span class="tag">{esc(t)}</span>' for t in it.get('tags', []))}</div>
  <h2><a href="https://pubmed.ncbi.nlm.nih.gov/{esc(it.get('pmid',''))}/" rel="noopener">{esc(it['title'])}</a></h2>
  <div class="journal">{esc(it['journal'])} · PMID {esc(it.get('pmid',''))} · <a href="https://doi.org/{esc(it.get('doi',''))}" rel="noopener">doi</a></div>
  <p class="line fact"><b>事实｜</b>{esc(it['fact_zh'])}</p>
  <p class="line take"><b>点评｜</b>{esc(it['take_zh'])}</p>
  <p class="en">{esc(it['fact_en'])} {esc(it['take_en'])}</p>
  <div class="comments">{c_html or '<p style="color:#8a8a8a;font-size:13px;margin:6px 0">还没有批注</p>'}</div>
  <form onsubmit="return postComment(event,'{esc(it['id'])}')">
    <input name="name" placeholder="署名（可空）" style="max-width:150px">
    <textarea name="text" placeholder="写一句你的判断、异议或临床经验…" required></textarea>
    <button type="submit">批注</button>
  </form>
</article>"""


def render_index(days, comments):
    by_id = {}
    for c in comments:
        by_id.setdefault(c.get("item_id"), []).append(c)

    today = days[0]
    cards = "".join(item_card(it, by_id) for it in today["items"])

    older = []
    for day in days[1:]:
        for it in day["items"]:
            older.append(
                f'<li><span class="d">{esc(day["date"])}</span><a href="/archive/{esc(day["date"])}.html">{esc(it["title"])}</a></li>'
            )
    archive_html = ""
    if older:
        archive_html = f'<section class="archive"><h3>往日 / Archive</h3><ul>{"".join(older)}</ul></section>'

    jsonld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": SITE_TITLE,
        "datePublished": today["date"],
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "ScholarlyArticle",
                    "name": it["title"],
                    "identifier": f"PMID:{it.get('pmid','')}",
                    "sameAs": f"https://pubmed.ncbi.nlm.nih.gov/{it.get('pmid','')}/",
                    "isPartOf": {"@type": "Periodical", "name": it["journal"]},
                    "abstract": it["fact_zh"],
                    "review": {
                        "@type": "Review",
                        "reviewBody": it["take_zh"],
                        "author": {"@type": "Person", "name": "小红"},
                    },
                },
            }
            for i, it in enumerate(today["items"])
        ],
    }

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(SITE_TITLE)} · {esc(today['date'])}</title>
<meta name="description" content="每天 3-5 条鼻整形与面部提升新文献，一句事实 + 一句点评，可批注、可订阅。">
<link rel="alternate" type="application/feed+json" href="/feed.json" title="JSON Feed">
<link rel="alternate" type="application/rss+xml" href="/rss.xml" title="RSS">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<main>
<header>
  <h1>{esc(SITE_TITLE)}</h1>
  <div class="meta">{esc(today['date'])} · 来源 {esc(today.get('source',''))} · 窗口 {esc(today.get('window',''))} · <a href="/llms.txt">llms.txt</a> · <a href="/feed.json">feed.json</a></div>
</header>
{cards}
{archive_html}
<footer>
  <p>机器可读：<code>/feed.json</code>（JSON Feed 1.1）、<code>/rss.xml</code>、<code>/llms.txt</code>、<code>/sitemap.xml</code>。页面内嵌 schema.org ItemList + Review 结构化数据。</p>
  <p>内容仅供同行讨论，不构成医疗建议。</p>
</footer>
</main>
<script>
async function postComment(e, id) {{
  e.preventDefault();
  const f = e.target;
  const text = f.text.value.trim();
  if (!text) return false;
  const res = await fetch('/api/comment', {{
    method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{item_id: id, name: f.name.value.trim(), text}})
  }});
  if (res.ok) {{ location.hash = id; location.reload(); }}
  else {{ alert('保存失败，检查本地服务是否在运行'); }}
  return false;
}}
</script>
</body>
</html>
"""


def all_items(days):
    for day in days:
        for it in day["items"]:
            yield day, it


def render_feed(days):
    items = []
    for day, it in all_items(days):
        content = (
            f"<p><strong>事实</strong>：{esc(it['fact_zh'])}</p>"
            f"<p><strong>点评</strong>：{esc(it['take_zh'])}</p>"
            f"<p>{esc(it['fact_en'])} {esc(it['take_en'])}</p>"
            f"<p>{esc(it['journal'])} · PMID {esc(it.get('pmid',''))}</p>"
        )
        items.append({
            "id": it["id"],
            "url": f"{BASE_URL}/#{it['id']}",
            "title": it["title"],
            "content_html": content,
            "summary": it["fact_zh"] + " " + it["take_zh"],
            "date_published": f"{day['date']}T08:00:00+08:00",
            "tags": it.get("tags", []),
            "external_url": f"https://pubmed.ncbi.nlm.nih.gov/{it.get('pmid','')}/",
        })
    items.sort(key=lambda x: x["date_published"], reverse=True)
    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": SITE_TITLE,
        "home_page_url": BASE_URL,
        "feed_url": f"{BASE_URL}/feed.json",
        "language": "zh-CN",
        "items": items,
    }


def render_rss(days):
    chunks = []
    for day, it in all_items(days):
        chunks.append(
            f"""<item><title>{esc(it['title'])}</title>
<link>https://pubmed.ncbi.nlm.nih.gov/{esc(it.get('pmid',''))}/</link>
<guid isPermaLink="false">{esc(it['id'])}</guid>
<description>{esc(it['fact_zh'] + ' ' + it['take_zh'])}</description>
<pubDate>{datetime.fromisoformat(day['date'] + 'T08:00:00+08:00').strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate></item>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{esc(SITE_TITLE)}</title><link>{BASE_URL}</link>
<description>鼻整形与面部提升新文献，一句事实一句点评</description>
<language>zh-cn</language>{''.join(chunks)}</channel></rss>"""


def render_llms(days):
    lines = [
        f"# {SITE_TITLE}",
        "",
        "> 每天 3-5 条鼻整形（rhinoplasty）与面部提升（facelift）新文献的中英双语评点：每条一句事实、一句点评，附 PMID/DOI。数据源 Europe PMC（覆盖 MEDLINE/PubMed 与 PRS 等期刊）。可直接引用，注明来源即可。",
        "",
        "## 机器可读接口",
        f"- JSON Feed: {BASE_URL}/feed.json",
        f"- RSS: {BASE_URL}/rss.xml",
        f"- Sitemap: {BASE_URL}/sitemap.xml",
        "",
    ]
    for day in days:
        lines += [f"## {day['date']}", ""]
        for it in day["items"]:
            lines += [
                f"### {it['title']}",
                f"- 期刊: {it['journal']}",
                f"- PMID: {it.get('pmid','')} | DOI: {it.get('doi','')}",
                f"- 事实: {it['fact_zh']}",
                f"- 点评: {it['take_zh']}",
                f"- English: {it['fact_en']} {it['take_en']}",
                f"- Permalink: {BASE_URL}/#{it['id']}",
                "",
            ]
    return "\n".join(lines)


def render_sitemap_extra(default_date):
    """把 brand/ 与 archive/ 下磁盘实有的页面并进 sitemap。

    旧版 build_site.py 只写首页一条，导致品牌页与问答页从未被登记，
    2026-11-13 前线上 sitemap 长期只有 1 条 URL。改为扫盘，加页减页都不用改代码。
    """
    from urllib.parse import quote
    seen, out = set(), []
    for sub in ("brand", "archive"):
        root = os.path.join(HERE, sub)
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            for fn in sorted(filenames):
                if not (fn.endswith(".html") or (sub == "brand" and fn == "llms.txt")):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, HERE).replace(os.sep, "/")
                url = f"{BASE_URL}/{quote(rel)}"
                if url in seen:
                    continue
                seen.add(url)
                lm = datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d")
                out.append(f"<url><loc>{url}</loc><lastmod>{lm}</lastmod></url>")
    return "".join(out)


def render_archive_page(day, comments_by_id):
    cards = "".join(item_card(it, comments_by_id) for it in day["items"])
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(SITE_TITLE)} · {esc(day['date'])}</title>
<link rel="alternate" type="application/feed+json" href="/feed.json">
<style>{CSS}</style></head>
<body><main>
<header><h1>{esc(SITE_TITLE)}</h1>
<div class="meta"><a href="/">← 最新一期</a> · {esc(day['date'])}</div></header>
{cards}
<footer><p>机器可读：<code>/feed.json</code>、<code>/rss.xml</code>、<code>/llms.txt</code>。</p></footer>
</main></body></html>"""


def build():
    days = load_days()
    comments = load_comments()
    by_id = {}
    for c in comments:
        by_id.setdefault(c.get("item_id"), []).append(c)
    pages = {
        "index.html": render_index(days, comments),
        "feed.json": json.dumps(render_feed(days), ensure_ascii=False, indent=2),
        "rss.xml": render_rss(days),
        "llms.txt": render_llms(days),
        "robots.txt": "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE_URL,
        "sitemap.xml": (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<url><loc>{BASE_URL}/</loc><lastmod>{days[0]['date']}</lastmod></url>"
            + render_sitemap_extra(days[0]["date"])
            + "</urlset>"
        ),
    }
    for name, body in pages.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
            fh.write(body)
    os.makedirs(os.path.join(HERE, "archive"), exist_ok=True)
    for day in days:
        with open(os.path.join(HERE, "archive", f"{day['date']}.html"), "w", encoding="utf-8") as fh:
            fh.write(render_archive_page(day, by_id))
    return list(pages)


def main():
    print("built:", ", ".join(build()))


if __name__ == "__main__":
    main()
