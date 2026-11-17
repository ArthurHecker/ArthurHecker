"""Kit de SVG do perfil: fontes embutidas (só os caracteres usados), medida de
texto, linhas do tempo em CSS (animações em loop) e as linhas de gravura do site.

Usado por tools/build.py (artes fixas) e por .github/scripts/live.py (artes ao vivo).
Depende só de fontTools + brotli (pip install fonttools brotli).
"""
from __future__ import annotations

import base64
import io
import math
import os
from collections import defaultdict
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')

# paleta do arthurhecker.space
INK = '#0b0b0d'
PAPER = '#fdfcf9'
PAPER2 = '#f7f5f0'
RED = '#e3060c'
GOLD = '#c9a35e'
GREY = '#6a6865'
GREY2 = '#8a8782'
LINE = '#d8d5cf'
CREAM = '#efe9df'

FONTS = {
    'script': 'PinyonScript.ttf',   # logo "Arthur Hecker"
    'serif': 'BodoniModa-700.ttf',  # títulos
    'hand': 'PatrickHand.ttf',      # legendas e balões
    'sans': 'Inter-500.ttf',
    'sans7': 'Inter-700.ttf',
    'sans8': 'Inter-800.ttf',       # rótulos em caixa alta
    'mono': 'VT323.ttf',            # terminal
    'pixel': 'PressStart2P.ttf',    # arcade
}


class FontBook:
    def __init__(self):
        self._f = {}
        self._adv = {}

    def font(self, key):
        if key not in self._f:
            f = TTFont(os.path.join(FONT_DIR, FONTS[key]))
            self._f[key] = f
            cmap = f.getBestCmap()
            hmtx = f['hmtx'].metrics
            upm = f['head'].unitsPerEm
            self._adv[key] = (cmap, hmtx, upm)
        return self._f[key]

    def width(self, key, text, size, ls=0.0):
        self.font(key)
        cmap, hmtx, upm = self._adv[key]
        w = 0
        for ch in text:
            g = cmap.get(ord(ch))
            w += hmtx[g][0] if g else upm * 0.5
        return w * size / upm + ls * max(0, len(text) - 1)

    def has(self, key, ch):
        self.font(key)
        return ord(ch) in self._adv[key][0]

    def woff2(self, key, chars):
        o = subset.Options()
        o.flavor = 'woff2'
        o.hinting = False
        o.layout_features = ['kern', 'liga', 'calt', 'ccmp', 'locl', 'mark', 'mkmk']
        o.name_IDs = []
        o.notdef_outline = True
        f = TTFont(os.path.join(FONT_DIR, FONTS[key]))
        s = subset.Subsetter(o)
        s.populate(text=''.join(sorted(chars)) + ' ')
        s.subset(f)
        buf = io.BytesIO()
        f.flavor = 'woff2'
        f.save(buf)
        return base64.b64encode(buf.getvalue()).decode()

    def wrap(self, key, text, size, maxw):
        lines, cur = [], ''
        for word in text.split(' '):
            t = (cur + ' ' + word).strip()
            if cur and self.width(key, t, size) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = t
        if cur:
            lines.append(cur)
        return lines


BOOK = FontBook()


def f1(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


class Svg:
    """Monta um SVG com fontes embutidas e CSS próprio."""

    def __init__(self, w, h, title, desc=''):
        self.w, self.h = w, h
        self.title, self.desc = title, desc
        self.parts = []
        self.defs = []
        self.css = []
        self.used = defaultdict(set)
        self._n = 0

    def uid(self, p='e'):
        self._n += 1
        return f'{p}{self._n}'

    def add(self, *s):
        self.parts.extend(s)

    def text(self, x, y, s, font='sans', size=16, fill=INK, anchor='start', ls=0, cls=None, extra=''):
        self.used[font].update(s)
        a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
        l = f' letter-spacing="{f1(ls)}"' if ls else ''
        c = f' class="{cls}"' if cls else ''
        return (f'<text x="{f1(x)}" y="{f1(y)}" font-family="ah-{font}" font-size="{f1(size)}" '
                f'fill="{fill}"{a}{l}{c}{extra}>{escape(s)}</text>')

    def rich(self, x, y, runs, font='sans', size=16, anchor='start', cls=None, extra=''):
        """Texto com trechos coloridos: runs = [(texto, cor, fonte|None), ...]."""
        spans = []
        for r in runs:
            t, col = r[0], r[1]
            fnt = r[2] if len(r) > 2 and r[2] else font
            self.used[fnt].update(t)
            ff = f' font-family="ah-{fnt}"' if fnt != font else ''
            spans.append(f'<tspan fill="{col}"{ff}>{escape(t)}</tspan>')
        a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
        c = f' class="{cls}"' if cls else ''
        return (f'<text x="{f1(x)}" y="{f1(y)}" font-family="ah-{font}" font-size="{f1(size)}"{a}{c}{extra} '
                f'xml:space="preserve">{"".join(spans)}</text>')

    def render(self):
        faces = []
        for key, chars in self.used.items():
            if not chars:
                continue
            faces.append(f"@font-face{{font-family:'ah-{key}';src:url(data:font/woff2;base64,{BOOK.woff2(key, chars)}) format('woff2')}}")
        style = '\n'.join(faces + [
            'text{text-rendering:geometricPrecision;font-kerning:normal}',
            '.ff{transform-box:fill-box;transform-origin:center}',
        ] + self.css)
        defs = ''.join(self.defs)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t d">'
                f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
                f'<style>{style}</style><defs>{defs}</defs>{"".join(self.parts)}</svg>\n')


