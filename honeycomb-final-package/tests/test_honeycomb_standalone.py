"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
벌집 구조 학습 시스템 - 독립 실행 테스트 코드
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

실행 방법:
  python test_honeycomb_standalone.py

테스트 항목:
  1. 학습자 프로필 생성
  2. 벌집 유니트 생성 (61개)
  3. 생성정보 6개 필드
  4. 5가지 적합성 점수 계산
  5. 인접 셀 잠금 해제
  6. 프로필 업데이트
  7. 전체 시뮬레이션 흐름

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Literal
import random
import uuid
import math
from datetime import datetime
import sys

# ════════════════════════════════════════════════════════════════════════════
# 타입 정의
# ════════════════════════════════════════════════════════════════════════════
Level3 = Literal["낮음", "중간", "높음"]
UnitType = Literal["개념", "실전", "탐색", "보조"]
RewardType = Literal["칭찬", "개방", "시각효과"]
MediaType = Literal["이미지", "텍스트", "숫자", "영상", "혼합"]


# ════════════════════════════════════════════════════════════════════════════
# 유틸리티 함수
# ════════════════════════════════════════════════════════════════════════════
def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


# ════════════════════════════════════════════════════════════════════════════
# 1. 학습자 프로필
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class PersonalityAxis:
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


@dataclass
class LearnerProfile:
    learner_id: str = ""
    name: str = ""
    personality: PersonalityAxis = field(default_factory=PersonalityAxis)
    도전_선호도: Level3 = "중간"
    실패_인내도: Level3 = "중간"
    미디어_이미지: float = 0.5
    미디어_텍스트: float = 0.5
    미디어_숫자: float = 0.5
    미디어_영상: float = 0.5
    평균_집중_지속시간_초: int = 180
    지루함_임계치_초: int = 120
    이탈_임계치_실패횟수: int = 3
    재도전_확률: int = 50
    확장_선택_확률: int = 30
    휴식_수용도: Level3 = "중간"
    state_version: int = 0
    completed_cells: List[int] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════════════
# 2. 벌집 유니트
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class HexUnit:
    cell_id: int
    unit_type: UnitType
    difficulty: int
    subject: str
    subject_name: str
    prereq_required: List[int] = field(default_factory=list)
    prereq_recommended: List[int] = field(default_factory=list)
    adjacent_cells: List[int] = field(default_factory=list)
    recommended_media: MediaType = "혼합"
    estimated_time_sec: int = 180
    fail_allow: int = 3
    reward_type: RewardType = "칭찬"
    is_completed: bool = False
    is_locked: bool = True
    score: float = 0.0


# ════════════════════════════════════════════════════════════════════════════
# 3. 학습 생성정보
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class LearningLog:
    log_id: str = ""
    cell_id: int = 0
    learner_id: str = ""
    timestamp: str = ""
    체류시간_초: int = 0
    실패횟수: int = 0
    재도전_여부: bool = False
    이탈_여부: bool = False
    보상반응: RewardType = "칭찬"
    선호미디어_반응점수: Dict[str, float] = field(default_factory=dict)
    성취도: float = 0.0


# ════════════════════════════════════════════════════════════════════════════
# 4. 적합성 점수
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class UnitMatchScore:
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
# 5. 벌집 좌표 계산
# ════════════════════════════════════════════════════════════════════════════
def get_ring_from_cell(cell_id: int) -> int:
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
    if cell_id == 1:
        return [2, 3, 4, 5, 6, 7]
    
    ring = get_ring_from_cell(cell_id)
    adjacent = []
    
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
    
    if ring > 1:
        prev_ring_start = 2 + sum(6 * r for r in range(1, ring - 1))
        offset = cell_id - ring_start
        prev_cell = prev_ring_start + int(offset * (ring - 1) / ring)
        if 1 < prev_cell <= 61:
            adjacent.append(prev_cell)
    elif ring == 1:
        adjacent.append(1)
    
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
    centers = []
    cell_num = 1
    size = 1.0
    h = size * math.sqrt(3)
    
    centers.append((0, 0, cell_num))
    cell_num += 1
    
    for ring in range(1, num_rings + 1):
        directions = [
            (1.5 * size, -h/2), (0, -h), (-1.5 * size, -h/2),
            (-1.5 * size, h/2), (0, h), (1.5 * size, h/2),
        ]
        x, y = 0, ring * h
        for dir_idx, (dx, dy) in enumerate(directions):
            for step in range(ring):
                centers.append((x, y, cell_num))
                cell_num += 1
                x += dx
                y += dy
    
    return [(x, y, n) for x, y, n in centers if n <= 61]


