# -*- coding: utf-8 -*-
"""변·방 가르기 — 기준 글리프와 대조한다. 같은 글리프가 안 나오면 버그다.

  PYTHONPATH=tools/src python -m unittest discover -s tests -v
"""
import glob, json, os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import split_golden as G


class SplitGolden(unittest.TestCase):
    pass


def _make(path):
    def test(self):
        with open(path, encoding='utf-8') as f:
            case = json.load(f)
        font = G.FONT % case['weight']
        if not os.path.exists(font):
            self.skipTest('소스 글꼴이 없다 — hapchija fetch 로 받는다: %s' % font)
        if G.sha256(font) != case['source']['sha256']:
            self.skipTest('소스 글꼴이 기준을 만들 때와 다르다: %s' % font)
        left, right = G.run(case)
        for name, got, want in (('변', left, case['left']), ('방', right, case['right'])):
            self.assertEqual(G.canon(got), G.canon(want),
                             '%s %s 의 %s 이 기준 글리프와 다르다' % (case['char'], case['weight'], name))
    return test


for _p in sorted(glob.glob(os.path.join(G.GOLDEN, '*.json'))):
    _n = os.path.splitext(os.path.basename(_p))[0]
    setattr(SplitGolden, 'test_%s' % _n, _make(_p))

if __name__ == '__main__':
    unittest.main()
