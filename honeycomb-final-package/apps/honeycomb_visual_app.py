"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
벌집 구조 학습 시스템 - 벌집 시각화 버전
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

실행 방법:
  pip install streamlit plotly numpy
  streamlit run honeycomb_visual_app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Literal
import json

# ════════════════════════════════════════════════════════════════════════════
# 타입 정의
# ════════════════════════════════════════════════════════════════════════════
Level3 = Literal["낮음", "중간", "높음"]
UnitType = Literal["개념", "실전", "탐색", "보조"]
RewardType = Literal["칭찬", "개방", "시각효과"]

# ════════════════════════════════════════════════════════════════════════════
# 벌집 좌표 계산 (61개 셀)
# ════════════════════════════════════════════════════════════════════════════
def generate_hexagon_centers(num_rings: int = 4) -> List[Tuple[float, float, int]]:
    """
    벌집 구조의 육각형 중심 좌표 생성
    나선형 순서로 번호 매김 (중앙=1, 시계방향 확장)
    
    Returns: [(x, y, cell_number), ...]
    """
    centers = []
    cell_num = 1
    
    # 육각형 크기
    size = 1.0
    h = size * math.sqrt(3)
    
    # 중앙 (1번)
    centers.append((0, 0, cell_num))
    cell_num += 1
    
    # 각 링 처리
    for ring in range(1, num_rings + 1):
        # 6방향 벡터 (시계방향)
        directions = [
            (1.5 * size, -h/2),   # 우하
            (0, -h),              # 하
            (-1.5 * size, -h/2),  # 좌하
            (-1.5 * size, h/2),   # 좌상
            (0, h),               # 상
            (1.5 * size, h/2),    # 우상
        ]
        
        # 시작점 (상단)
        x, y = 0, ring * h
        
        for dir_idx, (dx, dy) in enumerate(directions):
            for step in range(ring):
                centers.append((x, y, cell_num))
                cell_num += 1
                x += dx
                y += dy
    
    return centers


def get_hexagon_vertices(cx: float, cy: float, size: float = 0.9) -> Tuple[List[float], List[float]]:
    """육각형 꼭짓점 좌표 반환"""
    angles = [math.pi/6 + i * math.pi/3 for i in range(6)]
    xs = [cx + size * math.cos(a) for a in angles]
    ys = [cy + size * math.sin(a) for a in angles]
    return xs + [xs[0]], ys + [ys[0]]  # 닫힌 다각형


# ════════════════════════════════════════════════════════════════════════════
# 벌집 유니트 정보
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class HexUnit:
    """벌집 셀 유니트"""
    cell_id: int
    unit_type: UnitType
    difficulty: int
    subject: str
    title: str
    adjacent_cells: List[int] = field(default_factory=list)
    
    # 학습 상태
    is_completed: bool = False
    is_locked: bool = True
    is_current: bool = False
    
    # 학습 결과
    stay_time: int = 0
    fail_count: int = 0
    score: float = 0.0


def generate_hex_units(num_cells: int = 61) -> Dict[int, HexUnit]:
    """61개 벌집 유니트 생성"""
    units = {}
    
    subjects = ['수학', '과학', '언어', '사회', '예술', '체육', '코딩']
    unit_types: List[UnitType] = ["개념", "보조", "실전", "탐색"]
    
    for i in range(1, num_cells + 1):
        ring = get_ring_from_cell(i)
        
        # 난이도: 링 기반 (중앙=1, 외곽=높음)
        difficulty = min(12, ring * 2 + random.randint(0, 2))
        
        # 유니트 타입: 링별 패턴
        if ring == 0:
            utype = "개념"
        elif ring == 1:
            utype = random.choice(["개념", "보조"])
        elif ring == 2:
            utype = random.choice(["보조", "실전"])
        else:
            utype = random.choice(["실전", "탐색"])
        
        units[i] = HexUnit(
            cell_id=i,
            unit_type=utype,
            difficulty=difficulty,
            subject=subjects[(i-1) % len(subjects)],
            title=f"유니트 {i}",
            adjacent_cells=get_adjacent_cells(i),
            is_locked=(i != 1)  # 1번만 열림
        )
    
    return units


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
    """인접 셀 ID 반환 (간략화 버전)"""
    # 실제로는 좌표 기반으로 계산해야 하지만, 여기서는 간략화
    adjacency_map = {
        1: [2, 3, 4, 5, 6, 7],
        2: [1, 3, 7, 8, 9, 19],
        3: [1, 2, 4, 9, 10, 11],
        4: [1, 3, 5, 11, 12, 13],
        5: [1, 4, 6, 13, 14, 15],
        6: [1, 5, 7, 15, 16, 17],
        7: [1, 2, 6, 17, 18, 19],
    }
    
    # 기본적으로 이전/이후 셀 + 같은 링의 인접 셀
    if cell_id in adjacency_map:
        return adjacency_map[cell_id]
    
    # 단순화: 이전 링의 가까운 셀들
    ring = get_ring_from_cell(cell_id)
    if ring <= 1:
        return [1]
    
    # 이전 링의 셀들 중 일부
    prev_ring_start = 1 + sum(6 * r for r in range(1, ring))
    prev_ring_end = prev_ring_start + 6 * (ring - 1) - 1
    
    adjacent = []
    if cell_id > 1:
        adjacent.append(cell_id - 1)
    
    # 이전 링에서 가장 가까운 셀 추정
    offset = (cell_id - prev_ring_end - 1) % (6 * ring)
    prev_cell = prev_ring_start + int(offset * (ring - 1) / ring)
    if 1 <= prev_cell <= 61:
        adjacent.append(prev_cell)
    
    return adjacent[:3]


