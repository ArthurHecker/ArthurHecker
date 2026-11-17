"""Artes com dados do GitHub (painel com cooler, gravura, cobra) e a linha do tempo
dos estudos. Geradas junto com as outras por tools/build.py, no momento em que o
perfil é atualizado: cada arte diz de que dia são os números.

Sem leitura (rede fora, limite da API), a arte mostra "sem leitura" em vez de
inventar números.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import urllib.error
import urllib.request

from svgkit import (BOOK, GOLD, GREY, GREY2, INK, LINE, PAPER, PAPER2, RED, Svg,
                    blink, clamp, css_anim, engrave_v, f1, panel)

USER = os.environ.get('PROFILE_USER', 'ArthurHecker')
TOKEN = os.environ.get('GITHUB_TOKEN', '')
UA = 'profile-readme/1.0'
BRT = dt.timezone(dt.timedelta(hours=-3))
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
DIAS = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']


def get(url, api=False, timeout=20):
    h = {'User-Agent': UA}
    if api:
        h['Accept'] = 'application/vnd.github+json'
        if TOKEN:
            h['Authorization'] = f'Bearer {TOKEN}'
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def fmt(n):
    return f'{n:,}'.replace(',', '.')


# ------------------------------------------------------------------ dados

def contributions():
    """Calendário público do perfil: [(data, nível 0-4, quantidade)]."""
    html = get(f'https://github.com/users/{USER}/contributions')
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        n = re.match(r'([\d,]+) contribution', m.group(2).strip())
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
        'repos': u.get('public_repos', len(repos)),
        'stars': sum(r.get('stargazers_count', 0) for r in repos),
        'langs': sorted(langs.items(), key=lambda kv: -kv[1]),
    }


def streaks(days):
    today = days[-1][0]
    cur = best = run = 0
    for _d, _lv, n in days:
        run = run + 1 if n > 0 else 0
        best = max(best, run)
    rev = list(reversed(days))
    if rev and rev[0][2] == 0 and rev[0][0] == today:
        rev = rev[1:]  # hoje pode ainda não ter commit
    for _d, _lv, n in rev:
        if n == 0:
            break
        cur += 1
    return cur, best


def weeks_of(days):
    """Agrupa por semana (domingo a sábado, como no GitHub): [[(data, n) | None] * 7]."""
    weeks = []
    for d, _lv, n in days:
        wd = (d.weekday() + 1) % 7
        if wd == 0 or not weeks:
            weeks.append([None] * 7)
        weeks[-1][wd] = (d, n)
    return weeks


def stamp():
    now = dt.datetime.now(BRT)
    return f'{now.day:02d}/{now.month:02d}/{now.year}'


def write(out, name, svg):
    data = svg.render()
    with open(os.path.join(out, name), 'w', encoding='utf-8') as fh:
        fh.write(data)
    print(f'{name:28s} {len(data) / 1024:7.1f} KB')


# ------------------------------------------------------------------ painel com cooler

def painel(out, days, gh):
    W, H = 860, 336
    s = Svg(W, H, 'Painel do Arthur',
            'Um cooler que gira mais rápido quanto mais commits houve nos últimos 30 dias, '
            'contribuições no ano, nos últimos 30 dias, a sequência atual e as linguagens dos repositórios.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    s.add(s.text(24, 35, 'PAINEL', 'sans8', 10.5, RED, ls=2.6),
          s.text(W - 30, 35, f'dados de {stamp()}', 'hand', 18, GREY, 'end'))

    last30 = sum(n for d, _l, n in days if d > days[-1][0] - dt.timedelta(days=30)) if days else None
    rpm = 800 if last30 is None else int(min(6000, 800 + last30 * 120))
    dur = clamp(1.4 * 800 / rpm, 0.18, 1.4)
    cx, cy, r = 160, 158, 88
    s.add(f'<rect x="{cx - r - 14}" y="{cy - r - 14}" width="{2 * r + 28}" height="{2 * r + 28}" rx="16" fill="{INK}"/>',
          *[f'<circle cx="{x}" cy="{y}" r="5.5" fill="{GREY}" stroke="{PAPER}" stroke-width="1.2"/>'
            for x in (cx - r - 2, cx + r + 2) for y in (cy - r - 2, cy + r + 2)],
          f'<circle cx="{cx}" cy="{cy}" r="{r + 2}" fill="#1b1b1e" stroke="{GREY}" stroke-width="1.5"/>')
    spin = css_anim(s, '0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}', round(dur, 3), timing='linear')
    blades = ''.join(
        f'<path transform="rotate({i * 360 / 7:.1f})" d="M0 -{r * .2:.1f}C{r * .32:.1f} -{r * .3:.1f} {r * .5:.1f} -{r * .62:.1f} '
        f'{r * .34:.1f} -{r * .9:.1f}C{r * .12:.1f} -{r * .78:.1f} -{r * .06:.1f} -{r * .5:.1f} 0 -{r * .2:.1f}Z" '
        f'fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>' for i in range(7))
    s.add(f'<g transform="translate({cx} {cy})"><g class="{spin}">{blades}</g>'
          f'<circle r="{r * .22:.1f}" fill="{RED}" stroke="{INK}" stroke-width="2"/><circle r="{r * .08:.1f}" fill="{INK}"/></g>')
    s.add(s.rich(cx, 296, [(fmt(rpm), INK), (' RPM', GREY)], font='mono', size=34, anchor='middle'),
          s.text(cx, 318, '+120 RPM por commit nos últimos 30 dias', 'hand', 15.5, GREY, 'middle'))

    total = sum(n for _d, _l, n in days) if days else None
    cur = streaks(days)[0] if days else None
    tiles = [('CONTRIBUIÇÕES NO ANO', total, ''), ('ÚLTIMOS 30 DIAS', last30, ''), ('SEQUÊNCIA ATUAL', cur, 'dias')]
    tx0, ty0, tw, th = 300, 60, 172, 84
    for i, (lab, val, unit) in enumerate(tiles):
        x = tx0 + i * (tw + 9)
        s.add(f'<rect x="{x}" y="{ty0}" width="{tw}" height="{th}" fill="{PAPER2}" stroke="{INK}" stroke-width="1.3"/>',
              s.text(x + 12, ty0 + 48, '—' if val is None else fmt(val), 'serif', 34, RED if i == 0 else INK),
              s.text(x + 12, ty0 + 70, lab, 'sans8', 8.5, GREY, ls=1.2))
        if unit and val is not None:
            s.add(s.text(x + tw - 10, ty0 + 48, unit, 'hand', 16, GREY2, 'end'))

    ly = 196
    s.add(s.text(tx0, ly, 'LINGUAGENS DOS REPOSITÓRIOS', 'sans8', 10, RED, ls=2.4))
    langs = list((gh or {}).get('langs') or [])
    tot = sum(v for _k, v in langs) or 1
    top = langs[:5]
    rest = tot - sum(v for _k, v in top)
    if rest > 0:
        top.append(('Outras', rest))
    cols = [INK, RED, GOLD, GREY, GREY2, LINE]
    bx, bw = tx0, W - 30 - tx0
    if langs:
        grow = css_anim(s, '0%{transform:scaleX(0)}100%{transform:scaleX(1)}', 1.6,
                        timing='cubic-bezier(.5,0,.2,1)', extra='1 both', origin='left center')
        s.css.append(f'.{grow}{{animation-delay:.3s}}')
        x = bx
        bars = []
        for (k, v), c in zip(top, cols):
            w = bw * v / tot
            bars.append(f'<rect x="{f1(x)}" y="{ly + 12}" width="{f1(max(w, 1.5))}" height="18" fill="{c}"/>')
            x += w
        s.add(f'<g class="{grow}">{"".join(bars)}</g>',
              f'<rect x="{bx}" y="{ly + 12}" width="{bw}" height="18" fill="none" stroke="{INK}" stroke-width="1.3"/>')
        lx, lyy = bx, ly + 56
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
        s.add(s.text(bx, ly + 38, 'sem leitura agora', 'hand', 18, GREY))
    write(out, 'painel.svg', s)


# ------------------------------------------------------------------ gravura das contribuições

def gravura(out, days):
    W, H = 860, 268
    s = Svg(W, H, 'Gravura das contribuições',
            'O calendário de contribuições do último ano desenhado como gravura: cada linha vertical é uma semana '
            'e a espessura mostra quantos commits houve em cada dia.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    s.add(s.text(24, 36, 'GRAVURA DAS CONTRIBUIÇÕES', 'sans8', 10.5, RED, ls=2.6),
          s.text(W - 30, 36, 'cada linha é uma semana; a espessura, os commits', 'hand', 18, GREY, 'end'))
    x0, x1, y0, y1 = 70, 826, 58, 200
    if not days:
        s.add(s.text(W / 2, 140, 'sem leitura agora', 'hand', 22, GREY, 'middle'))
        write(out, 'gravura.svg', s)
        return
    weeks = weeks_of(days)
    mx = max(n for _d, _l, n in days) or 1
    nw = len(weeks)
    gap = (x1 - x0) / max(1, nw - 1)
    rowh = (y1 - y0) / 6

    def amount(wi, yy):
        f = (yy - y0) / rowh
        i0 = int(math.floor(f))
        t = f - i0
        vals = []
        for i in (i0, i0 + 1):
            c = weeks[wi][i] if 0 <= i < 7 else None
            vals.append(math.sqrt(c[1] / mx) if c else 0.0)
        k = (1 - math.cos(t * math.pi)) / 2
        return vals[0] * (1 - k) + vals[1] * k
    paths = []
    for wi in range(nw):
        x = x0 + wi * gap
        dfun = (lambda w_: (lambda xx, yy: 0.07 + 0.93 * amount(w_, yy)))(wi)
        paths.append(engrave_v(x, x + 0.01, y0 - 6, y1 + 6, 100, dfun, min(gap * 0.92, 13), dy=4.5,
                               wave=lambda xx, yy: 1.1 * math.sin(yy / 15 + xx / 40)))
    sway = css_anim(s, '0%{transform:translateX(-1.5px)}100%{transform:translateX(1.5px)}', 6, extra='infinite alternate')
    reveal = css_anim(s, '0%{transform:translateX(0)}100%{transform:translateX(780px)}', 2.6,
                      timing='cubic-bezier(.5,0,.3,1)', extra='1 both')
    s.css.append(f'.{reveal}{{animation-delay:.3s}}')
    s.defs.append(f'<clipPath id="gf"><rect x="{x0 - 14}" y="{y0 - 12}" width="{x1 - x0 + 28}" height="{y1 - y0 + 24}"/></clipPath>')
    s.add(f'<g clip-path="url(#gf)"><g class="{sway}"><path d="{"".join(paths)}" fill="{INK}"/></g>'
          f'<rect class="{reveal}" x="{x0 - 14}" y="{y0 - 12}" width="{x1 - x0 + 28}" height="{y1 - y0 + 24}" fill="{PAPER}"/></g>')
    bd, bn = max(((d, n) for d, _l, n in days), key=lambda t: (t[1], t[0]))
    for wi, wk in enumerate(weeks):
        for di, c in enumerate(wk):
            if c and c[0] == bd:
                bx, by = x0 + wi * gap, y0 + di * rowh
                bl = blink(s, 1.2)
                s.add(f'<circle cx="{f1(bx)}" cy="{f1(by)}" r="9" fill="none" stroke="{RED}" stroke-width="2.4"/>',
                      f'<circle class="{bl}" cx="{f1(bx)}" cy="{f1(by)}" r="3.5" fill="{RED}"/>')
    for di, lab in ((1, 'seg'), (3, 'qua'), (5, 'sex')):
        s.add(s.text(28, y0 + di * rowh + 5, lab, 'mono', 16, GREY2))
    last_m = None
    for wi, wk in enumerate(weeks):
        first = next((c[0] for c in wk if c), None)
        if first and first.month != last_m and first.day <= 7:
            s.add(s.text(x0 + wi * gap - 3, y1 + 28, MESES[first.month - 1], 'mono', 17, GREY))
            last_m = first.month
    total = sum(n for _d, _l, n in days)
    wd_tot = [0] * 7
    for d, _l, n in days:
        wd_tot[d.weekday()] += n
    fav = DIAS[max(range(7), key=lambda i: wd_tot[i])]
    s.add(s.rich(24, H - 22, [(f'{fmt(total)} contribuições no último ano', INK), ('  ·  ', GREY2),
                              (f'melhor dia: {bn} em {bd.day:02d}/{bd.month:02d}', RED), ('  ·  ', GREY2),
                              (f'dia favorito: {fav}', INK)], font='mono', size=19))
    write(out, 'gravura.svg', s)


# ------------------------------------------------------------------ cobra

def cobra(out, days):
    """Uma cobra vermelha percorre o calendário (coluna por coluna, em zigue-zague)
    e come os dias; no fim, o calendário volta e ela recomeça."""
    W, H = 860, 236
    s = Svg(W, H, 'A cobra das contribuições',
            'Uma cobra vermelha percorre o calendário de contribuições em zigue-zague e come os dias, um por um.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    s.add(s.text(24, 36, 'A COBRA DAS CONTRIBUIÇÕES', 'sans8', 10.5, RED, ls=2.6),
          s.text(W - 30, 36, 'cada ponto é um dia; quanto maior, mais commits', 'hand', 18, GREY, 'end'))
    if not days:
        s.add(s.text(W / 2, 140, 'sem leitura agora', 'hand', 22, GREY, 'middle'))
        write(out, 'cobra.svg', s)
        return
    weeks = weeks_of(days)
    x0, x1, y0, y1 = 44, 816, 66, 204
    nw = len(weeks)
    gap = (x1 - x0) / max(1, nw - 1)
    rowh = (y1 - y0) / 6
    # caminho em zigue-zague pelas células existentes
    cells = []
    for wi, wk in enumerate(weeks):
        rows = range(7) if wi % 2 == 0 else range(6, -1, -1)
        for di in rows:
            if wk[di]:
                cells.append((x0 + wi * gap, y0 + di * rowh, wk[di][1]))
    dt_cell = 0.05
    n = len(cells)
    run = n * dt_cell
    T = run + 2.4  # pausa com o calendário vazio antes de recomeçar
    pts = [(x0 - 40, cells[0][1])] + [(x, y) for x, y, _ in cells] + [(x1 + 60, cells[-1][1])]
    d = 'M' + 'L'.join(f'{f1(x)} {f1(y)}' for x, y in pts)
    # tempo de chegada em cada ponto: entrada (0,3 s), uma célula por dt, saída
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total_len = sum(seg)
    times = [0.0, 0.3] + [0.3 + (i + 1) * dt_cell for i in range(n - 1)] + [0.3 + n * dt_cell + 0.6]
    lens = [0.0]
    for sg in seg:
        lens.append(lens[-1] + sg)
    kt = [t / T for t in times] + [1.0]
    kp = [l_ / total_len for l_ in lens] + [1.0]
    kt_s = ';'.join(f'{v:.4f}' for v in kt)
    kp_s = ';'.join(f'{v:.4f}' for v in kp)
    mx = max(c for _x, _y, c in cells) or 1
    dots = []
    for i, (x, y, c) in enumerate(cells):
        rr = 1.6 + 4.4 * math.sqrt(c / mx) if c else 1.4
        col = INK if c else LINE
        t_eat = (0.3 + i * dt_cell) / T
        dots.append(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="{f1(rr)}" fill="{col}">'
                    f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;{t_eat:.5f};{min(.999, t_eat + .002):.5f};.995;1" '
                    f'dur="{T:.2f}s" repeatCount="indefinite"/></circle>')
    s.add(*dots)
    body = []
    nseg = 16
    for k in range(nseg, -1, -1):
        rad = 7.5 if k == 0 else 6.6 - k * 0.22
        fill = RED
        extra = ''
        if k == 0:
            extra = (f'<circle cx="2.5" cy="-2.6" r="2.1" fill="{PAPER}"/><circle cx="3" cy="-2.6" r="1" fill="{INK}"/>'
                     f'<path d="M7 0h5M12 0l2 -2M12 0l2 2" stroke="{RED}" stroke-width="1.2" fill="none"/>')
        body.append(f'<g><circle r="{f1(rad)}" fill="{fill}" stroke="{INK}" stroke-width="1.4"/>{extra}'
                    f'<animateMotion path="{d}" dur="{T:.2f}s" begin="{k * dt_cell * 0.28:.3f}s" repeatCount="indefinite" '
                    f'calcMode="linear" keyTimes="{kt_s}" keyPoints="{kp_s}" rotate="auto"/></g>')
    s.defs.append(f'<clipPath id="cb"><rect x="3" y="44" width="{W - 14}" height="{H - 58}"/></clipPath>')
    # fora do caminho até começar (begin > 0): as partes ficam escondidas à esquerda
    s.add(f'<g clip-path="url(#cb)"><g transform="translate(0 0)">{"".join(body)}</g></g>')
    write(out, 'cobra.svg', s)


# ------------------------------------------------------------------ estudos

COURSES = [
    ('Engenharia da Computação', 'Faculdade Galileu', dt.date(2023, 2, 1), dt.date(2027, 12, 15)),
    ('Ciência de Dados', 'Univesp', dt.date(2024, 2, 1), dt.date(2028, 12, 15)),
]


def estudos(out):
    W, H = 860, 260
    today = dt.datetime.now(BRT).date()
    s = Svg(W, H, 'Estudos',
            'Linha do tempo: Engenharia da Computação na Faculdade Galileu (2023–2027) e '
            'Ciência de Dados na Univesp (2024–2028), com a marca de hoje.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    s.add(s.text(24, 36, 'LINHA DO TEMPO', 'sans8', 10.5, RED, ls=2.6),
          s.text(W - 30, 36, f'hoje: {stamp()}', 'hand', 18, GREY, 'end'))
    a, b = dt.date(2023, 1, 1), dt.date(2029, 1, 1)
    x0, x1 = 318, 826

    def X(d):
        return x0 + (x1 - x0) * (d - a).days / (b - a).days
    # régua dos anos
    ay = 214
    s.add(f'<path d="M{x0} {ay}H{x1}" stroke="{INK}" stroke-width="1.6"/>')
    for yr in range(2023, 2030):
        x = X(dt.date(yr, 1, 1))
        s.add(f'<path d="M{f1(x)} {ay - 6}V{ay + 6}" stroke="{INK}" stroke-width="1.6"/>')
        if yr < 2029:
            s.add(s.text(X(dt.date(yr, 7, 1)), ay + 24, str(yr), 'mono', 18, GREY, 'middle'))
    s.defs.append(f'<pattern id="eh" width="6" height="4" patternUnits="userSpaceOnUse"><rect width="6" height="2.3" fill="{RED}"/></pattern>')
    for i, (curso, onde, ini, fim) in enumerate(COURSES):
        y = 70 + i * 68
        s.add(s.text(24, y + 20, curso, 'serif', 20, INK),
              s.text(25, y + 42, f'{onde.upper()}  ·  {ini.year}–{fim.year}', 'sans8', 9.5, GREY, ls=1.6))
        bx0, bx1 = X(ini), X(fim)
        hoje = clamp((today - ini).days / (fim - ini).days)
        grow = css_anim(s, '0%{transform:scaleX(0)}100%{transform:scaleX(1)}', 1.8,
                        timing='cubic-bezier(.5,0,.2,1)', extra='1 both', origin='left center')
        s.css.append(f'.{grow}{{animation-delay:{.3 + i * .35:.2f}s}}')
        s.add(f'<rect x="{f1(bx0)}" y="{y + 6}" width="{f1(bx1 - bx0)}" height="28" fill="{PAPER2}" stroke="{INK}" stroke-width="1.5"/>',
              f'<g class="{grow}"><rect x="{f1(bx0)}" y="{y + 6}" width="{f1((bx1 - bx0) * hoje)}" height="28" fill="url(#eh)"/></g>',
              f'<rect x="{f1(bx0)}" y="{y + 6}" width="{f1(bx1 - bx0)}" height="28" fill="none" stroke="{INK}" stroke-width="1.5"/>')
        # capelo no fim
        cx = bx1 + 2
        s.add(f'<g transform="translate({f1(cx - 14)} {y + 20})"><path d="M0 -6L14 -12L28 -6L14 0Z" fill="{INK}"/>'
              f'<path d="M6 -3V4C10 7 18 7 22 4V-3" fill="{INK}"/><path d="M26 -6V3" stroke="{RED}" stroke-width="1.6"/></g>')
    tx = X(today)
    pulse = css_anim(s, '0%,100%{opacity:1}50%{opacity:.3}', 1.6)
    s.add(f'<path d="M{f1(tx)} 56V{ay}" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 4"/>',
          f'<circle class="{pulse}" cx="{f1(tx)}" cy="{ay}" r="6" fill="{RED}" stroke="{INK}" stroke-width="1.4"/>')
    write(out, 'estudos.svg', s)


def build_all(out):
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
    painel(out, days, gh)
    gravura(out, days)
    cobra(out, days)
    estudos(out)
