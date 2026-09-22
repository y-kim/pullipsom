"""빌드한 글꼴이 레시피가 약속한 대로 나왔는지 잰다.

    python3 scripts/audit.py build/Pullipsom

소스 글꼴 버전을 올리면 다시 돌려 보세요. 소스가 바뀌면 여기서 걸리는 종류의
문제가 통째로 다시 들어옵니다. 무엇을 왜 재는지는 RECIPE.md 에 있습니다.

    1. 한글·한자·가나의 세로 위치
    2. 레시피가 적은 만큼만 내려갔는지 (소스와 한 글자씩 대조)
    3. 수학 축에서 벗어난 기호
    4. 한 블록 안에서 폭이 갈리는 곳
    5. 폭이 0 이 아닌 결합 기호
    6. 굵기마다 다른 커버리지
"""

from __future__ import annotations

import glob
import os
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

FULL = 1000          # 전각 폭
AXIS = 305           # 수학 축. IBM Plex Sans 의 + = − × ÷ 가 놓인 자리
AXIS_TOLERANCE = 25  # 축에서 이만큼 벗어나면 알린다

BLOCKS = [
    (0x2000, 0x206F, "General Punctuation"), (0x2100, 0x214F, "Letterlike"),
    (0x2150, 0x218F, "Number Forms"), (0x2190, 0x21FF, "Arrows"),
    (0x2200, 0x22FF, "Mathematical Operators"), (0x2300, 0x23FF, "Misc Technical"),
    (0x2460, 0x24FF, "Enclosed Alphanumerics"), (0x25A0, 0x25FF, "Geometric Shapes"),
    (0x2600, 0x26FF, "Misc Symbols"), (0x2700, 0x27BF, "Dingbats"),
]

# 축에 세우기로 한 기호. RECIPE.md "수학 축" 을 보세요.
ON_AXIS = ("+=−×÷≈≠∞∝∈∉∊∋∧∨∩∪⊂⊃⊄⊅⊆⊇≡≢≒∼∽≃≅⊕⊖⊗⊘⊙⊞⊠∅")


def body(font, codepoints, skip_marks=True, percentile=0.95):
    """자면의 위끝·아래끝·중심. 상위 5% 로 잰다. 최대값은 한두 글자가 끌어올린다."""
    cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
    tops, bots, centers, widths = [], [], [], []
    for code in codepoints:
        if code not in cmap:
            continue
        if skip_marks and unicodedata.decomposition(chr(code)):
            continue                      # 탁점이 붙은 가나 등은 위로 넘친다
        pen = BoundsPen(glyphs)
        glyphs[cmap[code]].draw(pen)
        if not pen.bounds:
            continue
        x0, y0, x1, y1 = pen.bounds
        tops.append(y1)
        bots.append(y0)
        centers.append((y0 + y1) / 2)
        widths.append(hmtx[cmap[code]][0])
    if not tops:
        return None
    pick = lambda v, q: sorted(v)[min(len(v) - 1, int(len(v) * q))]
    return {
        "n": len(tops), "top": pick(tops, percentile), "bottom": pick(bots, 1 - percentile),
        "center": statistics.median(centers), "widths": Counter(widths),
    }


def vertical(font):
    print("## 세로 위치 (자면 상위 5%)")
    groups = [
        ("한글", range(0xAC00, 0xD7A4)),
        ("한자", list(range(0x4E00, 0xA000)) + list(range(0x3400, 0x4DC0))),
        ("히라가나", range(0x3041, 0x3097)),
        ("가타카나", range(0x30A1, 0x30FB)),
        ("반각 가타카나", range(0xFF66, 0xFFA0)),
        ("CJK 구두점", range(0x3000, 0x3040)),
        ("전각 기호", list(range(0x2460, 0x2500)) + list(range(0x3200, 0x3300))),
        ("라틴 대문자", range(0x41, 0x5B)),
    ]
    for label, codes in groups:
        m = body(font, codes)
        if m:
            print("   %-14s n=%5d  위끝 %4d  아래끝 %5d  중심 %6.1f"
                  % (label, m["n"], m["top"], m["bottom"], m["center"]))