# ════════════════════════════════════════════════════════════════════════════
# 6. 데이터 생성기
# ════════════════════════════════════════════════════════════════════════════
SUBJECTS = {'A': '수와 연산', 'B': '도형과 측정', 'C': '규칙성', 'D': '자료와 가능성',
            'E': '물질과 에너지', 'F': '생명과 환경', 'G': '지구와 우주'}
NAMES = ["민준", "서연", "도윤", "하윤", "지호", "서준", "예린", "지민"]
LAST_NAMES = ["김", "이", "박", "최", "정", "강", "조", "윤"]


def generate_learner_profile() -> LearnerProfile:
    raw = [random.random() ** 0.7 for _ in range(4)]
    total = sum(raw)
    norm = [int(r / total * 100) for r in raw]
    norm[0] += 100 - sum(norm)
    
    personality = PersonalityAxis(탐험형=norm[0], 성취형=norm[1], 경쟁형=norm[2], 창조형=norm[3])
    
    return LearnerProfile(
        learner_id=str(uuid.uuid4())[:8],
        name=f"{random.choice(LAST_NAMES)}{random.choice(NAMES)}",
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
    units = {}
    subject_list = list(SUBJECTS.keys())
    media_types: List[MediaType] = ["이미지", "텍스트", "숫자", "영상", "혼합"]
    
    for i in range(1, num_cells + 1):
        ring = get_ring_from_cell(i)
        difficulty = min(12, ring * 3 + random.randint(0, 2)) or 1
        
        if ring == 0:
            utype = "개념"
        elif ring == 1:
            utype = random.choice(["개념", "보조"])
        elif ring == 2:
            utype = random.choice(["보조", "실전"])
        else:
            utype = random.choice(["실전", "탐색"])
        
        subj = subject_list[(i - 1) % len(subject_list)]
        adjacent = get_adjacent_cells(i)
        prereq_req = [a for a in adjacent if a < i and get_ring_from_cell(a) < ring][:1]
        prereq_rec = [a for a in adjacent if a < i][:2]
        
        units[i] = HexUnit(
            cell_id=i, unit_type=utype, difficulty=difficulty,
            subject=subj, subject_name=SUBJECTS[subj],
            prereq_required=prereq_req, prereq_recommended=prereq_rec,
            adjacent_cells=adjacent, recommended_media=random.choice(media_types),
            estimated_time_sec=120 + difficulty * 15 + random.randint(-20, 20),
            fail_allow=max(1, 5 - difficulty // 3),
            reward_type=random.choice(["칭찬", "개방", "시각효과"]),
            is_locked=(i != 1)
        )
    
    return units


# ════════════════════════════════════════════════════════════════════════════
# 7. 시뮬레이터
# ════════════════════════════════════════════════════════════════════════════
class HoneycombSimulator:
    def __init__(self):
        self.units: Dict[int, HexUnit] = {}
    
    def load_units(self, units: Dict[int, HexUnit]):
        self.units = units
    
    def simulate_learning(self, profile: LearnerProfile, unit: HexUnit) -> LearningLog:
        log = LearningLog(
            log_id=str(uuid.uuid4())[:8],
            cell_id=unit.cell_id,
            learner_id=profile.learner_id,
            timestamp=datetime.now().isoformat()
        )
        
        # 1. 체류시간
        base_time = profile.평균_집중_지속시간_초
        diff_factor = (unit.difficulty - 6) * 8
        type_mult = {"개념": 1.2, "실전": 1.0, "탐색": 0.8, "보조": 0.7}.get(unit.unit_type, 1.0)
        log.체류시간_초 = max(20, int((base_time + diff_factor + random.gauss(0, 25)) * type_mult))
        
        # 2. 실패횟수
        base_fail = max(0, (unit.difficulty - 5) // 2) + random.randint(0, 2)
        if profile.도전_선호도 == "높음":
            base_fail += random.randint(0, 2)
        elif profile.도전_선호도 == "낮음":
            base_fail = max(0, base_fail - 1)
        if profile.실패_인내도 == "높음":
            base_fail = max(0, base_fail - 1)
        log.실패횟수 = min(base_fail, 10)
        
        # 3. 이탈 여부
        if log.실패횟수 >= profile.이탈_임계치_실패횟수:
            log.이탈_여부 = random.random() < 0.6
        if log.체류시간_초 > profile.지루함_임계치_초 and unit.unit_type in ["개념", "보조"]:
            log.이탈_여부 = log.이탈_여부 or (random.random() < 0.25)
        
        # 4. 재도전 여부
        if log.실패횟수 > 0 and not log.이탈_여부:
            log.재도전_여부 = random.random() * 100 < profile.재도전_확률
        
        # 5. 보상반응
        weights = {"칭찬": profile.personality.성취형 + 10, 
                   "개방": profile.personality.탐험형 + profile.personality.창조형,
                   "시각효과": profile.personality.창조형 + profile.personality.경쟁형}
        r, cum = random.random() * sum(weights.values()), 0
        for reward, w in weights.items():
            cum += w
            if r <= cum:
                log.보상반응 = reward
                break
        
        # 6. 미디어 반응점수
        log.선호미디어_반응점수 = {
            "이미지": _clamp01(profile.미디어_이미지 + random.uniform(-0.15, 0.15)),
            "텍스트": _clamp01(profile.미디어_텍스트 + random.uniform(-0.15, 0.15)),
            "숫자": _clamp01(profile.미디어_숫자 + random.uniform(-0.15, 0.15)),
            "영상": _clamp01(profile.미디어_영상 + random.uniform(-0.15, 0.15))
        }
        if unit.recommended_media in log.선호미디어_반응점수:
            log.선호미디어_반응점수[unit.recommended_media] = _clamp01(
                log.선호미디어_반응점수[unit.recommended_media] + 0.2)
        
        # 성취도
        if log.이탈_여부:
            log.성취도 = random.uniform(0.1, 0.4)
        elif log.실패횟수 > unit.fail_allow:
            log.성취도 = random.uniform(0.4, 0.7)
        else:
            log.성취도 = random.uniform(0.7, 1.0)
        
        return log
    
    def update_profile(self, profile: LearnerProfile, log: LearningLog, unit: HexUnit) -> LearnerProfile:
        # 미디어 선호 업데이트
        best_media = max(log.선호미디어_반응점수, key=log.선호미디어_반응점수.get)
        for media, attr in [("이미지", "미디어_이미지"), ("텍스트", "미디어_텍스트"), 
                            ("숫자", "미디어_숫자"), ("영상", "미디어_영상")]:
            current = getattr(profile, attr)
            delta = 0.03 if media == best_media else -0.01
            setattr(profile, attr, _clamp01(current + delta))
        
        # 난이도 반응 조정
        if log.이탈_여부 or log.실패횟수 > unit.fail_allow:
            if profile.도전_선호도 == "높음":
                profile.도전_선호도 = "중간"
        
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
        
        profile.state_version += 1
        if not log.이탈_여부:
            profile.completed_cells.append(log.cell_id)
        
        return profile
    
    def calculate_match_scores(self, profile: LearnerProfile, last_log: Optional[LearningLog],
                               candidate_cells: List[int]) -> List[UnitMatchScore]:
        scores = []
        
        for cell_id in candidate_cells:
            unit = self.units.get(cell_id)
            if not unit:
                continue
            
            score = UnitMatchScore(cell_id=cell_id)
            
            if cell_id in profile.completed_cells:
                score.is_available = False
                score.block_reason = "이미 완료"
                scores.append(score)
                continue
            
            if unit.is_locked:
                score.is_available = False
                score.block_reason = "잠김"
                scores.append(score)
                continue
            
            # 1. 선행조건 충족도
            required_met = all(req in profile.completed_cells for req in unit.prereq_required)
            if not required_met and unit.prereq_required:
                score.is_available = False
                score.block_reason = "필수 선행조건 미충족"
                scores.append(score)
                continue
            
            rec_count = sum(1 for r in unit.prereq_recommended if r in profile.completed_cells)
            rec_total = max(len(unit.prereq_recommended), 1)
            score.선행조건_충족도 = 0.6 + (rec_count / rec_total) * 0.4
            
            # 2. 난이도 적합성
            ideal_diff = 6
            if last_log:
                if last_log.실패횟수 > 2:
                    ideal_diff -= 1
                if not last_log.이탈_여부 and last_log.실패횟수 <= 1:
                    ideal_diff += 1
            if profile.도전_선호도 == "높음":
                ideal_diff += 2
            elif profile.도전_선호도 == "낮음":
                ideal_diff -= 1
            score.난이도_적합성 = max(0, 1 - abs(unit.difficulty - ideal_diff) * 0.12)
            
            # 3. 학습타입 적합성
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
            
            # 4. 미디어 궁합
            media_pref = {"이미지": profile.미디어_이미지, "텍스트": profile.미디어_텍스트,
                          "숫자": profile.미디어_숫자, "영상": profile.미디어_영상, "혼합": 0.5}
            if last_log and last_log.선호미디어_반응점수:
                for k in ["이미지", "텍스트", "숫자", "영상"]:
                    if k in last_log.선호미디어_반응점수:
                        media_pref[k] = (media_pref[k] + last_log.선호미디어_반응점수[k]) / 2
            score.미디어_궁합 = media_pref.get(unit.recommended_media, 0.5)
            
            # 5. 성향 방향성
            direction = 0.5
            if unit.unit_type == "탐색":
                direction += axis.탐험형 * 0.004
            elif unit.unit_type == "실전":
                direction += axis.성취형 * 0.004 + axis.경쟁형 * 0.002
            elif unit.unit_type == "개념":
                direction += axis.창조형 * 0.003
            score.성향_방향성 = min(1.0, direction)
            
            # 총점 (가중치: 난이도 25%, 학습타입 20%, 미디어 15%, 선행조건 25%, 성향 15%)
            score.total_score = (score.난이도_적합성 * 0.25 + score.학습타입_적합성 * 0.20 +
                                 score.미디어_궁합 * 0.15 + score.선행조건_충족도 * 0.25 +
                                 score.성향_방향성 * 0.15)
            
            scores.append(score)
        
        scores.sort(key=lambda s: (s.is_available, s.total_score), reverse=True)
        return scores
    
    def unlock_adjacent(self, completed_cell: int):
        unit = self.units.get(completed_cell)
        if not unit:
            return
        for adj_id in unit.adjacent_cells:
            if adj_id in self.units and self.units[adj_id].is_locked:
                self.units[adj_id].is_locked = False
    
    def get_available_cells(self) -> List[int]:
        return [cell_id for cell_id, unit in self.units.items() if not unit.is_completed and not unit.is_locked]


# ════════════════════════════════════════════════════════════════════════════
# 테스트 클래스
# ════════════════════════════════════════════════════════════════════════════

class TestRunner:
    """테스트 실행기"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def assert_true(self, condition, msg=""):
        if not condition:
            raise AssertionError(msg)
    
    def assert_equal(self, a, b, msg=""):
        if a != b:
            raise AssertionError(f"{msg}: {a} != {b}")
    
    def run_test(self, test_name, test_func):
        try:
            test_func()
            self.passed += 1
            self.results.append((test_name, True, ""))
            print(f"  ✅ {test_name}")
        except AssertionError as e:
            self.failed += 1
            self.results.append((test_name, False, str(e)))
            print(f"  ❌ {test_name}: {e}")
        except Exception as e:
            self.failed += 1
            self.results.append((test_name, False, str(e)))
            print(f"  ❌ {test_name}: {type(e).__name__}: {e}")


def run_all_tests():
    """모든 테스트 실행"""
    runner = TestRunner()
    
    print("=" * 70)
    print("벌집 구조 학습 시스템 - 테스트 실행")
    print("=" * 70)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. 학습자 프로필 테스트
    # ═══════════════════════════════════════════════════════════════════════
    print("\n📋 학습자 프로필 테스트")
    print("─" * 50)
    
    def test_profile_generation():
        profile = generate_learner_profile()
        runner.assert_true(profile is not None, "프로필이 None")
        runner.assert_true(profile.learner_id != "", "ID가 비어있음")
        runner.assert_true(profile.name != "", "이름이 비어있음")
    
    def test_personality_sum_100():
        profile = generate_learner_profile()
        p = profile.personality
        total = p.탐험형 + p.성취형 + p.경쟁형 + p.창조형
        runner.assert_equal(total, 100, "성향축 합계")
    
    def test_personality_normalize():
        axis = PersonalityAxis(탐험형=50, 성취형=50, 경쟁형=50, 창조형=50)
        axis.normalize()
        total = axis.탐험형 + axis.성취형 + axis.경쟁형 + axis.창조형
        runner.assert_equal(total, 100, "정규화 후 합계")
    
    def test_media_preference_range():
        profile = generate_learner_profile()
        runner.assert_true(0 <= profile.미디어_이미지 <= 1, "미디어_이미지 범위")
        runner.assert_true(0 <= profile.미디어_텍스트 <= 1, "미디어_텍스트 범위")
    
    runner.run_test("프로필 생성", test_profile_generation)
    runner.run_test("성향축 합계 100", test_personality_sum_100)
    runner.run_test("성향축 정규화", test_personality_normalize)
    runner.run_test("미디어 선호도 범위", test_media_preference_range)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. 벌집 유니트 테스트
    # ═══════════════════════════════════════════════════════════════════════
    print("\n📋 벌집 유니트 테스트")
    print("─" * 50)
    
    def test_generate_61_units():
        units = generate_hex_units(61)
        runner.assert_equal(len(units), 61, "유니트 수")
    
    def test_unit_types():
        units = generate_hex_units(61)
        valid_types = ["개념", "실전", "탐색", "보조"]
        for cell_id, unit in units.items():
            runner.assert_true(unit.unit_type in valid_types, f"셀 {cell_id} 타입 오류")
    
    def test_difficulty_range():
        units = generate_hex_units(61)
        for cell_id, unit in units.items():
            runner.assert_true(1 <= unit.difficulty <= 12, f"셀 {cell_id} 난이도 범위")
    
    def test_cell_1_unlocked():
        units = generate_hex_units(61)
        runner.assert_true(units[1].is_locked == False, "셀 1 잠금 해제")
    
    def test_ring_calculation():
        runner.assert_equal(get_ring_from_cell(1), 0, "셀 1 링")
        runner.assert_equal(get_ring_from_cell(7), 1, "셀 7 링")
        runner.assert_equal(get_ring_from_cell(19), 2, "셀 19 링")
        runner.assert_equal(get_ring_from_cell(37), 3, "셀 37 링")
        runner.assert_equal(get_ring_from_cell(61), 4, "셀 61 링")
    
    def test_adjacent_cell_1():
        adj = get_adjacent_cells(1)
        runner.assert_equal(set(adj), {2, 3, 4, 5, 6, 7}, "셀 1 인접")
    
    def test_hexagon_centers():
        centers = generate_hexagon_centers(4)
        runner.assert_equal(len(centers), 61, "육각형 중심 수")
    
    runner.run_test("61개 유니트 생성", test_generate_61_units)
    runner.run_test("유니트 타입 유효성", test_unit_types)
    runner.run_test("난이도 범위 1~12", test_difficulty_range)
    runner.run_test("셀 1 잠금 해제", test_cell_1_unlocked)
    runner.run_test("링 번호 계산", test_ring_calculation)
    runner.run_test("셀 1 인접 셀", test_adjacent_cell_1)
    runner.run_test("육각형 중심 좌표", test_hexagon_centers)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. 생성정보 6개 필드 테스트
    # ═══════════════════════════════════════════════════════════════════════
    print("\n📋 생성정보 6개 필드 테스트")
    print("─" * 50)
    
    profile = generate_learner_profile()
    units = generate_hex_units(61)
    simulator = HoneycombSimulator()
    simulator.load_units(units)
    
    def test_log_creation():
        log = simulator.simulate_learning(profile, units[1])
        runner.assert_true(log is not None, "로그 생성")
        runner.assert_true(isinstance(log, LearningLog), "로그 타입")
    
    def test_log_6_fields():
        log = simulator.simulate_learning(profile, units[1])
        runner.assert_true(hasattr(log, '체류시간_초'), "체류시간 필드")
        runner.assert_true(hasattr(log, '실패횟수'), "실패횟수 필드")
        runner.assert_true(hasattr(log, '재도전_여부'), "재도전 필드")
        runner.assert_true(hasattr(log, '이탈_여부'), "이탈 필드")
        runner.assert_true(hasattr(log, '보상반응'), "보상반응 필드")
        runner.assert_true(hasattr(log, '선호미디어_반응점수'), "미디어점수 필드")
    
    def test_stay_time_positive():
        for _ in range(10):
            log = simulator.simulate_learning(profile, units[1])
            runner.assert_true(log.체류시간_초 > 0, "체류시간 양수")
    
    def test_fail_count_non_negative():
        for _ in range(10):
            log = simulator.simulate_learning(profile, units[1])
            runner.assert_true(log.실패횟수 >= 0, "실패횟수 비음수")
    
    def test_reward_response_valid():
        valid = ["칭찬", "개방", "시각효과"]
        for _ in range(10):
            log = simulator.simulate_learning(profile, units[1])
            runner.assert_true(log.보상반응 in valid, "보상반응 유효")
    
    def test_media_score_range():
        log = simulator.simulate_learning(profile, units[1])
        for media, score in log.선호미디어_반응점수.items():
            runner.assert_true(0 <= score <= 1, f"{media} 점수 범위")
    
    def test_media_4_types():
        log = simulator.simulate_learning(profile, units[1])
        expected = {"이미지", "텍스트", "숫자", "영상"}
        actual = set(log.선호미디어_반응점수.keys())
        runner.assert_equal(expected, actual, "미디어 4가지 타입")
    
    runner.run_test("학습 로그 생성", test_log_creation)
    runner.run_test("6개 핵심 필드 존재", test_log_6_fields)
    runner.run_test("체류시간 양수", test_stay_time_positive)
    runner.run_test("실패횟수 비음수", test_fail_count_non_negative)
    runner.run_test("보상반응 유효값", test_reward_response_valid)
    runner.run_test("미디어 점수 0~1", test_media_score_range)
    runner.run_test("미디어 4가지 타입", test_media_4_types)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. 5가지 적합성 점수 테스트
    # ═══════════════════════════════════════════════════════════════════════
    print("\n📋 5가지 적합성 점수 테스트")
    print("─" * 50)
    
    def test_scores_list():
        available = simulator.get_available_cells()
        scores = simulator.calculate_match_scores(profile, None, available)
        runner.assert_true(isinstance(scores, list), "점수 리스트")
        runner.assert_true(len(scores) > 0, "점수 개수")
    
    def test_5_fitness_fields():
        available = simulator.get_available_cells()
        scores = simulator.calculate_match_scores(profile, None, available)
        s = scores[0]
        runner.assert_true(hasattr(s, '난이도_적합성'), "난이도 필드")
        runner.assert_true(hasattr(s, '학습타입_적합성'), "학습타입 필드")
        runner.assert_true(hasattr(s, '미디어_궁합'), "미디어 필드")
        runner.assert_true(hasattr(s, '선행조건_충족도'), "선행조건 필드")
        runner.assert_true(hasattr(s, '성향_방향성'), "성향 필드")
    
    def test_fitness_range():
        available = simulator.get_available_cells()
        scores = simulator.calculate_match_scores(profile, None, available)
        for s in scores:
            if s.is_available:
                runner.assert_true(0 <= s.난이도_적합성 <= 1, "난이도 범위")
                runner.assert_true(0 <= s.학습타입_적합성 <= 1, "학습타입 범위")
                runner.assert_true(0 <= s.미디어_궁합 <= 1, "미디어 범위")
                runner.assert_true(0 <= s.선행조건_충족도 <= 1, "선행조건 범위")
                runner.assert_true(0 <= s.성향_방향성 <= 1, "성향 범위")
    
    def test_weighted_sum():
        available = simulator.get_available_cells()
        scores = simulator.calculate_match_scores(profile, None, available)
        for s in scores:
            if s.is_available:
                expected = (s.난이도_적합성 * 0.25 + s.학습타입_적합성 * 0.20 +
                            s.미디어_궁합 * 0.15 + s.선행조건_충족도 * 0.25 + s.성향_방향성 * 0.15)
                runner.assert_true(abs(s.total_score - expected) < 0.001, "가중 평균")
    
    def test_sorted_descending():
        available = simulator.get_available_cells()
        scores = simulator.calculate_match_scores(profile, None, available)
        available_scores = [s for s in scores if s.is_available]
        for i in range(len(available_scores) - 1):
            runner.assert_true(available_scores[i].total_score >= available_scores[i+1].total_score, "내림차순")
    
    runner.run_test("점수 리스트 반환", test_scores_list)
    runner.run_test("5가지 적합성 필드", test_5_fitness_fields)
    runner.run_test("적합성 점수 0~1 범위", test_fitness_range)
    runner.run_test("총점 가중 평균", test_weighted_sum)
    runner.run_test("점수 내림차순 정렬", test_sorted_descending)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 5. 인접 셀 잠금 해제 테스트
    # ═══════════════════════════════════════════════════════════════════════
    print("\n📋 인접 셀 잠금 해제 테스트")
    print("─" * 50)
    
    def test_unlock_adjacent():
        units2 = generate_hex_units(61)
        sim2 = HoneycombSimulator()
        sim2.load_units(units2)
        
        # 초기: 셀 2~7 잠김
        for i in range(2, 8):
            runner.assert_true(units2[i].is_locked, f"셀 {i} 초기 잠김")
        
        sim2.unlock_adjacent(1)
        unlocked = sum(1 for i in range(2, 8) if not units2[i].is_locked)
        runner.assert_true(unlocked > 0, "인접 셀 잠금 해제")
    
    def test_non_adjacent_locked():
        units2 = generate_hex_units(61)
        sim2 = HoneycombSimulator()
        sim2.load_units(units2)
        sim2.unlock_adjacent(1)
        
        # 외곽 셀(링 4)은 여전히 잠김
        for i in range(38, 62):
            runner.assert_true(units2[i].is_locked, f"셀 {i} 잠금 유지")
    
    runner.run_test("인접 셀 잠금 해제", test_unlock_adjacent)
    runner.run_test("비인접 셀 잠금 유지", test_non_adjacent_locked)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 6. 프로필 업데이트 테스트
    # ═══════════════════════════════════════════════════════════════════════
    print("\n📋 프로필 업데이트 테스트")
    print("─" * 50)
    
    def test_version_increment():
        p = generate_learner_profile()
        u = generate_hex_units(61)
        s = HoneycombSimulator()
        s.load_units(u)
        
        initial = p.state_version
        log = s.simulate_learning(p, u[1])
        p = s.update_profile(p, log, u[1])
        runner.assert_equal(p.state_version, initial + 1, "버전 증가")
    
    def test_personality_normalized():
        p = generate_learner_profile()
        u = generate_hex_units(61)
        s = HoneycombSimulator()
        s.load_units(u)
        
        for _ in range(5):
            log = s.simulate_learning(p, u[1])
            p = s.update_profile(p, log, u[1])
        
        total = p.personality.탐험형 + p.personality.성취형 + p.personality.경쟁형 + p.personality.창조형
        runner.assert_equal(total, 100, "성향축 합계 유지")
    
    runner.run_test("상태 버전 증가", test_version_increment)
    runner.run_test("업데이트 후 성향축 합계", test_personality_normalized)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 7. 전체 시뮬레이션 흐름 테스트
    # ═══════════════════════════════════════════════════════════════════════
    print("\n📋 전체 시뮬레이션 흐름 테스트")
    print("─" * 50)
    
    def test_full_simulation():
        p = generate_learner_profile()
        u = generate_hex_units(61)
        s = HoneycombSimulator()
        s.load_units(u)
        
        history = []
        current = 1
        
        print(f"\n  🎮 시뮬레이션 시작: {p.name}")
        
        for round_num in range(1, 11):
            available = s.get_available_cells()
            if not available:
                break
            
            scores = s.calculate_match_scores(p, history[-1] if history else None, available)
            best = next((sc for sc in scores if sc.is_available), None)
            if not best:
                break
            
            current = best.cell_id
            unit = u[current]
            log = s.simulate_learning(p, unit)
            history.append(log)
            
            status = "❌" if log.이탈_여부 else "✅"
            print(f"    [{round_num}] 셀#{current} {unit.unit_type} | {status} | 체류:{log.체류시간_초}초")
            
            p = s.update_profile(p, log, unit)
            
            if not log.이탈_여부:
                unit.is_completed = True
                s.unlock_adjacent(current)
        
        runner.assert_true(len(history) > 0, "학습 히스토리")
        runner.assert_true(p.state_version > 0, "버전 업데이트")
        
        completed = sum(1 for unit in u.values() if unit.is_completed)
        print(f"\n  📊 결과: {completed}개 완료, v{p.state_version}")
    
    runner.run_test("전체 시뮬레이션 (10회)", test_full_simulation)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 결과 출력
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print(f"테스트 결과: ✅ {runner.passed}개 통과, ❌ {runner.failed}개 실패")
    print("=" * 70)
    
    return runner.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
