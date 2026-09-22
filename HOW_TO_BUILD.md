# 글꼴 빌드 방법

빌드 도구는 [hapchija](https://github.com/y-kim/hapchija) 라는 별도 저장소에
있고, 이 저장소에는 `tools/` 서브모듈로 들어와 있습니다. 이 저장소가 가진 것은
레시피([recipes/pullipsom.json](recipes/pullipsom.json))와 견본 그림을 만드는
스크립트뿐입니다.

## 받기

서브모듈까지 같이 받고, 소스 글꼴을 내려받습니다.

```bash
git clone --recursive https://github.com/y-kim/pullipsom
cd pullipsom
PYTHONPATH=tools/src python3 -m hapchija fetch --recipe recipes/pullipsom.json
```

이미 클론했다면 `git submodule update --init` 을 먼저 실행하세요.

### 디렉터리

| | 내용 | git |
|---|---|---|
| `recipes/` | 레시피 | 추적 |
| `scripts/` | README 견본 그림을 만드는 스크립트 | 추적 |
| `vendor/` | 받아온 소스 글꼴 | 무시 |
| `work/` | 빌드 중간 산출물. 끝나면 지워집니다 | 무시 |
| `build/` | 생성된 TTF | 무시 |

소스 글꼴은 용량이 커서 저장소에 넣지 않습니다. 레시피의 `fetch` 가 받을 곳과
체크섬을 적어 두고, 받은 압축 파일은 `~/.cache/hapchija` 에 두고 재사용합니다.
빌드는 시작 전에 소스가 다 있는지 확인하고, 없으면 무엇이 없는지와 받는
방법을 알려 줍니다.

## Docker 로 빌드 (권장)

FontForge, ttfautohint, fontTools 가 들어 있는 공개 이미지를 씁니다.

```bash
docker run --rm -v "$(pwd):/work" ghcr.io/yuru7/composite-font-builder \
  bash -c "cd /work && PYTHONPATH=tools/src python3 -m hapchija build --recipe recipes/pullipsom.json"
```

빠르게 확인하려면 `--quick` 을 붙입니다. `-w normal -s normal` 의 줄임말로,
Regular 하나만 만듭니다. 두께(`-w`)와 기울임(`-s`)은 서로 독립인 선택자라
따로따로 고를 수 있고, 둘 다 쉼표로 여러 개를 적습니다.

```bash
hapchija build --recipe recipes/pullipsom.json --quick           # Regular 하나
hapchija build --recipe recipes/pullipsom.json -w 700 -s italic   # BoldItalic
hapchija build --recipe recipes/pullipsom.json -w text,semibold   # Text, SemiBold 와 그 이탤릭
```

레시피가 어떤 값을 받는지는 `hapchija options --recipe recipes/pullipsom.json`
으로 봅니다.

생성된 TTF 는 `build/Pullipsom/` 아래에 `Pullipsom-{style}.ttf` 로 나옵니다.
16개 스타일이 나오며, 여덟 두께를 병렬로 만들어 2분 안팎 걸립니다.

## Docker 없이 빌드

FontForge 와 ttfautohint 는 pip 으로 설치되지 않습니다.

```bash
# Ubuntu
sudo apt-get install -y fontforge python3-fontforge ttfautohint
# Arch
sudo pacman -S fontforge && yay -S ttfautohint-cli
```

그다음 도구를 설치하고 빌드합니다.

```bash
pip install -e ./tools
hapchija build --recipe recipes/pullipsom.json
```

설치하지 않고 쓰려면 `PYTHONPATH=tools/src python3 -m hapchija ...` 로도 됩니다.

## 레시피 고치기

메트릭, 두께 표, 소스 우선순위, 글리프 조작은 전부
[recipes/pullipsom.json](recipes/pullipsom.json) 에 있습니다. 값만 바꿀 때는 이
파일만 고치면 됩니다. 왜 그 값인지는 [RECIPE.md](RECIPE.md) 에 적어 두었고,
레시피 안의 `$note` 에도 같은 근거가 짧게 붙어 있습니다.

레시피 형식과 쓸 수 있는 `fit` 전략, 글리프 `ops` 목록은
[tools/README.md](tools/README.md) 를 보세요. 이 레시피는 가변폭이라 `fit` 을
쓰지 않습니다.

## 빌드 후 검증

빌드가 끝나면 기대한 파일이 모두 생겼는지, 생성된 TTF 를 fontTools 로 읽을 수
있는지 자동으로 확인합니다. 둘 중 하나라도 실패하면 0 이 아닌 종료 코드로
끝납니다.

# 견본 그림 만들기

열여섯 스타일을 모두 빌드한 뒤 아래를 돌리면 `images/` 의 그림이 다시
만들어집니다. Pillow 가 필요하고, 그리는 데 Raqm 레이아웃 엔진을 씁니다.

```bash
python3 scripts/specimen.py build/Pullipsom images
```

| 스크립트 | 만드는 것 |
|---|---|
| `scripts/specimen.py` | 이름 그림, 본문 견본, 굵기 견본, 글자 갈래 견본 |
| `scripts/render.py` | 글꼴을 열고 글줄을 그리는 공통 부분 |

가변폭 글꼴이라 글줄을 통째로 넘겨서 커닝이 들어간 실제 폭으로 그립니다.
굵기를 섞어 그리는 이름 그림에서만 글자 단위로 끊고, 그때는 `hmtx` 의 폭을
직접 읽습니다. 그림에 없는 글자가 있으면 스크립트가 멈추고 무엇이 없는지
알려 줍니다.
