# -*- coding: utf-8 -*-
"""변·방 가르기의 기준 글리프(golden reference).

기준 글리프는 사람이 그림으로 보고 **맞다고 통과시킨** 자리의 결과다. 가르는
함수(`hapchija.outline.split_glyph`)를 고친 뒤 같은 입력에서 같은 글리프가 나오지
않으면 버그다.

한 자리 = tests/golden/split/<글자>-<굵기>.json
  source   — 소스 글꼴 파일 이름과 sha256 (다르면 대조하지 않고 건너뛴다)
  guide    — 안내로 쓴 변·방 윤곽 (같은 글자의 더 가는 굵기에서 떼어 낸 것). 파일에
             넣어 두어, 안내를 구하는 쪽이 바뀌어도 가르는 함수만 대조된다.
  left / right — 기준 글리프: 가르고 되살린 변 · 방 윤곽

등록 (사람이 통과시킨 뒤에만):
  python tests/split_golden.py register 祔 Medium Regular
    안내는 graft/shi_all.py 의 clean_split 으로 구한다 (작업 폴더가 있어야 한다).
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(ROOT, 'tests', 'golden', 'split')
FONT = os.path.join(ROOT, 'vendor', 'IBM-Plex-Sans-JP', 'IBMPlexSansJP-%s.ttf')
sys.path.insert(0, os.path.join(ROOT, 'tools', 'src'))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def dump(contours):
    """윤곽들 → [[[x, y, on], …], …] (좌표는 소수 셋째 자리까지)."""
    return [[[round(p.x, 3), round(p.y, 3), bool(p.on_curve)] for p in c] for c in contours]


def canon(data):
    """비교용 — 윤곽마다 가장 작은 온커브 점에서 시작하게 돌리고, 윤곽을 정렬한다.
    시작점과 윤곽 차례만 다른 것은 같은 글리프다. 돌아가는 방향은 그대로 본다."""
    out = []
    for c in data:
        c = [tuple(p) for p in c]
        ons = [i for i, p in enumerate(c) if p[2]] or [0]
        k = min(ons, key=lambda i: (c[i][0], c[i][1]))
        out.append(tuple(c[k:] + c[:k]))
    return sorted(out)


def load(contours_data):
    import fontforge
    out = []
    for c in contours_data:
        cc = fontforge.contour()
        cc.is_quadratic = True
        for x, y, on in c:
            cc += fontforge.point(x, y, on)
        cc.closed = True
        out.append(cc)
    return out


def glyph(ch, weight):
    import fontforge
    path = FONT % weight
    f = fontforge.open(path)
    try:
        return [c.dup() for c in f[ord(ch)].foreground]
    finally:
        f.close()


def run(case):
    """기준 파일 하나의 입력으로 지금의 함수를 돌려 (변, 방) 을 dump 꼴로."""
    from hapchija import outline as O
    orig = glyph(case['char'], case['weight'])
    left, right = O.split_glyph(orig, load(case['guide']['left']), load(case['guide']['right']))
    return dump(left), dump(right)


def register(ch, weight, guide_weight):
    sys.path[:0] = [os.path.join(ROOT, 'scripts'), os.path.join(ROOT, 'graft')]
    import fontforge
    import shi_all as A
    gf = fontforge.open(FONT % guide_weight)
    got = A.clean_split(gf[ord(ch)])
    if not got:
        sys.exit('%s %s 에서 변·방이 떨어지지 않는다 — 안내가 못 된다' % (ch, guide_weight))
    case = {
        'char': ch, 'codepoint': 'U+%04X' % ord(ch), 'weight': weight,
        'source': {'file': os.path.basename(FONT % weight), 'sha256': sha256(FONT % weight)},
        'guide': {'weight': guide_weight, 'left': dump(got[0]), 'right': dump(got[1])},
    }
    gf.close()
    case['left'], case['right'] = run(case)
    os.makedirs(GOLDEN, exist_ok=True)
    path = os.path.join(GOLDEN, '%s-%s.json' % (ch, weight))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(case, f, ensure_ascii=False, indent=1)
    print(path, '변 %d · 방 %d 윤곽' % (len(case['left']), len(case['right'])))


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == 'register':
        register(*sys.argv[2:])
    else:
        sys.exit(__doc__)
