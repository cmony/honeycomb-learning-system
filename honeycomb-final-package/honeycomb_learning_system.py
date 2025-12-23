"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
벌집 구조 학습 시스템 - 최종본 (Final Version)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

핵심 흐름:
  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │  유니트 고정정보  │  ×  │   학습자 프로필   │  →  │   생성정보(로그)  │
  └─────────────────┘     └─────────────────┘     └─────────────────┘
                                   ↓
                          ┌─────────────────┐
                          │  프로필 미세 업데이트 │
                          └─────────────────┘
                                   ↓
                          ┌─────────────────┐
                          │  다음 유니트 추천  │
                          └─────────────────┘

"학생은 바뀌지 않는다. 하지만 학생의 '상태 벡터'는 매 유니트마다 업데이트된다."
"같은 학생 × 같은 유니트라도 학습 '순간'이 다르면 생성정보는 달라진다."

Author: Claude (Anthropic)
Version: 1.0 Final
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Literal, Optional, Tuple
import random
import uuid
import json
import csv
from datetime import datetime
from enum import Enum

# ════════════════════════════════════════════════════════════════════════════
# 타입 정의
# ════════════════════════════════════════════════════════════════════════════
Level3 = Literal["낮음", "중간", "높음"]
MediaType = Literal["이미지", "텍스트", "숫자", "영상", "혼합"]
UnitType = Literal["개념", "실전", "탐색", "보조"]
RewardType = Literal["칭찬", "개방", "시각효과"]


# ════════════════════════════════════════════════════════════════════════════
# 1. 유니트 고정정보 (Unit Fixed Info)
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class UnitFixedInfo:
    """
    유니트 고정정보 - 학습 전에 이미 결정된 값들
    
    필드:
    - unit_id: 고유 ID (예: A-01-C)
    - subject: 과목코드 (A~G)
    - chapter: 단원 (1~3)
    - difficulty: 난이도 (1~12)
    - unit_type: 학습타입 (개념/실전/탐색/보조)
    - prereq_required/recommended/optional: 선행조건
    - recommended_media: 추천표현방식
    - estimated_time_sec: 예상시간
    - fail_allow: 실패허용 기본값
    """
    unit_id: str
    subject: str
    chapter: int
    difficulty: int
    unit_type: UnitType
    
    # 선행조건 (필수/권장/선택)
    prereq_required: List[str] = field(default_factory=list)
    prereq_recommended: List[str] = field(default_factory=list)
    prereq_optional: List[str] = field(default_factory=list)
    
    # 표현 및 시간
    recommended_media: MediaType = "혼합"
    media_candidates: List[MediaType] = field(default_factory=list)
    estimated_time_sec: int = 180
    fail_allow: int = 3
    
    # 보상 및 연계
    reward_type: RewardType = "칭찬"
    rest_linkable: bool = True
    
    def to_dict(self) -> dict:
        return asdict(self)


# ════════════════════════════════════════════════════════════════════════════
# 2. 학습자 프로필 (Learner Profile)
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class PersonalityAxis:
    """성향축 (4가지, 합계 100)"""
    탐험형: int = 25
    성취형: int = 25
    경쟁형: int = 25
    창조형: int = 25
    
    def normalize(self):
        """합계 100 유지"""
        total = self.탐험형 + self.성취형 + self.경쟁형 + self.창조형
        if total == 0:
            self.탐험형 = self.성취형 = self.경쟁형 = self.창조형 = 25
        else:
            factor = 100 / total
            self.탐험형 = int(self.탐험형 * factor)
            self.성취형 = int(self.성취형 * factor)
            self.경쟁형 = int(self.경쟁형 * factor)
            self.창조형 = 100 - self.탐험형 - self.성취형 - self.경쟁형
    
    def to_dict(self) -> dict:
        return {"탐험형": self.탐험형, "성취형": self.성취형, 
                "경쟁형": self.경쟁형, "창조형": self.창조형}


