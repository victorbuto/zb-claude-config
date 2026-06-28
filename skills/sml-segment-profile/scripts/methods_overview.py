#!/usr/bin/env python3
"""
Считает частотности всех методов в SML-CSV.

Используется на старте — пользователь видит какие сегменты есть в каждом методе,
чтобы выбрать фильтр для анализа.

Usage:
    python methods_overview.py <path_to_csv> [--top N]

Output:
    Markdown-таблица с топ-N сегментов по каждому методу.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd


SPLIT = "; "
SKIP_COLS = {
    "Дата", "Текст", "Источник", "Url", "Тип источника", "Тип сообщения", "Сюжет",
    "Автор", "Url автора", "Пол", "Возраст", "Аудитория", "Комментариев",
    "Цитируемость СМИ", "Репостов", "Лайков", "Вовлеченность", "Просмотров",
    "Тональность", "Роль объекта", "Агрессия", "Страна", "Регион", "Город",
    "Язык", "WOM", "Продукты", "Тип продукта", "Ценность", "Все сегменты",
    "segments_count", "Lenth", "Length",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    df = pd.read_csv(args.csv_path)
    method_cols = [c for c in df.columns if c not in SKIP_COLS]

    print(f"Файл: {args.csv_path}")
    print(f"Всего строк: {len(df)}")
    print()

    # Сводка по методам
    print(f'{"Метод":<32} {"Размечено":>10} {"Уник.":>8}')
    print("-" * 54)
    method_stats = []
    for col in method_cols:
        if df[col].dtype != object:
            continue
        c = Counter()
        rows_with = 0
        for cell in df[col].fillna("").astype(str):
            if not cell:
                continue
            rows_with += 1
            for seg in cell.split(SPLIT):
                seg = seg.strip()
                if seg:
                    c[seg] += 1
        if rows_with == 0:
            continue
        method_stats.append((col, c, rows_with))
        print(f"{col:<32} {rows_with:>10} {len(c):>8}")

    # Топ-N сегментов по каждому методу
    for col, c, rows_with in method_stats:
        if not c:
            continue
        top = c.most_common(args.top)
        print(f"\n### {col}  —  {rows_with} строк, {len(c)} уник.")
        print("| сегмент | строк |")
        print("|---|---:|")
        for seg, n in top:
            print(f"| {seg} | {n} |")


if __name__ == "__main__":
    main()
