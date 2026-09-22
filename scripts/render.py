"""견본 그림을 그리는 공통 부분.

가변폭 글꼴이라 글자 폭을 칸으로 세지 않는다. 글줄은 통째로 넘겨서
FreeType 과 Raqm 이 커닝과 합자를 적용하게 둔다. 굵기를 섞어 그릴 때만
글자 단위로 끊고, 그때는 hmtx 의 폭을 직접 읽어 이어 붙인다.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

# 가는 것부터. Text 는 Regular 와 Medium 사이에 있는 IBM Plex 고유의 굵기다.
WEIGHTS = ["Thin", "ExtraLight", "Light", "Regular",
           "Text", "Medium", "SemiBold", "Bold"]


class Family:
    """글꼴 한 가족. 굵기와 이탤릭을 이름으로 꺼내 쓴다."""

    def __init__(self, directory, prefix="Pullipsom"):
        self.dir, self.prefix = directory, prefix
        self._faces, self._adv = {}, {}

    def path(self, style):
        return os.path.join(self.dir, "%s-%s.ttf" % (self.prefix, style))

    def face(self, style="Regular", size=64):
        key = (style, size)
        if key not in self._faces:
            self._faces[key] = ImageFont.truetype(self.path(style), size)
        return self._faces[key]

    def advances(self, style="Regular"):
        """코드포인트 -> 폭 (1000 단위). 굵기를 섞어 그릴 때만 쓴다."""
        if style not in self._adv:
            tt = TTFont(self.path(style), lazy=True)
            upem = tt["head"].unitsPerEm
            hmtx = tt["hmtx"]
            self._adv[style] = {cp: hmtx[g][0] * 1000 / upem
                                for cp, g in tt.getBestCmap().items()}
        return self._adv[style]

    def missing(self, text, style="Regular"):
        adv = self.advances(style)
        return [c for c in text if ord(c) not in adv and not c.isspace()]

    def width(self, text, style="Regular", size=64):
        """글줄 전체의 폭. 커닝이 들어간 실제 값이다."""
        return self.face(style, size).getlength(text)


def draw_ramp(draw, x, y, text, family, size, weights=None, span=None, origin=None):
    """글자마다 굵기를 바꿔 가며 한 줄을 그린다.

    굵기는 글자의 가로 위치로만 정한다. 왼쪽 끝이 가장 가늘고 오른쪽 끝이
    가장 굵으며, 같은 세로축에 놓인 글자는 줄이 달라도 같은 굵기가 된다.
    """
    weights = weights or WEIGHTS
    span = span or family.width(text, "Regular", size)
    origin = x if origin is None else origin
    last = len(weights) - 1
    for ch in text:
        weight = weights[max(0, min(last, round((x - origin) / span * last)))]
        draw.text((x, y), ch, font=family.face(weight, size), fill=(0, 0, 0),
                  anchor="ls")
        x += family.advances(weight).get(ord(ch), 0) * size / 1000
    return x


def crop(img, margin=28, paper=(255, 255, 255)):
    """잉크가 닿은 사각형으로 잘라내고 여백을 두른다."""
    box = img.convert("L").point(lambda v: 255 - v).getbbox()
    if not box:
        return img
    left, top, right, bottom = box
    out = Image.new("RGB", (right - left + 2 * margin, bottom - top + 2 * margin),
                    paper)
    out.paste(img.crop((left, top, right, bottom)), (margin, margin))
    return out


def canvas(size, color=(255, 255, 255)):
    img = Image.new("RGB", size, color)
    return img, ImageDraw.Draw(img)
