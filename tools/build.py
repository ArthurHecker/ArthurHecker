"""Gera as artes fixas do perfil (assets/*.svg) no estilo do arthurhecker.space.

    pip install fonttools brotli
    python tools/build.py

As artes "ao vivo" (monitor, gravura das contribuições, cobra) são geradas pelo
GitHub Actions em .github/workflows/vivo.yml.
"""
from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import (BOOK, CREAM, GOLD, GREY, GREY2, INK, LINE, PAPER, PAPER2, RED, Svg, Timeline,  # noqa: E402
                    blink, clamp, css_anim, engrave_h, engrave_v, f1, hand_line, panel)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets')


def save(name, svg: Svg):
    data = svg.render()
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as fh:
        fh.write(data)
    print(f'{name:28s} {len(data) / 1024:7.1f} KB')


# ------------------------------------------------------------------ balões

def balloon(cx, cy, rx, ry, tip, spiky=False, seed=3, n=None):
    """Contorno de balão (oval ou grito) com rabicho até `tip`, num path só."""
    rnd = random.Random(seed)
    tx, ty = tip
    ang_tip = math.atan2((ty - cy) / ry, (tx - cx) / rx)
    spread = 0.16 if not spiky else 0.12
    n = n or (26 if spiky else 64)
    pts = []
    for i in range(n):
        a = ang_tip + spread + (2 * math.pi - 2 * spread) * i / (n - 1)
        if spiky:
            k = 1.0 if i % 2 == 0 else 0.74
            k *= 1 + rnd.uniform(-0.07, 0.07)
        else:
            k = 1 + 0.012 * math.sin(i * 1.7)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    pts.append((tx, ty))
    return 'M' + 'L'.join(f'{f1(x)} {f1(y)}' for x, y in pts) + 'Z'


# ------------------------------------------------------------------ cabeçalho

