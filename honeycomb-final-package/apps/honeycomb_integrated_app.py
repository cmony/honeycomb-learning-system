"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
벌집 구조 학습 시스템 - 통합 버전 (Final Integrated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

기존 기능:
  - 학습자 프로필 (5가지 카테고리)
  - 생성정보 6개 필드
  - 5가지 적합성 점수 기반 추천

+ 새 기능:
  - 61개 벌집 시각화
  - 나선형 학습 경로
  - 인접 셀 잠금 해제

실행 방법:
  pip install streamlit plotly numpy
  streamlit run honeycomb_integrated_app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import random
import math
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Literal
from datetime import datetime

# ════════════════════════════════════════════════════════════════════════════
# 타입 정의
# ════════════════════════════════════════════════════════════════════════════
Level3 = Literal["낮음", "중간", "높음"]
UnitType = Literal["개념", "실전", "탐색", "보조"]
RewardType = Literal["칭찬", "개방", "시각효과"]
MediaType = Literal["이미지", "텍스트", "숫자", "영상", "혼합"]


# ════════════════════════════════════════════════════════════════════════════
# 1. 학습자 프로필 (기존 코드)
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class PersonalityAxis:
    """성향축 (4가지, 합계 100)"""
    탐험형: int = 25
    성취형: int = 25
    경쟁형: int = 25
    창조형: int = 25
    
    def normalize(self):
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
    학습자 프로필 - 5가지 카테고리
    
    1️⃣ 성향축 (4가지, 합 100)
    2️⃣ 난이도 반응
    3️⃣ 미디어 선호 (0~1)
    4️⃣ 몰입·이탈 특성
    5️⃣ 행동 성향
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
    재도전_확률: int = 50
    확장_선택_확률: int = 30
    휴식_수용도: Level3 = "중간"
    
    # 상태 추적
    state_version: int = 0
    completed_cells: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "learner_id": self.learner_id,
            "이름": self.name,
            "상태벡터_버전": self.state_version,
            "완료_유니트_수": len(self.completed_cells),
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
# 2. 벌집 유니트 고정정보
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class HexUnit:
    """벌집 셀 유니트 - 고정정보"""
    cell_id: int
    unit_type: UnitType
    difficulty: int  # 1~12
    subject: str
    subject_name: str
    
    # 선행조건
    prereq_required: List[int] = field(default_factory=list)
    prereq_recommended: List[int] = field(default_factory=list)
    adjacent_cells: List[int] = field(default_factory=list)
    
    # 표현 및 시간
    recommended_media: MediaType = "혼합"
    estimated_time_sec: int = 180
    fail_allow: int = 3
    reward_type: RewardType = "칭찬"
    
    # 학습 상태 (동적)
    is_completed: bool = False
    is_locked: bool = True
    score: float = 0.0


# ════════════════════════════════════════════════════════════════════════════
# 3. 학습 생성정보 (6개 핵심 필드) - 기존 코드
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class LearningLog:
    """
    유니트 학습 후 생성되는 정보 (6개 핵심 필드)
    
    고정정보(유니트) × 학생프로필 → 생성정보(로그)
    """
    log_id: str = ""
    cell_id: int = 0
    learner_id: str = ""
    timestamp: str = ""
    
    # ━━━ 핵심 6개 필드 ━━━
    체류시간_초: int = 0
    실패횟수: int = 0
    재도전_여부: bool = False
    이탈_여부: bool = False
    보상반응: RewardType = "칭찬"
    선호미디어_반응점수: Dict[str, float] = field(default_factory=dict)
    
    # 추가 정보
    성취도: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "log_id": self.log_id,
            "cell_id": self.cell_id,
            "체류시간_초": self.체류시간_초,
            "실패횟수": self.실패횟수,
            "재도전_여부": self.재도전_여부,
            "이탈_여부": self.이탈_여부,
            "보상반응": self.보상반응,
            "선호미디어_반응점수": {k: round(v, 2) for k, v in self.선호미디어_반응점수.items()},
            "성취도": round(self.성취도, 2)
        }