# ════════════════════════════════════════════════════════════════════════════
# 학습자 프로필
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class LearnerProfile:
    """학습자 프로필"""
    name: str = ""
    
    # 성향축 (합 100)
    탐험형: int = 25
    성취형: int = 25
    경쟁형: int = 25
    창조형: int = 25
    
    # 난이도 반응
    도전_선호도: Level3 = "중간"
    실패_인내도: Level3 = "중간"
    
    # 미디어 선호
    미디어_이미지: float = 0.5
    미디어_텍스트: float = 0.5
    미디어_숫자: float = 0.5
    미디어_영상: float = 0.5
    
    # 몰입/이탈
    평균_집중시간: int = 180
    이탈_임계치: int = 3
    
    # 행동 성향
    재도전_확률: int = 50


def generate_random_profile() -> LearnerProfile:
    """랜덤 프로필 생성"""
    names = ["김민준", "이서연", "박지호", "최유나", "정현우", "강수아", "조예린", "윤시우"]
    
    # 성향축 (합 100)
    raw = [random.random() for _ in range(4)]
    total = sum(raw)
    norm = [int(r / total * 100) for r in raw]
    norm[0] += 100 - sum(norm)
    
    return LearnerProfile(
        name=random.choice(names),
        탐험형=norm[0],
        성취형=norm[1],
        경쟁형=norm[2],
        창조형=norm[3],
        도전_선호도=random.choice(["낮음", "중간", "높음"]),
        실패_인내도=random.choice(["낮음", "중간", "높음"]),
        미디어_이미지=random.uniform(0.3, 0.9),
        미디어_텍스트=random.uniform(0.3, 0.9),
        미디어_숫자=random.uniform(0.3, 0.9),
        미디어_영상=random.uniform(0.3, 0.9),
        평균_집중시간=random.randint(120, 300),
        이탈_임계치=random.randint(2, 5),
        재도전_확률=random.randint(30, 80)
    )


# ════════════════════════════════════════════════════════════════════════════
# 학습 시뮬레이션
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class LearningResult:
    """학습 결과 (생성정보)"""
    cell_id: int
    체류시간_초: int = 0
    실패횟수: int = 0
    재도전_여부: bool = False
    이탈_여부: bool = False
    보상반응: RewardType = "칭찬"
    성취도: float = 0.0
    
    def to_dict(self):
        return {
            "셀": self.cell_id,
            "체류시간": f"{self.체류시간_초}초",
            "실패": self.실패횟수,
            "재도전": "✅" if self.재도전_여부 else "❌",
            "이탈": "❌" if self.이탈_여부 else "✅",
            "보상반응": self.보상반응,
            "성취도": f"{self.성취도:.0%}"
        }


