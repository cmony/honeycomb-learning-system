# 🐝 벌집 구조 학습 시스템

가상 학습자 생성 → 유니트 학습 시뮬레이션 → 다음 유니트 추천

---

## 📁 프로젝트 구조

```
honeycomb-learning-system/
│
├── honeycomb_learning_system.py   # 핵심 엔진 (필수)
├── honeycomb_app.py               # Streamlit UI (선택)
│
├── data/
│   ├── honeycomb_units_final.csv  # 84개 유니트 고정정보
│   └── honeycomb_units_final.json
│
├── docs/
│   └── honeycomb_system_documentation.docx  # 기술 문서
│
├── requirements.txt               # 패키지 목록
└── README.md                      # 이 파일
```

---

## 🚀 빠른 시작

### 1단계: 폴더 생성

```bash
mkdir honeycomb-learning-system
cd honeycomb-learning-system
```

### 2단계: 파일 복사

다운로드한 파일들을 위 구조대로 배치합니다.

### 3단계: 가상환경 생성 (권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4단계: 패키지 설치

```bash
pip install -r requirements.txt
```

### 5단계: 실행

```bash
# 콘솔 테스트
python honeycomb_learning_system.py

# Streamlit UI
streamlit run honeycomb_app.py
```

---

## 📦 필요 패키지

| 패키지 | 버전 | 용도 |
|--------|------|------|
| Python | 3.9+ | 기본 |
| streamlit | 1.28+ | UI |
| plotly | 5.18+ | 차트 |

---

## 🔧 상세 설정

### Python 버전 확인

```bash
python --version  # 3.9 이상 필요
```

### 패키지 개별 설치 (requirements.txt 없이)

```bash
pip install streamlit plotly
```

---

## 💻 실행 화면

### 콘솔 실행 결과

```
======================================================================
벌집 구조 학습 시스템 - 최종본 데모
======================================================================

✅ 84개 유니트 로드 완료

👤 학습자 생성: 김민준 (ID: a1b2c3d4)
   성향: 탐험25% / 성취30% / 경쟁20% / 창조25%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 학습 시뮬레이션 시작 (5회)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1회차]
  📌 선택 유니트: A-01-C (개념, 난이도 1)
     매칭점수: 0.750
  📊 생성정보:
     체류시간: 185초, 실패: 0회
     이탈: False, 재도전: False
...
```

### Streamlit UI

브라우저에서 `http://localhost:8501` 접속

---

## 🛠️ 문제 해결

### "streamlit 명령어를 찾을 수 없음"

```bash
# 가상환경 활성화 확인
# Windows
venv\Scripts\activate

# 또는 전체 경로로 실행
python -m streamlit run honeycomb_app.py
```

### "ModuleNotFoundError: No module named 'plotly'"

```bash
pip install plotly
```

### 포트 충돌 (8501 사용 중)

```bash
streamlit run honeycomb_app.py --server.port 8502
```

---

## 📚 핵심 개념

### 데이터 흐름

```
[유니트 고정정보] × [학습자 프로필] → [생성정보(로그)]
         ↓
    [프로필 업데이트]
         ↓
    [다음 유니트 추천]
```

### 생성정보 6개 필드

1. **체류시간_초** - 유니트에서 머문 시간
2. **실패횟수** - 학습 중 실패 횟수
3. **재도전_여부** - 실패 후 재시도 여부
4. **이탈_여부** - 중도 포기 여부
5. **보상반응** - 칭찬/개방/시각효과 중 반응
6. **선호미디어_반응점수** - 미디어별 반응 (0~1)

### 5가지 적합성 점수

1. **난이도 적합성** (25%)
2. **선행조건 충족도** (25%)
3. **학습타입 적합성** (20%)
4. **미디어 궁합** (15%)
5. **성향 방향성** (15%)

---

## 📞 문의

기술적 질문이나 기능 요청은 연구팀에 문의해주세요.

---

*Version 1.0 Final | 2024년 12월*
