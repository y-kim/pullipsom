"""README 의 견본 그림을 만든다.

    python3 scripts/specimen.py build/Pullipsom images

네 장을 만든다.

    pullipsom.png  맨 위의 이름 그림. 굵기가 가로 위치를 따라 변한다
    mixed.png     한글·한자·가나·라틴을 섞은 본문
    weights.png   여덟 굵기와 이탤릭
    coverage.png  글자 갈래별 견본
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import Family, WEIGHTS, canvas, crop, draw_ramp

INK, PAPER, GREY = (26, 26, 26), (255, 255, 255), (130, 130, 130)


def header(fam, out):
    """이름 그림. 굵기는 글자의 가로 위치로만 정한다."""
    size, pitch, pad = 132, 176, 300
    lines = ["풀잎솜 Pullipsom", "한글 漢字 かな"]
    span = max(fam.width(t, "Regular", size) for t in lines)
    for line in lines:
        gone = fam.missing(line)
        if gone:
            raise SystemExit("ERROR: 글꼴에 없는 글자: " + " ".join(gone))
    img, d = canvas((int(span) + 2 * pad, pitch * len(lines) + 2 * pad), PAPER)
    for i, line in enumerate(lines):
        x = pad + (span - fam.width(line, "Regular", size)) / 2
        draw_ramp(d, x, pad + pitch * (i + 1), line, fam, size, span=span,
                  origin=pad)
    crop(img, 40).save(out)
    print(out)


BODY = [
    ("Bold", 58, "活字(활자)와 組版(조판)"),
    (None, 0, ""),
    ("Regular", 40, "글자를 새긴 조각을 活字라 하고, 그 조각을 줄 세워"),
    ("Regular", 40, "紙面을 짜는 일을 組版이라 한다. 印刷는 거기에"),
    ("Regular", 40, "잉크를 묻혀 종이에 찍는 일이다."),
    (None, 0, ""),
    ("Italic", 40, "한자와 가나는 이탤릭에서도 곧게 선다 — 漢字 かな"),
    (None, 0, ""),
    ("Regular", 40, "日本語の漢字とかなも混ぜて組める。カタカナも。"),
    ("Regular", 40, "The quick brown fox jumps over the lazy dog."),
    ("Regular", 40, "Αα Ββ Γγ · Аа Бб Вв · ɑ ɛ ɪ ʃ ʒ · ½ ¾ №"),
]


def mixed(fam, out):
    width, pad = 1180, 60
    img, d = canvas((width, 900), PAPER)
    y = pad + 60
    for style, size, text in BODY:
        if not text:
            y += 26
            continue
        gone = fam.missing(text)
        if gone:
            raise SystemExit("ERROR: 글꼴에 없는 글자: " + " ".join(gone))
        d.text((pad, y), text, font=fam.face(style, size), fill=INK, anchor="ls")
        y += int(size * 1.62)
    crop(img, 34).save(out)
    print(out)


def weights(fam, out):
    size, pad = 46, 60
    img, d = canvas((1180, 40 + len(WEIGHTS) * 78), PAPER)
    y = pad + 20
    for w in WEIGHTS:
        d.text((pad, y), w, font=fam.face("Regular", 22), fill=GREY, anchor="ls")
        d.text((pad + 170, y), "한글 漢字 かな Pullipsom 0123",
               font=fam.face(w, size), fill=INK, anchor="ls")
        italic = w + "Italic" if w != "Regular" else "Italic"
        d.text((pad + 830, y), "이탤릭 Italic",
               font=fam.face(italic, size), fill=INK, anchor="ls")
        y += 78
    crop(img, 34).save(out)
    print(out)


ROWS = [
    ("한글 11,172자", "다람쥐 헌 쳇바퀴에 타고파 · 웬 쇰말 꽃삽 뷁"),
    ("한자 28,000여자", "漢字 韓國 東京 龍 鬱 齒 爨 麤 靐"),
    ("가나", "ひらがな カタカナ ヴォ ﾊﾝｶｸ ぱぴぷぺぽ"),
    ("라틴·그리스·키릴", "Hamburgefonstiv Ταχίστη Съешь ещё"),
    ("국제음성기호", "[pʰullipsom] ɑ ɛ ɪ ɔ ʊ ʃ ʒ θ ð ŋ ɾ"),
    ("숫자와 기호", "0123456789 ½ ⅓ ¾ ₩ € ± × ÷ ≠ ≤ ∞"),
    ("수학", "∈ ∉ ⊂ ⊄ ⊆ ⊊ ∩ ∪ ∧ ∨ ∴ ∵ ≡ ≒ ⊕ ⊗"),
    ("기호와 괄호", "「」『』〈〉【】 ※ ○ ● ■ □ ① ㉮ ㈜ ℃ ㎏"),
]


def coverage(fam, out):
    size, pad = 40, 60
    img, d = canvas((1180, 60 + len(ROWS) * 74), PAPER)
    y = pad + 20
    for label, text in ROWS:
        gone = fam.missing(text)
        if gone:
            raise SystemExit("ERROR: 글꼴에 없는 글자: " + " ".join(gone))
        d.text((pad, y), label, font=fam.face("Regular", 21), fill=GREY, anchor="ls")
        d.text((pad + 250, y), text, font=fam.face("Regular", size), fill=INK,
               anchor="ls")
        y += 74
    crop(img, 34).save(out)
    print(out)


def main(argv):
    directory = argv[1] if len(argv) > 1 else "build/Pullipsom"
    out_dir = argv[2] if len(argv) > 2 else "images"
    fam = Family(directory)
    os.makedirs(out_dir, exist_ok=True)
    header(fam, os.path.join(out_dir, "pullipsom.png"))
    mixed(fam, os.path.join(out_dir, "mixed.png"))
    weights(fam, os.path.join(out_dir, "weights.png"))
    coverage(fam, os.path.join(out_dir, "coverage.png"))


if __name__ == "__main__":
    main(sys.argv)