def simulate_learning(profile: LearnerProfile, unit: HexUnit) -> LearningResult:
    """학습 시뮬레이션 - 생성정보 생성"""
    result = LearningResult(cell_id=unit.cell_id)
    
    # 1. 체류시간
    base_time = profile.평균_집중시간
    diff_factor = (unit.difficulty - 6) * 10
    result.체류시간_초 = max(30, int(base_time + diff_factor + random.gauss(0, 30)))
    
    # 2. 실패횟수
    base_fail = max(0, (unit.difficulty - 4) // 2) + random.randint(0, 2)
    if profile.도전_선호도 == "높음":
        base_fail += 1
    result.실패횟수 = min(base_fail, 8)
    
    # 3. 이탈 여부
    if result.실패횟수 >= profile.이탈_임계치:
        result.이탈_여부 = random.random() < 0.5
    
    # 4. 재도전 여부
    if result.실패횟수 > 0 and not result.이탈_여부:
        result.재도전_여부 = random.random() * 100 < profile.재도전_확률
    
    # 5. 보상반응
    weights = {
        "칭찬": profile.성취형 + 10,
        "개방": profile.탐험형 + profile.창조형,
        "시각효과": profile.창조형 + profile.경쟁형
    }
    result.보상반응 = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    # 6. 성취도
    if result.이탈_여부:
        result.성취도 = random.uniform(0.1, 0.4)
    elif result.실패횟수 > 3:
        result.성취도 = random.uniform(0.4, 0.7)
    else:
        result.성취도 = random.uniform(0.7, 1.0)
    
    return result


def get_next_available_cells(units: Dict[int, HexUnit]) -> List[int]:
    """학습 가능한 다음 셀들 반환"""
    available = []
    
    for cell_id, unit in units.items():
        if unit.is_completed or unit.is_locked:
            continue
        available.append(cell_id)
    
    return available


def unlock_adjacent_cells(units: Dict[int, HexUnit], completed_cell: int):
    """완료된 셀의 인접 셀들 잠금 해제"""
    completed_unit = units[completed_cell]
    
    for adj_id in completed_unit.adjacent_cells:
        if adj_id in units and units[adj_id].is_locked:
            units[adj_id].is_locked = False


# ════════════════════════════════════════════════════════════════════════════
# 벌집 시각화
# ════════════════════════════════════════════════════════════════════════════
def create_honeycomb_figure(
    units: Dict[int, HexUnit],
    current_cell: Optional[int] = None,
    show_numbers: bool = True
) -> go.Figure:
    """벌집 맵 시각화"""
    
    fig = go.Figure()
    
    # 셀 좌표 생성
    centers = generate_hexagon_centers(num_rings=4)
    
    # 색상 정의
    colors = {
        'completed': '#2ecc71',      # 초록 - 완료
        'current': '#f39c12',        # 주황 - 현재
        'available': '#3498db',      # 파랑 - 학습가능
        'locked': '#bdc3c7',         # 회색 - 잠김
    }
    
    # 각 셀 그리기
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
        elif not unit.is_locked:
            color = colors['available']
            line_color = '#2980b9'
        else:
            color = colors['locked']
            line_color = '#95a5a6'
        
        # 육각형 그리기
        xs, ys = get_hexagon_vertices(cx, cy, size=0.95)
        
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            fill='toself',
            fillcolor=color,
            line=dict(color=line_color, width=2),
            mode='lines',
            hoverinfo='text',
            hovertext=f"셀 {cell_num}<br>{unit.unit_type} | 난이도 {unit.difficulty}<br>{unit.subject}",
            showlegend=False
        ))
        
        # 셀 번호 표시
        if show_numbers:
            fig.add_annotation(
                x=cx, y=cy,
                text=str(cell_num),
                showarrow=False,
                font=dict(size=14, color='white' if unit.is_completed or cell_num == current_cell else 'black'),
            )
    
    # 레이아웃
    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor='y'),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=20, b=20),
        height=600,
        width=700,
    )
    
    return fig


def create_legend() -> str:
    """범례 HTML"""
    return """
    <div style="display: flex; gap: 20px; justify-content: center; margin: 10px 0;">
        <span>🟢 완료</span>
        <span>🟠 현재</span>
        <span>🔵 학습가능</span>
        <span>⚪ 잠김</span>
    </div>
    """


# ════════════════════════════════════════════════════════════════════════════
# 성향 레이더 차트
# ════════════════════════════════════════════════════════════════════════════
def create_profile_radar(profile: LearnerProfile) -> go.Figure:
    """성향축 레이더"""
    categories = ['탐험형', '성취형', '경쟁형', '창조형']
    values = [profile.탐험형, profile.성취형, profile.경쟁형, profile.창조형]
    
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
        height=250,
        margin=dict(l=50, r=50, t=30, b=30)
    )
    return fig


