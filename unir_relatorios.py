# -*- coding: utf-8 -*-
"""Une Relatório Visitas (GSC) + Palavras (Semrush) + Mercado Livre em um HTML só."""
from pathlib import Path
import re

ROOT = Path(r"c:\Users\Usuario\Desktop\mamba seo")
BASE = ROOT / "mamba dados"
GSC = BASE / "relatorio-gsc-3meses.html"
TRAFEGO = BASE / "relatorio-trafego.html"
PAGINAS = BASE / "relatorio-paginas-semrush.html"
BACKLINKS = BASE / "relatorio-backlinks.html"
IA_VISITAS = BASE / "relatorio-ia-visitas.html"
PALAVRAS = BASE / "relatorio-top-1-5-10.html"
ML = BASE / "relatorio-mercado-livre.html"
OUT = BASE / "relatorio-mamba-seo.html"
OUT_DOCS = ROOT / "docs" / "index.html"


def extract_style(html: str) -> str:
    m = re.search(r"<style>(.*?)</style>", html, re.S)
    return m.group(1) if m else ""


def extract_body_inner(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S | re.I)
    return m.group(1).strip() if m else ""


def strip_scripts(html: str) -> str:
    return re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S | re.I)


def prefix_ids(html: str, prefix: str) -> str:
    ids = sorted(set(re.findall(r'id="([^"]+)"', html)), key=len, reverse=True)
    out = html
    for iid in ids:
        out = out.replace(f'id="{iid}"', f'id="{prefix}{iid}"')
    return out


gsc_html = GSC.read_text(encoding="utf-8")
traf_html = TRAFEGO.read_text(encoding="utf-8") if TRAFEGO.exists() else ""
pag_html = PAGINAS.read_text(encoding="utf-8") if PAGINAS.exists() else ""
bl_html = BACKLINKS.read_text(encoding="utf-8") if BACKLINKS.exists() else ""
ia_html = IA_VISITAS.read_text(encoding="utf-8") if IA_VISITAS.exists() else ""
pal_html = PALAVRAS.read_text(encoding="utf-8")
ml_html = ML.read_text(encoding="utf-8") if ML.exists() else ""

gsc_style = extract_style(gsc_html)
traf_style = extract_style(traf_html) if traf_html else ""
pag_style = extract_style(pag_html) if pag_html else ""
bl_style = extract_style(bl_html) if bl_html else ""
ia_style = extract_style(ia_html) if ia_html else ""
pal_style = extract_style(pal_html)
ml_style = extract_style(ml_html) if ml_html else ""
gsc_body = prefix_ids(extract_body_inner(gsc_html), "v-")
traf_body = prefix_ids(extract_body_inner(traf_html), "t-") if traf_html else "<p>Gere relatorio-trafego.html primeiro.</p>"
pag_body = prefix_ids(extract_body_inner(pag_html), "pg-") if pag_html else "<p>Gere relatorio-paginas-semrush.html primeiro.</p>"
bl_body = prefix_ids(extract_body_inner(bl_html), "bl-") if bl_html else "<p>Gere relatorio-backlinks.html primeiro.</p>"
# JS no HTML original usa #table/#search; após prefix viram #bl-table/#bl-search — script abaixo religa.
ia_body = prefix_ids(extract_body_inner(ia_html), "ia-") if ia_html else "<p>Gere relatorio-ia-visitas.html primeiro.</p>"
pal_body = prefix_ids(extract_body_inner(pal_html), "p-")
ml_raw = strip_scripts(extract_body_inner(ml_html)) if ml_html else "<p>Gere relatorio-mercado-livre.html primeiro.</p>"
ml_body = prefix_ids(ml_raw, "ml-")
# page toggles: data-target="p1" stays; detail ids become ml-detail-p1
# wire script to use ml-detail- + original data-target

nav = """
<nav class="topnav" id="topnav">
  <div class="topnav-inner">
    <div class="topnav-brand">Mamba Digital · SEO</div>
    <div class="topnav-links">
      <a href="#report-visitas" class="topnav-link active" data-report="visitas">Relatório Visitas</a>
      <a href="#report-ia-visitas" class="topnav-link" data-report="ia-visitas">IA Visitas</a>
      <a href="#report-trafego" class="topnav-link" data-report="trafego">Tráfego Semrush</a>
      <a href="#report-paginas" class="topnav-link" data-report="paginas">Páginas Semrush</a>
      <a href="#report-backlinks" class="topnav-link" data-report="backlinks">Backlinks</a>
      <a href="#report-palavras" class="topnav-link" data-report="palavras">Relatório Palavras</a>
      <a href="#report-ml" class="topnav-link" data-report="ml">Mercado Livre</a>
    </div>
  </div>
</nav>
"""