@dataclass
class LearnerProfile:
    """
    가상 학습자 프로필
    
    구성:
    1️⃣ 성향축 (4가지, 합 100): 탐험형/성취형/경쟁형/창조형
    2️⃣ 난이도 반응: 도전 선호도, 실패 인내도
    3️⃣ 미디어 선호 (0~1): 이미지/텍스트/숫자/영상
    4️⃣ 몰입·이탈 특성: 평균 집중 시간, 지루함 임계치, 이탈 임계치
    5️⃣ 행동 성향: 재도전 확률, 확장 선택 확률, 휴식 수용도
    """
    learner_id: str = ""
    name: str = ""
    
    # 1️⃣ 성향축
    personality: PersonalityAxis = field(default_factory=PersonalityAxis)
    
    # 2️⃣ 난이도 반응
    도전_선호도: Level3 = "중간"
    실패_인내도: Level3 = "중간"
    
    # 3️⃣ 미디어 선호 (0~1)
    미디어_이미지: float = 0.5
    미디어_텍스트: float = 0.5
    미디어_숫자: float = 0.5
    미디어_영상: float = 0.5
    
    # 4️⃣ 몰입·이탈 특성
    평균_집중_지속시간_초: int = 180
    지루함_임계치_초: int = 120
    이탈_임계치_실패횟수: int = 3
    
    # 5️⃣ 행동 성향
    재도전_확률: int = 50       # %
    확장_선택_확률: int = 30    # %
    휴식_수용도: Level3 = "중간"
    
    # 상태 추적
    state_version: int = 0
    completed_units: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "learner_id": self.learner_id,
            "이름": self.name,
            "상태벡터_버전": self.state_version,
            "완료_유니트_수": len(self.completed_units),
            "성향축": self.personality.to_dict(),
            "난이도반응": {
                "도전_선호도": self.도전_선호도,
                "실패_인내도": self.실패_인내도
            },
            "미디어선호": {
                "이미지": round(self.미디어_이미지, 2),
                "텍스트": round(self.미디어_텍스트, 2),
                "숫자": round(self.미디어_숫자, 2),
                "영상": round(self.미디어_영상, 2)
            },
            "몰입이탈": {
                "평균_집중_지속시간_초": self.평균_집중_지속시간_초,
                "지루함_임계치_초": self.지루함_임계치_초,
                "이탈_임계치_실패횟수": self.이탈_임계치_실패횟수
            },
            "행동성향": {
                "재도전_확률_%": self.재도전_확률,
                "확장_선택_확률_%": self.확장_선택_확률,
                "휴식_수용도": self.휴식_수용도
            }
        }


# ════════════════════════════════════════════════════════════════════════════
# 3. 학습 생성정보 (Learning Generated Info)
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class LearningLog:
    """
    유니트 학습 후 생성되는 정보 (6개 핵심 필드)
    
    고정정보(유니트) × 학생프로필 → 생성정보(로그)
    
    필드 (요구사항 6개):
    1. 체류시간_초
    2. 실패횟수
    3. 재도전_여부
    4. 이탈_여부
    5. 보상반응 (칭찬/개방/시각효과)
    6. 선호미디어_반응점수 (Dict)
    """
    # 기본 식별
    log_id: str = ""
    unit_id: str = ""
    learner_id: str = ""
    timestamp: str = ""
    
    # ━━━ 핵심 6개 필드 ━━━
    체류시간_초: int = 0
    실패횟수: int = 0
    재도전_여부: bool = False
    이탈_여부: bool = False
    보상반응: RewardType = "칭찬"
    선호미디어_반응점수: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "log_id": self.log_id,
            "unit_id": self.unit_id,
            "learner_id": self.learner_id,
            "timestamp": self.timestamp,
            "체류시간_초": self.체류시간_초,
            "실패횟수": self.실패횟수,
            "재도전_여부": self.재도전_여부,
            "이탈_여부": self.이탈_여부,
            "보상반응": self.보상반응,
            "선호미디어_반응점수": {k: round(v, 2) for k, v in self.선호미디어_반응점수.items()}
        }


