# -*- coding: utf-8 -*-
"""한자 자형을 손볼 때 쓰는 연장.

풀잎솜은 IBM Plex Sans JP 의 한자를 그대로 쓰는데, 그 가운데에는 일본 자형과
한국 자형이 갈리는 글자가 있다. 그런 글자는 **선을 새로 그리지 않고** 고친다 —
같은 글꼴 안에서 한국 자형을 가진 다른 글자를 찾아 그 부분을 옮겨 심거나,
제 획을 옮기거나, 흰 칸을 트거나, 눕은 획을 세운다.

윤곽을 재고 가르고 놓고 자르는 연장은 합치자 (`hapchija.outline`) 에 있다 —
레시피의 op 도 같은 것을 쓰기 때문이다. 이 파일은 그것을 그대로 내보내고,
풀잎솜 쪽 일만 더 얹는다.

    소스      WEIGHTS SHORT source
    재기      stroke_runs — 글꼴 파일을 FreeType 으로 그려 본다
    보기      sheet edu_image korean_font

쓰는 법은 짧다. 굵기마다 소스를 열고, 손보고, 따로 뽑아 두었다가 리뷰 페이지에서
여덟 굵기를 나란히 본다. 굵은 굵기에서 획이 붙어 버리는 일이 잦으니 여덟 굵기를
모두 확인해야 한다.
"""

from __future__ import annotations

import base64
import io
import json
import os

from hapchija.outline import *            # noqa: F401,F403 — 연장은 합치자에 있다
from hapchija.outline import box, bbox, runs, dup   # 이 파일에서 직접 쓰는 것

WEIGHTS = ['Thin', 'ExtraLight', 'Light', 'Regular', 'Text', 'Medium', 'SemiBold', 'Bold']
SHORT = {'Thin': 'Th', 'ExtraLight': 'EL', 'Light': 'Lt', 'Regular': 'Rg',
         'Text': 'Tx', 'Medium': 'Md', 'SemiBold': 'SB', 'Bold': 'Bd'}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLEX_JP = os.path.join(ROOT, 'vendor/IBM-Plex-Sans-JP/IBMPlexSansJP-%s.ttf')


def source(weight):
    """그 굵기의 IBM Plex Sans JP 파일."""
    return PLEX_JP % weight


# ─── 재기 ────────────────────────────────────────────────────────────────

def stroke_runs(path, ch, y, size=1000, base=800):
    """글꼴 파일을 **진짜 래스터라이저**로 그려 그 높이의 먹 구간을 잰다.

    윤곽을 직접 채워 보는 raster() 와 달리 FreeType 이 그린 결과를 본다.
    맞댄 변에 실낱이 비치는지 같은 것은 이쪽으로 봐야 한다.
    """
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(path, size)
    im = Image.new('L', (size, size), 255)
    ImageDraw.Draw(im).text((0, base), ch, 0, font=f, anchor='ls')
    a = np.array(im) < 128
    return runs(a[base - int(y)])


# ─── 보기 ────────────────────────────────────────────────────────────────

def edu_image(ch, size=None):
    """교육부 편수자료 그림 — 비교용이다. 글꼴에 넣지 않는다."""
    from PIL import Image
    path = os.path.join(ROOT, 'review/data/edu_img2.json')
    if not os.path.exists(path):
        return None
    data = json.load(open(path, encoding='utf-8'))
    if ch not in data:
        return None
    im = Image.open(io.BytesIO(base64.b64decode(data[ch]))).convert('RGBA')
    im = Image.alpha_composite(Image.new('RGBA', im.size, (255,) * 4), im).convert('RGB')
    return im.resize((size, size), Image.LANCZOS) if size else im


def korean_font():
    """줄 이름에 쓸 한글 글꼴 — 빌드한 풀잎솜이 있으면 그것을 쓴다."""
    for p in (os.path.join(ROOT, 'build/Pullipsom/Pullipsom-Regular.ttf'),
              os.path.join(ROOT, 'vendor/IBM-Plex-Sans-KR/unhinted/IBMPlexSansKR-Regular.ttf')):
        if os.path.exists(p):
            return p
    return None