class Timeline:
    """Animações em loop com período fixo: cada elemento recebe um @keyframes próprio
    com os tempos em segundos convertidos para porcentagem do período."""

    def __init__(self, svg: Svg, period: float):
        self.svg, self.T = svg, period

    def pct(self, t):
        return max(0.0, min(100.0, t / self.T * 100))

    def keyframes(self, stops, timing='linear', loop=True):
        """stops = [(t, 'css; css', timing|None), ...] ordenados por t."""
        name = self.svg.uid('k')
        rows = []
        for st in stops:
            t, css = st[0], st[1]
            tf = st[2] if len(st) > 2 and st[2] else None
            tfs = f'animation-timing-function:{tf};' if tf else ''
            rows.append(f'{self.pct(t):.4f}%{{{css};{tfs}}}')
        self.svg.css.append(f'@keyframes {name}{{{"".join(rows)}}}')
        cls = self.svg.uid('a')
        it = 'infinite' if loop else '1'
        fill = '' if loop else ' both'
        self.svg.css.append(f'.{cls}{{animation:{name} {self.T}s {timing} {it}{fill}}}')
        return cls

    def show(self, t_on, t_off=None, fade=0.3, rise=0.0):
        """Aparece em t_on (com subida opcional em px) e some em t_off (padrão: fim do loop)."""
        t_off = self.T - 0.6 if t_off is None else t_off
        a = 0.004
        tr0 = f'transform:translateY({rise}px)' if rise else 'transform:none'
        stops = [(0, f'opacity:0;{tr0}'), (t_on - a, f'opacity:0;{tr0}'),
                 (min(t_on + fade, t_off), 'opacity:1;transform:none'),
                 (t_off, 'opacity:1;transform:none'), (min(self.T, t_off + fade), f'opacity:0;transform:none'),
                 (self.T, 'opacity:0;transform:none')]
        return self.keyframes(stops, timing='ease-out')

    def typing(self, t_on, n, width, cps=18.0, t_off=None):
        """Cobertura que corre para a direita em saltos de um caractere (texto monoespaçado)."""
        dur = max(0.05, n / cps)
        t_off = self.T - 0.6 if t_off is None else t_off
        stops = [(0, 'transform:translateX(0)'), (t_on, 'transform:translateX(0)', f'steps({max(1, n)},end)'),
                 (t_on + dur, f'transform:translateX({f1(width)}px)'), (self.T, f'transform:translateX({f1(width)}px)')]
        return self.keyframes(stops), dur

    def cursor(self, t_on, n, width, cps=18.0):
        """Cursor que acompanha a digitação e some no fim."""
        dur = max(0.05, n / cps)
        a = 0.004
        stops = [(0, 'opacity:0;transform:translateX(0)'), (t_on - a, 'opacity:0;transform:translateX(0)'),
                 (t_on, 'opacity:1;transform:translateX(0)', f'steps({max(1, n)},end)'),
                 (t_on + dur, f'opacity:1;transform:translateX({f1(width)}px)'),
                 (t_on + dur + 0.25, f'opacity:0;transform:translateX({f1(width)}px)'),
                 (self.T, f'opacity:0;transform:translateX({f1(width)}px)')]
        return self.keyframes(stops)