# ════════════════════════════════════════════════════════════════════════════
# 4. 다음 유니트 추천 점수 (Next Unit Match Score)
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class UnitMatchScore:
    """
    유니트-학습자 매칭 점수
    
    5가지 적합성 점수:
    1. 난이도_적합성: 현재 상태에 부담/적당/쉬움
    2. 학습타입_적합성: 밀어붙일/풀어줄/쉬어야 할 타이밍
    3. 미디어_궁합: 이 유니트가 학생에게 잘 먹힐 포장인가
    4. 선행조건_충족도: 들어가도 깨지지 않는지
    5. 성향_방향성: 학생이 '하고 싶어 할' 선택인지
    """
    unit_id: str
    total_score: float = 0.0
    
    # 5가지 적합성 점수 (각 0~1)
    난이도_적합성: float = 0.0
    학습타입_적합성: float = 0.0
    미디어_궁합: float = 0.0
    선행조건_충족도: float = 0.0
    성향_방향성: float = 0.0
    
    # 추천 여부
    is_available: bool = True
    block_reason: str = ""
    
    def to_dict(self) -> dict:
        return {
            "unit_id": self.unit_id,
            "총점": round(self.total_score, 3),
            "난이도_적합성": round(self.난이도_적합성, 2),
            "학습타입_적합성": round(self.학습타입_적합성, 2),
            "미디어_궁합": round(self.미디어_궁합, 2),
            "선행조건_충족도": round(self.선행조건_충족도, 2),
            "성향_방향성": round(self.성향_방향성, 2),
            "추천가능": self.is_available,
            "제외사유": self.block_reason
        }


# ════════════════════════════════════════════════════════════════════════════
# 5. 유틸리티 함수
# ════════════════════════════════════════════════════════════════════════════
def _clamp01(x: float) -> float:
    """0~1 범위로 제한"""
    return max(0.0, min(1.0, x))

def _clamp(x: int, lo: int, hi: int) -> int:
    """정수 범위 제한"""
    return max(lo, min(hi, x))

def _level3_to_num(level: Level3) -> float:
    """Level3를 숫자로 변환"""
    return {"낮음": -1.0, "중간": 0.0, "높음": 1.0}[level]


# ════════════════════════════════════════════════════════════════════════════
# 6. 학습자 프로필 생성기
# ════════════════════════════════════════════════════════════════════════════
FIRST_NAMES = ["민준", "서연", "도윤", "하윤", "지호", "서준", "예린", 
               "지민", "현우", "수아", "유나", "준호", "시우", "지아"]
LAST_NAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]

def generate_learner_profile() -> LearnerProfile:
    """가상 학습자 프로필 랜덤 생성"""
    # 성향축 랜덤 생성 (합 100)
    raw = [random.random() ** 0.7 for _ in range(4)]
    total = sum(raw)
    norm = [int(r / total * 100) for r in raw]
    norm[0] += 100 - sum(norm)
    
    personality = PersonalityAxis(
        탐험형=norm[0], 성취형=norm[1], 
        경쟁형=norm[2], 창조형=norm[3]
    )
    
    return LearnerProfile(
        learner_id=str(uuid.uuid4())[:8],
        name=f"{random.choice(LAST_NAMES)}{random.choice(FIRST_NAMES)}",
        personality=personality,
        도전_선호도=random.choice(["낮음", "중간", "높음"]),
        실패_인내도=random.choice(["낮음", "중간", "높음"]),
        미디어_이미지=random.uniform(0.2, 0.9),
        미디어_텍스트=random.uniform(0.2, 0.9),
        미디어_숫자=random.uniform(0.2, 0.9),
        미디어_영상=random.uniform(0.2, 0.9),
        평균_집중_지속시간_초=random.randint(90, 300),
        지루함_임계치_초=random.randint(60, 200),
        이탈_임계치_실패횟수=random.randint(2, 6),
        재도전_확률=random.randint(20, 80),
        확장_선택_확률=random.randint(15, 60),
        휴식_수용도=random.choice(["낮음", "중간", "높음"])
    )


