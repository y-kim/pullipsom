"""배포용 압축 파일을 만든다.

    python3 scripts/package.py            # build/Pullipsom → dist/Pullipsom_v{버전}.zip
    python3 scripts/package.py -o 시험.zip

이미 낸 버전의 압축 파일은 덮어쓰지 않는다. 레시피의 버전을 먼저 올린다.

압축 파일 안은 이렇게 놓는다. IBM Plex 의 배포판과 같은 나눔이다.

    Pullipsom/hinted/    힌팅을 넣은 글꼴. Windows 처럼 작은 크기에서 힌팅을 쓰는 곳
    Pullipsom/unhinted/  힌팅을 뺀 글꼴. macOS, 고해상도 화면, 웹. 파일이 절반쯤이다
    Pullipsom/LICENSE.md
    Pullipsom/README.md

레시피의 스타일이 두 쪽 모두에 다 있어야 만든다. 일부만 다시 빌드해서 예전 파일이
섞여 있으면 unhinted 쪽이 비므로 여기서 걸린다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    rec = json.load(open(os.path.join(ROOT, "recipes", "pullipsom.json"), encoding="utf-8"))
    family = rec["output"]["familyName"].replace(" ", "")
    ap = argparse.ArgumentParser(description="배포용 압축 파일을 만든다")
    ap.add_argument("build", nargs="?", default=os.path.join("build", family))
    ap.add_argument("-o", "--out", help="압축 파일 경로. 없으면 dist/{가족}_v{버전}.zip")
    args = ap.parse_args()
    build = os.path.join(ROOT, args.build)
    names = ["%s-%s.ttf" % (family, s["file"]) for s in rec["styles"]]
    sub = rec["finalize"]["unhintedDir"]

    missing = [os.path.join(d, n) for d in ("", sub) for n in names
               if not os.path.isfile(os.path.join(build, d, n))]
    for n in names:
        a, b = os.path.join(build, n), os.path.join(build, sub, n)
        if os.path.isfile(a) and os.path.isfile(b) and os.path.getmtime(b) < os.path.getmtime(a):
            missing.append("%s (hinted 보다 오래됨)" % os.path.join(sub, n))
    if missing:
        print("ERROR: 다음 파일이 없거나 맞지 않습니다. 16 스타일을 모두 다시 빌드하세요.", file=sys.stderr)
        for m in sorted(set(missing)):
            print("  " + m, file=sys.stderr)
        return 1

    out = args.out or os.path.join(ROOT, "dist", "%s_v%s.zip" % (family, rec["output"]["version"]))
    if os.path.exists(out):
        print("ERROR: %s 가 이미 있습니다. 낸 버전은 덮어쓰지 않습니다." % out, file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(build, n), "%s/hinted/%s" % (family, n))
            z.write(os.path.join(build, sub, n), "%s/unhinted/%s" % (family, n))
        for doc in ("LICENSE.md", "README.md"):
            z.write(os.path.join(ROOT, doc), "%s/%s" % (family, doc))
    print("%s  %d MB  %d 파일" % (os.path.relpath(out, ROOT), os.path.getsize(out) >> 20,
                                 len(zipfile.ZipFile(out).namelist())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
