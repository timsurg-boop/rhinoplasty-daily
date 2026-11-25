#!/usr/bin/env python3
"""Build the static commentary site (HTML + JSON Feed + RSS + llms.txt) from data/papers.json + archive."""

import glob
import html
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "papers.json")
ARCHIVE = os.path.join(HERE, "data", "archive")

# 站点部署位置决定两件事：站内链接前缀、绝对 URL 前缀。
# 1) 仓库里有 CNAME（已绑自定义域名）→ 站点在根路径，前缀为空。
# 2) 没有 CNAME → 走 GitHub Pages 项目页，站点在 /rhinoplasty-daily 子路径。
# 3) SITE_PREFIX / BASE_URL 环境变量优先，便于本地预览和临时部署。
CNAME_FILE = os.path.join(HERE, "CNAME")
CUSTOM_DOMAIN = ""
if os.path.exists(CNAME_FILE):
    CUSTOM_DOMAIN = open(CNAME_FILE, encoding="utf-8").read().strip()

SITE_PREFIX = os.environ.get(
    "SITE_PREFIX", "" if CUSTOM_DOMAIN else "/rhinoplasty-daily"
)
if SITE_PREFIX == "/":
    SITE_PREFIX = ""
SITE_PREFIX = SITE_PREFIX.rstrip("/")

BASE_URL = os.environ.get(
    "BASE_URL",
    (f"https://{CUSTOM_DOMAIN}" if CUSTOM_DOMAIN
     else "https://timsurg-boop.github.io" + SITE_PREFIX),
).rstrip("/")


def fix_links(markup):
    """把站内根路径链接（/archive/…）改写为带部署前缀的形式。"""
    if not SITE_PREFIX:
        return markup
    return re.sub(
        r'(href|src)="/(?!/)',
        lambda m: f'{m.group(1)}="{SITE_PREFIX}/',
        markup,
    )


