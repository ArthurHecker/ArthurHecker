"""Gera as artes fixas do perfil (assets/*.svg) no estilo do arthurhecker.space.

    pip install fonttools brotli
    python tools/build.py

As artes com números do GitHub (painel, gravura, cobra) e a linha do tempo dos
estudos vêm de tools/vivo.py: rode isto antes de cada push para atualizá-las.
"""
from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vivo  # noqa: E402
from svgkit import (BOOK, GOLD, GREY, GREY2, INK, PAPER, RED, Svg, Timeline,  # noqa: E402
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
            'Gravura: um dev diante de uma lua vermelha, num balcão à noite; balões dizem '
            '"Oi! Eu sou o Arthur.", "Bem-vindo!" e "Puxe uma cadeira, o código já está compilando...". '
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
    s.add(f'<g class="{b1}"><path d="{balloon(712, 96, 128, 38, (646, 186))}" {stroke}/>',
          s.text(712, 106, 'Oi! Eu sou o Arthur.', 'hand', 29, INK, 'middle'), '</g>')
    s.add(f'<g class="{b2}"><path d="{balloon(318, 118, 128, 64, (470, 200), spiky=True, seed=7)}" {stroke}/>',
          s.text(318, 131, 'Bem-vindo!', 'hand', 38, INK, 'middle', extra=f' stroke="{INK}" stroke-width=".9"'), '</g>')
    s.add(f'<g class="{b3}"><path d="{balloon(330, 120, 172, 56, (520, 214), seed=5)}" {stroke}/>',
          s.text(330, 112, 'Puxe uma cadeira, o código', 'hand', 28, INK, 'middle'),
          s.text(330, 141, 'já está compilando...', 'hand', 28, INK, 'middle'), '</g>')

    # etiqueta com o nome (como a prévia do site)
    lx, ly, lw, lh = 24, 290, 372, 80
    s.add(f'<rect x="{lx + 6}" y="{ly + lh}" width="{lw}" height="7" fill="{RED}"/>',
          f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>',
          s.text(lx + 18, ly + 50, 'Arthur Hecker', 'script', 56, INK),
          s.text(lx + 22, ly + 69, 'ARTHURHECKER.SPACE', 'sans8', 11.5, RED, ls=3.1))

    # barra do terminal: 03:00 e o que o Arthur faz, digitado em loop
    s.add(f'<rect x="{px}" y="{py}" width="{pw}" height="35" fill="{INK}"/>')
    prompt = 'C:\\arthur>'
    fs = 22
    pxw = BOOK.width('mono', prompt, fs)
    s.add(s.text(16, 27, prompt, 'mono', fs, GREY2))
    phrases = [
        'Engenharia da Computação + Ciência de Dados',
        'full-stack: Python, Django, JavaScript, Three.js',
        'fazendo os dados contarem histórias',
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
    ('I', 'SOBRE MIM', 'Quem é o Arthur',
     'Dev full-stack em formação, movido a café, curiosidade e bugs de madrugada.'),
    ('II', 'ESTUDOS', 'Duas graduações',
     'Uma para construir os sistemas, outra para entender os dados que eles geram.'),
    ('III', 'FERRAMENTAS', 'Caixa de ferramentas',
     'O que eu uso para transformar uma ideia em alguma coisa funcionando.'),
    ('IV', 'ATIVIDADE', 'Commits em gravura',
     'Os meus números do GitHub, desenhados no mesmo traço do meu site.'),
    ('V', 'CONTATO', 'Até a próxima',
     'Quer trocar uma ideia? É só chamar.'),
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
    idx = [c[0] for c in CHAPTERS].index(num) + 1
    s.add(s.text(26, 34, f'{idx:02d}  ·  {tag}', 'sans8', 11.5, RED, ls=3))
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
        ('out', [('  estudo    ', RED), ('Engenharia da Computação', PAPER), (' · Faculdade Galileu', DIM)]),
        ('out', [('            ', RED), ('Ciência de Dados', PAPER), (' · Univesp', DIM)]),
        ('out', [('  faço      ', RED), ('sites, bots, jogos e servidores, de ponta a ponta', FG)]),
        ('out', [('  gosto de  ', RED), ('web, ', FG), ('3D no navegador', GOLD), (', dados e IA', FG)]),
        ('out', [('  servidor  ', RED), ('um Linux só meu, administrado por mim (às 3h, claro)', FG)]),
        ('out', [('  status    ', RED), ('compilando... ', FG), ('com café', DIM)]),
        ('gap', None),
        ('end', None),
    ]
    top = 36
    H = top + 22 + lh * len(lines) + 20
    s = Svg(W, H, 'C:\\WINDOWS\\system32\\cmd.exe — sobre o Arthur',
            'Terminal do Windows: whoami responde arthur-hecker-silva; type sobre.txt mostra estudos '
            '(Engenharia da Computação na Faculdade Galileu e Ciência de Dados na Univesp), o que faz '
            '(sites, bots, jogos e servidores), do que gosta e o servidor Linux próprio.')
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


# ------------------------------------------------------------------ botões e rodapé

BUTTONS = [
    ('site', 'ARTHURHECKER.SPACE', 'moon'),
    ('linkedin', 'LINKEDIN', 'in'),
    ('instagram', 'INSTAGRAM', 'ig'),
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
            'Rodapé: céu escuro com a lua vermelha subindo; "Arthur Hecker", "obrigado pela visita".')
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
          s.text(228, 152, 'obrigado pela visita', 'serif', 19, RED, 'middle', ls=1),
          s.text(228, 178, 'GITHUB.COM/ARTHURHECKER', 'sans8', 9.5, GREY, 'middle', ls=2),
          s.text(228, 198, 'até o próximo commit', 'hand', 17, GREY2, 'middle'))
    save('footer.svg', s)


def main():
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])
    for name, fn in BUILDERS:
        if not only or name in only:
            fn()


BUILDERS = [('header', header), ('chapters', chapters), ('terminal', terminal),
            ('buttons', buttons), ('footer', footer), ('vivo', lambda: vivo.build_all(OUT))]

if __name__ == '__main__':
    main()
