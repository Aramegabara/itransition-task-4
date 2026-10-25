import html

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from task_4 import analyze_store, STORES


def plot_daily_revenue(daily, store, path):
    fig, ax = plt.subplots(figsize=(11, 3.6))

    ax.plot(list(daily.index), list(daily.values),
            linewidth=1.2, color='#2563eb')
    ax.set_ylabel('USD')

    ax.grid(axis='y', color='#e5e7eb', linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color('#d1d5db')
    ax.tick_params(colors='#6b7280', labelsize=9)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def build_panel(result, idx):
    top_rows = '\n'.join(
        f'<tr><td>{day:%Y-%m-%d}</td><td class="num">${value:,.2f}</td></tr>'
        for day, value in result['top_five'].items())

    authors = html.escape(', '.join(result['top_authors'].index[0]))
    buyer_ids = ', '.join(str(i) for i in result['best_buyer'])
    buyer_name = html.escape(str(result['best_name']))

    hidden = '' if idx == 0 else 'hidden'
    return f'''
<section class="panel" id="panel-{idx}" {hidden}>
  <div class="cards">
    <div class="card">
      <div class="label">Unique users</div>
      <div class="value">{result['unique_users']:,}</div>
    </div>
    <div class="card">
      <div class="label">Unique author sets</div>
      <div class="value">{result['author_sets']:,}</div>
    </div>
    <div class="card">
      <div class="label">Most popular author(s)</div>
      <div class="value sm">{authors}</div>
    </div>
    <div class="card">
      <div class="label">Best buyer</div>
      <div class="value sm">[{buyer_ids}]</div>
      <div class="sub">{buyer_name}</div>
    </div>
  </div>

  <div class="grid">
    <div class="block">
      <h3>Top 5 days by revenue</h3>
      <table>
        <thead><tr><th>Date</th><th class="num">Revenue</th></tr></thead>
        <tbody>{top_rows}</tbody>
      </table>
    </div>
    <div class="block">
      <h3>Daily revenue</h3>
      <img src="revenue_{result['store']}.png" alt="Daily revenue {result['store']}">
    </div>
  </div>
</section>'''


def build_page(results):
    tabs = '\n    '.join(
        f'<button class="tab{" active" if i == 0 else ""}" '
        f'data-i="{i}">{r["store"]}</button>'
        for i, r in enumerate(results))
    panels = '\n'.join(build_panel(r, i) for i, r in enumerate(results))

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bookstore Analytics</title>
<style>
:root {{ --bg:#f7f8fa; --surface:#fff; --ink:#111827; --muted:#6b7280;
        --line:#e5e7eb; --accent:#2563eb; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
header {{ background:var(--surface); border-bottom:1px solid var(--line);
  padding:20px 28px; }}
h1 {{ margin:0; font-size:20px; }}
.meta {{ color:var(--muted); font-size:13px; margin-top:4px; }}
main {{ max-width:1180px; margin:0 auto; padding:24px 20px 60px; }}
.tabs {{ display:flex; gap:6px; margin-bottom:20px; flex-wrap:wrap; }}
.tab {{ padding:8px 16px; border:1px solid var(--line); background:var(--surface);
  border-radius:6px; cursor:pointer; font-size:14px; color:var(--muted); }}
.tab.active {{ background:var(--accent); border-color:var(--accent); color:#fff; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:14px; margin-bottom:22px; }}
.card {{ background:var(--surface); border:1px solid var(--line);
  border-radius:10px; padding:16px 18px; }}
.label {{ color:var(--muted); font-size:12px; text-transform:uppercase;
  letter-spacing:.04em; margin-bottom:8px; }}
.value {{ font-size:28px; font-weight:600; }}
.value.sm {{ font-size:16px; font-weight:600; line-height:1.35; }}
.sub {{ color:var(--muted); font-size:13px; margin-top:6px; }}
.grid {{ display:grid; grid-template-columns:320px 1fr; gap:18px; }}
@media (max-width:860px) {{ .grid {{ grid-template-columns:1fr; }} }}
.block {{ background:var(--surface); border:1px solid var(--line);
  border-radius:10px; padding:18px; }}
.block h3 {{ margin:0 0 14px; font-size:14px; color:var(--muted);
  text-transform:uppercase; letter-spacing:.04em; font-weight:600; }}
table {{ width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }}
th, td {{ padding:9px 6px; border-bottom:1px solid var(--line); text-align:left; }}
th {{ font-size:12px; color:var(--muted); font-weight:600; }}
td.num, th.num {{ text-align:right; }}
tbody tr:last-child td {{ border-bottom:none; }}
img {{ width:100%; display:block; }}
</style>
</head>
<body>
<header>
  <h1>Bookstore Analytics</h1>
  <div class="meta">Task 4 &middot; 5 stores &middot; Artur Heraskov</div>
</header>
<main>
  <div class="tabs">
    {tabs}
  </div>
  {panels}
</main>
<script>
const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
tabs.forEach(tab => tab.addEventListener('click', () => {{
  tabs.forEach(t => t.classList.remove('active'));
  tab.classList.add('active');
  panels.forEach((panel, i) => {{
    panel.hidden = (i !== Number(tab.dataset.i));
  }});
}}));
</script>
</body>
</html>'''


if __name__ == '__main__':
    results = []
    for store in STORES:
        print(f'processing {store}...')
        result = analyze_store(store)
        plot_daily_revenue(result['daily'], store, f'revenue_{store}.png')
        results.append(result)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(build_page(results))

    print(f'\ndone: index.html + {len(results)} PNG')
