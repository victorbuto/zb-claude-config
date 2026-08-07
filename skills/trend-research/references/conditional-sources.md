# Условные источники сигналов

**Обновлено:** 2026-07-30  
**Назначение:** маршрутизация публичного Reddit, Hacker News Algolia, GitHub REST и Polymarket Gamma в тренд-рисёрче.  
**Описание:** правила включения, команды и ограничения источников, которые нельзя запускать автоматически для каждой темы.

## Главное правило

Сначала сформулировать, какой вопрос должен закрыть источник. Не запускать все четыре канала «для полноты». Нерелевантный источник создаёт ложные сигналы и повышает стоимость QA.

Единый скрипт:

```bash
python3 .claude/skills/trend-research/scripts/trend_sources.py --help
```

Все команды возвращают нормализованный JSON и поддерживают `--output FILE`.

## Public Reddit

Использовать для международных потребительских и профессиональных сообществ:

- язык аудитории, боли, возражения;
- сравнение альтернатив и willingness to pay;
- реакции на новый продукт;
- повторяющиеся практики и контр-сигналы.

Не использовать для исследования только российского рынка. В таком случае приоритетны Pikabu, Dzen, Otzovik, iRecommend и Telegram.

Пайплайн не требует API-ключа:

1. Reddit RSS для keyword discovery.
2. Публичные shreddit listing endpoints для score и comment count.
3. Публичный shreddit comments endpoint для топ-комментариев.
4. Дедупликация, фильтр свежести и relevance ranking.

```bash
python3 .claude/skills/trend-research/scripts/trend_sources.py reddit \
  "premium economy worth it" \
  --subreddit travel --subreddit TravelHacks \
  --days 30 --limit 20 --enrich 5 \
  --output /tmp/reddit-signals.json
```

Reddit является качественным материалом, но не доказательством масштаба рынка. Подтверждать найденные паттерны количественными или первичными источниками.

## Hacker News через Algolia

Использовать только когда предмет исследования связан с:

- AI и software;
- developer tools и open source;
- стартапами и технологическими бизнес-моделями;
- инфраструктурой, API, data и security.

Не использовать для моды, еды, путешествий, FMCG и других потребительских тем без явного технологического среза.

```bash
python3 .claude/skills/trend-research/scripts/trend_sources.py hn \
  "AI travel planning" --days 90 --limit 30 \
  --output /tmp/hn-signals.json
```

Algolia API бесплатный и не требует ключа.

## GitHub REST API

Использовать, когда активность репозиториев, issues, PR или releases сама является сигналом:

- рост open-source категории;
- появление новых протоколов, SDK и интеграций;
- повторяющиеся проблемы пользователей;
- скорость развития конкретного инструмента.

Не считать stars или количество issues доказательством массового потребительского спроса.

```bash
python3 .claude/skills/trend-research/scripts/trend_sources.py github \
  "travel MCP" --days 90 --limit 30 \
  --output /tmp/github-signals.json
```

Без токена работает публичный лимит GitHub. Для больших прогонов можно задать `GITHUB_TOKEN` или `GH_TOKEN`.

## Polymarket Gamma API

Использовать только для гипотез, которые можно выразить как событие с вероятностью:

- политика и регулирование;
- выборы;
- макроэкономические события;
- запуск или достижение измеримого результата;
- crypto и публичные технологические события.

Не использовать для общих культурных, эстетических или потребительских трендов. Рыночная вероятность отражает мнение участников конкретного рынка, а не репрезентативный прогноз населения.

```bash
python3 .claude/skills/trend-research/scripts/trend_sources.py polymarket \
  "airline merger" --limit 20 \
  --output /tmp/polymarket-signals.json
```

## Маршрутизация

Перед Phase 3.3 можно получить машинную подсказку:

```bash
python3 .claude/skills/trend-research/scripts/trend_sources.py route \
  "AI travel planning" --context tech --geo global
```

Окончательное решение принимает агент по исследовательскому вопросу:

| Условие | Reddit | HN | GitHub | Polymarket |
|---|---:|---:|---:|---:|
| Международное потребительское поведение | Да | Нет | Нет | Нет |
| Российское потребительское поведение | Нет | Нет | Нет | Нет |
| AI, software, developer ecosystem | Иногда | Да | Да | Иногда |
| Open-source adoption | Иногда | Да | Да | Нет |
| Политика, регулирование, прогнозируемое событие | Иногда | Иногда | Нет | Да |
| Общий cultural/lifestyle trend | Иногда | Нет | Нет | Нет |

Каждый включённый источник должен появиться в плане Phase 3.3 с вопросом, который он проверяет. В QA считать не количество результатов, а число сигналов, дошедших до Tier 1–2.
