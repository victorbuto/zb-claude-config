#!/usr/bin/env python3
"""Conditional signal sources for trend-research.

Updated: 2026-07-30
Purpose: provide keyless/public Reddit, Hacker News Algolia, GitHub REST, and
Polymarket Gamma searches with one normalized JSON contract.
Dependencies: Python standard library only. GITHUB_TOKEN is optional.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Optional


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]{3,}")
ATOM = "{http://www.w3.org/2005/Atom}"
TAG_RE = re.compile(r"<[^>]+>")
SHREDDIT_POST_RE = re.compile(r"<shreddit-post(?=[\s>])[^>]*>")
SHREDDIT_COMMENT_RE = re.compile(r"<shreddit-comment(?=[\s>])[^>]*>")
PARA_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S)


def log(message: str) -> None:
    print(f"[trend-sources] {message}", file=sys.stderr)


def token_set(value: str) -> set[str]:
    return {part.lower() for part in TOKEN_RE.findall(value or "")}


def relevance(query: str, text: str) -> float:
    wanted = token_set(query)
    if not wanted:
        return 0.0
    overlap = len(wanted & token_set(text)) / len(wanted)
    normalized_query = " ".join(query.casefold().split())
    normalized_text = " ".join((text or "").casefold().split())
    phrase_bonus = 0.2 if normalized_query and normalized_query in normalized_text else 0.0
    return round(min(1.0, overlap * 0.8 + phrase_bonus), 4)


def request(
    url: str,
    *,
    accept: str = "application/json",
    headers: Optional[dict[str, str]] = None,
    timeout: int = 20,
    retries: int = 2,
) -> bytes:
    merged = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
        **(headers or {}),
    }
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=merged),
                timeout=timeout,
            ) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == retries:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 1.5 * (attempt + 1)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == retries:
                raise
            time.sleep(1.5 * (attempt + 1))
    return b""


def get_json(url: str, **kwargs: Any) -> Any:
    return json.loads(request(url, **kwargs).decode("utf-8"))


def get_text(url: str, **kwargs: Any) -> str:
    return request(url, **kwargs).decode("utf-8", errors="replace")


def attr(tag: str, name: str) -> str:
    match = re.search(rf'\b{name}="([^"]*)"', tag)
    return html.unescape(match.group(1)) if match else ""


def normalize_url(url: str) -> str:
    if url.startswith("/"):
        return f"https://www.reddit.com{url}"
    return url


def reddit_rss_urls(query: str, subreddits: list[str]) -> list[str]:
    encoded = urllib.parse.quote_plus(query)
    urls = [f"https://www.reddit.com/search.rss?q={encoded}&sort=relevance&t=month"]
    for subreddit in subreddits:
        name = subreddit.removeprefix("r/").strip()
        if not name:
            continue
        urls.extend(
            [
                (
                    f"https://www.reddit.com/r/{name}/search.rss?"
                    f"q={encoded}&restrict_sr=on&sort=relevance&t=month"
                ),
                f"https://www.reddit.com/r/{name}/top.rss?t=month",
                f"https://www.reddit.com/r/{name}/new.rss?t=month",
            ]
        )
    return urls


def parse_reddit_feed(value: str, query: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(value)
    except ET.ParseError:
        return []
    items: list[dict[str, Any]] = []
    for entry in root.iter(f"{ATOM}entry"):
        link = entry.find(f"{ATOM}link")
        url = link.get("href", "") if link is not None else ""
        if "/comments/" not in url:
            continue
        title_node = entry.find(f"{ATOM}title")
        title = (title_node.text or "").strip() if title_node is not None else ""
        date_node = entry.find(f"{ATOM}updated")
        date = ((date_node.text or "")[:10] if date_node is not None else "")
        subreddit_match = re.search(r"/r/([^/]+)/", url)
        items.append(
            {
                "source": "reddit",
                "title": title,
                "url": url,
                "date": date,
                "community": subreddit_match.group(1) if subreddit_match else "",
                "score": 0,
                "comments_count": 0,
                "relevance": relevance(query, title),
                "top_comments": [],
                "provenance": "public RSS",
            }
        )
    return items


def reddit_listing(query: str, subreddit: str) -> list[dict[str, Any]]:
    name = subreddit.removeprefix("r/").strip()
    if not name:
        return []
    urls = [
        f"https://www.reddit.com/svc/shreddit/community-more-posts/top/?name={name}&t=month",
        f"https://www.reddit.com/svc/shreddit/community-more-posts/new/?name={name}",
    ]
    items: list[dict[str, Any]] = []
    for url in urls:
        try:
            value = get_text(url, accept="text/html")
        except Exception as exc:
            log(f"Reddit listing r/{name} failed: {exc}")
            continue
        for match in SHREDDIT_POST_RE.finditer(value):
            tag = match.group(0)
            title = attr(tag, "post-title")
            permalink = attr(tag, "permalink")
            if "/comments/" not in permalink:
                continue
            try:
                score = int(attr(tag, "score") or 0)
                comment_count = int(attr(tag, "comment-count") or 0)
            except ValueError:
                score, comment_count = 0, 0
            items.append(
                {
                    "source": "reddit",
                    "title": title,
                    "url": normalize_url(permalink),
                    "date": attr(tag, "created-timestamp")[:10],
                    "community": attr(tag, "subreddit-name") or name,
                    "score": score,
                    "comments_count": comment_count,
                    "relevance": relevance(query, title),
                    "top_comments": [],
                    "provenance": "public shreddit listing",
                }
            )
    return items


def reddit_comments(url: str, limit: int) -> tuple[list[dict[str, Any]], Optional[int]]:
    match = re.search(r"/r/([^/]+)/comments/([A-Za-z0-9]+)", url)
    if not match:
        return [], None
    subreddit, post_id = match.groups()
    endpoint = (
        f"https://www.reddit.com/svc/shreddit/comments/r/{subreddit}/t3_{post_id}?sort=top"
    )
    try:
        value = get_text(endpoint, accept="text/html", timeout=15)
    except Exception:
        return [], None
    comments: list[dict[str, Any]] = []
    for item in SHREDDIT_COMMENT_RE.finditer(value):
        tag = item.group(0)
        author = attr(tag, "author")
        thing_id = attr(tag, "thingId")
        if not author or author in ("[deleted]", "[removed]") or not thing_id:
            continue
        anchor = f'id="{thing_id}-post-rtjson-content"'
        start = value.find(anchor)
        if start < 0:
            continue
        window = value[start : start + 6000]
        paragraphs = PARA_RE.findall(window)
        text = re.sub(
            r"\s+",
            " ",
            " ".join(TAG_RE.sub("", paragraph) for paragraph in paragraphs),
        ).strip()
        if not text:
            continue
        try:
            score = int(attr(tag, "score") or 0)
        except ValueError:
            score = 0
        comments.append(
            {
                "score": score,
                "author": author,
                "text": html.unescape(text)[:500],
                "url": normalize_url(attr(tag, "permalink")),
            }
        )
    comments.sort(key=lambda item: item["score"], reverse=True)
    count_match = re.search(r'total-comments="(\d+)"', value)
    return comments[:limit], int(count_match.group(1)) if count_match else None


def search_reddit(args: argparse.Namespace) -> list[dict[str, Any]]:
    urls = reddit_rss_urls(args.query, args.subreddit)
    items: list[dict[str, Any]] = []
    # Public Reddit endpoints rate-limit bursts aggressively. Keep this lane
    # deliberately sequential instead of stampeding RSS/shreddit in parallel.
    for url in urls:
        try:
            items.extend(
                parse_reddit_feed(
                    get_text(url, accept="application/atom+xml"),
                    args.query,
                )
            )
        except Exception as exc:
            log(f"Reddit RSS lane failed: {exc}")
        time.sleep(0.45)
    for subreddit in args.subreddit:
        items.extend(reddit_listing(args.query, subreddit))

    deduped: dict[str, dict[str, Any]] = {}
    for item in items:
        current = deduped.get(item["url"])
        if current is None or (item["score"], item["relevance"]) > (
            current["score"],
            current["relevance"],
        ):
            deduped[item["url"]] = item
    items = list(deduped.values())
    cutoff = dt.date.today() - dt.timedelta(days=args.days)
    items = [
        item
        for item in items
        if not item["date"] or item["date"] >= cutoff.isoformat()
    ]
    on_topic = [item for item in items if item["relevance"] > 0]
    if on_topic:
        items = on_topic
    items.sort(
        key=lambda item: (item["relevance"], item["score"], item["comments_count"]),
        reverse=True,
    )
    items = items[: args.limit]

    for item in items[: args.enrich]:
        comments, count = reddit_comments(item["url"], args.comments)
        item["top_comments"] = comments
        if count is not None:
            item["comments_count"] = count
        time.sleep(0.45)
    return items


def search_hn(args: argparse.Namespace) -> list[dict[str, Any]]:
    cutoff = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)).timestamp())
    params = urllib.parse.urlencode(
        {
            "query": args.query,
            "tags": "story",
            "numericFilters": f"created_at_i>{cutoff}",
            "hitsPerPage": args.limit,
        }
    )
    data = get_json(f"https://hn.algolia.com/api/v1/search_by_date?{params}")
    items = []
    for hit in data.get("hits") or []:
        story_id = hit.get("objectID")
        items.append(
            {
                "source": "hackernews",
                "title": hit.get("title") or hit.get("story_title") or "",
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                "discussion_url": f"https://news.ycombinator.com/item?id={story_id}",
                "date": (hit.get("created_at") or "")[:10],
                "points": hit.get("points") or 0,
                "comments_count": hit.get("num_comments") or 0,
                "author": hit.get("author") or "",
                "relevance": relevance(
                    args.query,
                    f"{hit.get('title') or ''} {hit.get('story_text') or ''}",
                ),
                "provenance": "Hacker News Algolia API",
            }
        )
    on_topic = [item for item in items if item["relevance"] > 0]
    if on_topic:
        items = on_topic
    items.sort(key=lambda item: (item["relevance"], item["points"]), reverse=True)
    return items


def search_github(args: argparse.Namespace) -> list[dict[str, Any]]:
    cutoff = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    query = f"{args.query} updated:>={cutoff}"
    params = urllib.parse.urlencode(
        {"q": query, "sort": "updated", "order": "desc", "per_page": args.limit}
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = get_json(f"https://api.github.com/search/issues?{params}", headers=headers)
    items = []
    for issue in data.get("items") or []:
        repository_url = issue.get("repository_url") or ""
        repository = repository_url.rsplit("/repos/", 1)[-1]
        items.append(
            {
                "source": "github",
                "title": issue.get("title") or "",
                "url": issue.get("html_url") or "",
                "repository": repository,
                "date": (issue.get("created_at") or "")[:10],
                "updated": (issue.get("updated_at") or "")[:10],
                "comments_count": issue.get("comments") or 0,
                "state": issue.get("state") or "",
                "relevance": relevance(
                    args.query,
                    f"{issue.get('title') or ''} {issue.get('body') or ''}",
                ),
                "provenance": "GitHub REST Search API",
            }
        )
    on_topic = [item for item in items if item["relevance"] > 0]
    if on_topic:
        items = on_topic
    items.sort(
        key=lambda item: (item["relevance"], item["comments_count"], item["updated"]),
        reverse=True,
    )
    return items


def market_text(event: dict[str, Any]) -> str:
    markets = event.get("markets") or []
    market_questions = " ".join(
        str(market.get("question") or "") for market in markets if isinstance(market, dict)
    )
    return f"{event.get('title') or ''} {event.get('description') or ''} {market_questions}"


def search_polymarket(args: argparse.Namespace) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "active": "true",
            "closed": "false",
            "limit": 200,
            "order": "volume",
            "ascending": "false",
        }
    )
    data = get_json(f"https://gamma-api.polymarket.com/events?{params}")
    items = []
    for event in data if isinstance(data, list) else []:
        score = relevance(args.query, market_text(event))
        minimum = 0.75 if len(token_set(args.query)) > 1 else 0.6
        if score < minimum:
            continue
        markets = event.get("markets") or []
        top_market = markets[0] if markets and isinstance(markets[0], dict) else {}
        items.append(
            {
                "source": "polymarket",
                "title": event.get("title") or top_market.get("question") or "",
                "url": f"https://polymarket.com/event/{event.get('slug')}" if event.get("slug") else "",
                "end_date": event.get("endDate") or top_market.get("endDate") or "",
                "volume": event.get("volume") or top_market.get("volume") or 0,
                "liquidity": event.get("liquidity") or top_market.get("liquidity") or 0,
                "outcomes": top_market.get("outcomes") or [],
                "outcome_prices": top_market.get("outcomePrices") or [],
                "relevance": score,
                "provenance": "Polymarket Gamma API",
            }
        )
    items.sort(key=lambda item: (item["relevance"], float(item["volume"] or 0)), reverse=True)
    return items[: args.limit]


def route(args: argparse.Namespace) -> list[dict[str, Any]]:
    context = args.context
    lanes: list[dict[str, Any]] = []
    if context in ("consumer", "mixed") and args.geo not in ("ru", "russia", "rf"):
        lanes.append(
            {
                "source": "reddit",
                "use": True,
                "reason": "international consumer language, objections and community behavior",
            }
        )
    else:
        lanes.append(
            {
                "source": "reddit",
                "use": False,
                "reason": "skip for Russian-only or non-consumer research",
            }
        )
    lanes.append(
        {
            "source": "hackernews",
            "use": context in ("tech", "mixed"),
            "reason": "use only for technology, AI, startups and developer ecosystems",
        }
    )
    lanes.append(
        {
            "source": "github",
            "use": context in ("tech", "mixed"),
            "reason": "use only when repositories, releases, issues or adoption are meaningful signals",
        }
    )
    lanes.append(
        {
            "source": "polymarket",
            "use": context in ("prediction", "mixed"),
            "reason": "use only for forecastable events with a live market",
        }
    )
    return lanes


def emit(source: str, query: str, items: list[dict[str, Any]], output: Optional[str]) -> None:
    payload = {
        "source": source,
        "query": query,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    value = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(value + "\n")
        log(f"saved: {os.path.abspath(output)}")
    else:
        print(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conditional sources for trend-research")
    subparsers = parser.add_subparsers(dest="source", required=True)

    reddit = subparsers.add_parser("reddit", help="public Reddit RSS + shreddit pipeline")
    reddit.add_argument("query")
    reddit.add_argument("--subreddit", action="append", default=[])
    reddit.add_argument("--days", type=int, default=30)
    reddit.add_argument("--limit", type=int, default=20)
    reddit.add_argument("--enrich", type=int, default=5)
    reddit.add_argument("--comments", type=int, default=10)
    reddit.add_argument("--output")
    reddit.set_defaults(func=search_reddit)

    hn = subparsers.add_parser("hn", help="Hacker News via Algolia")
    hn.add_argument("query")
    hn.add_argument("--days", type=int, default=90)
    hn.add_argument("--limit", type=int, default=30)
    hn.add_argument("--output")
    hn.set_defaults(func=search_hn)

    github = subparsers.add_parser("github", help="GitHub issues and PRs via REST")
    github.add_argument("query")
    github.add_argument("--days", type=int, default=90)
    github.add_argument("--limit", type=int, default=30)
    github.add_argument("--output")
    github.set_defaults(func=search_github)

    polymarket = subparsers.add_parser("polymarket", help="prediction markets via Gamma API")
    polymarket.add_argument("query")
    polymarket.add_argument("--limit", type=int, default=20)
    polymarket.add_argument("--output")
    polymarket.set_defaults(func=search_polymarket)

    router = subparsers.add_parser("route", help="show which conditional lanes fit")
    router.add_argument("query")
    router.add_argument("--context", choices=("consumer", "tech", "prediction", "mixed"), required=True)
    router.add_argument("--geo", default="global")
    router.add_argument("--output")
    router.set_defaults(func=route)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        items = args.func(args)
    except Exception as exc:
        log(f"{args.source} failed: {exc}")
        return 2
    emit(args.source, args.query, items, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
