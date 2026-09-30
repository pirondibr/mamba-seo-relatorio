# -*- coding: utf-8 -*-
"""
Aba Mercado Livre no relatório Mamba:
- Páginas cuja URL contém 'mercado-livre' / 'mercado_livre'
- Cliques: janela atual (~28d) vs 1, 2 e 3 meses atrás
- Top queries + posição média por página (janela atual)
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE = Path(r"c:\Users\Usuario\Desktop\mamba seo")
TOKEN = BASE / "token.json"
SITE = "sc-domain:mambadigital.com.br"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
OUT_HTML = BASE / "relatorio-mercado-livre.html"
OUT_CACHE = BASE / "gsc-cache-mercado-livre.json"
OUT_DOCS = BASE / "docs" / "mercado-livre" / "index.html"

# GSC atrasa ~2–3 dias
END = date.today() - timedelta(days=3)
WINDOW = 28  # dias por janela
SHIFTS = {
    "atual": 0,
    "m1": 30,
    "m2": 60,
    "m3": 90,
}
URL_NEEDLES = ("mercado-livre", "mercado_livre", "mercadolivre")
TOP_QUERIES = 15


def get_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def window_for(shift_days: int) -> tuple[date, date]:
    end = END - timedelta(days=shift_days)
    start = end - timedelta(days=WINDOW - 1)
    return start, end


def query_api(service, start: date, end: date, dimensions: list[str], expression: str) -> list[dict]:
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": dimensions,
        "rowLimit": 25000,
        "type": "web",
        "dataState": "final",
        "dimensionFilterGroups": [
            {
                "filters": [
                    {
                        "dimension": "page",
                        "operator": "contains",
                        "expression": expression,
                    }
                ]
            }
        ],
    }
    return service.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])


def fetch_pages_all_needles(service, start: date, end: date) -> list[dict]:
    seen = set()
    rows = []
    for needle in URL_NEEDLES:
        for r in query_api(service, start, end, ["page"], needle):
            url = r["keys"][0]
            if url in seen:
                continue
            seen.add(url)
            rows.append(r)
    return rows


def fetch_queries_all_needles(service, start: date, end: date) -> list[dict]:
    seen = set()
    rows = []
    for needle in URL_NEEDLES:
        for r in query_api(service, start, end, ["page", "query"], needle):
            key = (r["keys"][0], r["keys"][1])
            if key in seen:
                continue
            seen.add(key)
            rows.append(r)
    return rows


def canon_url(url: str) -> str:
    """Normaliza URL (sem query/hash, sem barra final)."""
    u = url.split("?")[0].split("#")[0].rstrip("/")
    return u


def path_slug(url: str) -> str:
    path = urlparse(canon_url(url)).path
    return path or "/"


def is_ml_url(url: str) -> bool:
    low = url.lower()
    return any(n in low for n in URL_NEEDLES)


def agg_by_page(rows: list[dict]) -> dict[str, dict]:
    by: dict[str, dict] = {}
    for r in rows:
        url = canon_url(r["keys"][0])
        if not is_ml_url(url):
            continue
        c = float(r.get("clicks") or 0)
        i = float(r.get("impressions") or 0)
        p = float(r.get("position") or 0)
        if url not in by:
            by[url] = {"clicks": 0.0, "impressions": 0.0, "pos_w": 0.0, "url": url}
        by[url]["clicks"] += c
        by[url]["impressions"] += i
        by[url]["pos_w"] += p * i
    for v in by.values():
        imps = v["impressions"]
        v["ctr"] = (v["clicks"] / imps) if imps else 0.0
        v["position"] = (v["pos_w"] / imps) if imps else 0.0
        del v["pos_w"]
    return by


def queries_by_page(rows: list[dict]) -> dict[str, list[dict]]:
    by: dict[str, dict[str, dict]] = {}
    for r in rows:
        url = canon_url(r["keys"][0])
        q = r["keys"][1]
        if not is_ml_url(url):
            continue
        c = float(r.get("clicks") or 0)
        i = float(r.get("impressions") or 0)
        p = float(r.get("position") or 0)
        by.setdefault(url, {})
        if q not in by[url]:
            by[url][q] = {"query": q, "clicks": 0.0, "impressions": 0.0, "pos_w": 0.0}
        by[url][q]["clicks"] += c
        by[url][q]["impressions"] += i
        by[url][q]["pos_w"] += p * i
    out: dict[str, list[dict]] = {}
    for url, qs in by.items():
        lst = []
        for q, v in qs.items():
            imps = v["impressions"]
            lst.append(
                {
                    "query": v["query"],
                    "clicks": v["clicks"],
                    "impressions": imps,
                    "ctr": (v["clicks"] / imps) if imps else 0.0,
                    "position": (v["pos_w"] / imps) if imps else 0.0,
                }
            )
        lst.sort(key=lambda x: (-x["clicks"], -x["impressions"], x["position"]))
        out[url] = lst[:TOP_QUERIES]
    return out


def fmt_int(n) -> str:
    return f"{int(round(float(n or 0))):,}".replace(",", ".")


def fmt_pct(n) -> str:
    return f"{float(n or 0) * 100:.2f}%".replace(".", ",")


def fmt_pos(n) -> str:
    if not n:
        return "—"
    return f"{float(n):.1f}".replace(".", ",")


def delta_html(now: float, prev: float) -> str:
    d = now - prev
    if abs(d) < 0.5:
        return '<span class="delta flat">0</span>'
    cls = "up" if d > 0 else "down"
    sign = "+" if d > 0 else ""
    return f'<span class="delta {cls}">{sign}{fmt_int(d)}</span>'


def build_html(pages: list[dict], periods: dict) -> str:
    labels = {
        "atual": f"Atual ({periods['atual'][0].strftime('%d/%m')}–{periods['atual'][1].strftime('%d/%m')})",
        "m1": f"Há 1 mês ({periods['m1'][0].strftime('%d/%m')}–{periods['m1'][1].strftime('%d/%m')})",
        "m2": f"Há 2 meses ({periods['m2'][0].strftime('%d/%m')}–{periods['m2'][1].strftime('%d/%m')})",
        "m3": f"Há 3 meses ({periods['m3'][0].strftime('%d/%m')}–{periods['m3'][1].strftime('%d/%m')})",
    }
    total_atual = sum(p["atual"]["clicks"] for p in pages)
    total_m1 = sum(p["m1"]["clicks"] for p in pages)

    rows_html = []
    details_html = []
    for i, p in enumerate(pages, 1):
        url = p["url"]
        short = path_slug(url)
        a, m1, m2, m3 = p["atual"], p["m1"], p["m2"], p["m3"]
        pid = f"p{i}"
        rows_html.append(
            f"""
        <tr data-page="{pid}">
          <td class="rank">{i}</td>
          <td class="kw">
            <button type="button" class="page-toggle" data-target="{pid}">{escape(short)}</button>
            <a class="url" href="{escape(url)}" target="_blank" rel="noopener">abrir</a>
          </td>
          <td class="num">{fmt_int(a['clicks'])}</td>
          <td class="num">{fmt_int(m1['clicks'])} {delta_html(a['clicks'], m1['clicks'])}</td>
          <td class="num">{fmt_int(m2['clicks'])} {delta_html(a['clicks'], m2['clicks'])}</td>
          <td class="num">{fmt_int(m3['clicks'])} {delta_html(a['clicks'], m3['clicks'])}</td>
          <td class="num">{fmt_int(a['impressions'])}</td>
          <td class="num">{fmt_pos(a['position'])}</td>
          <td class="num">{len(p['queries'])}</td>
        </tr>"""
        )
        qrows = []
        for j, q in enumerate(p["queries"], 1):
            qrows.append(
                f"""
            <tr>
              <td class="rank">{j}</td>
              <td class="kw">{escape(q['query'])}</td>
              <td class="num">{fmt_int(q['clicks'])}</td>
              <td class="num">{fmt_int(q['impressions'])}</td>
              <td class="num">{fmt_pct(q['ctr'])}</td>
              <td class="num">{fmt_pos(q['position'])}</td>
            </tr>"""
            )
        if not qrows:
            qrows.append('<tr><td colspan="6" class="muted">Nenhuma query na janela atual.</td></tr>')
        details_html.append(
            f"""
        <div class="detail" id="detail-{pid}" hidden>
          <div class="detail-h">
            <strong>{escape(short)}</strong>
            <a href="{escape(url)}" target="_blank" rel="noopener">{escape(url)}</a>
          </div>
          <div class="mini-cards">
            <div class="mini"><span>Atual</span><strong>{fmt_int(a['clicks'])}</strong> cliques · pos {fmt_pos(a['position'])}</div>
            <div class="mini"><span>1 mês</span><strong>{fmt_int(m1['clicks'])}</strong> {delta_html(a['clicks'], m1['clicks'])}</div>
            <div class="mini"><span>2 meses</span><strong>{fmt_int(m2['clicks'])}</strong> {delta_html(a['clicks'], m2['clicks'])}</div>
            <div class="mini"><span>3 meses</span><strong>{fmt_int(m3['clicks'])}</strong> {delta_html(a['clicks'], m3['clicks'])}</div>
          </div>
          <h3>Palavras (janela atual) — top {TOP_QUERIES}</h3>
          <div class="table-wrap">
            <table>
              <thead><tr>
                <th>#</th><th>Query</th><th class="num">Cliques</th><th class="num">Impr.</th>
                <th class="num">CTR</th><th class="num">Pos. média</th>
              </tr></thead>
              <tbody>{''.join(qrows)}</tbody>
            </table>
          </div>
        </div>"""
        )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Mercado Livre — Páginas GSC | Mamba Digital</title>
<style>
  :root {{
    --bg: #f4f7fa; --surface: #fff; --surface2: #eef3f7; --border: #d5dee7;
    --text: #1a2330; --muted: #5c6b7a; --accent: #0d9488;
    --up: #059669; --down: #dc2626; --font: "Segoe UI", system-ui, sans-serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: var(--font); color: var(--text); line-height: 1.45;
    background: radial-gradient(1000px 480px at 8% -8%, #d8f3ef 0%, transparent 55%),
                radial-gradient(900px 420px at 100% 0%, #dde8f7 0%, transparent 50%), var(--bg);
    min-height: 100vh; padding: 2rem 1.25rem 4rem;
  }}
  .wrap {{ max-width: 1200px; margin: 0 auto; }}
  header {{ margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1.25rem; }}
  h1 {{ font-size: clamp(1.4rem, 3vw, 1.9rem); font-weight: 700; letter-spacing: -0.02em; }}
  .sub {{ color: var(--muted); margin-top: 0.35rem; font-size: 0.95rem; }}
  .cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem; margin-bottom: 1.25rem;
  }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 0.95rem 1rem;
  }}
  .card .label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em; color: var(--muted); }}
  .card .value {{ font-size: 1.55rem; font-weight: 700; margin-top: 0.2rem; }}
  .panel {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; overflow: hidden; margin-bottom: 1.15rem;
  }}
  .panel-h {{
    padding: 0.95rem 1.1rem; border-bottom: 1px solid var(--border);
    background: var(--surface2); display: flex; justify-content: space-between;
    gap: 0.75rem; flex-wrap: wrap; align-items: center;
  }}
  .panel-h h2 {{ font-size: 1.02rem; font-weight: 650; }}
  .filters {{ padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); display: flex; gap: 0.5rem; flex-wrap: wrap; }}
  .search {{
    padding: 0.4rem 0.7rem; border: 1px solid var(--border); border-radius: 8px;
    font-size: 0.85rem; min-width: 220px; flex: 1;
  }}
  .table-wrap {{ overflow: auto; max-height: 640px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.84rem; }}
  th {{
    text-align: left; padding: 0.6rem 0.8rem; color: var(--muted);
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em;
    position: sticky; top: 0; background: var(--surface); border-bottom: 1px solid var(--border); z-index: 1;
  }}
  th.sortable {{ cursor: pointer; user-select: none; white-space: nowrap; }}
  th.sortable::after {{ content: " ↕"; opacity: 0.35; }}
  th.sortable.asc::after {{ content: " ↑"; opacity: 1; color: var(--accent); }}
  th.sortable.desc::after {{ content: " ↓"; opacity: 1; color: var(--accent); }}
  td {{ padding: 0.5rem 0.8rem; border-bottom: 1px solid rgba(213,222,231,0.9); vertical-align: top; }}
  tr:hover td {{ background: rgba(13,148,136,0.05); }}
  .rank {{ color: var(--muted); width: 2.2rem; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .kw-text, .page-toggle {{ font-weight: 550; }}
  .page-toggle {{
    appearance: none; background: none; border: 0; color: var(--accent);
    cursor: pointer; font: inherit; font-weight: 650; text-align: left; padding: 0;
  }}
  .page-toggle:hover {{ text-decoration: underline; }}
  .url {{ display: inline-block; font-size: 0.72rem; color: var(--muted); margin-left: 0.4rem; }}
  .delta {{ display: block; font-size: 0.72rem; font-weight: 650; }}
  .delta.up {{ color: var(--up); }}
  .delta.down {{ color: var(--down); }}
  .delta.flat {{ color: var(--muted); }}
  .muted {{ color: var(--muted); }}
  .note {{ font-size: 0.8rem; color: var(--muted); padding: 0.85rem 1.1rem; }}
  .detail {{
    border-top: 1px solid var(--border); padding: 1rem 1.1rem 1.25rem;
    background: #f8fafc;
  }}
  .detail[hidden] {{ display: none !important; }}
  .detail-h {{ margin-bottom: 0.75rem; }}
  .detail-h a {{ display: block; font-size: 0.78rem; color: var(--muted); word-break: break-all; }}
  .detail h3 {{ font-size: 0.9rem; margin: 0.85rem 0 0.5rem; }}
  .mini-cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.5rem;
  }}
  .mini {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 0.65rem 0.75rem; font-size: 0.8rem;
  }}
  .mini span {{ display: block; color: var(--muted); font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .mini strong {{ font-size: 1.05rem; }}
  footer {{ margin-top: 1.25rem; color: var(--muted); font-size: 0.8rem; }}
  .chips {{ display: flex; gap: 0.4rem; flex-wrap: wrap; }}
  .chip {{
    font-size: 0.72rem; padding: 0.25rem 0.55rem; border-radius: 999px;
    background: var(--bg); border: 1px solid var(--border); color: var(--muted);
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Páginas Mercado Livre</h1>
    <p class="sub">mambadigital.com.br · URLs com “mercado-livre” · GSC · janelas de {WINDOW} dias</p>
  </header>

  <div class="cards">
    <div class="card"><div class="label">Páginas</div><div class="value">{fmt_int(len(pages))}</div></div>
    <div class="card"><div class="label">Cliques atuais</div><div class="value">{fmt_int(total_atual)}</div></div>
    <div class="card"><div class="label">Cliques há 1 mês</div><div class="value">{fmt_int(total_m1)}</div>
      {delta_html(total_atual, total_m1)}
    </div>
  </div>

  <div class="panel">
    <div class="panel-h">
      <h2>Priorização — tráfego e palavras</h2>
      <div class="chips">
        <span class="chip">{escape(labels['atual'])}</span>
        <span class="chip">Clique na URL para ver queries</span>
      </div>
    </div>
    <div class="filters">
      <input class="search" id="search" type="search" placeholder="Filtrar por URL..." />
    </div>
    <div class="table-wrap">
      <table id="ml-table" class="sortable-table">
        <thead>
          <tr>
            <th class="sortable" data-col="0" data-type="num">#</th>
            <th class="sortable" data-col="1" data-type="str">Página</th>
            <th class="sortable num" data-col="2" data-type="num">Atual</th>
            <th class="sortable num" data-col="3" data-type="num">1 mês</th>
            <th class="sortable num" data-col="4" data-type="num">2 meses</th>
            <th class="sortable num" data-col="5" data-type="num">3 meses</th>
            <th class="sortable num" data-col="6" data-type="num">Impr.</th>
            <th class="sortable num" data-col="7" data-type="num">Pos.</th>
            <th class="sortable num" data-col="8" data-type="num">Queries</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
    <p class="note">
      Colunas de cliques = janelas de {WINDOW} dias. “Atual” termina em {END.strftime('%d/%m/%Y')} (GSC atrasa ~3 dias).
      Delta sob 1/2/3 meses = atual − janela correspondente. Clique no path da página para abrir as palavras e posição média.
    </p>
    {''.join(details_html)}
  </div>

  <footer>Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · {SITE}</footer>
</div>
<script>
(function () {{
  const search = document.getElementById('search');
  const table = document.getElementById('ml-table');
  search.addEventListener('input', () => {{
    const q = search.value.trim().toLowerCase();
    table.querySelectorAll('tbody tr').forEach(tr => {{
      tr.style.display = (!q || tr.textContent.toLowerCase().includes(q)) ? '' : 'none';
    }});
  }});

  document.querySelectorAll('.page-toggle').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const id = btn.dataset.target;
      const el = document.getElementById('detail-' + id);
      const open = el.hasAttribute('hidden');
      document.querySelectorAll('.detail').forEach(d => d.setAttribute('hidden', ''));
      if (open) {{
        el.removeAttribute('hidden');
        el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
      }}
    }});
  }});

  let sortCol = null, sortDir = 'desc';
  function sortTable(col, type, dir) {{
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {{
      let av, bv;
      if (col === 1) {{
        av = a.querySelector('.page-toggle').textContent.toLowerCase();
        bv = b.querySelector('.page-toggle').textContent.toLowerCase();
        return dir === 'asc' ? av.localeCompare(bv, 'pt-BR') : bv.localeCompare(av, 'pt-BR');
      }}
      const an = a.children[col].childNodes[0];
      const bn = b.children[col].childNodes[0];
      av = parseFloat(String(an.textContent || '0').replace(/\\./g, '').replace(',', '.')) || 0;
      bv = parseFloat(String(bn.textContent || '0').replace(/\\./g, '').replace(',', '.')) || 0;
      if (type === 'str') {{
        av = a.children[col].textContent.toLowerCase();
        bv = b.children[col].textContent.toLowerCase();
        return dir === 'asc' ? String(av).localeCompare(String(bv), 'pt-BR') : String(bv).localeCompare(String(av), 'pt-BR');
      }}
      return dir === 'asc' ? av - bv : bv - av;
    }});
    rows.forEach((tr, i) => {{
      tr.querySelector('.rank').textContent = String(i + 1);
      tbody.appendChild(tr);
    }});
  }}
  table.querySelectorAll('th.sortable').forEach(th => {{
    th.addEventListener('click', () => {{
      const col = +th.dataset.col;
      const type = th.dataset.type || 'num';
      if (sortCol === col) sortDir = sortDir === 'desc' ? 'asc' : 'desc';
      else {{ sortCol = col; sortDir = 'desc'; }}
      table.querySelectorAll('th.sortable').forEach(h => h.classList.remove('asc', 'desc'));
      th.classList.add(sortDir);
      sortTable(col, type, sortDir);
    }});
  }});
}})();
</script>
</body>
</html>
"""


