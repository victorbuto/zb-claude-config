#!/usr/bin/env python3
"""
build_review.py — собирает интерактивную HTML-страницу обзора контекста.

Вход:
  --slices    путь к slices.json   (массив нарезанных блоков)
  --analysis  путь к analysis.json (выводы + группировка)
  --out       путь к review.html   (куда записать страницу)

slices.json — массив объектов:
  { "id": "s1", "source": "file.md", "title": "...", "summary": "...",
    "original_text": "дословный блок", "tags": ["..."] }

analysis.json:
  { "overview": "общие выводы (текст/markdown)",
    "groups": [
       {"id":"g1","type":"similar","title":"Тема","slice_ids":["s2","s7"]},
       {"id":"g2","type":"unique","title":null,"slice_ids":["s1"]}
    ] }

HTML сам файл не пишет (браузер так не умеет). Кнопка «Создать контекст»
формирует текст выбора и показывает его в окне для копирования — этот текст
пользователь отдаёт обратно ассистенту, который собирает итоговый файл.
"""
import argparse
import html
import json


def esc(s):
    return html.escape(s if s is not None else "", quote=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slices", required=True)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Обзор контекста")
    args = ap.parse_args()

    with open(args.slices, encoding="utf-8") as f:
        slices = json.load(f)
    with open(args.analysis, encoding="utf-8") as f:
        analysis = json.load(f)

    by_id = {s["id"]: s for s in slices}
    groups = analysis.get("groups", [])
    overview = analysis.get("overview", "")

    n_unique = sum(1 for g in groups if g.get("type") != "similar")
    n_similar = sum(1 for g in groups if g.get("type") == "similar")

    # данные кладём в JSON прямо в страницу — карточки и «развернуть» работают офлайн
    data_json = json.dumps(
        {"slices": slices, "groups": groups, "title": args.title},
        ensure_ascii=False,
    )

    page = TEMPLATE.format(
        title=esc(args.title),
        overview_html=esc(overview).replace("\n", "<br>"),
        n_files=len({s.get("source", "") for s in slices}),
        n_slices=len(slices),
        n_unique=n_unique,
        n_similar=n_similar,
        data_json=data_json,
    )

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"OK: {args.out} ({len(slices)} блоков, {len(groups)} групп)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg:#0f1115; --panel:#171a21; --card:#1c2129; --line:#2a313c;
    --txt:#e6e9ef; --mut:#9aa4b2; --acc:#5b8cff; --ok:#34c759; --merge:#ffb020;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--txt);
    font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:24px 20px 120px; }}
  header h1 {{ margin:0 0 6px; font-size:24px; }}
  .stats {{ color:var(--mut); font-size:13px; margin-bottom:16px; }}
  .stats b {{ color:var(--txt); }}
  .overview {{ background:var(--panel); border:1px solid var(--line);
    border-radius:12px; padding:16px 18px; margin-bottom:24px; }}
  .overview h2 {{ margin:0 0 8px; font-size:15px; color:var(--acc);
    text-transform:uppercase; letter-spacing:.04em; }}
  .group {{ margin-bottom:20px; }}
  .group.similar {{ border:1px dashed var(--merge); border-radius:14px;
    padding:14px; background:rgba(255,176,32,.04); }}
  .group.similar > .group-head {{ color:var(--merge); font-size:13px;
    text-transform:uppercase; letter-spacing:.04em; margin-bottom:10px; }}
  .cards {{ display:grid; gap:14px; }}
  .group.similar .cards {{ grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); }}
  .card {{ background:var(--card); border:1px solid var(--line);
    border-radius:12px; padding:14px 16px; }}
  .card.on {{ border-color:var(--ok); box-shadow:0 0 0 1px var(--ok) inset; }}
  .card .src {{ font-size:11px; color:var(--mut); margin-bottom:4px; }}
  .card h3 {{ margin:0 0 6px; font-size:16px; }}
  .card .sum {{ color:var(--mut); font-size:13.5px; margin-bottom:10px; }}
  .orig {{ display:none; white-space:pre-wrap; background:#0c0e12;
    border:1px solid var(--line); border-radius:8px; padding:10px;
    font-size:13px; color:#cfd6e0; margin:8px 0; max-height:340px; overflow:auto; }}
  .orig.show {{ display:block; }}
  .toggle {{ background:none; border:none; color:var(--acc); cursor:pointer;
    padding:0; font-size:13px; }}
  .choices {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:10px;
    padding-top:10px; border-top:1px solid var(--line); font-size:13px; }}
  .choices label {{ cursor:pointer; color:var(--mut); display:flex;
    align-items:center; gap:5px; }}
  .choices input {{ accent-color:var(--acc); }}
  .bar {{ position:fixed; left:0; right:0; bottom:0; background:var(--panel);
    border-top:1px solid var(--line); padding:14px 20px; display:flex;
    align-items:center; gap:16px; justify-content:center; }}
  .bar .count {{ color:var(--mut); font-size:13px; }}
  .btn {{ background:var(--acc); color:#fff; border:none; border-radius:10px;
    padding:11px 22px; font-size:15px; font-weight:600; cursor:pointer; }}
  .modal {{ position:fixed; inset:0; background:rgba(0,0,0,.6); display:none;
    align-items:center; justify-content:center; padding:20px; }}
  .modal.show {{ display:flex; }}
  .modal .box {{ background:var(--panel); border:1px solid var(--line);
    border-radius:14px; padding:20px; max-width:680px; width:100%; }}
  .modal h2 {{ margin:0 0 6px; font-size:18px; }}
  .modal p {{ color:var(--mut); font-size:13px; margin:0 0 12px; }}
  .modal textarea {{ width:100%; height:260px; background:#0c0e12;
    color:var(--txt); border:1px solid var(--line); border-radius:8px;
    padding:12px; font:13px/1.5 ui-monospace,Menlo,monospace; resize:vertical; }}
  .modal .row {{ display:flex; gap:10px; margin-top:12px; }}
  .modal .ghost {{ background:none; border:1px solid var(--line); color:var(--txt); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{title}</h1>
    <div class="stats">Файлов: <b>{n_files}</b> &nbsp;·&nbsp;
      блоков: <b>{n_slices}</b> &nbsp;·&nbsp;
      уникальных: <b>{n_unique}</b> &nbsp;·&nbsp;
      групп схожих: <b>{n_similar}</b></div>
  </header>

  <div class="overview">
    <h2>Выводы и наблюдения</h2>
    <div>{overview_html}</div>
  </div>

  <div id="root"></div>
</div>

<div class="bar">
  <span class="count" id="count">Выбрано: 0</span>
  <button class="btn" onclick="buildSelection()">Создать контекст</button>
</div>

<div class="modal" id="modal">
  <div class="box">
    <h2>Готово — скопируй и отдай ассистенту</h2>
    <p>Этот текст описывает твой выбор. Скопируй его и вставь в чат —
       ассистент соберёт итоговый файл строго из оригинальных текстов.</p>
    <textarea id="out" readonly></textarea>
    <div class="row">
      <button class="btn" onclick="copyOut()">Скопировать</button>
      <button class="btn ghost" onclick="closeModal()">Закрыть</button>
    </div>
  </div>
</div>

<script>
const DATA = {data_json};
const SLICES = Object.fromEntries(DATA.slices.map(s => [s.id, s]));

function card(s, inGroup) {{
  const div = document.createElement('div');
  div.className = 'card';
  div.dataset.id = s.id;
  div.innerHTML = `
    <div class="src">${{s.source||''}}</div>
    <h3>${{s.title||s.id}}</h3>
    <div class="sum">${{s.summary||''}}</div>
    <button class="toggle">▸ показать оригинал</button>
    <div class="orig">${{(s.original_text||'').replace(/</g,'&lt;')}}</div>
  `;
  const tog = div.querySelector('.toggle');
  const orig = div.querySelector('.orig');
  tog.onclick = () => {{
    orig.classList.toggle('show');
    tog.textContent = orig.classList.contains('show') ? '▾ скрыть оригинал' : '▸ показать оригинал';
  }};
  return div;
}}

function choices(unitId, isGroup) {{
  const wrap = document.createElement('div');
  wrap.className = 'choices';
  const opts = isGroup
    ? [['merge','Смержить и принять'],['each','Принять по отдельности'],['skip','Пропустить']]
    : [['accept','Принять'],['skip','Пропустить']];
  opts.forEach(([val,label]) => {{
    const l = document.createElement('label');
    l.innerHTML = `<input type="radio" name="${{unitId}}" value="${{val}}" ${{val==='skip'?'checked':''}}> ${{label}}`;
    l.querySelector('input').onchange = updateCount;
    wrap.appendChild(l);
  }});
  return wrap;
}}

const root = document.getElementById('root');
DATA.groups.forEach(g => {{
  const block = document.createElement('div');
  const isSim = g.type === 'similar';
  block.className = 'group' + (isSim ? ' similar' : '');
  block.dataset.gid = g.id;
  block.dataset.ids = g.slice_ids.join(',');
  if (isSim) {{
    const head = document.createElement('div');
    head.className = 'group-head';
    head.textContent = 'Схожие рекомендации' + (g.title ? ' · ' + g.title : '');
    block.appendChild(head);
  }}
  const cards = document.createElement('div');
  cards.className = 'cards';
  g.slice_ids.forEach(id => cards.appendChild(card(SLICES[id], isSim)));
  block.appendChild(cards);
  block.appendChild(choices(g.id, isSim));
  root.appendChild(block);
}});

function selected() {{
  const res = [];
  DATA.groups.forEach(g => {{
    const val = document.querySelector(`input[name="${{g.id}}"]:checked`).value;
    if (val !== 'skip') res.push({{g, val}});
  }});
  return res;
}}

function updateCount() {{
  document.querySelectorAll('.group').forEach(b => {{
    const val = document.querySelector(`input[name="${{b.dataset.gid}}"]:checked`).value;
    b.querySelectorAll('.card').forEach(c => c.classList.toggle('on', val !== 'skip'));
  }});
  document.getElementById('count').textContent = 'Выбрано: ' + selected().length;
}}

function buildSelection() {{
  const sel = selected();
  let txt = '=== CONTEXT-MERGE: ВЫБОР ===\n';
  txt += 'Собери итоговый файл строго из оригинальных текстов перечисленных блоков.\n\n';
  if (!sel.length) txt += '(ничего не выбрано)\n';
  sel.forEach(({{g, val}}) => {{
    const ids = g.slice_ids;
    if (val === 'merge') {{
      txt += `[СМЕРЖИТЬ] ${{g.id}} (${{ids.join(', ')}})` + (g.title ? ` — ${{g.title}}` : '') + '\n';
      ids.forEach(id => txt += `    - ${{id}} | ${{SLICES[id].source}} | ${{SLICES[id].title}}\n`);
    }} else if (val === 'each') {{
      ids.forEach(id => txt += `[ПРИНЯТЬ] ${{id}} | ${{SLICES[id].source}} | ${{SLICES[id].title}}\n`);
    }} else {{ // accept (unique)
      const id = ids[0];
      txt += `[ПРИНЯТЬ] ${{id}} | ${{SLICES[id].source}} | ${{SLICES[id].title}}\n`;
    }}
  }});
  document.getElementById('out').value = txt;
  document.getElementById('modal').classList.add('show');
}}

function copyOut() {{
  const ta = document.getElementById('out');
  ta.select();
  navigator.clipboard.writeText(ta.value);
}}
function closeModal() {{ document.getElementById('modal').classList.remove('show'); }}

updateCount();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