def sheet(rows, ch, out, cell=200, pad=10, label=130, header=40, ratio=0.82):
    """굵기를 가로로 늘어놓은 견본판을 그린다.

    rows 는 (이름, 파일 목록) 들. 파일 목록이 None 이면 편수자료 그림을
    첫 칸에 넣는다. 열 이름은 WEIGHTS 를 쓴다.
    """
    from PIL import Image, ImageDraw, ImageFont
    ncol = max(len(p) for _, p in rows if p) if any(p for _, p in rows) else len(WEIGHTS)
    names = WEIGHTS[:ncol]
    lab = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
    kl = ImageFont.truetype(korean_font(), 20) if korean_font() else lab
    im = Image.new('RGB', (label + ncol * (cell + pad) + pad,
                           header + len(rows) * (cell + pad) + pad), 'white')
    d = ImageDraw.Draw(im)
    for c, w in enumerate(names):
        d.text((label + c * (cell + pad) + cell // 2, header - 10), w, '#666', font=lab, anchor='ms')
    for r, (name, paths) in enumerate(rows):
        y = header + r * (cell + pad)
        d.text((label - 16, y + cell // 2), name, '#000', font=kl, anchor='rm')
        for c in range(ncol):
            x = label + c * (cell + pad)
            d.rectangle([x, y, x + cell, y + cell], outline='#e0e0e0')
            if paths is None:
                if c == 0:
                    e = edu_image(ch, cell)
                    if e:
                        im.paste(e, (x + 1, y + 1))
                continue
            f = ImageFont.truetype(paths[c], int(cell * ratio))
            d.text((x + cell // 2, y + int(cell * (ratio + 0.02))), ch, '#000', font=f, anchor='ms')
    im.save(out)
    return im.size


# ─── 옛 이름 ─────────────────────────────────────────────────────────────
# 되살린 조립 스크립트(`graft/recovered/`)가 쓰던 이름들. 연장을 합치자로 옮기며
# 이름을 다듬었는데, 옛 스크립트를 **그대로 돌려** 답지와 견주려면 다리가 필요하다.
# 새 코드는 오른쪽 이름을 쓴다.

def raster(glyph, n=1200, base=1000):
    """옛 이름 — 글리프를 판에 그린다. 지금은 `part_mask(윤곽 묶음)` 이다."""
    return part_mask(list(glyph.foreground), n=n, base=base)


clip_glyph = clip_contours          # 윤곽 묶음을 한 직선으로 자른다
to_contour = loop_contour           # 도막 목록을 fontforge 윤곽으로


def tidy(thing, tol=0.6):                                    # noqa: F811
    """옛 이름 — 글리프를 받으면 제자리에서 다듬고 지운 점 수를 돌려준다.

    지금 `hapchija.outline.tidy` 는 윤곽 묶음을 받아 (새 묶음, 지운 수) 를
    돌려준다. 되살린 스크립트는 글리프를 넘기므로 여기서 갈라 받는다.
    """
    from hapchija.outline import tidy as _tidy
    if not hasattr(thing, 'foreground'):
        return _tidy(thing, tol)
    import fontforge
    kept, gone = _tidy(list(thing.foreground), tol)
    lay = fontforge.layer()
    lay.is_quadratic = thing.foreground.is_quadratic
    for c in kept:
        lay += c
    width = thing.width
    thing.foreground = lay
    thing.width = width
    return gone


# 아래 아홉은 글리프를 받던 것을 **윤곽 묶음을 받도록** 바꾼 것들이다. 되살린
# 스크립트는 옛 꼴로 부르므로, 글리프가 오면 갈라 받아 같은 값을 돌려준다.

def _cs(g):
    return list(g.foreground) if hasattr(g, 'foreground') else g


def outer(g):                                                # noqa: F811
    from hapchija.outline import outer as _f
    return _f(_cs(g))


def split_parts(g, *a, **kw):                                # noqa: F811
    from hapchija.outline import split_parts as _f
    if hasattr(g, 'foreground'):
        return _f(list(g.foreground), g.width, *a, **kw)
    return _f(g, *a, **kw)


def part_side(g, *a, **kw):                                  # noqa: F811
    from hapchija.outline import part_side as _f
    if hasattr(g, 'foreground'):
        return _f(list(g.foreground), g.width, *a, **kw)
    return _f(g, *a, **kw)


def stretch(g, *a, **kw):                                    # noqa: F811
    from hapchija.outline import stretch as _f
    return _f(_cs(g), *a, **kw)


def stacked_counters(g, *a, **kw):                           # noqa: F811
    from hapchija.outline import stacked_counters as _f
    if hasattr(g, 'foreground'):
        return _f(list(g.foreground), g.width, *a, **kw)
    return _f(g, *a, **kw)


def flat_edge(g, *a, **kw):                                  # noqa: F811
    from hapchija.outline import flat_edge as _f
    return _f(_cs(g), *a, **kw)


def splice_detour(g, *a, **kw):                              # noqa: F811
    from hapchija.outline import splice_detour as _f
    got = _f(_cs(g), *a, **kw)
    if hasattr(g, 'foreground'):                             # 옛 꼴은 제자리에서 고쳤다
        import fontforge
        lay = fontforge.layer()
        lay.is_quadratic = g.foreground.is_quadratic
        for c in got:
            lay += c
        width = g.width
        g.foreground = lay
        g.width = width
        return got
    return got


def straighten(g, *a, **kw):                                 # noqa: F811
    from hapchija.outline import straighten as _f
    got, info = _f(_cs(g), *a, **kw)
    if hasattr(g, 'foreground'):        # 옛 꼴은 레이어를 돌려주었다
        import fontforge
        lay = fontforge.layer()
        lay.is_quadratic = g.foreground.is_quadratic
        for c in got:
            lay += c
        return lay, info
    return got, info
