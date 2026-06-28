#!/usr/bin/env python3
"""
Генерирует HTML-сравнение нескольких сегментов с барами и таблицами.

Usage:
    python generate_comparison_html.py <csv> --output report.html \\
        --segment "Визажисты:Социально-экономический=визажист" \\
        --segment "Сухая кожа:Контекст потребления=сухая кожа,Контекст потребления=сухая кожа зимой" \\
        --lens Потребности --lens Проблемы

    Формат --segment: "Имя_сегмента:Колонка1=значение1,Колонка2=значение2,..."
    Все фильтры внутри одного сегмента — union (ИЛИ).
"""
from __future__ import annotations

import argparse
import html as html_lib
import sys
from collections import Counter

import pandas as pd


SPLIT = "; "


def has_any(cell, vals):
    cell = "" if pd.isna(cell) else str(cell)
    parts = [s.strip() for s in cell.split(SPLIT)]
    return any(v in parts for v in vals)


def parse_segment_spec(spec: str):
    """'Имя:Колонка1=значение1,Колонка2=значение2' → (name, [(col, val), ...])"""
    if ":" not in spec:
        raise ValueError(f"Невалидный формат сегмента: {spec}. Ожидается 'Имя:Колонка=значение,...'")
    name, filters_str = spec.split(":", 1)
    filters = []
    for f in filters_str.split(","):
        if "=" not in f:
            raise ValueError(f"Невалидный фильтр: {f}")
        col, val = f.split("=", 1)
        filters.append((col.strip(), val.strip()))
    return name.strip(), filters


def freq(sub, col):
    c = Counter()
    rows_with = 0
    for cell in sub[col].fillna("").astype(str):
        if not cell:
            continue
        rows_with += 1
        for seg in cell.split(SPLIT):
            seg = seg.strip()
            if seg:
                c[seg] += 1
    return c, rows_with