# ════════════════════════════════════════════════════════════════════════════
# Streamlit 앱
# ════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="🐝 벌집 학습 시스템",
        page_icon="🐝",
        layout="wide"
    )
    
    st.title("🐝 벌집 구조 학습 시스템")
    st.caption("중앙에서 시작하여 나선형으로 학습을 확장해 나갑니다")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 세션 상태 초기화
    # ─────────────────────────────────────────────────────────────────────────
    if "units" not in st.session_state:
        st.session_state.units = generate_hex_units(61)
    
    if "profile" not in st.session_state:
        st.session_state.profile = None
    
    if "current_cell" not in st.session_state:
        st.session_state.current_cell = None
    
    if "learning_history" not in st.session_state:
        st.session_state.learning_history = []
    
    if "total_completed" not in st.session_state:
        st.session_state.total_completed = 0
    
    # ─────────────────────────────────────────────────────────────────────────
    # 사이드바
    # ─────────────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("🎮 컨트롤")
        
        # 학습자 생성 버튼
        if st.button("🎲 학습자 생성", use_container_width=True, type="primary"):
            st.session_state.profile = generate_random_profile()
            st.session_state.units = generate_hex_units(61)
            st.session_state.current_cell = 1
            st.session_state.learning_history = []
            st.session_state.total_completed = 0
            st.rerun()
        
        # 학습 시뮬레이션 버튼
        if st.session_state.profile:
            st.divider()
            
            available = get_next_available_cells(st.session_state.units)
            
            if available:
                if st.button("📚 학습 시뮬레이션", use_container_width=True):
                    # 현재 셀에서 학습
                    current = st.session_state.current_cell or available[0]
                    unit = st.session_state.units[current]
                    
                    # 학습 시뮬레이션
                    result = simulate_learning(st.session_state.profile, unit)
                    
                    # 결과 저장
                    st.session_state.learning_history.append(result)
                    
                    # 이탈하지 않으면 완료 처리
                    if not result.이탈_여부:
                        unit.is_completed = True
                        unit.score = result.성취도
                        st.session_state.total_completed += 1
                        
                        # 인접 셀 잠금 해제
                        unlock_adjacent_cells(st.session_state.units, current)
                    
                    # 다음 셀 선택
                    next_available = get_next_available_cells(st.session_state.units)
                    if next_available:
                        # 가장 낮은 번호 선택 (또는 추천 알고리즘 적용 가능)
                        st.session_state.current_cell = min(next_available)
                    else:
                        st.session_state.current_cell = None
                    
                    st.rerun()
            else:
                st.success("🎉 모든 유니트 완료!")
        
        # 초기화
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.units = generate_hex_units(61)
            st.session_state.profile = None
            st.session_state.current_cell = None
            st.session_state.learning_history = []
            st.session_state.total_completed = 0
            st.rerun()
        
        st.divider()
        
        # 진행 상황
        st.header("📊 진행 상황")
        completed = st.session_state.total_completed
        st.metric("완료", f"{completed}/61")
        st.progress(completed / 61)
        
        if st.session_state.current_cell:
            st.metric("현재 셀", f"#{st.session_state.current_cell}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 메인 영역
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.profile is None:
        st.info("👈 사이드바에서 '학습자 생성' 버튼을 클릭하세요!")
        
        # 빈 벌집 맵 표시
        st.markdown(create_legend(), unsafe_allow_html=True)
        fig = create_honeycomb_figure(st.session_state.units)
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        profile = st.session_state.profile
        
        # 2열 레이아웃
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 벌집 맵
            st.subheader("🗺️ 학습 맵")
            st.markdown(create_legend(), unsafe_allow_html=True)
            
            fig = create_honeycomb_figure(
                st.session_state.units,
                current_cell=st.session_state.current_cell
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 학습자 정보
            st.subheader(f"👤 {profile.name}")
            
            st.plotly_chart(create_profile_radar(profile), use_container_width=True)
            
            col_a, col_b = st.columns(2)
            col_a.metric("도전 선호", profile.도전_선호도)
            col_b.metric("실패 인내", profile.실패_인내도)
            
            st.divider()
            
            # 최근 학습 결과
            st.subheader("📋 최근 학습 결과")
            
            if st.session_state.learning_history:
                last_result = st.session_state.learning_history[-1]
                
                result_cols = st.columns(3)
                result_cols[0].metric("체류시간", f"{last_result.체류시간_초}초")
                result_cols[1].metric("실패", f"{last_result.실패횟수}회")
                result_cols[2].metric("성취도", f"{last_result.성취도:.0%}")
                
                st.write(f"**보상반응:** {last_result.보상반응}")
                st.write(f"**이탈:** {'❌ 이탈' if last_result.이탈_여부 else '✅ 완료'}")
                st.write(f"**재도전:** {'✅' if last_result.재도전_여부 else '❌'}")
            else:
                st.info("아직 학습 기록이 없습니다")
        
        # 학습 히스토리 테이블
        if st.session_state.learning_history:
            st.divider()
            st.subheader("📜 학습 히스토리")
            
            history_data = [r.to_dict() for r in st.session_state.learning_history]
            st.dataframe(history_data, use_container_width=True)


if __name__ == "__main__":
    main()