LIGHT_THEME = """
  :root {
    --bg: #f4f7fa; --surface: #ffffff; --surface2: #eef3f7; --border: #d5dee7;
    --text: #1a2330; --muted: #5c6b7a; --accent: #0d9488;
    --pos1: #0d9488; --pos3: #2563eb; --pos5: #b45309; --pos10: #7c3aed;
    --up: #059669; --down: #dc2626;
  }
  body {
    background:
      radial-gradient(1000px 480px at 8% -8%, #d8f3ef 0%, transparent 55%),
      radial-gradient(900px 420px at 100% 0%, #dde8f7 0%, transparent 50%),
      var(--bg) !important;
    color: var(--text) !important;
  }
  .topnav { background: rgba(255, 255, 255, 0.92) !important; border-bottom-color: var(--border) !important; }
  .topnav-link { background: var(--surface) !important; color: var(--muted) !important; border-color: var(--border) !important; }
  .topnav-link:hover { color: var(--text) !important; border-color: #b8c5d1 !important; }
  .topnav-link.active { background: var(--accent) !important; color: #fff !important; border-color: var(--accent) !important; }
  .tab.active, .main-tab.active { background: var(--accent) !important; color: #fff !important; border-color: var(--accent) !important; }
  .bar, .mbar { background: linear-gradient(180deg, #14b8a6, #0f766e) !important; }
  .bar.bar-stack { background: transparent !important; }
  #report-trafego .sm-chart, #report-trafego .sm-svg {
    display: block !important; width: 100% !important; height: auto !important;
  }
  #report-trafego .sm-hit { fill: transparent !important; flex: none !important; }
  #report-trafego .sm-band, #report-trafego .sm-preset {
    cursor: pointer !important; font: inherit !important;
  }
  #report-trafego .sm-preset.active {
    background: var(--accent) !important; color: #fff !important; border-color: var(--accent) !important;
  }
  #report-trafego .sm-band.off { opacity: 0.38 !important; }
  #report-paginas .sm-chart, #report-paginas .sm-svg {
    display: block !important; width: 100% !important; height: auto !important;
  }
  #report-paginas .sm-hit { fill: transparent !important; flex: none !important; }
  #report-paginas .sm-band, #report-paginas .sm-preset, #report-paginas .pg-item {
    cursor: pointer !important; font: inherit !important;
  }
  #report-paginas .sm-preset.active {
    background: var(--accent) !important; color: #fff !important; border-color: var(--accent) !important;
  }
  #report-paginas .sm-band.off { opacity: 0.38 !important; }
  tr:hover td { background: rgba(13, 148, 136, 0.06) !important; }
  th { background: var(--surface) !important; }
"""