def blink(svg: Svg, period=1.0):
    name = svg.uid('k')
    svg.css.append(f'@keyframes {name}{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}')
    cls = svg.uid('a')
    svg.css.append(f'.{cls}{{animation:{name} {period}s steps(1,end) infinite}}')
    return cls


def css_anim(svg: Svg, frames: str, dur: float, timing='ease-in-out', extra='infinite', origin=None):
    """Animação livre: frames = '0%{...}100%{...}'."""
    name = svg.uid('k')
    svg.css.append(f'@keyframes {name}{{{frames}}}')
    cls = svg.uid('a')
    o = f'transform-box:fill-box;transform-origin:{origin};' if origin else ''
    svg.css.append(f'.{cls}{{{o}animation:{name} {dur}s {timing} {extra}}}')
    return cls


# ---------------------------------------------------------------- gravura

def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def engrave_v(x0, x1, y0, y1, gap, dark, maxw, wave=None, dy=9.0):
    """Linhas verticais onduladas cuja espessura segue a escuridão dark(x, y) em 0..1
    (o "luz vira linha" da gravura do site). Devolve o atributo d de um path."""
    wave = wave or (lambda x, y: 1.5 * math.sin(y / 23 + x / 37) + 0.7 * math.sin(y / 9 + x * 0.31))
    out = []
    n = int((x1 - x0) / gap) + 1
    ys = []
    y = y0
    while y < y1:
        ys.append(y)
        y += dy
    ys.append(y1)
    for i in range(n):
        x = x0 + i * gap
        left, right = [], []
        mx = 0
        for yy in ys:
            cx = x + wave(x, yy)
            hw = max(0.12, clamp(dark(cx, yy)) * maxw / 2)
            mx = max(mx, hw)
            left.append((cx - hw, yy))
            right.append((cx + hw, yy))
        if mx <= 0.13:
            continue
        pts = left + right[::-1]
        out.append('M' + 'L'.join(f'{f1(px)} {f1(py)}' for px, py in pts) + 'Z')
    return ''.join(out)


def engrave_h(y0, y1, x0, x1, gap, dark, maxw, wave=None, dx=9.0):
    """Igual a engrave_v, com linhas horizontais."""
    wave = wave or (lambda x, y: 1.2 * math.sin(x / 21 + y / 31) + 0.5 * math.sin(x / 7 + y * 0.4))
    out = []
    n = int((y1 - y0) / gap) + 1
    xs = []
    x = x0
    while x < x1:
        xs.append(x)
        x += dx
    xs.append(x1)
    for i in range(n):
        y = y0 + i * gap
        top, bot = [], []
        mx = 0
        for xx in xs:
            cy = y + wave(xx, y)
            hw = max(0.12, clamp(dark(xx, cy)) * maxw / 2)
            mx = max(mx, hw)
            top.append((xx, cy - hw))
            bot.append((xx, cy + hw))
        if mx <= 0.13:
            continue
        pts = top + bot[::-1]
        out.append('M' + 'L'.join(f'{f1(px)} {f1(py)}' for px, py in pts) + 'Z')
    return ''.join(out)


def hand_line(x0, y, x1, amp=2.2, seed=1.0):
    """Sublinhado "à mão" (como o traço da abertura do site)."""
    w = x1 - x0
    return (f'M{f1(x0)} {f1(y + amp * 0.4)} C {f1(x0 + w * .13)} {f1(y - amp)}, {f1(x0 + w * .23)} {f1(y + amp * 1.2)}, '
            f'{f1(x0 + w * .35)} {f1(y)} S {f1(x0 + w * .57)} {f1(y - amp * 1.1 * seed)}, {f1(x0 + w * .67)} {f1(y + amp * .3)} '
            f'S {f1(x0 + w * .87)} {f1(y + amp * 1.1)}, {f1(x1)} {f1(y - amp * .6)}')


def panel(x, y, w, h, fill=PAPER, stroke=INK, sw=2, shadow=INK, off=7, extra=''):
    """Painel de papel com sombra chapada (o "card" do site)."""
    s = ''
    if shadow:
        s += f'<rect x="{f1(x + off)}" y="{f1(y + off)}" width="{f1(w)}" height="{f1(h)}" fill="{shadow}"/>'
    s += f'<rect x="{f1(x)}" y="{f1(y)}" width="{f1(w)}" height="{f1(h)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>'
    return s