# ════════════════════════════════════════════════════════════════════════════
# 7. 84개 유니트 고정정보 생성기
# ════════════════════════════════════════════════════════════════════════════
SUBJECTS = {
    'A': '수와 연산', 'B': '도형과 측정', 'C': '규칙성', 'D': '자료와 가능성',
    'E': '물질과 에너지', 'F': '생명과 환경', 'G': '지구와 우주'
}

CHAPTERS = {
    'A': ['덧셈과 뺄셈', '곱셈과 나눗셈', '분수와 소수'],
    'B': ['평면도형', '입체도형', '넓이와 부피'],
    'C': ['수의 규칙', '도형의 규칙', '비와 비례'],
    'D': ['표와 그래프', '평균과 분포', '확률의 이해'],
    'E': ['물질의 성질', '힘과 운동', '에너지 전환'],
    'F': ['생물의 구조', '생태계', '환경과 적응'],
    'G': ['지구의 구조', '날씨와 기후', '태양계와 별'],
}

def generate_all_units() -> List[UnitFixedInfo]:
    """84개 유니트 고정정보 생성 (7과목 × 3단원 × 4유니트)"""
    units = []
    unit_types: List[UnitType] = ["개념", "보조", "실전", "탐색"]
    suffixes = ['C', 'S', 'P', 'E']  # Concept, Support, Practice, Explore
    
    for subj in SUBJECTS.keys():
        for chapter in range(1, 4):
            for idx, utype in enumerate(unit_types):
                unit_id = f"{subj}-{chapter:02d}-{suffixes[idx]}"
                difficulty = (chapter - 1) * 4 + idx + 1  # 1~12
                
                # 선행조건 설정
                prereq_req = []
                prereq_rec = []
                prereq_opt = []
                
                # 개념이 아닌 유니트는 해당 단원 개념이 필수
                if utype != "개념":
                    prereq_req.append(f"{subj}-{chapter:02d}-C")
                
                # 이전 단원 개념 권장
                if chapter > 1:
                    prereq_rec.append(f"{subj}-{chapter-1:02d}-C")
                
                unit = UnitFixedInfo(
                    unit_id=unit_id,
                    subject=subj,
                    chapter=chapter,
                    difficulty=difficulty,
                    unit_type=utype,
                    prereq_required=prereq_req,
                    prereq_recommended=prereq_rec,
                    prereq_optional=prereq_opt,
                    recommended_media=random.choice(["이미지", "텍스트", "숫자", "영상", "혼합"]),
                    media_candidates=random.sample(["이미지", "텍스트", "숫자", "영상"], 2),
                    estimated_time_sec=120 + difficulty * 10 + random.randint(-20, 20),
                    fail_allow=max(1, 5 - difficulty // 3),
                    reward_type=random.choice(["칭찬", "개방", "시각효과"]),
                    rest_linkable=(utype in ["개념", "보조"])
                )
                units.append(unit)
    
    return units


# ════════════════════════════════════════════════════════════════════════════
# 8. 학습 시뮬레이션 엔진
# ════════════════════════════════════════════════════════════════════════════
class LearningSimulator:
    """학습 시뮬레이션 엔진 - 핵심 클래스"""
    
    def __init__(self):
        self.units: Dict[str, UnitFixedInfo] = {}
    
    def load_units(self, units: List[UnitFixedInfo]):
        """유니트 고정정보 로드"""
        self.units = {u.unit_id: u for u in units}
    
    # ─────────────────────────────────────────────────────────────────────────
    # 핵심 1: 생성정보 생성
    # ─────────────────────────────────────────────────────────────────────────
    def simulate_learning(
        self, 
        profile: LearnerProfile, 
        unit: UnitFixedInfo
    ) -> LearningLog:
        """
        고정정보(유니트) × 학생프로필 → 생성정보(로그)
        
        6개 핵심 필드 생성:
        1. 체류시간_초
        2. 실패횟수
        3. 재도전_여부
        4. 이탈_여부
        5. 보상반응
        6. 선호미디어_반응점수
        """
        log = LearningLog(
            log_id=str(uuid.uuid4())[:8],
            unit_id=unit.unit_id,
            learner_id=profile.learner_id,
            timestamp=datetime.now().isoformat()
        )
        
        # ━━━ 1. 체류시간 계산 ━━━
        base_time = profile.평균_집중_지속시간_초
        difficulty_factor = (unit.difficulty - 6) * 8
        random_var = random.gauss(0, 25)
        type_factor = {"개념": 1.2, "실전": 1.0, "탐색": 0.8, "보조": 0.7}
        time_mult = type_factor.get(unit.unit_type, 1.0)
        log.체류시간_초 = max(20, int((base_time + difficulty_factor + random_var) * time_mult))
        
        # ━━━ 2. 실패횟수 계산 ━━━
        base_fail = max(0, (unit.difficulty - 5) // 2) + random.randint(0, 2)
        if profile.도전_선호도 == "높음":
            base_fail += random.randint(0, 2)
        elif profile.도전_선호도 == "낮음":
            base_fail = max(0, base_fail - 1)
        if profile.실패_인내도 == "높음":
            base_fail = max(0, base_fail - 1)
        log.실패횟수 = min(base_fail, 10)
        
        # ━━━ 3. 이탈 여부 ━━━
        log.이탈_여부 = False
        if log.실패횟수 >= profile.이탈_임계치_실패횟수:
            log.이탈_여부 = random.random() < 0.6
        if log.체류시간_초 > profile.지루함_임계치_초:
            if unit.unit_type in ["개념", "보조"]:
                log.이탈_여부 = log.이탈_여부 or (random.random() < 0.25)
        
        # ━━━ 4. 재도전 여부 ━━━
        if log.실패횟수 > 0 and not log.이탈_여부:
            log.재도전_여부 = random.random() * 100 < profile.재도전_확률
        
        # ━━━ 5. 보상반응 ━━━
        reward_weights = {
            "칭찬": profile.personality.성취형 + 10,
            "개방": profile.personality.탐험형 + profile.personality.창조형,
            "시각효과": profile.personality.창조형 + profile.personality.경쟁형
        }
        total_w = sum(reward_weights.values())
        r = random.random() * total_w
        cumulative = 0
        for reward, w in reward_weights.items():
            cumulative += w
            if r <= cumulative:
                log.보상반응 = reward
                break
        
        # ━━━ 6. 선호미디어 반응점수 ━━━
        log.선호미디어_반응점수 = {
            "이미지": _clamp01(profile.미디어_이미지 + random.uniform(-0.15, 0.15)),
            "텍스트": _clamp01(profile.미디어_텍스트 + random.uniform(-0.15, 0.15)),
            "숫자": _clamp01(profile.미디어_숫자 + random.uniform(-0.15, 0.15)),
            "영상": _clamp01(profile.미디어_영상 + random.uniform(-0.15, 0.15))
        }
        # 추천 미디어 일치 보너스
        if unit.recommended_media in log.선호미디어_반응점수:
            log.선호미디어_반응점수[unit.recommended_media] = _clamp01(
                log.선호미디어_반응점수[unit.recommended_media] + 0.2
            )
        
        return log
    
    # ─────────────────────────────────────────────────────────────────────────
    # 핵심 2: 프로필 업데이트
    # ─────────────────────────────────────────────────────────────────────────
    def update_profile(
        self, 
        profile: LearnerProfile, 
        log: LearningLog,
        unit: UnitFixedInfo
    ) -> LearnerProfile:
        """
        생성정보 + 학생프로필 → 프로필 미세 업데이트
        "학생은 바뀌지 않지만 상태 벡터는 매 유니트마다 업데이트"
        """
        # ━━━ 미디어 선호 업데이트 ━━━
        best_media = max(log.선호미디어_반응점수, key=log.선호미디어_반응점수.get)
        media_attr_map = {"이미지": "미디어_이미지", "텍스트": "미디어_텍스트", 
                          "숫자": "미디어_숫자", "영상": "미디어_영상"}
        for media, attr in media_attr_map.items():
            current = getattr(profile, attr)
            delta = 0.03 if media == best_media else -0.01
            setattr(profile, attr, _clamp01(current + delta))
        
        # ━━━ 난이도 반응 조정 ━━━
        if log.이탈_여부 or log.실패횟수 > unit.fail_allow:
            if profile.도전_선호도 == "높음":
                profile.도전_선호도 = "중간"
            elif profile.도전_선호도 == "중간" and random.random() < 0.3:
                profile.도전_선호도 = "낮음"
        
        # 성공 시 회복
        if not log.이탈_여부 and log.실패횟수 <= 1:
            if profile.도전_선호도 == "낮음" and random.random() < 0.2:
                profile.도전_선호도 = "중간"
        
        # ━━━ 성향축 미세 변화 (합 100 유지) ━━━
        axis = profile.personality
        
        if not log.이탈_여부 and random.random() * 100 < profile.확장_선택_확률:
            axis.탐험형 += 2
        elif log.이탈_여부:
            axis.탐험형 = max(0, axis.탐험형 - 1)
        
        if not log.이탈_여부:
            axis.성취형 += 1
        if log.재도전_여부:
            axis.성취형 += 1
        
        if unit.unit_type == "탐색" and not log.이탈_여부:
            axis.창조형 += 2
        
        axis.normalize()
        
        # ━━━ 상태 업데이트 ━━━
        profile.state_version += 1
        if not log.이탈_여부:
            profile.completed_units.append(log.unit_id)
        
        return profile
    
    # ─────────────────────────────────────────────────────────────────────────
    # 핵심 3: 다음 유니트 추천 점수 계산
    # ─────────────────────────────────────────────────────────────────────────
    def calculate_next_unit_scores(
        self,
        profile: LearnerProfile,
        last_log: Optional[LearningLog],
        candidate_units: List[UnitFixedInfo]
    ) -> List[UnitMatchScore]:
        """
        다음 유니트 선택 = (학생프로필 + 생성정보) ↔ (후보 유니트들의 고정정보) 매칭
        
        5가지 적합성 점수 계산:
        1. 난이도 적합성
        2. 학습타입 적합성
        3. 미디어 궁합
        4. 선행조건 충족도
        5. 성향 방향성
        """
        scores = []
        
        for unit in candidate_units:
            score = UnitMatchScore(unit_id=unit.unit_id)
            
            # 이미 완료한 유니트는 제외
            if unit.unit_id in profile.completed_units:
                score.is_available = False
                score.block_reason = "이미 완료"
                scores.append(score)
                continue
            
            # ━━━ 1. 선행조건 충족도 ━━━
            required_met = all(
                req in profile.completed_units 
                for req in unit.prereq_required
            )
            if not required_met:
                score.is_available = False
                score.block_reason = "필수 선행조건 미충족"
                scores.append(score)
                continue
            
            rec_count = sum(1 for r in unit.prereq_recommended if r in profile.completed_units)
            rec_total = max(len(unit.prereq_recommended), 1)
            opt_count = sum(1 for o in unit.prereq_optional if o in profile.completed_units)
            opt_total = max(len(unit.prereq_optional), 1)
            score.선행조건_충족도 = 0.6 + (rec_count / rec_total) * 0.3 + (opt_count / opt_total) * 0.1
            
            # ━━━ 2. 난이도 적합성 ━━━
            ideal_difficulty = 6
            if last_log:
                if last_log.실패횟수 > 2:
                    ideal_difficulty -= 1
                if not last_log.이탈_여부 and last_log.실패횟수 <= 1:
                    ideal_difficulty += 1
            
            if profile.도전_선호도 == "높음":
                ideal_difficulty += 2
            elif profile.도전_선호도 == "낮음":
                ideal_difficulty -= 1
            
            diff_gap = abs(unit.difficulty - ideal_difficulty)
            score.난이도_적합성 = max(0, 1 - diff_gap * 0.12)
            
            # ━━━ 3. 학습타입 적합성 ━━━
            type_scores = {"개념": 0.5, "실전": 0.5, "탐색": 0.5, "보조": 0.5}
            
            if last_log:
                if last_log.이탈_여부:
                    type_scores["보조"] += 0.3
                    type_scores["탐색"] += 0.2
                elif last_log.재도전_여부:
                    type_scores["실전"] += 0.3
            
            axis = profile.personality
            type_scores["탐색"] += axis.탐험형 * 0.005
            type_scores["실전"] += axis.성취형 * 0.005
            type_scores["개념"] += axis.창조형 * 0.003
            
            score.학습타입_적합성 = min(1.0, type_scores.get(unit.unit_type, 0.5))
            
            # ━━━ 4. 미디어 궁합 ━━━
            media_pref = {
                "이미지": profile.미디어_이미지,
                "텍스트": profile.미디어_텍스트,
                "숫자": profile.미디어_숫자,
                "영상": profile.미디어_영상,
                "혼합": 0.5
            }
            
            if last_log and last_log.선호미디어_반응점수:
                for k in ["이미지", "텍스트", "숫자", "영상"]:
                    if k in last_log.선호미디어_반응점수:
                        media_pref[k] = (media_pref[k] + last_log.선호미디어_반응점수[k]) / 2
            
            score.미디어_궁합 = media_pref.get(unit.recommended_media, 0.5)
            
            # ━━━ 5. 성향 방향성 ━━━
            direction_score = 0.5
            if unit.unit_type == "탐색":
                direction_score += axis.탐험형 * 0.004
            elif unit.unit_type == "실전":
                direction_score += axis.성취형 * 0.004 + axis.경쟁형 * 0.002
            elif unit.unit_type == "개념":
                direction_score += axis.창조형 * 0.003
            
            score.성향_방향성 = min(1.0, direction_score)
            
            # ━━━ 총점 계산 (가중 평균) ━━━
            weights = {"난이도": 0.25, "학습타입": 0.20, "미디어": 0.15, 
                       "선행조건": 0.25, "성향": 0.15}
            
            score.total_score = (
                score.난이도_적합성 * weights["난이도"] +
                score.학습타입_적합성 * weights["학습타입"] +
                score.미디어_궁합 * weights["미디어"] +
                score.선행조건_충족도 * weights["선행조건"] +
                score.성향_방향성 * weights["성향"]
            )
            
            scores.append(score)
        
        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores
    
    def recommend_next_units(
        self,
        profile: LearnerProfile,
        last_log: Optional[LearningLog],
        top_n: int = 3
    ) -> List[Tuple[UnitFixedInfo, UnitMatchScore]]:
        """상위 N개 추천 유니트 반환"""
        all_units = list(self.units.values())
        scores = self.calculate_next_unit_scores(profile, last_log, all_units)
        available = [s for s in scores if s.is_available]
        top_scores = available[:top_n]
        return [(self.units[s.unit_id], s) for s in top_scores]


# ════════════════════════════════════════════════════════════════════════════
# 9. 데이터 저장 유틸리티
# ════════════════════════════════════════════════════════════════════════════
def save_units_to_csv(units: List[UnitFixedInfo], filepath: str):
    """유니트 고정정보를 CSV로 저장"""
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = ['unit_id', 'subject', 'chapter', 'difficulty', 'unit_type',
                      'prereq_required', 'prereq_recommended', 'prereq_optional',
                      'recommended_media', 'estimated_time_sec', 'fail_allow',
                      'reward_type', 'rest_linkable']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for u in units:
            row = {
                'unit_id': u.unit_id,
                'subject': u.subject,
                'chapter': u.chapter,
                'difficulty': u.difficulty,
                'unit_type': u.unit_type,
                'prereq_required': '|'.join(u.prereq_required),
                'prereq_recommended': '|'.join(u.prereq_recommended),
                'prereq_optional': '|'.join(u.prereq_optional),
                'recommended_media': u.recommended_media,
                'estimated_time_sec': u.estimated_time_sec,
                'fail_allow': u.fail_allow,
                'reward_type': u.reward_type,
                'rest_linkable': u.rest_linkable
            }
            writer.writerow(row)

def save_units_to_json(units: List[UnitFixedInfo], filepath: str):
    """유니트 고정정보를 JSON으로 저장"""
    data = {
        'metadata': {
            'total_units': len(units),
            'structure': '7과목 × 3단원 × 4유니트(개념/보조/실전/탐색)',
            'difficulty_range': '1~12'
        },
        'subjects': SUBJECTS,
        'units': [u.to_dict() for u in units]
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════════════════════════════════
# 10. 메인 실행
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("벌집 구조 학습 시스템 - 최종본 데모")
    print("=" * 70)
    
    # 1. 시뮬레이터 초기화
    simulator = LearningSimulator()
    units = generate_all_units()
    simulator.load_units(units)
    print(f"\n✅ {len(units)}개 유니트 로드 완료")
    
    # 2. 학습자 프로필 생성
    profile = generate_learner_profile()
    print(f"\n👤 학습자 생성: {profile.name} (ID: {profile.learner_id})")
    print(f"   성향: 탐험{profile.personality.탐험형}% / 성취{profile.personality.성취형}% / "
          f"경쟁{profile.personality.경쟁형}% / 창조{profile.personality.창조형}%")
    print(f"   도전선호도: {profile.도전_선호도}, 실패인내도: {profile.실패_인내도}")
    
    # 3. 학습 시뮬레이션 (5회)
    print("\n" + "━" * 70)
    print("📚 학습 시뮬레이션 시작 (5회)")
    print("━" * 70)
    
    last_log = None
    for i in range(5):
        recommendations = simulator.recommend_next_units(profile, last_log, top_n=3)
        
        if not recommendations:
            print("추천 가능한 유니트 없음")
            break
        
        selected_unit, selected_score = recommendations[0]
        
        print(f"\n[{i+1}회차]")
        print(f"  📌 선택 유니트: {selected_unit.unit_id} ({selected_unit.unit_type}, 난이도 {selected_unit.difficulty})")
        print(f"     매칭점수: {selected_score.total_score:.3f}")
        print(f"     - 난이도 적합성: {selected_score.난이도_적합성:.2f}")
        print(f"     - 학습타입 적합성: {selected_score.학습타입_적합성:.2f}")
        print(f"     - 미디어 궁합: {selected_score.미디어_궁합:.2f}")
        print(f"     - 선행조건 충족도: {selected_score.선행조건_충족도:.2f}")
        print(f"     - 성향 방향성: {selected_score.성향_방향성:.2f}")
        
        log = simulator.simulate_learning(profile, selected_unit)
        print(f"\n  📊 생성정보:")
        print(f"     체류시간: {log.체류시간_초}초, 실패: {log.실패횟수}회")
        print(f"     이탈: {log.이탈_여부}, 재도전: {log.재도전_여부}")
        print(f"     보상반응: {log.보상반응}")
        
        profile = simulator.update_profile(profile, log, selected_unit)
        print(f"\n  🔄 프로필 업데이트: v{profile.state_version}")
        
        last_log = log
    
    # 4. 최종 상태
    print("\n" + "━" * 70)
    print("📈 최종 학습자 상태")
    print("━" * 70)
    print(f"   상태 버전: v{profile.state_version}")
    print(f"   완료 유니트: {profile.completed_units}")
    print(f"   성향: 탐험{profile.personality.탐험형}% / 성취{profile.personality.성취형}% / "
          f"경쟁{profile.personality.경쟁형}% / 창조{profile.personality.창조형}%")
    
    # 5. 파일 저장
    print("\n" + "━" * 70)
    print("💾 파일 저장")
    print("━" * 70)
    save_units_to_csv(units, '/mnt/user-data/outputs/honeycomb_units_final.csv')
    save_units_to_json(units, '/mnt/user-data/outputs/honeycomb_units_final.json')
    print("   ✅ honeycomb_units_final.csv")
    print("   ✅ honeycomb_units_final.json")