def esc(s):
    return html_lib.escape(str(s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--output", default="segments_comparison.html")
    ap.add_argument("--segment", action="append", required=True,
                    help="'Имя:Колонка=значение,...' — фильтры через union")
    ap.add_argument("--lens", action="append", required=True,
                    help="Какие методы-линзы показать")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    df = pd.read_csv(args.csv_path)

    # Парсим сегменты
    segments_data = []
    for spec in args.segment:
        name, filters = parse_segment_spec(spec)
        mask = pd.Series(False, index=df.index)
        for col, val in filters:
            if col not in df.columns:
                print(f"! Колонки '{col}' нет в CSV", file=sys.stderr)
                continue
            mask = mask | df[col].apply(lambda x: has_any(x, [val]))
        sub = df[mask]
        seg_data = {
            "name": name,
            "filters": filters,
            "total": len(sub),
            "lenses": {},
        }
        for lens in args.lens:
            if lens not in sub.columns:
                continue
            c, rows = freq(sub, lens)
            seg_data["lenses"][lens] = {"counter": c, "rows": rows}
        segments_data.append(seg_data)

    # HTML
    parts = ['''<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8">
<title>Сравнение сегментов</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1400px; margin: 24px auto; padding: 0 24px; color: #1a1a1a; background: #f7f7f8; }
  h1 { font-size: 24px; margin-bottom: 4px; }
  h2 { font-size: 20px; margin-top: 32px; padding-top: 16px; border-top: 2px solid #ddd; }
  h3 { font-size: 16px; margin-top: 24px; }
  .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 16px 0 24px; }
  .card { background: white; padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0; }
  .card .num { font-size: 28px; font-weight: 700; color: #0066cc; }
  .card .label { font-size: 13px; color: #333; font-weight: 600; margin-top: 4px; }
  .card .sublabel { font-size: 11px; color: #999; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; background: white; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden; margin: 12px 0; font-size: 13px; }
  th { background: #f0f0f3; padding: 8px 10px; text-align: left; font-weight: 600; border-bottom: 1px solid #e0e0e0; }
  td { padding: 6px 10px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
  td.bar-cell { padding: 4px 10px; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; color: #555; }
  .bar { background: #4a90e2; height: 18px; border-radius: 3px; min-width: 2px; position: relative; }
  .bar-label { color: white; font-weight: 700; font-size: 11px; position: absolute; right: 6px; top: 50%; transform: translateY(-50%); white-space: nowrap; }
  .bar-label.outside { color: #555; left: 100%; right: auto; margin-left: 6px; }
  details { background: white; border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px 16px; margin: 10px 0; }
  summary { cursor: pointer; font-weight: 600; outline: none; }
  .compare-cell { position: relative; padding: 4px 8px; }
  .compare-cell .inner-bar { background: #b3d1f0; height: 24px; border-radius: 3px; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px; color: #1a3a5c; font-weight: 700; font-size: 12px; }
  .compare-cell .inner-bar.high { background: #4a90e2; color: white; }
  .compare-cell.empty .inner-bar { background: #f0f0f0; color: #aaa; }
</style></head><body>''']

    parts.append(f"<h1>Сравнение сегментов</h1>")
    parts.append(f'<div style="color:#666;font-size:13px">Источник: {esc(args.csv_path)}</div>')

    # Карточки
    parts.append('<div class="summary-grid">')
    for seg in segments_data:
        parts.append(f'<div class="card"><div class="num">{seg["total"]}</div>')
        parts.append(f'<div class="label">{esc(seg["name"])}</div>')
        filters_str = " ∪ ".join(f'{c}={v}' for c, v in seg["filters"])
        parts.append(f'<div class="sublabel">{esc(filters_str)}</div></div>')
    parts.append('</div>')

    # Сравнительные таблицы по каждой линзе
    for lens in args.lens:
        # Собираем все топ-сегменты из всех групп для этой линзы
        all_top = set()
        for seg in segments_data:
            if lens in seg["lenses"]:
                for name, _ in seg["lenses"][lens]["counter"].most_common(15):
                    all_top.add(name)

        def total_count(name):
            return sum(s["lenses"].get(lens, {"counter": Counter()})["counter"].get(name, 0) for s in segments_data)

        ordered = sorted(all_top, key=total_count, reverse=True)

        parts.append(f'<h2>Линза: {esc(lens)}</h2>')
        parts.append('<table><thead><tr>')
        parts.append('<th style="width:25%">Сегмент</th>')
        for seg in segments_data:
            n_rows = seg["lenses"].get(lens, {"rows": 0})["rows"]
            parts.append(f'<th style="width:18%">{esc(seg["name"])}<br><span style="font-weight:normal;color:#999">({n_rows} строк)</span></th>')
        parts.append('</tr></thead><tbody>')

        for need in ordered[:30]:
            parts.append(f'<tr><td>{esc(need)}</td>')
            for seg in segments_data:
                lens_data = seg["lenses"].get(lens, {"counter": Counter(), "rows": 0})
                n = lens_data["counter"].get(need, 0)
                rows = lens_data["rows"]
                if not rows:
                    parts.append('<td class="compare-cell empty"><div class="inner-bar" style="width:6%">—</div></td>')
                    continue
                pct = 100 * n / rows
                width = min(pct * 2.5, 100)
                if n == 0:
                    parts.append('<td class="compare-cell empty"><div class="inner-bar" style="width:6%">0</div></td>')
                else:
                    cls = 'high' if pct >= 20 else ''
                    parts.append(f'<td class="compare-cell"><div class="inner-bar {cls}" style="width:{width:.1f}%">{n} ({pct:.0f}%)</div></td>')
            parts.append('</tr>')
        parts.append('</tbody></table>')

    # Детальные блоки по сегментам
    parts.append('<h2>Детальные частотности</h2>')
    for seg in segments_data:
        parts.append(f'<details open><summary>{esc(seg["name"])} — {seg["total"]} строк</summary>')
        for lens in args.lens:
            lens_data = seg["lenses"].get(lens)
            if not lens_data or not lens_data["counter"]:
                continue
            c = lens_data["counter"]
            rows = lens_data["rows"]
            parts.append(f'<h3>{esc(lens)} — {rows} строк, {len(c)} уник.</h3>')
            parts.append('<table><thead><tr><th style="width:30%">Сегмент</th><th class="bar-cell">Частота</th><th class="num" style="width:10%">Строк</th></tr></thead><tbody>')
            top = c.most_common(args.top)
            max_n = top[0][1] if top else 1
            for name, n in top:
                pct = 100 * n / rows if rows else 0
                width = max(2, n / max_n * 100)
                inside = width > 15
                label_html = f'<span class="bar-label">{n} ({pct:.0f}%)</span>' if inside else f'<span class="bar-label outside">{n} ({pct:.0f}%)</span>'
                parts.append(f'<tr><td>{esc(name)}</td><td class="bar-cell"><div class="bar" style="width:{width:.1f}%">{label_html}</div></td><td class="num">{n}</td></tr>')
            parts.append('</tbody></table>')
        parts.append('</details>')

    parts.append('</body></html>')

    out = "".join(parts)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