# ════════════════════════════════════════════════════════════════════════════
# 4. 다음 유니트 추천 점수 (5가지 적합성) - 기존 코드
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class UnitMatchScore:
    """5가지 적합성 점수"""
    cell_id: int
    total_score: float = 0.0
    
    난이도_적합성: float = 0.0
    학습타입_적합성: float = 0.0
    미디어_궁합: float = 0.0
    선행조건_충족도: float = 0.0
    성향_방향성: float = 0.0
    
    is_available: bool = True
    block_reason: str = ""


# ════════════════════════════════════════════════════════════════════════════
# 5. 유틸리티 함수
# ════════════════════════════════════════════════════════════════════════════
def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def _level3_to_num(level: Level3) -> float:
    return {"낮음": -1.0, "중간": 0.0, "높음": 1.0}[level]


# ════════════════════════════════════════════════════════════════════════════
# 6. 벌집 좌표 계산
# ════════════════════════════════════════════════════════════════════════════
def get_ring_from_cell(cell_id: int) -> int:
    """셀 번호로 링 번호 계산"""
    if cell_id == 1:
        return 0
    total = 1
    ring = 1
    while total < cell_id:
        total += 6 * ring
        if cell_id <= total:
            return ring
        ring += 1
    return ring


def get_adjacent_cells(cell_id: int) -> List[int]:
    """인접 셀 계산"""
    if cell_id == 1:
        return [2, 3, 4, 5, 6, 7]
    
    ring = get_ring_from_cell(cell_id)
    adjacent = []
    
    # 같은 링의 이웃
    ring_start = 2 + sum(6 * r for r in range(1, ring))
    ring_end = ring_start + 6 * ring - 1
    
    if cell_id > ring_start:
        adjacent.append(cell_id - 1)
    else:
        adjacent.append(ring_end)
    
    if cell_id < ring_end:
        adjacent.append(cell_id + 1)
    else:
        adjacent.append(ring_start)
    
    # 이전 링
    if ring > 1:
        prev_ring_start = 2 + sum(6 * r for r in range(1, ring - 1))
        offset = cell_id - ring_start
        prev_cell = prev_ring_start + int(offset * (ring - 1) / ring)
        if 1 < prev_cell <= 61:
            adjacent.append(prev_cell)
    elif ring == 1:
        adjacent.append(1)
    
    # 다음 링
    if ring < 4:
        next_ring_start = 2 + sum(6 * r for r in range(1, ring + 1))
        offset = cell_id - ring_start
        next_cell = next_ring_start + int(offset * (ring + 1) / ring)
        if next_cell <= 61:
            adjacent.append(next_cell)
            if next_cell + 1 <= 61:
                adjacent.append(next_cell + 1)
    
    return list(set(a for a in adjacent if 1 <= a <= 61 and a != cell_id))


def generate_hexagon_centers(num_rings: int = 4) -> List[Tuple[float, float, int]]:
    """벌집 중심 좌표 생성"""
    centers = []
    cell_num = 1
    size = 1.0
    h = size * math.sqrt(3)
    
    centers.append((0, 0, cell_num))
    cell_num += 1
    
    for ring in range(1, num_rings + 1):
        directions = [
            (1.5 * size, -h/2),
            (0, -h),
            (-1.5 * size, -h/2),
            (-1.5 * size, h/2),
            (0, h),
            (1.5 * size, h/2),
        ]
        
        x, y = 0, ring * h
        
        for dir_idx, (dx, dy) in enumerate(directions):
            for step in range(ring):
                centers.append((x, y, cell_num))
                cell_num += 1
                x += dx
                y += dy
    
    return [(x, y, n) for x, y, n in centers if n <= 61]


def get_hexagon_vertices(cx: float, cy: float, size: float = 0.9) -> Tuple[List[float], List[float]]:
    """육각형 꼭짓점"""
    angles = [math.pi/6 + i * math.pi/3 for i in range(6)]
    xs = [cx + size * math.cos(a) for a in angles]
    ys = [cy + size * math.sin(a) for a in angles]
    return xs + [xs[0]], ys + [ys[0]]


