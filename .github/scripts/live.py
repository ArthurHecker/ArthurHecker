"""Artes ao vivo do perfil, geradas pelo GitHub Actions (.github/workflows/vivo.yml).

    python .github/scripts/live.py <pasta-de-saída>

- monitor.svg: o "monitor do servidor" do site com dados de verdade: o cooler gira
  conforme os commits dos últimos 30 dias, números do GitHub, situação dos sites
  (resposta HTTP e latência medidas daqui) e linguagens dos repositórios.
- gravura.svg: o calendário de contribuições desenhado como gravura: cada linha é
  uma semana e a espessura, a quantidade de commits do dia.

Sem dados (rede fora, limite da API), cada parte mostra "sem leitura" em vez de
inventar números.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from svgkit import (BOOK, CREAM, GOLD, GREY, GREY2, INK, LINE, PAPER, PAPER2, RED, Svg,  # noqa: E402
                    blink, clamp, css_anim, engrave_v, f1, panel)

USER = os.environ.get('PROFILE_USER', 'ArthurHecker')
TOKEN = os.environ.get('GITHUB_TOKEN', '')
UA = 'profile-readme-live/1.0'
SITES = [
    ('Hub 3D', 'https://arthurhecker.space/'),
    ('Pyro', 'https://pyro.arthurhecker.space/'),
    ('WebCEI', 'https://univesp.arthurhecker.space/'),
    ('Formigas (beta)', 'https://game.arthurhecker.space/'),
]
BRT = dt.timezone(dt.timedelta(hours=-3))
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
DIAS = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']


def get(url, api=False, timeout=20):
    h = {'User-Agent': UA}
    if api:
        h['Accept'] = 'application/vnd.github+json'
        if TOKEN:
            h['Authorization'] = f'Bearer {TOKEN}'
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def fmt(n):
    return f'{n:,}'.replace(',', '.')


# ------------------------------------------------------------------ dados

def contributions():
    """Calendário público (o mesmo do perfil): [(data, nível 0-4, quantidade)]."""
    html = get(f'https://github.com/users/{USER}/contributions')
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        txt = m.group(2).strip()
        n = re.match(r'([\d,]+) contribution', txt)
        tips[m.group(1)] = int(n.group(1).replace(',', '')) if n else 0
    days = []
    for m in re.finditer(r'<td[^>]*ContributionCalendar-day[^>]*>', html):
        td = m.group(0)
        d = re.search(r'data-date="([\d-]+)"', td)
        lv = re.search(r'data-level="(\d)"', td)
        i = re.search(r'id="([^"]+)"', td)
        if d and lv:
            days.append((dt.date.fromisoformat(d.group(1)), int(lv.group(1)), tips.get(i.group(1) if i else '', 0)))
    days.sort()
    return days


def github_stats():
    u = json.loads(get(f'https://api.github.com/users/{USER}', api=True))
    repos = json.loads(get(f'https://api.github.com/users/{USER}/repos?per_page=100&type=owner', api=True))
    langs = {}
    for r in repos:
        if r.get('fork'):
            continue
        try:
            for k, v in json.loads(get(r['languages_url'], api=True)).items():
                langs[k] = langs.get(k, 0) + v
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass
    return {
        'followers': u.get('followers', 0),
        'repos': u.get('public_repos', len(repos)),
        'stars': sum(r.get('stargazers_count', 0) for r in repos),
        'langs': sorted(langs.items(), key=lambda kv: -kv[1]),
    }


def ping(url):
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA}, method='GET')
        with urllib.request.urlopen(req, timeout=15) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:  # noqa: BLE001 — qualquer falha de rede = fora do ar
        return None, None
    ms = (time.perf_counter() - t0) * 1000
    # 401/403/404 também provam que o servidor respondeu; 5xx (inclusive o 52x da
    # Cloudflare quando o túnel cai) conta como fora do ar
    return code < 500, ms


def streaks(days):
    today = days[-1][0] if days else dt.date.today()
    cur = best = run = 0
    for d, _lv, n in days:
        run = run + 1 if n > 0 else 0
        best = max(best, run)
    # sequência atual: termina hoje ou ontem (o dia de hoje pode ainda não ter commits)
    rev = list(reversed(days))
    if rev and rev[0][2] == 0 and rev[0][0] == today:
        rev = rev[1:]
    for _d, _lv, n in rev:
        if n > 0:
            cur += 1
        else:
            break
    return cur, best


# ------------------------------------------------------------------ monitor

def fan(cx, cy, r, dur):
    blades = []
    for i in range(7):
        a = i * 360 / 7
        blades.append(f'<path transform="rotate({a:.1f})" d="M0 -{r * .2:.1f}C{r * .32:.1f} -{r * .3:.1f} {r * .5:.1f} -{r * .62:.1f} {r * .34:.1f} -{r * .9:.1f}'
                      f'C{r * .12:.1f} -{r * .78:.1f} -{r * .06:.1f} -{r * .5:.1f} 0 -{r * .2:.1f}Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>')
    return blades, dur


def monitor(out, days, gh, sites):
    W, H = 860, 452
    now = dt.datetime.now(BRT)
    s = Svg(W, H, 'Monitor ao vivo do Arthur',
            'Cooler que gira conforme os commits dos últimos 30 dias, números do GitHub, situação dos sites e linguagens.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    pulse = css_anim(s, '0%,100%{opacity:1}50%{opacity:.2}', 1.4)
    s.add(f'<circle class="{pulse}" cx="28" cy="31" r="5" fill="{RED}"/>',
          s.text(40, 35, 'AO VIVO · ATUALIZADO PELO GITHUB ACTIONS', 'sans8', 10.5, RED, ls=2.4),
          s.text(W - 30, 35, now.strftime('%d/%m/%Y · %H:%M') + ' (Brasília)', 'mono', 19, GREY, 'end'))

    # cooler
    last30 = sum(n for d, _l, n in days if d > (days[-1][0] - dt.timedelta(days=30))) if days else None
    if last30 is None:
        rpm, mode = 800, 'SEM LEITURA'
    else:
        rpm = int(min(6000, 800 + last30 * 120))
        mode = 'MÁXIMO' if rpm >= 6000 else 'AUTOMÁTICO'
    dur = clamp(1.4 * 800 / rpm, 0.16, 1.4)
    cx, cy, r = 172, 176, 104
    s.add(f'<rect x="{cx - r - 16}" y="{cy - r - 16}" width="{2 * r + 32}" height="{2 * r + 32}" rx="18" fill="{INK}"/>',
          *[f'<circle cx="{x}" cy="{y}" r="6" fill="{GREY}" stroke="{PAPER}" stroke-width="1.2"/>'
            for x in (cx - r - 3, cx + r + 3) for y in (cy - r - 3, cy + r + 3)],
          f'<circle cx="{cx}" cy="{cy}" r="{r + 2}" fill="#1b1b1e" stroke="{GREY}" stroke-width="1.5"/>')
    spin = css_anim(s, '0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}', round(dur, 3), timing='linear')
    blades, _ = fan(cx, cy, r, dur)
    s.add(f'<g transform="translate({cx} {cy})"><g class="{spin}">{"".join(blades)}</g>'
          f'<circle r="{r * .22:.1f}" fill="{RED}" stroke="{INK}" stroke-width="2"/>'
          f'<circle r="{r * .08:.1f}" fill="{INK}"/></g>',
          f'<path d="M{cx - r} {cy}H{cx + r}M{cx} {cy - r}V{cy + r}" stroke="{GREY}" stroke-width="1" opacity=".5"/>')
    s.add(s.text(cx, 330, fmt(rpm), 'mono', 46, INK, 'middle'),
          s.text(cx, 352, 'RPM', 'sans8', 10.5, GREY, 'middle', ls=3))
    # modos (como no site)
    mx = 36
    for m in ('AUTOMÁTICO', 'MÁXIMO'):
        w = BOOK.width('sans8', m, 9) + 1.4 * (len(m) - 1) + 20
        on = m == mode
        s.add(f'<rect x="{f1(mx)}" y="368" width="{f1(w)}" height="24" fill="{INK if on else PAPER}" stroke="{INK}" stroke-width="1.3"/>',
              s.text(mx + w / 2, 384, m, 'sans8', 9, PAPER if on else INK, 'middle', ls=1.4))
        mx += w + 8
    s.add(s.text(36, 416, '1 commit nos últimos 30 dias = +120 RPM', 'hand', 16.5, GREY))

    # números
    total = sum(n for _d, _l, n in days) if days else None
    cur, best = streaks(days) if days else (None, None)
    tiles = [
        ('CONTRIBUIÇÕES NO ANO', total), ('NOS ÚLTIMOS 30 DIAS', last30), ('SEQUÊNCIA ATUAL', cur),
        ('MAIOR SEQUÊNCIA', best), ('REPOSITÓRIOS', gh and gh['repos']), ('ESTRELAS', gh and gh['stars']),
    ]
    tx0, ty0, tw, th = 366, 52, 148, 70
    for i, (lab, val) in enumerate(tiles):
        x = tx0 + (i % 3) * (tw + 9)
        y = ty0 + (i // 3) * (th + 9)
        s.add(f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" fill="{PAPER2}" stroke="{INK}" stroke-width="1.3"/>',
              s.text(x + 12, y + 40, '—' if val is None else fmt(val), 'serif', 30, RED if i == 0 else INK),
              s.text(x + 12, y + 58, lab, 'sans8', 8, GREY, ls=1))
    if cur is not None:
        s.add(s.text(tx0 + 2 * (tw + 9) + tw - 10, ty0 + 40, 'dias', 'hand', 15, GREY2, 'end'))
        s.add(s.text(tx0 + tw - 10, ty0 + th + 9 + 40, 'dias', 'hand', 15, GREY2, 'end'))

    # sites
    sy = 228
    s.add(s.text(tx0, sy, 'SITES NO AR', 'sans8', 10, RED, ls=2.4),
          f'<path d="M{tx0} {sy + 8}H{W - 30}" stroke="{LINE}" stroke-width="1.2"/>')
    for i, (name, url, (ok, ms)) in enumerate(sites):
        y = sy + 32 + i * 25
        host = url.split('//')[1].rstrip('/')
        if ok is None:
            dot, st, col = GREY2, 'SEM RESPOSTA', GREY
        elif ok:
            dot, st, col = INK, f'NO AR · {ms:.0f} ms', INK
        else:
            dot, st, col = RED, 'FORA DO AR', RED
        cl = f' class="{pulse}"' if ok else ''
        s.add(f'<circle{cl} cx="{tx0 + 6}" cy="{y - 5}" r="5" fill="{dot}"/>',
              s.text(tx0 + 20, y, name, 'sans7', 14, INK),
              s.text(tx0 + 150, y, host, 'mono', 18, GREY),
              s.text(W - 30, y, st, 'sans8', 9.5, col, 'end', ls=1.4))

    # linguagens
    ly = 362
    s.add(s.text(tx0, ly, 'LINGUAGENS DOS REPOSITÓRIOS', 'sans8', 10, RED, ls=2.4))
    langs = (gh or {}).get('langs') or []
    tot = sum(v for _k, v in langs) or 1
    top = langs[:5]
    rest = tot - sum(v for _k, v in top)
    if rest > 0:
        top.append(('Outras', rest))
    cols = [INK, RED, GOLD, GREY, GREY2, LINE]
    bx, bw = tx0, W - 30 - tx0
    if langs:
        x = bx
        for (k, v), c in zip(top, cols):
            w = bw * v / tot
            s.add(f'<rect x="{f1(x)}" y="{ly + 10}" width="{f1(max(w, 1.5))}" height="14" fill="{c}"/>')
            x += w
        s.add(f'<rect x="{bx}" y="{ly + 10}" width="{bw}" height="14" fill="none" stroke="{INK}" stroke-width="1.3"/>')
        lx, lyy = bx, ly + 46
        for (k, v), c in zip(top, cols):
            pc = v / tot * 100
            lab = f'{k} {pc:.0f}%' if pc >= 0.5 else f'{k} <1%'
            w = BOOK.width('mono', lab, 17) + 26
            if lx + w > W - 30:
                lx, lyy = bx, lyy + 22
            s.add(f'<rect x="{f1(lx)}" y="{lyy - 11}" width="11" height="11" fill="{c}" stroke="{INK}" stroke-width="1"/>',
                  s.text(lx + 16, lyy, lab, 'mono', 17, INK))
            lx += w
    else:
        s.add(s.text(bx, ly + 34, 'sem leitura agora — volta na próxima atualização', 'hand', 17, GREY))
    with open(os.path.join(out, 'monitor.svg'), 'w', encoding='utf-8') as fh:
        fh.write(s.render())


# ------------------------------------------------------------------ gravura das contribuições

def gravura(out, days):
    W, H = 860, 268
    s = Svg(W, H, 'Gravura das contribuições',
            'O calendário de contribuições do último ano desenhado como gravura: cada linha vertical é uma semana '
            'e a espessura mostra quantos commits houve em cada dia.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    s.add(s.text(24, 36, 'GRAVURA DAS CONTRIBUIÇÕES', 'sans8', 10.5, RED, ls=2.6),
          s.text(W - 30, 36, 'cada linha é uma semana; a espessura, os meus commits', 'hand', 18, GREY, 'end'))
    x0, x1, y0, y1 = 70, 826, 58, 200
    if not days:
        s.add(s.text(W / 2, 140, 'sem leitura agora — volta na próxima atualização', 'hand', 22, GREY, 'middle'))
    else:
        # agrupa por semana (domingo a sábado, como no GitHub)
        weeks = []
        for d, _lv, n in days:
            wd = (d.weekday() + 1) % 7  # domingo = 0
            if wd == 0 or not weeks:
                weeks.append([None] * 7)
            weeks[-1][wd] = (d, n)
        mx = max(n for _d, _l, n in days) or 1
        nw = len(weeks)
        gap = (x1 - x0) / max(1, nw - 1)
        rowh = (y1 - y0) / 6

        def amount(wi, yy):
            # interpolação suave entre os dias da semana
            f = (yy - y0) / rowh
            i0 = int(math.floor(f))
            t = f - i0
            vals = []
            for i in (i0, i0 + 1):
                c = weeks[wi][i] if 0 <= i < 7 and wi < nw else None
                vals.append(math.sqrt(c[1] / mx) if c else 0.0)
            k = (1 - math.cos(t * math.pi)) / 2
            return vals[0] * (1 - k) + vals[1] * k
        paths = []
        for wi in range(nw):
            x = x0 + wi * gap
            dfun = (lambda wi_: (lambda xx, yy: 0.07 + 0.93 * amount(wi_, yy)))(wi)
            paths.append(engrave_v(x, x + 0.01, y0 - 6, y1 + 6, 100, dfun, min(gap * 0.92, 13), dy=4.5,
                                   wave=lambda xx, yy: 1.1 * math.sin(yy / 15 + xx / 40)))
        sway = css_anim(s, '0%{transform:translateX(-1.5px)}100%{transform:translateX(1.5px)}', 6, extra='infinite alternate')
        reveal = css_anim(s, '0%{transform:translateX(0)}100%{transform:translateX(780px)}', 2.6,
                          timing='cubic-bezier(.5,0,.3,1)', extra='1 both')
        s.css.append(f'.{reveal}{{animation-delay:.3s}}')
        s.defs.append(f'<clipPath id="gf"><rect x="{x0 - 14}" y="{y0 - 12}" width="{x1 - x0 + 28}" height="{y1 - y0 + 24}"/></clipPath>')
        s.add(f'<g clip-path="url(#gf)"><g class="{sway}"><path d="{"".join(paths)}" fill="{INK}"/></g>'
              f'<rect class="{reveal}" x="{x0 - 14}" y="{y0 - 12}" width="{x1 - x0 + 28}" height="{y1 - y0 + 24}" fill="{PAPER}"/></g>')
        # melhor dia em vermelho
        bd, bn = max(((d, n) for d, _l, n in days), key=lambda t: (t[1], t[0]))
        for wi, wk in enumerate(weeks):
            for di, c in enumerate(wk):
                if c and c[0] == bd:
                    bx, by = x0 + wi * gap, y0 + di * rowh
                    bl = blink(s, 1.2)
                    s.add(f'<circle cx="{f1(bx)}" cy="{f1(by)}" r="9" fill="none" stroke="{RED}" stroke-width="2.4"/>',
                          f'<circle class="{bl}" cx="{f1(bx)}" cy="{f1(by)}" r="3.5" fill="{RED}"/>')
        # dias e meses
        for di, lab in ((1, 'seg'), (3, 'qua'), (5, 'sex')):
            s.add(s.text(28, y0 + di * rowh + 5, lab, 'mono', 16, GREY2))
        last_m = None
        for wi, wk in enumerate(weeks):
            first = next((c[0] for c in wk if c), None)
            if first and first.month != last_m and first.day <= 7:
                s.add(s.text(x0 + wi * gap - 3, y1 + 28, MESES[first.month - 1], 'mono', 17, GREY))
                last_m = first.month
        # rodapé
        total = sum(n for _d, _l, n in days)
        wd_tot = [0] * 7
        for d, _l, n in days:
            wd_tot[d.weekday()] += n
        fav = DIAS[max(range(7), key=lambda i: wd_tot[i])]
        s.add(s.rich(24, H - 22, [(f'{fmt(total)} contribuições no último ano', INK), ('  ·  ', GREY2),
                                  (f'melhor dia: {bn} em {bd.day:02d}/{bd.month:02d}', RED), ('  ·  ', GREY2),
                                  (f'dia favorito: {fav}', INK)], font='mono', size=19))
    with open(os.path.join(out, 'gravura.svg'), 'w', encoding='utf-8') as fh:
        fh.write(s.render())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'dist'
    os.makedirs(out, exist_ok=True)
    try:
        days = contributions()
    except Exception as e:  # noqa: BLE001
        print('contribuições: sem leitura:', e)
        days = []
    try:
        gh = github_stats()
    except Exception as e:  # noqa: BLE001
        print('API do GitHub: sem leitura:', e)
        gh = None
    sites = [(n, u, ping(u)) for n, u in SITES]
    for n, _u, (ok, ms) in sites:
        print(f'{n:16s} {"no ar" if ok else "fora" if ok is False else "sem resposta"} {ms or 0:.0f} ms')
    print('dias:', len(days), 'total:', sum(n for _d, _l, n in days), 'gh:', gh and {k: v for k, v in gh.items() if k != 'langs'})
    monitor(out, days, gh, sites)
    gravura(out, days)


if __name__ == '__main__':
    main()