SITE_TITLE = "鼻整形文献评点 · Rhinoplasty Daily Commentary"
MAIL_TO = "timsurg@icloud.com"
RECENT_DAYS = 14

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
.journal .affil{display:block;font-size:11.5px;color:var(--muted);opacity:.85;margin-top:2px;line-height:1.45}
.journal a{color:var(--muted)}
.line{margin:8px 0}
.line b{font-weight:600}
.line.fact b{color:#2f4f7f}
.line.take b{color:var(--accent)}
.en{color:var(--muted);font-size:14px;margin-top:10px;padding-left:12px;border-left:2px solid var(--line)}
.updated{font-size:12px;color:var(--muted);margin-top:2px}
.stale{margin:14px 0 0;padding:10px 12px;border:1px solid #e8d9b5;background:#fdf7e8;border-radius:8px;font-size:13px;color:#6b5a2e}
.related{margin-top:12px;font-size:13px;color:var(--muted);line-height:1.7}
.related a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line)}
.related a:hover{color:var(--accent)}
.respond{margin-top:10px;font-size:13px;color:var(--muted)}
.respond a{color:var(--ink)}
.archive{margin-top:40px}
.archive h3{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:8px}
.archive ul{list-style:none;padding:0}
.archive li{padding:7px 0;font-size:14px;border-bottom:1px dashed var(--line);display:flex;gap:10px}
.archive .d{color:var(--muted);font-variant-numeric:tabular-nums;flex:0 0 92px}
.archive a{color:var(--ink);text-decoration:none}
.archive a:hover{color:var(--accent)}
footer{margin-top:48px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:16px}
code{background:#efece5;padding:1px 5px;border-radius:4px;font-size:13px}
.hero{display:flex;gap:20px;align-items:flex-start;background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px;margin:0 0 30px}
.hero img{width:88px;height:88px;border-radius:50%;object-fit:cover;flex:0 0 88px;border:1px solid var(--line);background:#f3f0ea}
.hero .who{font-size:19px;font-weight:600;margin:0 0 2px;letter-spacing:.01em}
.hero .role{color:var(--muted);font-size:13px;margin-bottom:8px}
.hero .pos{font-size:14px;line-height:1.65;margin:0 0 10px;color:#333}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.chip{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:2px 9px;color:#444;background:#fdfcf9}
.hero .links{font-size:13px}
.hero .links a{color:var(--accent);text-decoration:none;margin-right:16px}
@media(max-width:560px){.hero{flex-direction:column;gap:12px}.hero .pos{font-size:13px}}
"""

HERO = """<section class="hero">
  <img src="brand/avatar.jpg" alt="王艇医生" width="88" height="88" loading="lazy">
  <div>
    <p class="who">王艇</p>
    <div class="role">副主任医师 · 技术院长 · 悦星澜（大连）医疗美容</div>
    <p class="pos">专注鼻整形与鼻修复。以自体肋软骨、鼻中隔与耳软骨做结构性鼻整形，关注东方人鼻部基础条件下的形态与功能平衡；参与《达拉斯鼻整形》中文版首版翻译。</p>
    <div class="chips"><span class="chip">鼻修复</span><span class="chip">肋软骨鼻综合</span><span class="chip">鼻中隔延长</span><span class="chip">耳软骨鼻尖</span><span class="chip">驼峰鼻矫正</span><span class="chip">面部提升</span></div>
    <div class="links"><a href="/brand/index.html">医生资料与价格区间 →</a><a href="/brand/patient.html">患者版说明</a><a href="/frontier/">前沿 · 读论文 →</a></div>
  </div>
</section>"""


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


def esc(text):
    return html.escape(str(text or ""))


def related_items(it, days, limit=3):
    """按标签找同主题、日期更早的条目（同一天的不算），最近优先。"""
    tags = set(it.get("tags") or [])
    if not tags:
        return []
    own_day = str(it.get("id", ""))[:10]
    hits = []
    for day in days:
        if day["date"] == own_day:
            continue
        for other in day["items"]:
            if other.get("id") == it.get("id"):
                continue
            if tags & set(other.get("tags") or []):
                hits.append((day["date"], other))
    hits.sort(key=lambda pair: pair[0], reverse=True)
    return hits[:limit]


def item_card(it, days=None):
    affil_html = (f'<span class="affil">{esc(it.get("first_affil"))}</span>'
                  if it.get("first_affil") else "")
    rel = related_items(it, days or [], limit=3)
    if rel:
        links = " · ".join(
            f'<a href="/archive/{esc(d)}.html#{esc(o["id"])}">{esc(o["title"][:52])}</a>'
            for d, o in rel
        )
        rel_html = f'<p class="related"><b>同题旧文｜</b>{links}</p>'
    else:
        rel_html = ""
    subject = f"批注｜{it['id'][:10]}｜PMID {it.get('pmid','')}｜{it['title'][:36]}"
    body = (f"\n\n—— 文献：{it['title']}\n"
            f"—— 链接：{BASE_URL}/#{it['id']}\n"
            f"—— PMID：{it.get('pmid','')}\n"
            f"（请勿写患者姓名、影像或任何可识别信息）")
    mail_href = (f"mailto:{MAIL_TO}?subject={quote(subject)}"
                 f"&body={quote(body)}")
    respond_html = (f'<p class="respond">有异议或临床经验？'
                    f'<a href="{esc(mail_href)}">写信给编辑部</a>（1–2 个工作日回复）</p>')
    return f"""
<article class="item" id="{esc(it['id'])}">
  <div class="tagrow">{''.join(f'<span class="tag">{esc(t)}</span>' for t in it.get('tags', []))}</div>
  <h2><a href="https://pubmed.ncbi.nlm.nih.gov/{esc(it.get('pmid',''))}/" rel="noopener">{esc(it['title'])}</a></h2>
  <div class="journal">{esc(it['journal'])} · {esc(it.get('first_author','')) or '—'} · PMID {esc(it.get('pmid',''))} · <a href="https://doi.org/{esc(it.get('doi',''))}" rel="noopener">doi</a>{affil_html}</div>
  <p class="line fact"><b>事实｜</b>{esc(it['fact_zh'])}</p>
  <p class="line take"><b>点评｜</b>{esc(it['take_zh'])}</p>
  <p class="en">{esc(it['fact_en'])} {esc(it['take_en'])}</p>
  {rel_html}
  {respond_html}
</article>"""


def render_index(days):
    today = days[0]
    cards = "".join(item_card(it, days) for it in today["items"])

    try:
        gap = (datetime.now().date() - datetime.strptime(today["date"], "%Y-%m-%d").date()).days
    except Exception:
        gap = 0
    stale_html = ""
    if gap >= 3:
        stale_html = (f'<div class="stale">本期尚未更新：最新一期为 {esc(today["date"])}，'
                      f'已 {gap} 天前。每日管线可能中断，请以页面日期为准。</div>')

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
                    "description": it["take_zh"],
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
<link rel="canonical" href="{BASE_URL}/">
<meta name="description" content="每天 3-5 条鼻整形与面部提升新文献，一句事实 + 一句点评，可订阅。">
<link rel="alternate" type="application/feed+json" href="/feed.json" title="JSON Feed">
<link rel="alternate" type="application/rss+xml" href="/rss.xml" title="RSS">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<main>
{HERO}
<header>
  <h1>{esc(SITE_TITLE)}</h1>
  <div class="meta">{esc(today['date'])} · 来源 {esc(today.get('source',''))} · 窗口 {esc(today.get('window',''))} · <a href="/llms.txt">llms.txt</a> · <a href="/feed.json">feed.json</a></div>
  <div class="updated">最后更新：{esc(today['date'])} · 每日 3–5 条，事实与点评各一句，附 PMID/DOI</div>
  {stale_html}
</header>
{cards}
{archive_html}
<footer>
  <p>机器可读：<code>/feed.json</code>（JSON Feed 1.1）、<code>/rss.xml</code>、<code>/llms.txt</code>、<code>/sitemap.xml</code>。页面内嵌 schema.org ItemList 结构化数据。</p>
  <p>内容仅供同行讨论，不构成医疗建议。详见<a href="/disclaimer.html">免责声明</a>。</p>
</footer>
</main>
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
            f"<p>{esc(it['journal'])} · {esc(it.get('first_author',''))} · {esc(it.get('first_affil',''))} · PMID {esc(it.get('pmid',''))}</p>"
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
        f"- 完整归档: {BASE_URL}/archive/",
        "",
    ]
    if len(days) > RECENT_DAYS:
        lines += [f"\u672c\u6587\u4ec5\u5217\u6700\u8fd1 {RECENT_DAYS} \u671f\uff08{days[0]['date']} \u81f3 {days[RECENT_DAYS - 1]['date']}\uff09\uff1b\u66f4\u65e9\u5185\u5bb9\u89c1\u5f52\u6863\u76ee\u5f55\u3002", ""]
    for day in days[:RECENT_DAYS]:
        lines += [f"## {day['date']}", ""]
        for it in day["items"]:
            lines += [
                f"### {it['title']}",
                f"- 期刊: {it['journal']}",
                f"- 第一作者: {it.get('first_author','')}",
                f"- 单位: {it.get('first_affil','')}",
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
    for sub in ("brand", "archive", "frontier"):
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
    dpath = os.path.join(HERE, "disclaimer.html")
    if os.path.exists(dpath):
        url = f"{BASE_URL}/disclaimer.html"
        if url not in seen:
            lm = datetime.fromtimestamp(os.path.getmtime(dpath)).strftime("%Y-%m-%d")
            out.append(f"<url><loc>{url}</loc><lastmod>{lm}</lastmod></url>")
    return "".join(out)


def render_archive_page(day, days=None):
    cards = "".join(item_card(it, days) for it in day["items"])
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(SITE_TITLE)} · {esc(day['date'])}</title>
<link rel="canonical" href="{BASE_URL}/archive/{esc(day['date'])}.html">
<link rel="alternate" type="application/feed+json" href="/feed.json">
<style>{CSS}</style></head>
<body><main>
<header><h1>{esc(SITE_TITLE)}</h1>
<div class="meta"><a href="/">← 最新一期</a> · {esc(day['date'])}</div></header>
{cards}
<footer><p>机器可读：<code>/feed.json</code>、<code>/rss.xml</code>、<code>/llms.txt</code>。内容为文献编译与同行讨论，不构成医疗建议，详见<a href="/disclaimer.html">免责声明</a>。</p></footer>
</main></body></html>"""


def _ensure_affiliations(days):
    """渲染前补齐第一作者单位：只补缺的，失败不影响出页。"""
    missing = sorted({str(it.get("pmid")) for _, it in all_items(days)
                      if it.get("pmid") and not it.get("first_affil")})
    if not missing:
        return
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        import enrich_affiliation as ea
        recs = ea.fetch(missing)
    except Exception as exc:  # 网络异常时照常出页
        print("affiliation lookup skipped:", exc)
        return
    for _, it in all_items(days):
        rec = recs.get(str(it.get("pmid") or ""))
        if not rec:
            continue
        fa, af = ea.first_author(rec), ea.affiliation(rec)
        if fa and not it.get("first_author"):
            it["first_author"] = fa
        if af and not it.get("first_affil"):
            it["first_affil"] = af


def build():
    days = load_days()
    _ensure_affiliations(days)
    pages = {
        "index.html": render_index(days),
        "feed.json": json.dumps(render_feed(days), ensure_ascii=False, indent=2),
        "rss.xml": render_rss(days),
        "llms.txt": render_llms(days),
        "robots.txt": "User-agent: *\nAllow: /\nDisallow: /v/\n\nSitemap: %s/sitemap.xml\n" % BASE_URL,
        "sitemap.xml": (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<url><loc>{BASE_URL}/</loc><lastmod>{days[0]['date']}</lastmod></url>"
            + render_sitemap_extra(days[0]["date"])
            + "</urlset>"
        ),
    }
    for name, body in pages.items():
        if name.endswith(".html"):
            body = fix_links(body)
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
            fh.write(body)
    os.makedirs(os.path.join(HERE, "archive"), exist_ok=True)
    for day in days:
        page = fix_links(render_archive_page(day, days))
        with open(os.path.join(HERE, "archive", f"{day['date']}.html"), "w", encoding="utf-8") as fh:
            fh.write(page)
    return list(pages)


def main():
    print("built:", ", ".join(build()))


if __name__ == "__main__":
    main()