# ════════════════════════════════════════════════════════════════════════════
# 7. 데이터 생성기
# ════════════════════════════════════════════════════════════════════════════
SUBJECTS = {
    'A': '수와 연산', 'B': '도형과 측정', 'C': '규칙성', 'D': '자료와 가능성',
    'E': '물질과 에너지', 'F': '생명과 환경', 'G': '지구와 우주'
}

FIRST_NAMES = ["민준", "서연", "도윤", "하윤", "지호", "서준", "예린", 
               "지민", "현우", "수아", "유나", "준호", "시우", "지아"]
LAST_NAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]


def generate_learner_profile() -> LearnerProfile:
    """학습자 프로필 랜덤 생성"""
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


def generate_hex_units(num_cells: int = 61) -> Dict[int, HexUnit]:
    """61개 벌집 유니트 생성"""
    units = {}
    subject_list = list(SUBJECTS.keys())
    unit_types: List[UnitType] = ["개념", "보조", "실전", "탐색"]
    media_types: List[MediaType] = ["이미지", "텍스트", "숫자", "영상", "혼합"]
    
    for i in range(1, num_cells + 1):
        ring = get_ring_from_cell(i)
        
        # 난이도: 링 기반 (1~12)
        difficulty = min(12, ring * 3 + random.randint(0, 2))
        if difficulty == 0:
            difficulty = 1
        
        # 유니트 타입
        if ring == 0:
            utype = "개념"
        elif ring == 1:
            utype = random.choice(["개념", "보조"])
        elif ring == 2:
            utype = random.choice(["보조", "실전"])
        else:
            utype = random.choice(["실전", "탐색"])
        
        # 과목
        subj = subject_list[(i - 1) % len(subject_list)]
        
        # 선행조건
        adjacent = get_adjacent_cells(i)
        prereq_req = [a for a in adjacent if a < i and get_ring_from_cell(a) < ring][:1]
        prereq_rec = [a for a in adjacent if a < i][:2]
        
        units[i] = HexUnit(
            cell_id=i,
            unit_type=utype,
            difficulty=difficulty,
            subject=subj,
            subject_name=SUBJECTS[subj],
            prereq_required=prereq_req,
            prereq_recommended=prereq_rec,
            adjacent_cells=adjacent,
            recommended_media=random.choice(media_types),
            estimated_time_sec=120 + difficulty * 15 + random.randint(-20, 20),
            fail_allow=max(1, 5 - difficulty // 3),
            reward_type=random.choice(["칭찬", "개방", "시각효과"]),
            is_locked=(i != 1)
        )
    
    return units


# ════════════════════════════════════════════════════════════════════════════
# 8. 학습 시뮬레이션 엔진 (기존 로직 + 벌집 통합)
# ════════════════════════════════════════════════════════════════════════════
class HoneycombSimulator:
    """벌집 학습 시뮬레이션 엔진"""
    
    def __init__(self):
        self.units: Dict[int, HexUnit] = {}
    
    def load_units(self, units: Dict[int, HexUnit]):
        self.units = units
    
    # ─────────────────────────────────────────────────────────────────────────
    # 핵심 1: 생성정보 생성 (기존 로직)
    # ─────────────────────────────────────────────────────────────────────────
    def simulate_learning(
        self, 
        profile: LearnerProfile, 
        unit: HexUnit
    ) -> LearningLog:
        """
        고정정보(유니트) × 학생프로필 → 생성정보(로그)
        
        6개 핵심 필드 생성
        """
        log = LearningLog(
            log_id=str(uuid.uuid4())[:8],
            cell_id=unit.cell_id,
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
        if unit.recommended_media in log.선호미디어_반응점수:
            log.선호미디어_반응점수[unit.recommended_media] = _clamp01(
                log.선호미디어_반응점수[unit.recommended_media] + 0.2
            )
        
        # ━━━ 성취도 계산 ━━━
        if log.이탈_여부:
            log.성취도 = random.uniform(0.1, 0.4)
        elif log.실패횟수 > unit.fail_allow:
            log.성취도 = random.uniform(0.4, 0.7)
        else:
            log.성취도 = random.uniform(0.7, 1.0)
        
        return log
    
    # ─────────────────────────────────────────────────────────────────────────
    # 핵심 2: 프로필 업데이트 (기존 로직)
    # ─────────────────────────────────────────────────────────────────────────
    def update_profile(
        self, 
        profile: LearnerProfile, 
        log: LearningLog,
        unit: HexUnit
    ) -> LearnerProfile:
        """생성정보 + 학생프로필 → 프로필 미세 업데이트"""
        
        # 미디어 선호 업데이트
        best_media = max(log.선호미디어_반응점수, key=log.선호미디어_반응점수.get)
        media_attr_map = {"이미지": "미디어_이미지", "텍스트": "미디어_텍스트", 
                          "숫자": "미디어_숫자", "영상": "미디어_영상"}
        for media, attr in media_attr_map.items():
            current = getattr(profile, attr)
            delta = 0.03 if media == best_media else -0.01
            setattr(profile, attr, _clamp01(current + delta))
        
        # 난이도 반응 조정
        if log.이탈_여부 or log.실패횟수 > unit.fail_allow:
            if profile.도전_선호도 == "높음":
                profile.도전_선호도 = "중간"
            elif profile.도전_선호도 == "중간" and random.random() < 0.3:
                profile.도전_선호도 = "낮음"
        
        if not log.이탈_여부 and log.실패횟수 <= 1:
            if profile.도전_선호도 == "낮음" and random.random() < 0.2:
                profile.도전_선호도 = "중간"
        
        # 성향축 미세 변화
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
        
        # 상태 업데이트
        profile.state_version += 1
        if not log.이탈_여부:
            profile.completed_cells.append(log.cell_id)
        
        return profile
    
    # ─────────────────────────────────────────────────────────────────────────
    # 핵심 3: 5가지 적합성 점수 계산 (기존 로직)
    # ─────────────────────────────────────────────────────────────────────────
    def calculate_match_scores(
        self,
        profile: LearnerProfile,
        last_log: Optional[LearningLog],
        candidate_cells: List[int]
    ) -> List[UnitMatchScore]:
        """5가지 적합성 점수 계산"""
        
        scores = []
        
        for cell_id in candidate_cells:
            unit = self.units.get(cell_id)
            if not unit:
                continue
            
            score = UnitMatchScore(cell_id=cell_id)
            
            # 이미 완료된 셀
            if cell_id in profile.completed_cells:
                score.is_available = False
                score.block_reason = "이미 완료"
                scores.append(score)
                continue
            
            # 잠긴 셀
            if unit.is_locked:
                score.is_available = False
                score.block_reason = "잠김"
                scores.append(score)
                continue
            
            # ━━━ 1. 선행조건 충족도 ━━━
            required_met = all(
                req in profile.completed_cells 
                for req in unit.prereq_required
            )
            if not required_met and unit.prereq_required:
                score.is_available = False
                score.block_reason = "필수 선행조건 미충족"
                scores.append(score)
                continue
            
            rec_count = sum(1 for r in unit.prereq_recommended if r in profile.completed_cells)
            rec_total = max(len(unit.prereq_recommended), 1)
            score.선행조건_충족도 = 0.6 + (rec_count / rec_total) * 0.4
            
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
            
            # ━━━ 총점 계산 ━━━
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
        
        scores.sort(key=lambda s: (s.is_available, s.total_score), reverse=True)
        return scores
    
    # ─────────────────────────────────────────────────────────────────────────
    # 벌집 잠금 해제
    # ─────────────────────────────────────────────────────────────────────────
    def unlock_adjacent(self, completed_cell: int):
        """완료된 셀의 인접 셀 잠금 해제"""
        unit = self.units.get(completed_cell)
        if not unit:
            return
        
        for adj_id in unit.adjacent_cells:
            if adj_id in self.units and self.units[adj_id].is_locked:
                self.units[adj_id].is_locked = False
    
    def get_available_cells(self) -> List[int]:
        """학습 가능한 셀 목록"""
        return [
            cell_id for cell_id, unit in self.units.items()
            if not unit.is_completed and not unit.is_locked
        ]
    
    def recommend_next_cell(
        self,
        profile: LearnerProfile,
        last_log: Optional[LearningLog]
    ) -> Optional[int]:
        """다음 추천 셀 (5가지 적합성 기반)"""
        available = self.get_available_cells()
        if not available:
            return None
        
        scores = self.calculate_match_scores(profile, last_log, available)
        for s in scores:
            if s.is_available:
                return s.cell_id
        
        return min(available)


# ════════════════════════════════════════════════════════════════════════════
# 9. 시각화 함수
# ════════════════════════════════════════════════════════════════════════════
def create_honeycomb_figure(
    units: Dict[int, HexUnit],
    current_cell: Optional[int] = None,
    recommended_cells: List[int] = None
) -> go.Figure:
    """벌집 맵 시각화"""
    
    fig = go.Figure()
    centers = generate_hexagon_centers(num_rings=4)
    
    colors = {
        'completed': '#2ecc71',
        'current': '#f39c12',
        'recommended': '#9b59b6',
        'available': '#3498db',
        'locked': '#bdc3c7',
    }
    
    recommended_cells = recommended_cells or []
    
    for cx, cy, cell_num in centers:
        if cell_num > 61:
            continue
        
        unit = units.get(cell_num)
        if not unit:
            continue
        
        # 색상 결정
        if unit.is_completed:
            color = colors['completed']
            line_color = '#27ae60'
        elif cell_num == current_cell:
            color = colors['current']
            line_color = '#e67e22'
        elif cell_num in recommended_cells[:3]:
            color = colors['recommended']
            line_color = '#8e44ad'
        elif not unit.is_locked:
            color = colors['available']
            line_color = '#2980b9'
        else:
            color = colors['locked']
            line_color = '#95a5a6'
        
        xs, ys = get_hexagon_vertices(cx, cy, size=0.95)
        
        hover_text = (
            f"<b>셀 {cell_num}</b><br>"
            f"타입: {unit.unit_type}<br>"
            f"난이도: {unit.difficulty}<br>"
            f"과목: {unit.subject_name}<br>"
            f"상태: {'완료' if unit.is_completed else '현재' if cell_num == current_cell else '가능' if not unit.is_locked else '잠김'}"
        )
        
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            fill='toself',
            fillcolor=color,
            line=dict(color=line_color, width=2),
            mode='lines',
            hoverinfo='text',
            hovertext=hover_text,
            showlegend=False
        ))
        
        fig.add_annotation(
            x=cx, y=cy,
            text=str(cell_num),
            showarrow=False,
            font=dict(
                size=12, 
                color='white' if unit.is_completed or cell_num == current_cell or cell_num in recommended_cells[:3] else 'black'
            ),
        )
    
    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor='y'),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=10, b=10),
        height=550,
    )
    
    return fig