# 소스에서 이만큼 줄이고 이만큼 내려와 있어야 한다. RECIPE.md "세로 정렬" 의 표와 같다.
# 배율은 가로세로가 같은 값이어야 한다.
EXPECTED = [
    ("한자", 0.9603, -53, [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0xF900, 0xFAFF), (0x2E80, 0x2FDF)]),
    ("가나", 0.9603, -53, [(0x3041, 0x3096), (0x30A1, 0x30FA), (0x30FC, 0x30FF), (0xFF66, 0xFF9F)]),
    ("、。", 0.9603, -53, [(0x3001, 0x3002)]),
]
CJK_SOURCES = ["IBM-Plex-Sans-JP/IBMPlexSansJP-Regular.ttf",
               "IBM-Plex-Sans-TC/IBMPlexSansTC-Regular.ttf",
               "IBM-Plex-Sans-SC/IBMPlexSansSC-Regular.ttf"]


def shape(font, cmap, glyphs, hmtx, code):
    """자면 상자의 위끝과 크기, 가로 자리, 폭. 평행이동만 했다면 위끝 말고는 다 같아야 한다."""
    if code not in cmap:
        return None
    pen = BoundsPen(glyphs)
    glyphs[cmap[code]].draw(pen)
    if not pen.bounds:
        return None
    x0, y0, x1, y1 = pen.bounds
    return (y1, x1 - x0, y1 - y0, x0, hmtx[cmap[code]][0])