combined = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Mamba Digital · Relatório SEO</title>
<style>
{gsc_style}
{traf_style}
{pag_style}
{bl_style}
{ia_style}
{pal_style}
{ml_style}
{LIGHT_THEME}
  .topnav {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(255, 255, 255, 0.92); backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border, #d5dee7);
    margin: -2rem -1.25rem 1.5rem; padding: 0.75rem 1.25rem;
  }}
  .topnav-inner {{
    max-width: 1180px; margin: 0 auto; display: flex; align-items: center;
    justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  }}
  .topnav-brand {{
    font-size: 0.75rem; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--accent, #0d9488); font-weight: 600;
  }}
  .topnav-links {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
  .topnav-link {{
    text-decoration: none; color: var(--muted, #5c6b7a); font-size: 0.88rem; font-weight: 600;
    padding: 0.45rem 0.9rem; border-radius: 10px; border: 1px solid var(--border, #d5dee7);
    background: var(--surface, #fff);
  }}
  .topnav-link:hover {{ color: var(--text, #1a2330); border-color: #b8c5d1; }}
  .topnav-link.active {{ background: var(--accent, #0d9488); color: #fff; border-color: var(--accent, #0d9488); }}
  .report {{ display: none; }}
  .report.active {{ display: block; }}
  .cross-link-wrap {{ max-width: 1180px; margin: 0 auto 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }}
  .cross-link {{
    display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.55rem 0.95rem;
    border-radius: 10px; border: 1px solid var(--border, #d5dee7); background: var(--surface2, #eef3f7);
    color: var(--accent, #0d9488); text-decoration: none; font-size: 0.88rem; font-weight: 600;
  }}
  .cross-link:hover {{ border-color: var(--accent, #0d9488); }}
  button.tab[data-view="focus"], #v-view-focus, #view-focus {{ display: none !important; }}
  button.tab[data-view="daily"], #v-view-daily, #view-daily {{ display: none !important; }}
  /* Mercado Livre oculto por agora */
  .topnav-link[data-report="ml"],
  .cross-link[data-report="ml"],
  #report-ml {{ display: none !important; }}
</style>
</head>
<body>
{nav}

<section class="report active" id="report-visitas">
  <div class="cross-link-wrap">
    <a class="cross-link" href="#report-ia-visitas" data-report="ia-visitas">Ir para IA Visitas →</a>
  </div>
  {gsc_body}
</section>

<section class="report" id="report-ia-visitas">
  <div class="cross-link-wrap">
    <a class="cross-link" href="#report-visitas" data-report="visitas">← Relatório Visitas</a>
    <a class="cross-link" href="#report-trafego" data-report="trafego">Ir para Tráfego Semrush →</a>
  </div>
  {ia_body}
</section>

<section class="report" id="report-trafego">
  <div class="cross-link-wrap">
    <a class="cross-link" href="#report-ia-visitas" data-report="ia-visitas">← IA Visitas</a>
    <a class="cross-link" href="#report-paginas" data-report="paginas">Ir para Páginas Semrush →</a>
  </div>
  {traf_body}
</section>

<section class="report" id="report-paginas">
  <div class="cross-link-wrap">
    <a class="cross-link" href="#report-trafego" data-report="trafego">← Tráfego Semrush</a>
    <a class="cross-link" href="#report-backlinks" data-report="backlinks">Ir para Backlinks →</a>
  </div>
  {pag_body}
</section>

<section class="report" id="report-backlinks">
  <div class="cross-link-wrap">
    <a class="cross-link" href="#report-paginas" data-report="paginas">← Páginas Semrush</a>
    <a class="cross-link" href="#report-palavras" data-report="palavras">Ir para Relatório Palavras →</a>
  </div>
  {bl_body}
</section>

<section class="report" id="report-palavras">
  <div class="cross-link-wrap">
    <a class="cross-link" href="#report-backlinks" data-report="backlinks">← Backlinks</a>
  </div>
  {pal_body}
</section>

<section class="report" id="report-ml">
  <div class="cross-link-wrap">
    <a class="cross-link" href="#report-visitas" data-report="visitas">← Relatório Visitas</a>
  </div>
  {ml_body}
</section>

<script>
(function() {{
  function showReport(name) {{
    document.querySelectorAll('.report').forEach(r => r.classList.remove('active'));
    document.querySelectorAll('.topnav-link').forEach(a => a.classList.remove('active'));
    const el = document.getElementById('report-' + name);
    if (el) el.classList.add('active');
    document.querySelectorAll('.topnav-link[data-report="' + name + '"]').forEach(a => a.classList.add('active'));
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }}
  function fromHash() {{
    const h = (location.hash || '#report-visitas').replace('#report-', '');
    const ok = ['palavras', 'visitas', 'ia-visitas', 'trafego', 'paginas', 'backlinks'];
    showReport(ok.includes(h) ? h : 'visitas');
  }}
  document.querySelectorAll('[data-report]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      const name = el.getAttribute('data-report');
      if (!name) return;
      e.preventDefault();
      location.hash = 'report-' + name;
      showReport(name);
    }});
  }});
  window.addEventListener('hashchange', fromHash);
  fromHash();
}})();
</script>

<script>
(function() {{
  const root = document.getElementById('report-visitas');
  if (!root) return;
  root.querySelectorAll('.tabs > .tab').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const tabs = btn.parentElement;
      tabs.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      root.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      btn.classList.add('active');
      const panel = root.querySelector('#v-view-' + btn.dataset.view);
      if (panel) panel.classList.add('active');
    }});
  }});
}})();
</script>

<script>
(function() {{
  const root = document.getElementById('report-backlinks');
  if (!root) return;
  const table = root.querySelector('#bl-table');
  const search = root.querySelector('#bl-search');
  const visibleEl = root.querySelector('#bl-visible');
  if (!table) return;
  const rows = Array.from(table.tBodies[0].querySelectorAll('tr'));
  let pageFilter = '';
  let dateFilter = '';
  function apply() {{
    const q = (search && search.value || '').trim().toLowerCase();
    let shown = 0;
    rows.forEach(tr => {{
      const okPage = !pageFilter || tr.dataset.page === pageFilter;
      const okDate = !dateFilter || tr.dataset.date === dateFilter;
      const okQ = !q || tr.textContent.toLowerCase().includes(q);
      const show = okPage && okDate && okQ;
      tr.classList.toggle('hidden', !show);
      if (show) {{
        shown += 1;
        const rank = tr.querySelector('.rank');
        if (rank) rank.textContent = String(shown);
      }}
    }});
    if (visibleEl) visibleEl.textContent = String(shown);
  }}
  root.querySelectorAll('.filter-chip').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const kind = btn.dataset.filter;
      const value = btn.dataset.value || '';
      root.querySelectorAll('.filter-chip[data-filter="' + kind + '"]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (kind === 'page') pageFilter = value;
      if (kind === 'date') dateFilter = value;
      apply();
    }});
  }});
  if (search) search.addEventListener('input', apply);
  apply();
}})();
</script>

