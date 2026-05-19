---
name: company-profile-search
description: >
  Быстрый сбор профиля компании перед питчем или звонком с клиентом.
  Использовать когда пользователь просит собрать информацию о компании,
  подготовиться к встрече с клиентом, сделать research компании.
  Триггеры: собери инфу о компании, профиль компании, подготовка к питчу,
  company research, что за компания, research компании, узнай про компанию.
---

# Company Profile Search

Сбор профиля компании за 3-5 минут для подготовки к питчу/звонку.

## Workflow

1. **Найти сайт компании** (если не указан):
   ```
   WebSearch(query="название компании официальный сайт Россия")
   ```
   По умолчанию искать русский сайт (.ru, .рф), если не указано иное.
   Извлечь домен из результатов.

2. **Запустить 3 параллельных запроса** (см. [data-sources.md](references/data-sources.md)):
   - Exa Company Research → профиль, новости
   - WebFetch сайта → продукты, цены, соцсети (полные URL из footer)
   - WebSearch комбо → выручка, ИНН, руководство

3. **Собрать трафик** — WebSearch `"domain.ru" site:semrush.com traffic`, если нет результата → WebFetch `hypestat.com/info/domain.ru`

4. **Сформировать вывод** по шаблону [output-template.md](references/output-template.md)

5. **Сохранить** в `/Users/fixed/Documents/ZB CLOUD 3600/CLOUD ZB (3600)/Researches/company-profiles/[company]_summary.md`

## Ключевые правила

- **Новости** — всегда со ссылкой `[Источник](URL)`
- **Выступления** — должность + дата выступления рядом с именем спикера
- **Продукты/Позиционирование** — сначала 1-2 предложения, потом таблица
- **Цены** — указывать ценовой сегмент (бюджетный / middle / upper-middle / premium)
- **Трафик** — обязателен: сначала Semrush сниппет, если нет — HypeStat
- **Соцсети** — брать ТОЛЬКО с сайта компании через WebFetch, не угадывать
- **Конкуренты** — добавлять сразу после блока "Продукты и ЦА"
- **НЕ добавлять:** блок "Ключевые цитаты", блок "Источники"

## Параллельные запросы

```
# Блок A: Профиль
mcp__exa__company_research_exa(companyName="Компания", numResults=10)

# Блок B: Сайт
WebFetch(url="https://company.ru", prompt="продукты, цены, слоган, соцсети")

# Блок C: Финансы + люди
WebSearch(query="компания выручка ИНН CEO site:rusprofile.ru OR site:vc.ru")
```

## References

- [output-template.md](references/output-template.md) — шаблон вывода
- [data-sources.md](references/data-sources.md) — источники и стратегия сбора