def against_sources(font, vendor, sample=600):
    """소스와 한 글자씩 대조한다.

    한 글리프가 여러 코드포인트에 걸려 있으면 평행이동이 그 수만큼 먹을 수 있다.
    CJK 글꼴은 한자를 강희부수에도 매핑해 두므로 이 실수가 조용히 들어온다.
    소스에서 잰 값에 레시피가 적은 값을 더한 것과 결과가 같아야 한다. 평행이동만
    하므로 자면의 크기와 가로 자리, 폭은 소스와 똑같아야 한다.
    """
    print("\n## 레시피가 적은 만큼만 내려갔는지 (소스와 대조)")
    if not os.path.isdir(vendor):
        print("   %s 가 없어 건너뜀" % vendor)
        return 0
    srcs = []
    for rel in CJK_SOURCES:
        path = os.path.join(vendor, rel)
        if os.path.exists(path):
            f = TTFont(path, lazy=True)
            srcs.append((os.path.basename(path), f, f.getBestCmap(), f.getGlyphSet()))
    if not srcs:
        print("   소스 글꼴이 없어 건너뜀")
        return 0
    cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
    problems = 0
    for name, scale, dy, ranges in EXPECTED:
        codes = [c for lo, hi in ranges for c in range(lo, hi + 1) if c in cmap]
        step = max(1, len(codes) // sample)
        moved, resized = [], []
        for code in codes[::step]:
            got = shape(font, cmap, glyphs, hmtx, code)
            if got is None:
                continue
            cands = [shape(f, cm, gs, f["hmtx"], code) for _, f, cm, gs in srcs]
            cands = [c for c in cands if c]
            if not cands:
                continue
            want_top = lambda c: c[0] * scale + dy
            if min(abs(want_top(c) - got[0]) for c in cands) > 2:
                near = min(cands, key=lambda c: abs(want_top(c) - got[0]))
                moved.append((code, got[0], want_top(near)))
            # 가로세로에 같은 배율이 걸렸는지. 하나라도 어긋나면 비율이 깨진 것이다.
            if not any(abs(c[1] * scale - got[1]) <= 2 and abs(c[2] * scale - got[2]) <= 2
                       and abs(c[3] * scale - got[3]) <= 2
                       and abs(c[4] * scale - got[4]) <= 2 for c in cands):
                resized.append(code)
        print("   %-4s %5d 자 확인 (배율 %.4f, dy %+d)  세로 어긋남 %d, 크기·폭 어긋남 %d"
              % (name, len(codes[::step]), scale, dy, len(moved), len(resized)))
        for code, got, want in moved[:10]:
            print("      U+%04X %s  기대 %.0f, 실제 %.0f  (%+.0f)" % (code, chr(code), want, got, got - want))
        for code in resized[:10]:
            print("      U+%04X %s  자면 크기나 폭이 소스와 다르다" % (code, chr(code)))
        problems += len(moved) + len(resized)
    for _, f, _, _ in srcs:
        f.close()
    return problems


def math_axis(font):
    print("\n## 수학 축에서 벗어난 기호 (기준 %d, 허용 ±%d)" % (AXIS, AXIS_TOLERANCE))
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
    bad = []
    for ch in ON_AXIS:
        code = ord(ch)
        if code not in cmap:
            bad.append((ch, None))
            continue
        pen = BoundsPen(glyphs)
        glyphs[cmap[code]].draw(pen)
        if not pen.bounds:
            continue
        center = (pen.bounds[1] + pen.bounds[3]) / 2
        if abs(center - AXIS) > AXIS_TOLERANCE:
            bad.append((ch, center))
    if not bad:
        print("   없음 (%d자 확인)" % len(ON_AXIS))
    for ch, center in bad:
        print("   %s %s" % (ch, "글꼴에 없음" if center is None else "중심 %.1f" % center))
    return len(bad)


def cell_widths(font):
    """전각 칸이 몇 가지인지 알린다. 지금은 두 가지다 — 아직 정하는 중이라 실패로 세지 않는다."""
    print("\n## 폭 분포")
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    counts = {}
    for c, g in cmap.items():
        counts[hmtx[g][0]] = counts.get(hmtx[g][0], 0) + 1
    for w in sorted(counts, key=lambda x: -counts[x])[:6]:
        tag = {1000: " (Sans KR 이 정한 전각)", 960: " (한자·가나)", 892: " (한글)"}.get(w, "")
        print("   %5d 유닛 %6d 자%s" % (w, counts[w], tag))
    return 0


def widths(font):
    """잉크가 없는 글리프(공백)는 뺀다. 공백은 폭이 뜻이라 섞여 있는 것이 맞다."""
    print("\n## 한 블록 안에서 폭이 갈리는 곳")
    cmap, hmtx, glyphs = font.getBestCmap(), font["hmtx"], font.getGlyphSet()
    for lo, hi, name in BLOCKS:
        full, prop = [], []
        for code in range(lo, hi + 1):
            if code not in cmap:
                continue
            pen = BoundsPen(glyphs)
            glyphs[cmap[code]].draw(pen)
            if not pen.bounds:
                continue
            (full if hmtx[cmap[code]][0] == FULL else prop).append(code)
        if full and prop:
            print("   %-24s 전각 %3d / 비례 %3d" % (name, len(full), len(prop)))
            print("      전각: " + "".join(chr(c) for c in full))


def marks(font):
    print("\n## 폭이 0 이 아닌 결합 기호")
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    bad = [c for c in list(range(0x300, 0x370)) + list(range(0x20D0, 0x2100))
           if c in cmap and hmtx[cmap[c]][0] != 0]
    print("   " + (" ".join("U+%04X" % c for c in bad) if bad else "없음"))
    return len(bad)


def coverage(directory):
    print("\n## 굵기마다 다른 커버리지")
    sizes = {}
    for path in sorted(glob.glob(os.path.join(directory, "*.ttf"))):
        font = TTFont(path, lazy=True)
        sizes[os.path.basename(path)] = set(font.getBestCmap())
        font.close()
    common = set.intersection(*sizes.values())
    for name, codes in sizes.items():
        extra = len(codes) - len(common)
        print("   %-34s %6d자%s" % (name, len(codes), "" if not extra else "  (+%d)" % extra))
    missing = defaultdict(list)
    union = set.union(*sizes.values())
    for code in union - common:
        for name, codes in sizes.items():
            if code not in codes:
                missing[name].append(code)
    for name, codes in missing.items():
        print("   %s 에만 없는 %d자: %s" % (name, len(codes),
              " ".join("U+%04X" % c for c in sorted(codes)[:8]) + (" ..." if len(codes) > 8 else "")))


def main(argv):
    directory = argv[1] if len(argv) > 1 else "build/Pullipsom"
    regular = os.path.join(directory, "Pullipsom-Regular.ttf")
    if not os.path.exists(regular):
        raise SystemExit("ERROR: %s 가 없습니다" % regular)
    font = TTFont(regular)
    print("# %s\n" % regular)
    vertical(font)
    problems = against_sources(font, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(directory))), "vendor") if not os.path.isdir("vendor") else "vendor")
    problems += math_axis(font)
    problems += cell_widths(font)
    widths(font)
    problems += marks(font)
    coverage(directory)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