<script>
(function() {{
  const root = document.getElementById('report-palavras');
  if (!root) return;
  root.querySelectorAll('.main-tab').forEach(btn => {{
    btn.addEventListener('click', () => {{
      root.querySelectorAll('.main-tab').forEach(t => t.classList.remove('active'));
      root.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      btn.classList.add('active');
      const el = root.querySelector('#p-view-' + btn.dataset.view);
      if (el) el.classList.add('active');
    }});
  }});
  root.querySelectorAll('.panel').forEach(panel => {{
    panel.querySelectorAll('.tab').forEach(btn => {{
      btn.addEventListener('click', () => {{
        panel.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        panel.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const el = panel.querySelector('#p-' + btn.dataset.tab);
        if (el) el.classList.add('active');
      }});
    }});
  }});
}})();
</script>

<script>
(function() {{
  const root = document.getElementById('report-ml');
  if (!root) return;
  const search = root.querySelector('#ml-search');
  const table = root.querySelector('#ml-ml-table') || root.querySelector('#ml-table');
  if (search && table) {{
    search.addEventListener('input', () => {{
      const q = search.value.trim().toLowerCase();
      table.querySelectorAll('tbody tr').forEach(tr => {{
        tr.style.display = (!q || tr.textContent.toLowerCase().includes(q)) ? '' : 'none';
      }});
    }});
  }}
  root.querySelectorAll('.page-toggle').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const id = btn.dataset.target; // e.g. p1
      const el = document.getElementById('ml-detail-' + id);
      if (!el) return;
      const open = el.hasAttribute('hidden');
      root.querySelectorAll('.detail').forEach(d => d.setAttribute('hidden', ''));
      if (open) {{
        el.removeAttribute('hidden');
        el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
      }}
    }});
  }});
  if (table) {{
    let sortCol = null, sortDir = 'desc';
    table.querySelectorAll('th.sortable').forEach(th => {{
      th.addEventListener('click', () => {{
        const col = +th.dataset.col;
        if (sortCol === col) sortDir = sortDir === 'desc' ? 'asc' : 'desc';
        else {{ sortCol = col; sortDir = 'desc'; }}
        table.querySelectorAll('th.sortable').forEach(h => h.classList.remove('asc', 'desc'));
        th.classList.add(sortDir);
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort((a, b) => {{
          if (col === 1) {{
            const av = a.querySelector('.page-toggle').textContent.toLowerCase();
            const bv = b.querySelector('.page-toggle').textContent.toLowerCase();
            return sortDir === 'asc' ? av.localeCompare(bv, 'pt-BR') : bv.localeCompare(av, 'pt-BR');
          }}
          const an = a.children[col].childNodes[0];
          const bn = b.children[col].childNodes[0];
          const av = parseFloat(String(an.textContent || '0').replace(/\\./g, '').replace(',', '.')) || 0;
          const bv = parseFloat(String(bn.textContent || '0').replace(/\\./g, '').replace(',', '.')) || 0;
          return sortDir === 'asc' ? av - bv : bv - av;
        }});
        rows.forEach((tr, i) => {{
          tr.querySelector('.rank').textContent = String(i + 1);
          tbody.appendChild(tr);
        }});
      }});
    }});
  }}
}})();
</script>
</body>
</html>
"""

OUT.write_text(combined, encoding="utf-8")
OUT_DOCS.parent.mkdir(parents=True, exist_ok=True)
OUT_DOCS.write_text(combined, encoding="utf-8")
print("Wrote", OUT)
print("Wrote", OUT_DOCS)
print("Size MB:", round(OUT.stat().st_size / 1024 / 1024, 2))
