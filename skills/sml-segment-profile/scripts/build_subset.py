#!/usr/bin/env python3
"""
Готовит подвыборку для анализа сегмента.

1. Фильтрует строки CSV по выбранным значениям сегмента (union по нескольким колонкам)
2. Считает частотности по линзам-методам
3. Дампит компактный текст (для чтения тексов целиком в стадиях B/C)
4. Сохраняет JSON-подвыборку

Usage:
    python build_subset.py <csv> --filter "Колонка1=значение1" --filter "Колонка2=значение2" \\
        --lens Потребности --lens Проблемы \\
        --output-dir analysis/

    Несколько --filter применяются через ИЛИ (union по строкам).
    Несколько --lens — для каких методов посчитать частотности.

Output:
    {output_dir}/{slug}_subset.json   — полная подвыборка
    {output_dir}/{slug}_compact.txt   — компактный текст для чтения
    {output_dir}/{slug}_freq.md       — markdown с частотностями
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd


SPLIT = "; "
KEEP_COLS = [
    "Тональность", "Продукты", "Тип продукта", "Ценность",
    "JTBD", "Потребности", "Проблемы", "Контекст потребления",
    "Привычки", "Триггеры", "Ценности", "Стиль жизни",
    "Опыт в категории", "Value chain",
    "Социально-демографический", "Социально-экономический",
    "Интересы", "Психотипы", "ЛПР", "Ценовая категория",
    "География", "Индустрия", "Размер компании", "Технология",
    "Кривая инноваций",
    "Текст",  # текст всегда последним
]


def has_any(cell, vals):
    cell = "" if pd.isna(cell) else str(cell)
    parts = [s.strip() for s in cell.split(SPLIT)]
    return any(v in parts for v in vals)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-zа-я0-9]+", "_", text)
    return text.strip("_")[:50]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--filter", action="append", required=True,
                    help='Формат "Колонка=значение". Можно указать несколько (применяются через ИЛИ).')
    ap.add_argument("--lens", action="append", required=True,
                    help="Названия методов-линз, по которым считать частотности.")
    ap.add_argument("--name", required=True,
                    help="Имя сегмента (используется в имени файла и заголовках).")
    ap.add_argument("--output-dir", default="analysis")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    df = pd.read_csv(args.csv_path)

    # Разбираем фильтры
    filters = []
    for f in args.filter:
        if "=" not in f:
            print(f"! Неверный формат фильтра: {f}", file=sys.stderr)
            sys.exit(1)
        col, val = f.split("=", 1)
        col, val = col.strip(), val.strip()
        if col not in df.columns:
            print(f"! Колонки '{col}' нет в CSV. Доступные: {list(df.columns)}", file=sys.stderr)
            sys.exit(1)
        filters.append((col, val))

    # Маска: union по всем фильтрам
    mask = pd.Series(False, index=df.index)
    for col, val in filters:
        mask = mask | df[col].apply(lambda x: has_any(x, [val]))

    sub = df[mask].copy()
    print(f"Подвыборка «{args.name}»: {len(sub)} строк из {len(df)}")
    print(f"Фильтры (union):")
    for col, val in filters:
        n = df[col].apply(lambda x: has_any(x, [val])).sum()
        print(f"  • {col} = {val}  →  {n} строк")
    print()

    # Создаём output dir
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.name)

    # Частотности по линзам — выводим в markdown
    freq_md = [f"# Сегмент: {args.name}", ""]
    freq_md.append(f"**Подвыборка:** {len(sub)} строк из {len(df)}")
    freq_md.append("")
    freq_md.append("**Фильтр (union):**")
    for col, val in filters:
        freq_md.append(f"- `{col}` ∈ `{val}`")
    freq_md.append("")

    for lens in args.lens:
        if lens not in sub.columns:
            print(f"! Линзы '{lens}' нет в CSV.", file=sys.stderr)
            continue
        c = Counter()
        rows_with = 0
        for cell in sub[lens].fillna("").astype(str):
            if not cell:
                continue
            rows_with += 1
            for seg in cell.split(SPLIT):
                seg = seg.strip()
                if seg:
                    c[seg] += 1
        print(f"\n--- {lens}: {rows_with} строк размечено, {len(c)} уник. ---")
        for seg, n in c.most_common(args.top):
            pct = 100 * n / rows_with if rows_with else 0
            print(f"  {n:>3}  ({pct:>3.0f}%)  {seg}")

        freq_md.append(f"## Линза: {lens}")
        freq_md.append("")
        freq_md.append(f"Размечено: {rows_with} из {len(sub)} строк. Уникальных: {len(c)}.")
        freq_md.append("")
        freq_md.append("| Сегмент | Строк | Доля |")
        freq_md.append("|---|---:|---:|")
        for seg, n in c.most_common(args.top):
            pct = 100 * n / rows_with if rows_with else 0
            freq_md.append(f"| {seg} | {n} | {pct:.0f}% |")
        freq_md.append("")

    (out_dir / f"{slug}_freq.md").write_text("\n".join(freq_md), encoding="utf-8")

    # Сохраняем подвыборку JSON
    keep_cols = [c for c in KEEP_COLS if c in sub.columns]
    out = sub[keep_cols].fillna("").astype(str).to_dict(orient="records")
    (out_dir / f"{slug}_subset.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Компактный текст-дамп для чтения текстов
    with open(out_dir / f"{slug}_compact.txt", "w", encoding="utf-8") as f:
        for i, row in enumerate(out, 1):
            f.write(f"=== [{i}] ===\n")
            for k in keep_cols:
                v = row.get(k, "").strip()
                if v:
                    f.write(f"{k}: {v}\n")
            f.write("\n")

    import os
    compact_bytes = os.path.getsize(out_dir / f"{slug}_compact.txt")
    print(f"\nСохранил в {out_dir}/")
    print(f"  • {slug}_freq.md        — частотности")
    print(f"  • {slug}_subset.json    — подвыборка JSON ({len(out)} строк)")
    print(f"  • {slug}_compact.txt    — компактный текст ({compact_bytes} bytes)")

    if compact_bytes > 200_000:
        print(f"\n⚠️  Файл compact.txt большой ({compact_bytes/1024:.0f}KB).")
        print(f"   При чтении через Read tool используй offset/limit (лимит 256KB / 25k токенов).")
        print(f"   Рекомендуемые чанки по 700 строк через offset.")


if __name__ == "__main__":
    main()