def header():
    W, H = 860, 400
    s = Svg(W, H, 'Arthur Hecker',
            'Gravura do arthurhecker.space: um dev de cabelo comprido diante de uma lua vermelha, '
            'num balcão à noite; balões dizem "Ei, Arthur...", "Acorde." e "Você ainda tem muito trabalho a fazer...". '
            'No topo, um terminal às 03:00 digita o que o Arthur faz.')
    px, py, pw, ph = 2, 2, 846, 386
    s.add(panel(px, py, pw, ph, shadow=INK, off=8))
    s.defs.append(f'<clipPath id="scene"><rect x="{px + 1}" y="38" width="{pw - 2}" height="{ph - 37}"/></clipPath>')
    cx, cy, r = 575, 214, 150
    rail_y0, rail_y1 = 270, 290

    # fundo: linhas verticais que escurecem nas bordas e no chão
    def dbg(x, y):
        u = clamp((y - 38) / 350)
        edge = abs(x - 430) / 430
        d = 0.2 + 0.2 * u + 0.62 * edge ** 2.4 + 0.22 * clamp(1 - (y - 38) / 70)
        if y > rail_y1:
            d += 0.25
        # halo claro em volta da lua
        dd = math.hypot(x - cx, y - cy)
        d -= 0.16 * math.exp(-((dd - r) / 70) ** 2)
        return d
    bg = engrave_v(-4, W + 6, 36, H - 10, 6.2, dbg, 5.4)
    sway = css_anim(s, '0%{transform:translateX(-2.5px)}100%{transform:translateX(2.5px)}', 7, extra='infinite alternate')

    # lua vermelha com hachura de esfera e "crateras"
    L = (0.5, -0.55, 0.67)
    ln = math.sqrt(sum(v * v for v in L))
    L = tuple(v / ln for v in L)
    craters = [(520, 150, 26, .5), (640, 260, 34, .45), (500, 280, 22, .4), (655, 140, 16, .35), (585, 205, 18, .25)]

    def dmoon(x, y):
        nx, ny = (x - cx) / r, (y - cy) / r
        rr = nx * nx + ny * ny
        if rr >= 1:
            return 0.9
        nz = math.sqrt(1 - rr)
        lam = max(0.0, nx * L[0] + ny * L[1] + nz * L[2])
        d = 0.06 + 0.8 * (1 - lam) ** 1.8
        for qx, qy, qr, qa in craters:
            d += qa * math.exp(-((x - qx) ** 2 + (y - qy) ** 2) / (qr * qr))
        return d
    moon = engrave_h(cy - r - 4, cy + r + 4, cx - r - 6, cx + r + 6, 5.2, dmoon, 4.4)
    s.defs.append(f'<clipPath id="moon"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    bob = css_anim(s, '0%{transform:translateY(-1.5px)}100%{transform:translateY(1.5px)}', 5, extra='infinite alternate')

    # balcão: corrimão + balaústres na frente da lua
    rail = [f'<rect x="{px}" y="{rail_y0}" width="{pw}" height="{rail_y1 - rail_y0}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>',
            f'<path d="M{px} {rail_y1 - 6}H{px + pw}" stroke="{INK}" stroke-width=".8" opacity=".55"/>']
    for i in range(20):
        bx = 12 + i * 46
        if bx > W - 20:
            break
        rail.append(f'<rect x="{bx}" y="{rail_y1}" width="17" height="{H - rail_y1}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>'
                    f'<path d="M{bx + 12} {rail_y1 + 3}V{H}M{bx + 14.5} {rail_y1 + 3}V{H}" stroke="{INK}" stroke-width=".9"/>')

    # silhueta de costas (cabelo comprido) na frente de tudo
    sil = ('M462 400C470 352 503 326 540 318C552 314 560 310 562 302L590 302C592 312 602 318 616 322'
           'C652 332 682 352 690 400Z')
    hair = ('M536 268C531 236 549 216 574 216C601 216 617 236 615 266C614 286 622 302 636 316'
            'C648 328 662 338 676 350L662 348L674 364L654 354L658 372L640 358L638 376L626 356L618 366L612 348'
            'C600 340 590 332 584 324C566 328 548 324 536 314L530 326L528 308C524 296 532 284 536 268Z')
    head = '<ellipse cx="575" cy="262" rx="31" ry="38"/>'

    # fumaça do sono que se dissipa ao abrir (uma vez)
    s.defs.append('<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="26"/></filter>')
    smoke_cls = css_anim(s, '0%{opacity:.96;transform:scale(1)}100%{opacity:0;transform:scale(1.5)}', 2.6,
                         timing='cubic-bezier(.6,0,.4,1)', extra='1 both', origin='center')
    s.css.append(f'.{smoke_cls}{{animation-delay:.25s}}')
    smoke = ''.join(f'<ellipse class="{smoke_cls}" cx="{x}" cy="{y}" rx="{a}" ry="{b}" fill="{INK}"/>'
                    for x, y, a, b in [(160, 200, 260, 190), (460, 260, 300, 200), (720, 170, 260, 200), (600, 360, 320, 120)])

    s.add(f'<g clip-path="url(#scene)">',
          f'<g class="{sway}"><path d="{bg}" fill="{INK}"/></g>',
          f'<circle cx="{cx}" cy="{cy}" r="{r + 14}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>',
          f'<circle cx="{cx}" cy="{cy}" r="{r + 7}" fill="none" stroke="{INK}" stroke-width=".7" stroke-dasharray="2 3"/>',
          f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{RED}" stroke="{INK}" stroke-width="1.6"/>',
          f'<g clip-path="url(#moon)"><g class="{bob}"><path d="{moon}" fill="#2a0204" opacity=".82"/></g></g>',
          *rail,
          f'<g fill="{INK}" transform="translate(575 392) scale(1.32) translate(-575 -392)"><path d="{sil}"/>{head}<path d="{hair}"/></g>',
          f'<g filter="url(#blur)">{smoke}</g>',
          '</g>')

    # balões do sonho (em loop)
    tl = Timeline(s, 15)

    def pop(t_on, t_off, shake=False):
        a = .004
        sh = (f'({t_on + .42},"transform:translate(-3px,1px) rotate(-1.5deg)"),'
              f'({t_on + .5},"transform:translate(3px,-1px) rotate(1.5deg)"),'
              f'({t_on + .58},"transform:translate(-2px,0) rotate(-1deg)"),') if shake else ''
        stops = [(0, 'opacity:0;transform:scale(.4)'), (t_on - a, 'opacity:0;transform:scale(.4)'),
                 (t_on + .22, 'opacity:1;transform:scale(1.08)'), (t_on + .36, 'opacity:1;transform:scale(1)')]
        if shake:
            stops += [(t_on + .44, 'opacity:1;transform:translate(-3px,1px) rotate(-1.6deg)'),
                      (t_on + .52, 'opacity:1;transform:translate(3px,-1px) rotate(1.6deg)'),
                      (t_on + .6, 'opacity:1;transform:translate(-2px,0) rotate(-.8deg)'),
                      (t_on + .68, 'opacity:1;transform:none')]
        stops += [(t_off, 'opacity:1;transform:none'), (t_off + .3, 'opacity:0;transform:scale(.96)'),
                  (tl.T, 'opacity:0;transform:scale(.96)')]
        del sh
        c = tl.keyframes(stops, timing='ease-out')
        s.css.append(f'.{c}{{transform-box:fill-box;transform-origin:center}}')
        return c

    b1 = pop(1.0, 6.2)
    b2 = pop(2.1, 6.2, shake=True)
    b3 = pop(6.9, 13.6)
    stroke = f'fill="{PAPER}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"'
    s.add(f'<g class="{b1}"><path d="{balloon(738, 98, 100, 38, (650, 186))}" {stroke}/>',
          s.text(738, 109, 'Ei, Arthur...', 'hand', 34, INK, 'middle'), '</g>')
    s.add(f'<g class="{b2}"><path d="{balloon(318, 118, 112, 62, (470, 200), spiky=True, seed=7)}" {stroke}/>',
          s.text(318, 132, 'Acorde.', 'hand', 44, INK, 'middle', extra=f' stroke="{INK}" stroke-width=".9"'), '</g>')
    s.add(f'<g class="{b3}"><path d="{balloon(330, 120, 168, 56, (520, 214), seed=5)}" {stroke}/>',
          s.text(330, 112, 'Você ainda tem muito', 'hand', 30, INK, 'middle'),
          s.text(330, 142, 'trabalho a fazer...', 'hand', 30, INK, 'middle'), '</g>')

    # etiqueta com o nome (como a prévia do site)
    lx, ly, lw, lh = 24, 290, 372, 80
    s.add(f'<rect x="{lx + 6}" y="{ly + lh}" width="{lw}" height="7" fill="{RED}"/>',
          f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>',
          s.text(lx + 18, ly + 50, 'Arthur Hecker', 'script', 56, INK),
          s.text(lx + 22, ly + 69, 'HUB · ARTHURHECKER.SPACE', 'sans8', 11.5, RED, ls=3.1))

    # barra do terminal: 03:00 e o que o Arthur faz, digitado em loop
    s.add(f'<rect x="{px}" y="{py}" width="{pw}" height="35" fill="{INK}"/>')
    prompt = 'C:\\arthur>'
    fs = 22
    pxw = BOOK.width('mono', prompt, fs)
    s.add(s.text(16, 27, prompt, 'mono', fs, GREY2))
    phrases = [
        'estudante de Engenharia e de Ciência da Computação',
        'full-stack: Python, Django, Quart, Three.js',
        'jogos em Godot nas horas vagas (e nas não vagas)',
        'administro o meu próprio servidor Linux',
        'corrigindo o último bug do dia...',
    ]
    cps, hold = 26.0, 2.6
    seg = [len(p) / cps + hold + .35 for p in phrases]
    T = sum(seg)
    tt = Timeline(s, T)
    x0 = 16 + pxw + 6
    t = 0.3
    ch = BOOK.width('mono', 'M', fs)
    wmax = max(BOOK.width('mono', p, fs) for p in phrases)
    s.defs.append(f'<clipPath id="bar"><rect x="{f1(x0 - 2)}" y="4" width="{f1(wmax + ch + 6)}" height="32"/></clipPath>')
    s.add('<g clip-path="url(#bar)">')
    for p, d in zip(phrases, seg):
        w = BOOK.width('mono', p, fs)
        n = len(p)
        vis = tt.keyframes([(0, 'opacity:0'), (t - .004, 'opacity:0'), (t, 'opacity:1'), (t + d - .35, 'opacity:1'),
                            (t + d - .3, 'opacity:0'), (T, 'opacity:0')])
        cov, dur = tt.typing(t, n, w + 2, cps=cps)
        cur = tt.keyframes([(0, 'opacity:0;transform:translateX(0)'), (t - .004, 'opacity:0;transform:translateX(0)'),
                            (t, 'opacity:1;transform:translateX(0)', f'steps({n},end)'),
                            (t + dur, f'opacity:1;transform:translateX({f1(w)}px)'),
                            (t + d - .35, f'opacity:1;transform:translateX({f1(w)}px)'),
                            (t + d - .3, f'opacity:0;transform:translateX({f1(w)}px)'),
                            (T, f'opacity:0;transform:translateX({f1(w)}px)')])
        s.add(f'<g class="{vis}">', s.text(x0, 27, p, 'mono', fs, PAPER),
              f'<rect class="{cov}" x="{f1(x0 - 1)}" y="8" width="{f1(w + 4)}" height="26" fill="{INK}"/></g>',
              f'<g class="{cur}"><rect x="{f1(x0 + 1)}" y="11" width="{f1(ch * .8)}" height="19" fill="{RED}"/></g>')
        t += d
    s.add('</g>')
    # relógio
    bl = blink(s, 1.0)
    s.add(s.text(750, 26, 'três da manhã', 'hand', 18, GREY2, 'end'),
          s.text(796, 28, '03', 'mono', 28, RED, 'end'),
          s.text(800, 28, ':', 'mono', 28, RED, 'middle', cls=bl),
          s.text(804, 28, '00', 'mono', 28, RED))
    save('header.svg', s)


# ------------------------------------------------------------------ capítulos

CHAPTERS = [
    ('I', 'SOBRE MIM', 'Três da manhã',
     'Três da manhã, o último bug do dia... e o sono chegando como fumaça, escurecendo a visão.'),
    ('II', 'CONTATO', 'Um chat comigo mesmo',
     'Abri o navegador e, numa aba, havia um chat para conversar comigo mesmo. Paranoia? Certamente é o Arthur.'),
    ('III', 'ESTUDOS', 'O bug do Newton',
     'Mudei de aba... e lá estava o Newton tropeçando na maçã, com o mesmo bug de sempre.'),
    ('IV', 'PROJETOS', 'O arcade',
     'Para parar de alucinar, tentei jogar alguma coisa no arcade e acordar de vez... mas tinha algo de errado.'),
    ('V', 'AO VIVO', 'O PC superaqueceu',
     'Só que o PC não aguentou e superaqueceu... inexplicavelmente. (Os números abaixo são de verdade.)'),
    ('VI', 'FERRAMENTAS', 'Voltei a trabalhar',
     '...então eu voltei a trabalhar. Só faltava mais um bug, não é?'),
    ('VII', 'ATALHOS', 'Os atalhos',
     'E, no fim da noite, os atalhos: as ferramentas e os projetos finalizados.'),
]


def chapter(num, tag, title, caption):
    W = 860
    cap_lines = BOOK.wrap('hand', caption, 20, 548)
    H = 100 + 24 * len(cap_lines) + 18
    s = Svg(W, H, f'Capítulo {num}: {title}', caption)
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    # gravura à direita, escurecendo para a borda
    x0 = 610

    def d(x, y):
        return clamp((x - x0) / (W - 12 - x0)) ** 1.6 * 0.95 + 0.05 * math.sin(y / 9)
    s.defs.append(f'<clipPath id="pc"><rect x="3" y="3" width="{W - 14}" height="{H - 14}"/></clipPath>')
    sway = css_anim(s, '0%{transform:translateX(-2px)}100%{transform:translateX(2px)}', 6, extra='infinite alternate')
    s.add(f'<g clip-path="url(#pc)"><g class="{sway}"><path d="{engrave_v(x0, W - 4, 0, H, 5.6, d, 4.6)}" fill="{INK}" opacity=".9"/></g></g>')
    # numeral gravado em vermelho
    s.defs.append(f'<pattern id="hatch" width="6" height="4.2" patternUnits="userSpaceOnUse">'
                  f'<rect width="6" height="2.5" fill="{RED}"/></pattern>')
    nx = W - 40
    s.add(s.text(nx, H - 30, num, 'serif', 104, PAPER, 'end', extra=f' stroke="{PAPER}" stroke-width="12" stroke-linejoin="round"'),
          s.text(nx, H - 30, num, 'serif', 104, 'url(#hatch)', 'end', extra=f' stroke="{RED}" stroke-width="1.3"'))
    s.add(s.text(26, 34, f'CAPÍTULO {num}  ·  {tag}', 'sans8', 11.5, RED, ls=3))
    s.add(s.text(24, 74, title, 'serif', 36, INK))
    tw = BOOK.width('serif', title, 36)
    line = hand_line(24, 86, 24 + tw + 18, amp=1.8)
    draw = css_anim(s, '0%{stroke-dashoffset:100}100%{stroke-dashoffset:0}', 1.3, timing='cubic-bezier(.6,0,.3,1)', extra='1 both')
    s.css.append(f'.{draw}{{animation-delay:.25s}}')
    s.add(f'<path class="{draw}" d="{line}" pathLength="100" stroke-dasharray="100" fill="none" stroke="{RED}" stroke-width="2.6" stroke-linecap="round"/>')
    for i, ln in enumerate(cap_lines):
        s.add(s.text(26, 114 + 24 * i, ln, 'hand', 20, GREY))
    save(f'cap-{num.lower()}.svg', s)


def chapters():
    for c in CHAPTERS:
        chapter(*c)


# ------------------------------------------------------------------ terminal (sobre mim)

def terminal():
    W = 860
    fs, lh = 22, 26
    BG, FG, DIM = '#0c0c0c', '#cccccc', '#7c7c7c'
    P = 'C:\\Users\\arthur>'
    # (tipo, conteúdo); conteúdo de 'out' pode ser lista de trechos (texto, cor)
    lines = [
        ('out', [('Microsoft Windows [versão 10.0.26100.300]', DIM)]),
        ('out', [('(c) Arthur Hecker Silva. Alguns direitos possivelmente reservados.', DIM)]),
        ('gap', None),
        ('cmd', 'whoami'),
        ('out', [('arthurhecker\\', DIM), ('arthur-hecker-silva', PAPER)]),
        ('gap', None),
        ('cmd', 'type sobre.txt'),
        ('out', [('  nome      ', RED), ('Arthur Hecker Silva', PAPER)]),
        ('out', [('  estudo    ', RED), ('Engenharia da Computação', PAPER), (' · Galileu (2023-2027)', DIM)]),
        ('out', [('            ', RED), ('Ciência da Computação', PAPER), (' · Univesp (2024-2028)', DIM)]),
        ('out', [('  faço      ', RED), ('sites, bots, jogos e servidores, de ponta a ponta', FG)]),
        ('out', [('  servidor  ', RED), ('um Linux só meu, administrado por mim (às 3h, claro)', FG)]),
        ('out', [('  agora     ', RED), ('o jogo ', FG), ('Formigas no Piquenique', GOLD), (', em Godot', FG)]),
        ('out', [('  status    ', RED), ('compilando... ', FG), ('(eu não estava dormindo!)', DIM)]),
        ('gap', None),
        ('end', None),
    ]
    top = 36
    H = top + 22 + lh * len(lines) + 20
    s = Svg(W, H, 'C:\\WINDOWS\\system32\\cmd.exe — sobre o Arthur',
            'Terminal do Windows: whoami responde arthur-hecker-silva; type sobre.txt mostra estudos '
            '(Engenharia da Computação na Galileu e Ciência da Computação na Univesp), o que faz '
            '(sites, bots, jogos e servidores), o servidor Linux próprio e o jogo em Godot.')
    ww, wh = W - 12, H - 12
    s.add(f'<rect x="10" y="10" width="{ww}" height="{wh}" fill="{INK}"/>',
          f'<rect x="2" y="2" width="{ww}" height="{wh}" fill="{BG}" stroke="{INK}" stroke-width="2"/>',
          f'<rect x="2" y="2" width="{ww}" height="{top - 2}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
    # ícone + título + botões da janela
    s.add(f'<rect x="14" y="10" width="20" height="16" fill="{INK}"/>',
          s.text(16.5, 22.5, 'C:\\', 'mono', 13, PAPER),
          s.text(44, 23.5, 'C:\\WINDOWS\\system32\\cmd.exe', 'sans', 13, INK))
    bx = W - 10 - 46 * 3
    s.add(f'<path d="M{bx + 17} 19h12" stroke="{INK}" stroke-width="1.4"/>',
          f'<rect x="{bx + 46 + 17.5}" y="13.5" width="11" height="11" fill="none" stroke="{INK}" stroke-width="1.4"/>',
          f'<rect x="{bx + 92}" y="3" width="44" height="{top - 4}" fill="{RED}"/>',
          f'<path d="M{bx + 92 + 16.5} 13.5l11 11M{bx + 92 + 27.5} 13.5l-11 11" stroke="{PAPER}" stroke-width="1.6"/>')
    T = 17.0
    tl = Timeline(s, T)
    cps = 15.0
    pw = BOOK.width('mono', P, fs)
    ch = BOOK.width('mono', 'M', fs)
    t = 0.25
    y = top + 30
    for kind, val in lines:
        if kind == 'gap':
            y += lh
            t += 0.12
            continue
        if kind == 'out':
            c = tl.show(t, fade=0.05)
            s.add(f'<g class="{c}">', s.rich(16, y, val, font='mono', size=fs), '</g>')
            t += 0.11
        elif kind == 'cmd':
            t += 0.35
            c = tl.show(t, fade=0.05)
            w = BOOK.width('mono', val, fs)
            cov, dur = tl.typing(t + 0.35, len(val), w + 3, cps=cps)
            cur = tl.cursor(t + 0.35, len(val), w, cps=cps)
            x = 16 + pw
            s.add(f'<g class="{c}">', s.text(16, y, P, 'mono', fs, FG), s.text(x, y, val, 'mono', fs, PAPER),
                  f'<rect class="{cov}" x="{f1(x - 1)}" y="{y - 19}" width="{f1(w + 4)}" height="24" fill="{BG}"/>',
                  f'<g class="{cur}"><rect x="{f1(x)}" y="{y + 1}" width="{f1(ch)}" height="3" fill="{PAPER}"/></g></g>')
            t += 0.35 + dur + 0.3
        elif kind == 'end':
            c = tl.show(t + 0.2, fade=0.05)
            bl = blink(s, 1.06)
            s.add(f'<g class="{c}">', s.text(16, y, P, 'mono', fs, FG),
                  f'<rect class="{bl}" x="{f1(16 + pw + 1)}" y="{y + 1}" width="{f1(ch)}" height="3" fill="{PAPER}"/></g>')
        y += lh
    save('terminal.svg', s)


# ------------------------------------------------------------------ chat comigo mesmo

def chat():
    W = 860
    msgs = [
        ('v', 'oi! quem é você?'),
        ('a', 'Certamente é o Arthur.'),
        ('v', 'e o que você faz da vida?'),
        ('a', 'Sites, bots, jogos e servidores. Quase sempre às três da manhã.'),
        ('v', 'como eu falo com você?'),
        ('a', 'Pelos botões aqui embaixo. Ou com a minha IA, no arthurhecker.space.'),
    ]
    fs = 16
    bh, gap = 40, 12
    top = 86
    H = top + len(msgs) * (bh + gap) + 86
    s = Svg(W, H, 'Certamente é o Arthur — chat',
            'Chat do site: o visitante pergunta quem é, e o Arthur responde "Certamente é o Arthur"; '
            'faz sites, bots, jogos e servidores, quase sempre às três da manhã; contato pelos botões abaixo '
            'ou pela IA em arthurhecker.space.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    # cabeçalho: espelho como foto de perfil
    s.add(f'<circle cx="44" cy="44" r="25" fill="{INK}"/>',
          f'<ellipse cx="44" cy="44" rx="13" ry="17" fill="{PAPER}" stroke="{GOLD}" stroke-width="3"/>',
          f'<path d="M38 36l7-6M37 44l11-10M40 51l9-8" stroke="{LINE}" stroke-width="1.6" stroke-linecap="round"/>',
          s.text(82, 40, 'Certamente é o Arthur', 'sans7', 18, INK))
    pulse = css_anim(s, '0%,100%{opacity:1}50%{opacity:.25}', 1.6)
    s.add(f'<circle class="{pulse}" cx="88" cy="58" r="4.5" fill="{RED}"/>',
          s.text(98, 63, 'online', 'sans', 13.5, GREY),
          s.text(W - 34, 50, 'ARTHURHECKER.SPACE', 'sans8', 10.5, GREY2, 'end', ls=2.4),
          f'<path d="M20 {top - 12}H{W - 24}" stroke="{LINE}" stroke-width="1.5"/>')
    T = 21.0
    tl = Timeline(s, T)
    t = 0.6
    y = top
    for who, txt in msgs:
        w = BOOK.width('sans', txt, fs) + 36
        if who == 'a':
            # "digitando..." antes da resposta
            dots_on, dots_off = t, t + 1.1
            c = tl.keyframes([(0, 'opacity:0'), (dots_on - .004, 'opacity:0'), (dots_on, 'opacity:1'),
                              (dots_off - .004, 'opacity:1'), (dots_off, 'opacity:0'), (T, 'opacity:0')])
            dots = []
            for i in range(3):
                b = css_anim(s, '0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}', 0.9)
                s.css.append(f'.{b}{{animation-delay:{i * 0.15:.2f}s}}')
                dots.append(f'<circle class="{b}" cx="{46 + i * 13}" cy="{y + bh / 2}" r="4" fill="{GREY2}"/>')
            s.add(f'<g class="{c}"><rect x="26" y="{y}" width="78" height="{bh}" rx="14" fill="{PAPER2}" stroke="{INK}" stroke-width="1.4"/>',
                  *dots, '</g>')
            t = dots_off
            c = tl.show(t, fade=.25, rise=6)
            s.add(f'<g class="{c}"><path d="M{26 + 14} {y}H{26 + w - 14}a14 14 0 0 1 14 14V{y + bh - 14}a14 14 0 0 1 -14 14'
                  f'H{26 + 4}a4 4 0 0 1 -4 -4V{y + 14}a14 14 0 0 1 14 -14Z" fill="{PAPER2}" stroke="{INK}" stroke-width="1.4"/>',
                  s.text(26 + 18, y + 26, txt, 'sans', fs, INK), '</g>')
            t += 1.0
        else:
            x = W - 30 - w
            c = tl.show(t, fade=.25, rise=6)
            s.add(f'<g class="{c}"><path d="M{x + 14} {y}H{x + w - 14}a14 14 0 0 1 14 14V{y + bh - 4}a4 4 0 0 1 -4 4'
                  f'H{x + 14}a14 14 0 0 1 -14 -14V{y + 14}a14 14 0 0 1 14 -14Z" fill="{INK}"/>',
                  s.text(x + 18, y + 26, txt, 'sans', fs, PAPER), '</g>')
            t += 1.0
        y += bh + gap
    # campo de mensagem
    iy = H - 74
    s.add(f'<rect x="26" y="{iy}" width="{W - 120}" height="46" rx="23" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>',
          s.text(52, iy + 29, 'Diga algo para o Arthur...', 'sans', 15.5, GREY2),
          f'<circle cx="{W - 60}" cy="{iy + 23}" r="23" fill="{RED}"/>',
          f'<path transform="translate({W - 72} {iy + 11})" d="M2 21.5 23 12 2 2.5l.01 7.4L15 12 2.01 14.1z" fill="{PAPER}"/>')
    save('chat.svg', s)


# ------------------------------------------------------------------ o bug do Newton

def newton():
    W, H = 860, 350
    s = Svg(W, H, 'O bug do Newton',
            'Folha de caderno com o código da classe Isaac_Newton; a maçã cai, o Newton tropeça nela, '
            'colisão detectada e os erros: "Ação e reação não definida", "Terceira lei de Newton não encontrada". Carimbo: BUG.')
    s.add(panel(2, 2, W - 12, H - 12, off=7))
    # caderno
    s.defs.append(f'<clipPath id="nb"><rect x="3" y="3" width="{W - 14}" height="{H - 14}"/></clipPath>')
    rows = ''.join(f'M3 {y}H{W - 11}' for y in range(58, H - 12, 28))
    s.add(f'<g clip-path="url(#nb)"><path d="{rows}" stroke="#b9cfe0" stroke-width="1"/>'
          f'<path d="M70 3V{H - 11}" stroke="{RED}" stroke-width="1.4" opacity=".55"/></g>')
    for hy in (60, 175, 290):
        s.add(f'<circle cx="32" cy="{hy}" r="9" fill="{CREAM}" stroke="{LINE}" stroke-width="1.5"/>')
    s.add(s.text(84, 40, '// Criando a classe Personagem', 'hand', 18, GREY))
    code = [
        ([('class ', RED), ('Isaac_Newton {', INK)], 'c'),
        ([('    constructor(x, y) { this.x = x; this.y = y; }', INK)], 'c'),
        ([('    correr() { this.x += velocidade; }', INK)], 'c'),
        ([('}', INK)], 'c'),
        ([('maca.velocidade += gravidade * dt;', INK), ('   // 9.8 m/s²', GREY)], 'apple'),
        ([('Newton.rotacao += 15;', INK), ('   // tropeçou!', GREY)], 'trip'),
        ([('// COLISÃO DETECTADA: Isaac vs Maçã', RED)], 'hit'),
        ([('ERROR: TypeError: Ação e reação não definida', RED)], 'err'),
        ([('FATAL: Terceira lei de Newton não encontrada', RED)], 'err'),
    ]
    T = 13.0
    tl = Timeline(s, T)
    times = [0.4, 0.8, 1.2, 1.6, 2.3, 3.9, 4.7, 5.5, 6.1]
    for i, ((runs, _k), t) in enumerate(zip(code, times)):
        c = tl.show(t, fade=.2)
        s.add(f'<g class="{c}">', s.rich(84, 68 + 28 * i, runs, font='hand', size=19), '</g>')

    # cena: chão, árvore, maçã e o Newton de peruca
    gy = 300
    s.add(f'<path d="{hand_line(560, gy, 846, amp=1.6)}" fill="none" stroke="{INK}" stroke-width="2.2"/>')
    s.add(f'<path d="M802 {gy}C804 260 798 230 806 196M794 {gy}C792 262 786 236 792 200M806 222l18 -18" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    tcx, tcy, tr = 792, 140, 54
    crown = [(tcx, tcy, tr), (tcx - 46, tcy + 22, 32), (tcx + 22, tcy + 28, 30)]
    s.defs.append('<clipPath id="crown">' + ''.join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in crown) + '</clipPath>')

    def dtree(x, y):
        return 0.25 + 0.6 * clamp((y - tcy + 40) / 110) + 0.2 * clamp((x - tcx) / 60)
    s.add(f'<g clip-path="url(#crown)"><rect x="700" y="80" width="160" height="150" fill="{PAPER}"/>'
          f'<path d="{engrave_h(86, 226, 700, 860, 4.6, dtree, 3.6)}" fill="{INK}"/></g>',
          f'<g fill="none" stroke="{INK}" stroke-width="2">' + ''.join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in crown) + '</g>')
    for ax, ay in ((820, 122), (766, 104), (808, 172)):
        s.add(f'<circle cx="{ax}" cy="{ay}" r="6.5" fill="{RED}" stroke="{INK}" stroke-width="1.2"/>')
    # maçã que cai (2,3 s) e quica
    a0, a1, apx = 176, gy - 9, 666
    apple = tl.keyframes([(0, 'transform:translateY(0)'), (2.3, 'transform:translateY(0)', 'cubic-bezier(.5,0,1,1)'),
                          (2.85, f'transform:translateY({a1 - a0}px)', 'ease-out'),
                          (3.0, f'transform:translateY({a1 - a0 - 12}px)', 'ease-in'),
                          (3.15, f'transform:translateY({a1 - a0}px)'), (T - .4, f'transform:translateY({a1 - a0}px)'),
                          (T - .2, 'transform:translateY(0)'), (T, 'transform:translateY(0)')])
    s.add(f'<g class="{apple}"><circle cx="{apx}" cy="{a0}" r="9" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>'
          f'<path d="M{apx} {a0 - 9}c0 -5 2 -8 5 -9" stroke="{INK}" stroke-width="1.6" fill="none"/></g>')

    # Newton: casaco escuro e peruca branca cacheada; anda, tropeça e cai
    wig = ''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="1.4"/>'
                  for x, y, r in [(-10, -66, 6), (-12, -56, 5.5), (10, -66, 6), (12, -56, 5.5), (-6, -82, 6.5), (6, -82, 6.5), (0, -86, 6)])
    legs = []
    walk_end = 3.75
    for side, ph in ((1, 0), (-1, 1)):
        stops = [(0, 'transform:rotate(0deg)')]
        k = 0
        tt = 0.5
        while tt < walk_end:
            ang = 24 * side * (1 if (k + ph) % 2 == 0 else -1)
            stops.append((tt, f'transform:rotate({ang}deg)', 'ease-in-out'))
            tt += 0.3
            k += 1
        stops += [(walk_end + .05, 'transform:rotate(-30deg)'), (T - .4, 'transform:rotate(-30deg)'), (T, 'transform:rotate(0deg)')]
        cl = tl.keyframes(stops)
        s.css.append(f'.{cl}{{transform-box:view-box;transform-origin:0px -34px}}')
        legs.append(f'<g class="{cl}"><path d="M0 -34L0 0" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
                    f'<path d="M0 0h7" stroke="{INK}" stroke-width="4" stroke-linecap="round"/></g>')
    body = (f'<path d="M-8 -62L8 -62L13 -26L-13 -26Z" fill="{INK}"/>'
            f'<path d="M-6 -58L-15 -38M6 -58L15 -38" stroke="{INK}" stroke-width="3.6" stroke-linecap="round"/>'
            f'<circle cx="0" cy="-72" r="10.5" fill="{PAPER}" stroke="{INK}" stroke-width="1.8"/>{wig}'
            f'<circle cx="4.5" cy="-73" r="1.5" fill="{INK}"/>')
    x_start, x_end = 548, 638
    walk = tl.keyframes([(0, f'transform:translateX({x_start}px)'), (0.5, f'transform:translateX({x_start}px)'),
                         (walk_end, f'transform:translateX({x_end}px)'), (T - .4, f'transform:translateX({x_end}px)'),
                         (T - .2, f'transform:translateX({x_start}px)'), (T, f'transform:translateX({x_start}px)')])
    fall = tl.keyframes([(0, 'transform:rotate(0deg)'), (walk_end, 'transform:rotate(0deg)', 'cubic-bezier(.5,0,.8,.6)'),
                         (walk_end + .5, 'transform:rotate(84deg)', 'ease-out'), (walk_end + .62, 'transform:rotate(78deg)'),
                         (walk_end + .72, 'transform:rotate(82deg)'), (T - .4, 'transform:rotate(82deg)'),
                         (T - .2, 'transform:rotate(0deg)'), (T, 'transform:rotate(0deg)')])
    s.css.append(f'.{fall}{{transform-box:view-box;transform-origin:15px 0px}}')
    s.add(f'<g transform="translate(0 {gy - 2})"><g class="{walk}"><g class="{fall}"><g transform="scale(1.25)">{"".join(legs)}{body}</g></g></g></g>')
    # estrelinhas da queda
    stars = tl.show(walk_end + .55, T - .6, fade=.15)
    st = ''.join(f'<path transform="translate({x} {y}) scale({k})" d="M0 -8L2 -2L8 0L2 2L0 8L-2 2L-8 0L-2 -2Z" fill="{c}"/>'
                 for x, y, k, c in [(740, 256, 1.2, RED), (762, 242, .8, INK), (722, 238, .9, INK)])
    s.add(f'<g class="{stars}">{st}</g>')
    # carimbo BUG
    stamp = tl.keyframes([(0, 'opacity:0;transform:scale(2.2) rotate(-14deg)'), (6.7, 'opacity:0;transform:scale(2.2) rotate(-14deg)', 'cubic-bezier(.3,0,.2,1)'),
                          (6.95, 'opacity:.92;transform:scale(1) rotate(-14deg)'), (T - .6, 'opacity:.92;transform:scale(1) rotate(-14deg)'),
                          (T - .3, 'opacity:0;transform:scale(1) rotate(-14deg)'), (T, 'opacity:0;transform:scale(1) rotate(-14deg)')])
    s.css.append(f'.{stamp}{{transform-box:fill-box;transform-origin:center}}')
    s.add(f'<g class="{stamp}"><rect x="590" y="40" width="150" height="62" rx="6" fill="none" stroke="{RED}" stroke-width="4.5"/>'
          f'<rect x="597" y="47" width="136" height="48" rx="3" fill="none" stroke="{RED}" stroke-width="1.6"/>',
          s.text(665, 88, 'BUG', 'serif', 44, RED, 'middle', ls=4), '</g>')
    save('newton.svg', s)


# ------------------------------------------------------------------ cartões dos projetos

def icon(kind, cx, cy):
    """Ícones em tinta (papel e vermelho) dentro de um círculo preto de raio 26."""
    P, R = PAPER, RED
    g = f'<circle cx="{cx}" cy="{cy}" r="26" fill="{INK}"/><g transform="translate({cx} {cy})">'
    if kind == 'moon':
        g += (f'<circle r="15" fill="{R}"/><path d="M-13 -5H13M-15 0H15M-14 5H14M-10 10H10" stroke="#2a0204" stroke-width="1.3"/>'
              f'<circle r="18.5" fill="none" stroke="{P}" stroke-width="1.6"/>')
    elif kind == 'robot':
        g += (f'<rect x="-14" y="-10" width="28" height="22" rx="5" fill="{P}"/><path d="M0 -10V-17" stroke="{P}" stroke-width="2.4"/>'
              f'<circle cy="-18" r="3" fill="{R}"/><circle cx="-6" cy="0" r="3.4" fill="{INK}"/><circle cx="6" cy="0" r="3.4" fill="{R}"/>'
              f'<path d="M-6 7H6" stroke="{INK}" stroke-width="2"/><path d="M-18 -2V6M18 -2V6" stroke="{P}" stroke-width="3" stroke-linecap="round"/>')
    elif kind == 'duck':
        g += (f'<path d="M-15 8C-17 -4 -10 -15 1 -15C10 -15 14 -8 13 -2C13 4 9 9 3 11C-4 13 -12 13 -15 8Z" fill="{P}"/>'
              f'<path d="M11 -5L22 -2L11 3Z" fill="{R}"/><circle cx="4" cy="-6" r="2.4" fill="{INK}"/>'
              f'<path d="M-2 -10l7 -2" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>')
    elif kind == 'ant':
        g += (f'<g stroke="{P}" stroke-width="1.8" fill="none" stroke-linecap="round"><path d="M-4 0L-10 -9M-4 0L-12 2M-4 0L-9 10M3 0L7 -10M3 0L12 1M3 0L8 11"/>'
              f'<path d="M12 -5C15 -12 19 -13 21 -12M12 -5C17 -9 20 -7 22 -5"/></g>'
              f'<ellipse cx="-12" cy="2" rx="7" ry="5.5" fill="{P}"/><ellipse cx="-1" cy="0" rx="5" ry="3.6" fill="{P}"/>'
              f'<circle cx="10" cy="-3" r="5" fill="{R}"/>')
    elif kind == 'school':
        g += (f'<path d="M-15 -2L0 -14L15 -2V14H-15Z" fill="{P}"/><rect x="-4" y="4" width="8" height="10" fill="{INK}"/>'
              f'<path d="M0 -14V-22h8v4h-8" fill="{R}" stroke="{P}" stroke-width="1.2"/>'
              f'<path d="M-9 1h5v4h-5zM4 1h5v4h-5z" fill="{INK}"/>')
    elif kind == 'grid':
        g += (f'<path d="M-5 -15V15M5 -15V15M-15 -5H15M-15 5H15" stroke="{P}" stroke-width="2.4" stroke-linecap="round"/>'
              f'<path d="M-13 -13l6 6M-7 -13l-6 6" stroke="{P}" stroke-width="2"/><circle cx="10" cy="10" r="3.6" fill="none" stroke="{R}" stroke-width="2.2"/>'
              f'<circle cx="0" cy="0" r="3.6" fill="none" stroke="{R}" stroke-width="2.2"/>')
    elif kind == 'pad':
        g += (f'<rect x="-12" y="-15" width="22" height="30" rx="2" fill="{P}"/><path d="M-8 -7H6M-8 -1H6M-8 5H2" stroke="{INK}" stroke-width="1.6"/>'
              f'<path d="M15 -12L19 -8L5 6L0 8L2 3Z" fill="{R}" stroke="{INK}" stroke-width="1"/>')
    elif kind == 'server':
        g += ''.join(f'<rect x="-14" y="{y}" width="28" height="8" rx="1.5" fill="{P}"/><path d="M-9 {y + 4}H0" stroke="{INK}" stroke-width="1.4"/>'
                     for y in (-14, -4, 6))
    g += '</g>'
    return g


PROJECTS = [
    dict(id='hub', icon='moon', kind='SITE · WEBGL 3D', title='Hub 3D', status='NO AR',
         desc='O meu site contado como uma história em gravura 3D: chat com IA, arcade, terminal, '
              'o monitor do servidor com cooler e os atalhos para tudo.',
         tags=['Three.js', 'WebGL', 'Quart']),
    dict(id='mordekay', icon='robot', kind='IA · BOT', title='Mordekay', status='NO AR',
         desc='Central de comandos com IA integrada para controlar o servidor, que também é o bot '
              'do Discord que mantém tudo de pé.',
         tags=['Python', 'Quart', 'Discord', 'Gemini']),
    dict(id='pyro', icon='duck', kind='ASSISTENTE PESSOAL', title='Pyro', status='NO AR',
         desc='O seu pato pessoal: botas grandes, bico afiado e rotina em ordem. Personagem 3D '
              'procedural, chat com IA rodando no meu servidor e app para Android.',
         tags=['Python', 'Ollama', 'PWA']),
    dict(id='formigas', icon='ant', kind='JOGO · GODOT 4', title='Formigas no Piquenique', status='BETA FECHADO', cta='EM BREVE',
         desc='Tower defense de caminhos e combinações: 42 defesas, 68 formigas, 60 ondas, '
              'elementos que se misturam e três idiomas.',
         tags=['Godot', 'GDScript', 'Blender']),
    dict(id='webcei', icon='school', kind='UNIVESP · PROJETO INTEGRADOR', title='WebCEI', status='NO AR', cta='CÓDIGO  →',
         desc='Site de uma creche de Botucatu feito com o time da Univesp: coleta, organização e '
              'análise de dados, com leitura em voz alta.',
         tags=['Django', 'Python', 'TTS']),
    dict(id='velha', icon='grid', kind='MULTIPLAYER', title='Jogo da Velha Global', status='NO AR',
         desc='Desafie qualquer pessoa em tempo real, no mesmo tabuleiro sincronizado para '
              'todo mundo que estiver no site.',
         tags=['JavaScript', 'Tempo real']),
    dict(id='dontpad', icon='pad', kind='FERRAMENTA', title='Dontpad', status='NO AR',
         desc='Bloco de notas no mesmo formato do dontpad.com: escolha um endereço, escreva '
              'e compartilhe. Sem conta, sem cadastro.',
         tags=['Python', 'JavaScript']),
    dict(id='homelab', icon='server', kind='INFRAESTRUTURA', title='Homelab', status='SEMPRE LIGADO', cta='AO VIVO  ↓',
         desc='O servidor por trás de tudo: nuvem de arquivos, e-mail, VPN, IA local e os sites, '
              'em Docker e túneis da Cloudflare.',
         tags=['Linux', 'Docker', 'Cloudflare', 'Nginx']),
]


def card(p):
    W, H = 420, 236
    s = Svg(W, H, p['title'], f"{p['kind']}: {p['desc']} Tecnologias: {', '.join(p['tags'])}. Situação: {p['status']}.")
    s.add(panel(2, 2, W - 14, H - 14, off=8))
    # gravura na borda direita
    x0 = W - 78

    def d(x, y):
        return clamp((x - x0) / 66) ** 1.7 * 0.9
    s.defs.append(f'<clipPath id="cc"><rect x="3" y="3" width="{W - 16}" height="{H - 16}"/></clipPath>')
    s.add(f'<g clip-path="url(#cc)"><path d="{engrave_v(x0, W - 10, 0, H, 5.2, d, 4.4)}" fill="{INK}" opacity=".85"/></g>')
    s.add(icon(p['icon'], 42, 46))
    s.add(s.text(80, 34, p['kind'], 'sans8', 9.5, RED, ls=2.2))
    tsize = min(25.0, 25 * 262 / BOOK.width('serif', p['title'], 25))
    s.add(s.text(79, 63, p['title'], 'serif', tsize, INK))
    y = 98
    for ln in BOOK.wrap('sans', p['desc'], 13.5, 300)[:4]:
        s.add(s.text(20, y, ln, 'sans', 13.5, '#2b2a28'))
        y += 19.5
    lab = p.get('cta', 'ABRIR  →')
    lw = BOOK.width('sans8', lab, 9.5) + 2 * (len(lab) - 1) + 22
    # etiquetas (as que cabem antes do botão)
    x = 20
    for tg in p['tags']:
        w = BOOK.width('mono', tg, 17) + 14
        if x + w > W - 26 - lw - 8:
            break
        s.add(f'<rect x="{f1(x)}" y="186" width="{f1(w)}" height="22" fill="{PAPER2}" stroke="{INK}" stroke-width="1.2"/>',
              s.text(x + 7, 202, tg, 'mono', 17, INK))
        x += w + 6
    # situação
    st = p['status']
    sw = BOOK.width('sans8', st, 9) + 1.6 * (len(st) - 1) + 30
    sx = W - 26 - sw
    s.add(f'<rect x="{f1(sx)}" y="16" width="{f1(sw)}" height="22" rx="11" fill="{PAPER}" stroke="{INK}" stroke-width="1.3"/>')
    pulse = css_anim(s, '0%,100%{opacity:1}50%{opacity:.2}', 1.8)
    col = GOLD if 'BETA' in st else RED
    s.add(f'<circle class="{pulse}" cx="{f1(sx + 12)}" cy="27" r="4" fill="{col}"/>',
          s.text(sx + 21, 30.5, st, 'sans8', 9, INK, ls=1.6))
    cta_fill = RED if 'BREVE' not in lab else GREY
    s.add(f'<rect x="{f1(W - 26 - lw)}" y="186" width="{f1(lw)}" height="22" fill="{cta_fill}" stroke="{INK}" stroke-width="1.2"/>',
          s.text(W - 26 - lw / 2, 200.5, lab, 'sans8', 9.5, PAPER, 'middle', ls=2))
    save(f"card-{p['id']}.svg", s)


def cards():
    for p in PROJECTS:
        card(p)


# ------------------------------------------------------------------ botões e rodapé

BUTTONS = [
    ('site', 'ARTHURHECKER.SPACE', 'moon'),
    ('linkedin', 'LINKEDIN', 'in'),
    ('instagram', 'INSTAGRAM', 'ig'),
    ('ia', 'FALAR COM A IA', 'chat'),
    ('topo', 'VOLTAR AO INÍCIO', 'up'),
]


def button(bid, label, ic):
    lw = BOOK.width('sans8', label, 11.5) + 2.4 * (len(label) - 1)
    W, H = int(lw + 76), 54
    s = Svg(W, H, label, f'Botão: {label}')
    s.add(f'<rect x="7" y="7" width="{W - 9}" height="{H - 9}" fill="{RED}"/>',
          f'<rect x="1" y="1" width="{W - 9}" height="{H - 9}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
    cx, cy = 26, (H - 8) / 2 + 1
    if ic == 'moon':
        s.add(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{RED}" stroke="{INK}" stroke-width="1.4"/>'
              f'<path d="M{cx - 7} {cy - 2}h14M{cx - 8} {cy + 2}h16M{cx - 6} {cy + 6}h12" stroke="{INK}" stroke-width="1"/>')
    elif ic == 'in':
        s.add(f'<rect x="{cx - 10}" y="{cy - 10}" width="20" height="20" rx="3" fill="{INK}"/>'
              f'<path d="M{cx - 5} {cy - 1}v7M{cx - 5} {cy - 5}v.1M{cx - 1} {cy + 6}v-7m0 3c0-2 1.2-3 2.8-3s2.4 1 2.4 3v4" stroke="{PAPER}" stroke-width="2.2" stroke-linecap="round" fill="none"/>')
    elif ic == 'ig':
        s.add(f'<rect x="{cx - 10}" y="{cy - 10}" width="20" height="20" rx="6" fill="none" stroke="{INK}" stroke-width="2.2"/>'
              f'<circle cx="{cx}" cy="{cy}" r="4.6" fill="none" stroke="{INK}" stroke-width="2.2"/><circle cx="{cx + 5.6}" cy="{cy - 5.6}" r="1.5" fill="{RED}"/>')
    elif ic == 'chat':
        s.add(f'<path d="M{cx - 11} {cy - 9}h22v14h-12l-6 5v-5h-4z" fill="{INK}"/>'
              + ''.join(f'<circle cx="{cx - 5 + i * 5}" cy="{cy - 2}" r="1.6" fill="{PAPER}"/>' for i in range(3)))
    elif ic == 'up':
        s.add(f'<path d="M{cx} {cy + 10}V{cy - 9}M{cx - 8} {cy - 1}l8 -8 8 8" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>')
    s.add(s.text(46, cy + 4.5, label, 'sans8', 11.5, INK, ls=2.4))
    save(f'btn-{bid}.svg', s)


def buttons():
    for b in BUTTONS:
        button(*b)


def footer():
    W, H = 860, 300
    s = Svg(W, H, 'Arthur Hecker — fim da noite',
            'Rodapé: o céu escuro clareando atrás da lua vermelha; "Arthur Hecker", "H U B", '
            '"Desenvolvido por Arthur Hecker Silva" e "Alguns direitos possivelmente reservados".')
    s.add(f'<rect x="8" y="8" width="{W - 10}" height="{H - 10}" fill="{RED}"/>',
          f'<rect x="2" y="2" width="{W - 10}" height="{H - 10}" fill="{INK}" stroke="{INK}" stroke-width="2"/>')
    s.defs.append(f'<clipPath id="fc"><rect x="3" y="3" width="{W - 12}" height="{H - 12}"/></clipPath>')

    # gravura invertida (linhas de papel no escuro), mais clara embaixo: o dia chegando
    def d(x, y):
        return 0.04 + 0.9 * clamp((y - 120) / 170) ** 1.8 + 0.12 * clamp(abs(x - 430) / 430) ** 3
    sway = css_anim(s, '0%{transform:translateX(-2px)}100%{transform:translateX(2px)}', 7, extra='infinite alternate')
    rise = css_anim(s, '0%{transform:translateY(16px)}100%{transform:translateY(-6px)}', 9, extra='infinite alternate')
    mx, my, mr = 690, 168, 74

    def dm(x, y):
        nx, ny = (x - mx) / mr, (y - my) / mr
        return 0.1 + 0.75 * clamp(nx * -0.6 + ny * 0.7 + 0.4) ** 1.5
    s.defs.append(f'<clipPath id="fm"><circle cx="{mx}" cy="{my}" r="{mr}"/></clipPath>')
    tw = blink(s, 2.3)
    tw2 = blink(s, 3.1)
    stars = ''.join(f'<circle class="{tw if i % 2 else tw2}" cx="{x}" cy="{y}" r="{r}" fill="{PAPER}"/>'
                    for i, (x, y, r) in enumerate([(80, 40, 1.4), (190, 72, 1.1), (300, 30, 1.6), (530, 54, 1.2), (610, 26, 1.3),
                                                   (790, 48, 1.5), (820, 120, 1.1), (140, 130, 1.0), (470, 110, 1.2)]))
    s.add(f'<g clip-path="url(#fc)">{stars}',
          f'<g class="{sway}"><path d="{engrave_v(-4, W + 4, 120, H, 6, d, 5)}" fill="{PAPER}" opacity=".95"/></g>',
          f'<g class="{rise}"><circle cx="{mx}" cy="{my}" r="{mr + 10}" fill="{INK}" stroke="{PAPER}" stroke-width="1.5"/>'
          f'<circle cx="{mx}" cy="{my}" r="{mr}" fill="{RED}"/>'
          f'<g clip-path="url(#fm)"><path d="{engrave_h(my - mr, my + mr, mx - mr, mx + mr, 4.8, dm, 4)}" fill="#2a0204" opacity=".8"/></g></g>',
          '</g>')
    # bloco do nome sobre uma etiqueta de papel
    s.add(f'<rect x="38" y="60" width="380" height="150" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>',
          f'<rect x="44" y="210" width="380" height="7" fill="{RED}"/>',
          s.text(228, 122, 'Arthur Hecker', 'script', 60, INK, 'middle'),
          s.text(228, 152, 'H U B', 'serif', 20, RED, 'middle', ls=6),
          s.text(228, 178, 'DESENVOLVIDO POR ARTHUR HECKER SILVA', 'sans8', 9.5, GREY, 'middle', ls=2),
          s.text(228, 198, '© 2026 · alguns direitos possivelmente reservados', 'hand', 16, GREY2, 'middle'))
    save('footer.svg', s)


def main():
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])
    for name, fn in BUILDERS:
        if not only or name in only:
            fn()


BUILDERS = [('header', header), ('chapters', chapters), ('terminal', terminal), ('chat', chat),
            ('newton', newton), ('cards', cards), ('buttons', buttons), ('footer', footer)]

if __name__ == '__main__':
    main()
