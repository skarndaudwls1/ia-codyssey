# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요
Codyssey 프로그래밍 교육

## 스크립트 실행 방법
각 스크립트는 해당 폴더 안에서 직접 실행한다:
```bash
python3 week01/problem01/main.py          # 미션 컴퓨터 로그 분석
python3 week02/problem03/Mars.py          # 인화성 물질 분류
python3 week02/problem04/dom.py           # 화성 돔 설계 계산기
python3 week03/problem06/Mission.py       # 더미 환경 센서
```

빌드 단계 없음, 가상환경 불필요, 추가 패키지 설치 불필요.

## 폴더 구조

```
week01/problem01/   # problem 01~02: 미션 컴퓨터 로그 분석
week01/problem02/   # (예비)
week02/problem03/   # problem 03: 인화성 물질 분류 (Mars.py)
week02/problem04/   # problem 04: 돔 설계 계산기 (dom.py)
week03/problem06/   # problem 06: 더미 환경 센서 (Mission.py)
```

## 아키텍처
### Problem 01/02 — 미션 컴퓨터 로그 분석 (`week01/problem01/main.py`)
- `mission_computer_main.log` 읽기 (CSV: timestamp, event, message)
- 처리 파이프라인: 로그 파일 → 2차원 리스트 → 정렬 → 딕셔너리 → JSON
- `import json` 사용 금지 — 과제 제약사항이므로 JSON을 직접 문자열로 생성함
- 번호 메뉴 방식의 한국어 CLI

### Problem 03 — 인화성 물질 분류 (`week02/problem03/Mars.py`)
- `Mars_Base_Inventory_List.csv` 읽기 (물질명, 중량, 비중, 강도, 인화성)
- 위험 물질 기준: 인화성 ≥ 0.7
- 커스텀 바이너리 직렬화 (표준 라이브러리 직렬화 사용 금지):
  - 4바이트 항목 수 헤더
  - 항목별: 필드 수 → 키-값 쌍 (타입 태그 `0x00`=문자열, `0x01`=float)
  - float 인코딩: `float.hex()` 사용
- 출력 파일: `Mars_Base_Inventory_danger.csv`, `Mars_Base_Inventory_List.bin`

### Problem 04 — 돔 설계 계산기 (`week02/problem04/dom.py`)
- 반구 표면적 = 2πr², 화성 중력 적용 (지구 중력 × 0.376)
- 재료 DB: 유리, 알루미늄, 탄소강 (밀도 하드코딩)
- 결과를 `design_dome.py` 텍스트 파일로 저장

### Problem 06 — 더미 환경 센서 (`week03/problem06/Mission.py`)
- `DummySensor` 클래스: `set_env()`로 랜덤 값 생성, `get_env()`로 반환 및 로그 기록
- 측정 항목: 내부/외부 온도, 내부 습도, 외부 광량, 내부 CO₂, 내부 산소 농도
- 보너스: `get_env()` 호출 시 `sensor.log`에 CSV 형식으로 누적 기록


## 개발 환경
- UI 문자열, 주석, 변수명은 모두 한국어
- Python 버전은 3.x 버전으로 한다. 
- Python에서 기본 제공되는 명령어만 사용해야 하며 별도의 라이브러리나 패키지를 사용해서는 안된다. (제약사항에 따라 사용할 수도 있다)
- Python의 coding style guide를 확인하고 가이드를 준수해서 코딩한다.(PEP 8 – 파이썬 코드 스타일 가이드 | peps.python.org)
- 문자열을 표현 할 때에는 ‘ ’을 기본으로 사용한다. 다만 문자열 내에서 ‘을 사용할 경우와 - 같이 부득이한 경우에는 “ “를 사용한다. 
- foo = (0,) 와 같이 대입문의  = 앞 뒤로는 공백을 준다. 
- 들여 쓰기는 공백을 기본으로 사용합니다.