def create_profile_radar(profile: LearnerProfile) -> go.Figure:
    """성향축 레이더"""
    p = profile.personality
    categories = ['탐험형', '성취형', '경쟁형', '창조형']
    values = [p.탐험형, p.성취형, p.경쟁형, p.창조형]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(52, 152, 219, 0.3)',
        line=dict(color='#3498db', width=2),
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 50])),
        showlegend=False,
        height=220,
        margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig


def create_score_bar(score: UnitMatchScore) -> go.Figure:
    """5가지 적합성 점수 막대"""
    categories = ['난이도', '학습타입', '미디어', '선행조건', '성향']
    values = [score.난이도_적합성, score.학습타입_적합성, 
              score.미디어_궁합, score.선행조건_충족도, score.성향_방향성]
    
    fig = go.Figure(data=go.Bar(
        x=values,
        y=categories,
        orientation='h',
        marker_color=['#e74c3c', '#f39c12', '#9b59b6', '#3498db', '#2ecc71']
    ))
    
    fig.update_layout(
        xaxis=dict(range=[0, 1]),
        height=180,
        margin=dict(l=70, r=20, t=10, b=20)
    )
    return fig


# ════════════════════════════════════════════════════════════════════════════
# 10. Streamlit 앱
# ════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="🐝 벌집 학습 시스템",
        page_icon="🐝",
        layout="wide"
    )
    
    st.title("🐝 벌집 구조 학습 시스템")
    st.caption("5가지 적합성 점수 기반 학습 시뮬레이션 + 벌집 시각화")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 세션 상태 초기화
    # ─────────────────────────────────────────────────────────────────────────
    if "simulator" not in st.session_state:
        st.session_state.simulator = HoneycombSimulator()
        units = generate_hex_units(61)
        st.session_state.simulator.load_units(units)
    
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "current_cell" not in st.session_state:
        st.session_state.current_cell = None
    if "last_log" not in st.session_state:
        st.session_state.last_log = None
    if "learning_history" not in st.session_state:
        st.session_state.learning_history = []
    if "last_scores" not in st.session_state:
        st.session_state.last_scores = []
    
    sim = st.session_state.simulator
    
    # ─────────────────────────────────────────────────────────────────────────
    # 사이드바
    # ─────────────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("🎮 컨트롤")
        
        if st.button("🎲 학습자 생성", use_container_width=True, type="primary"):
            st.session_state.profile = generate_learner_profile()
            st.session_state.simulator = HoneycombSimulator()
            units = generate_hex_units(61)
            st.session_state.simulator.load_units(units)
            st.session_state.current_cell = 1
            st.session_state.last_log = None
            st.session_state.learning_history = []
            st.session_state.last_scores = []
            st.rerun()
        
        if st.session_state.profile:
            st.divider()
            
            available = sim.get_available_cells()
            
            if available:
                if st.button("📚 학습 시뮬레이션", use_container_width=True):
                    profile = st.session_state.profile
                    current = st.session_state.current_cell or sim.recommend_next_cell(profile, st.session_state.last_log)
                    
                    if current and current in sim.units:
                        unit = sim.units[current]
                        
                        # 학습 시뮬레이션
                        log = sim.simulate_learning(profile, unit)
                        
                        # 프로필 업데이트
                        st.session_state.profile = sim.update_profile(profile, log, unit)
                        
                        # 결과 저장
                        st.session_state.last_log = log
                        st.session_state.learning_history.append(log)
                        
                        # 이탈하지 않으면 완료 처리
                        if not log.이탈_여부:
                            unit.is_completed = True
                            unit.score = log.성취도
                            sim.unlock_adjacent(current)
                        
                        # 다음 셀 추천
                        next_available = sim.get_available_cells()
                        if next_available:
                            # 5가지 적합성 점수 계산
                            scores = sim.calculate_match_scores(
                                st.session_state.profile, 
                                log, 
                                next_available
                            )
                            st.session_state.last_scores = scores
                            
                            # 최고 점수 셀 선택
                            for s in scores:
                                if s.is_available:
                                    st.session_state.current_cell = s.cell_id
                                    break
                        else:
                            st.session_state.current_cell = None
                        
                        st.rerun()
            else:
                st.success("🎉 모든 셀 완료!")
        
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.simulator = HoneycombSimulator()
            units = generate_hex_units(61)
            st.session_state.simulator.load_units(units)
            st.session_state.profile = None
            st.session_state.current_cell = None
            st.session_state.last_log = None
            st.session_state.learning_history = []
            st.session_state.last_scores = []
            st.rerun()
        
        st.divider()
        
        # 진행 상황
        completed = sum(1 for u in sim.units.values() if u.is_completed)
        st.metric("진행률", f"{completed}/61")
        st.progress(completed / 61)
        
        if st.session_state.current_cell:
            st.metric("현재 셀", f"#{st.session_state.current_cell}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 메인 영역
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.profile is None:
        st.info("👈 '학습자 생성' 버튼을 클릭하여 시작하세요!")
        
        # 범례
        st.markdown("""
        <div style="display: flex; gap: 20px; justify-content: center; margin: 10px 0;">
            <span>🟢 완료</span>
            <span>🟠 현재</span>
            <span>🟣 추천</span>
            <span>🔵 학습가능</span>
            <span>⚪ 잠김</span>
        </div>
        """, unsafe_allow_html=True)
        
        fig = create_honeycomb_figure(sim.units)
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        profile = st.session_state.profile
        
        # 2열 레이아웃
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("🗺️ 학습 맵")
            
            st.markdown("""
            <div style="display: flex; gap: 15px; justify-content: center; margin-bottom: 10px; font-size: 0.9em;">
                <span>🟢 완료</span>
                <span>🟠 현재</span>
                <span>🟣 추천 Top3</span>
                <span>🔵 학습가능</span>
                <span>⚪ 잠김</span>
            </div>
            """, unsafe_allow_html=True)
            
            recommended = [s.cell_id for s in st.session_state.last_scores if s.is_available]
            fig = create_honeycomb_figure(
                sim.units,
                current_cell=st.session_state.current_cell,
                recommended_cells=recommended
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 학습자 정보
            st.subheader(f"👤 {profile.name}")
            st.caption(f"v{profile.state_version} | 완료: {len(profile.completed_cells)}개")
            
            st.plotly_chart(create_profile_radar(profile), use_container_width=True)
            
            col_a, col_b = st.columns(2)
            col_a.metric("도전 선호", profile.도전_선호도)
            col_b.metric("실패 인내", profile.실패_인내도)
            
            st.divider()
            
            # 최근 학습 결과 (생성정보 6개 필드)
            if st.session_state.last_log:
                log = st.session_state.last_log
                st.subheader(f"📊 생성정보 (셀 #{log.cell_id})")
                
                cols = st.columns(3)
                cols[0].metric("체류시간", f"{log.체류시간_초}초")
                cols[1].metric("실패횟수", f"{log.실패횟수}회")
                cols[2].metric("성취도", f"{log.성취도:.0%}")
                
                cols2 = st.columns(3)
                cols2[0].metric("이탈", "❌" if log.이탈_여부 else "✅")
                cols2[1].metric("재도전", "✅" if log.재도전_여부 else "❌")
                cols2[2].metric("보상반응", log.보상반응)
                
                # 미디어 반응
                with st.expander("📺 미디어 반응 점수"):
                    for k, v in log.선호미디어_반응점수.items():
                        st.progress(v, text=f"{k}: {v:.2f}")
            
            st.divider()
            
            # 5가지 적합성 점수
            if st.session_state.last_scores:
                st.subheader("🎯 다음 셀 추천 (Top 3)")
                
                for i, score in enumerate(st.session_state.last_scores[:3]):
                    if not score.is_available:
                        continue
                    
                    unit = sim.units.get(score.cell_id)
                    if not unit:
                        continue
                    
                    with st.expander(f"**{i+1}위: 셀 #{score.cell_id}** ({unit.unit_type}) - {score.total_score:.3f}"):
                        st.write(f"난이도: {unit.difficulty} | 과목: {unit.subject_name}")
                        st.plotly_chart(create_score_bar(score), use_container_width=True)
        
        # 학습 히스토리
        if st.session_state.learning_history:
            st.divider()
            st.subheader("📜 학습 히스토리")
            
            history_data = []
            for log in st.session_state.learning_history:
                history_data.append({
                    "셀": f"#{log.cell_id}",
                    "체류시간": f"{log.체류시간_초}초",
                    "실패": log.실패횟수,
                    "재도전": "✅" if log.재도전_여부 else "❌",
                    "완료": "❌이탈" if log.이탈_여부 else "✅완료",
                    "성취도": f"{log.성취도:.0%}",
                    "보상반응": log.보상반응
                })
            
            st.dataframe(history_data, use_container_width=True)


if __name__ == "__main__":
    main()