def empty_metrics() -> dict:
    return {"clicks": 0.0, "impressions": 0.0, "ctr": 0.0, "position": 0.0, "url": ""}


def main():
    print(f"Propriedade: {SITE}")
    print(f"Janela: {WINDOW} dias | fim atual: {END.isoformat()}")
    service = get_service()

    periods = {k: window_for(v) for k, v in SHIFTS.items()}
    for k, (s, e) in periods.items():
        print(f"  {k}: {s} -> {e}")

    page_maps: dict[str, dict[str, dict]] = {}
    for key, (start, end) in periods.items():
        print(f"Buscando páginas ({key})...")
        rows = fetch_pages_all_needles(service, start, end)
        page_maps[key] = agg_by_page(rows)
        print(f"  {len(page_maps[key])} páginas únicas")

    print("Buscando queries (janela atual)...")
    q_rows = fetch_queries_all_needles(service, periods["atual"][0], periods["atual"][1])
    q_by_page = queries_by_page(q_rows)
    print(f"  queries em {len(q_by_page)} páginas")

    all_urls = set()
    for m in page_maps.values():
        all_urls |= set(m.keys())

    pages = []
    for url in all_urls:
        pages.append(
            {
                "url": url,
                "atual": page_maps["atual"].get(url) or empty_metrics(),
                "m1": page_maps["m1"].get(url) or empty_metrics(),
                "m2": page_maps["m2"].get(url) or empty_metrics(),
                "m3": page_maps["m3"].get(url) or empty_metrics(),
                "queries": q_by_page.get(url, []),
            }
        )
    pages.sort(key=lambda p: (-p["atual"]["clicks"], -p["atual"]["impressions"], p["url"]))

    cache = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "site": SITE,
        "end": END.isoformat(),
        "window_days": WINDOW,
        "periods": {k: [s.isoformat(), e.isoformat()] for k, (s, e) in periods.items()},
        "pages": [
            {
                "url": p["url"],
                "atual": p["atual"],
                "m1": p["m1"],
                "m2": p["m2"],
                "m3": p["m3"],
                "queries": p["queries"],
            }
            for p in pages
        ],
    }
    OUT_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    html = build_html(pages, periods)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_DOCS.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOCS.write_text(html, encoding="utf-8")
    print(f"\nOK: {len(pages)} páginas")
    print(f"HTML: {OUT_HTML}")
    print(f"Pages: {OUT_DOCS}")
    print(f"Cache: {OUT_CACHE}")


if __name__ == "__main__":
    main()
