"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
벌집 구조 학습 시스템 - Streamlit UI 버전
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

실행 방법:
  pip install streamlit plotly
  streamlit run honeycomb_app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json

# 메인 시스템 임포트
from honeycomb_learning_system import (
    LearningSimulator, 
    generate_learner_profile, 
    generate_all_units,
    LearnerProfile,
    UnitFixedInfo,
    LearningLog,
    UnitMatchScore
)


# ════════════════════════════════════════════════════════════════════════════
# 시각화 함수
# ════════════════════════════════════════════════════════════════════════════
def create_personality_radar(profile: LearnerProfile) -> go.Figure:
    """성향축 레이더 차트"""
    p = profile.personality
    categories = ['탐험형', '성취형', '경쟁형', '창조형']
    values = [p.탐험형, p.성취형, p.경쟁형, p.창조형]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(99, 110, 250, 0.3)',
        line=dict(color='rgb(99, 110, 250)', width=2),
        name='성향'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 60])),
        showlegend=False,
        height=300,
        margin=dict(l=60, r=60, t=30, b=30)
    )
    return fig


def create_media_bar(profile: LearnerProfile) -> go.Figure:
    """미디어 선호 막대 그래프"""
    categories = ['이미지', '텍스트', '숫자', '영상']
    values = [profile.미디어_이미지, profile.미디어_텍스트, 
              profile.미디어_숫자, profile.미디어_영상]
    
    fig = go.Figure(data=go.Bar(
        x=categories,
        y=values,
        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    ))
    
    fig.update_layout(
        yaxis=dict(range=[0, 1], title='선호도'),
        height=250,
        margin=dict(l=40, r=20, t=20, b=40)
    )
    return fig


def create_score_radar(score: UnitMatchScore) -> go.Figure:
    """5가지 적합성 점수 레이더"""
    categories = ['난이도', '학습타입', '미디어', '선행조건', '성향']
    values = [score.난이도_적합성, score.학습타입_적합성, 
              score.미디어_궁합, score.선행조건_충족도, score.성향_방향성]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(46, 204, 113, 0.3)',
        line=dict(color='rgb(46, 204, 113)', width=2)
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        height=250,
        margin=dict(l=50, r=50, t=20, b=20)
    )
    return fig


def create_learning_history_chart(history: list) -> go.Figure:
    """학습 히스토리 차트"""
    if not history:
        return None
    
    x = list(range(1, len(history) + 1))
    stay_times = [h['체류시간_초'] for h in history]
    failures = [h['실패횟수'] for h in history]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=stay_times, name='체류시간(초)', 
                             line=dict(color='#3498db', width=2)))
    fig.add_trace(go.Bar(x=x, y=failures, name='실패횟수',
                         marker_color='#e74c3c', opacity=0.6))
    
    fig.update_layout(
        xaxis_title='학습 회차',
        height=250,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation='h', y=-0.2)
    )
    return fig


# ════════════════════════════════════════════════════════════════════════════
# Streamlit 앱
# ════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="벌집 구조 학습 시스템",
        page_icon="🐝",
        layout="wide"
    )
    
    st.title("🐝 벌집 구조 학습 시스템")
    st.caption("가상 학습자 생성 → 유니트 학습 시뮬레이션 → 다음 유니트 추천")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 세션 상태 초기화
    # ─────────────────────────────────────────────────────────────────────────
    if "simulator" not in st.session_state:
        st.session_state.simulator = LearningSimulator()
        units = generate_all_units()
        st.session_state.simulator.load_units(units)
        st.session_state.units = units
    
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "last_log" not in st.session_state:
        st.session_state.last_log = None
    if "learning_history" not in st.session_state:
        st.session_state.learning_history = []
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []
    
    # ─────────────────────────────────────────────────────────────────────────
    # 사이드바: 시스템 정보
    # ─────────────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("📊 시스템 정보")
        st.metric("총 유니트 수", f"{len(st.session_state.units)}개")
        st.metric("과목 수", "7개 (A~G)")
        st.metric("단원/과목", "3개")
        
        st.divider()
        
        if st.session_state.profile:
            st.header("👤 현재 학습자")
            p = st.session_state.profile
            st.write(f"**{p.name}** (v{p.state_version})")
            st.write(f"완료: {len(p.completed_units)}개")
        
        st.divider()
        st.caption("벌집 구조 학습 시스템 v1.0")
        st.caption("© 2024 유상현 교수님 연구")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 메인 영역: 버튼
    # ─────────────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎲 학습자 프로필 생성", use_container_width=True, type="primary"):
            st.session_state.profile = generate_learner_profile()
            st.session_state.last_log = None
            st.session_state.learning_history = []
            st.session_state.recommendations = []
            st.rerun()
    
    with col2:
        disabled = st.session_state.profile is None
        if st.button("📚 유니트 학습 시뮬레이션", use_container_width=True, disabled=disabled):
            sim = st.session_state.simulator
            profile = st.session_state.profile
            
            # 추천 유니트 가져오기
            recs = sim.recommend_next_units(profile, st.session_state.last_log, top_n=5)
            
            if recs:
                selected_unit, selected_score = recs[0]
                
                # 학습 시뮬레이션
                log = sim.simulate_learning(profile, selected_unit)
                
                # 프로필 업데이트
                st.session_state.profile = sim.update_profile(profile, log, selected_unit)
                st.session_state.last_log = log
                st.session_state.learning_history.append(log.to_dict())
                st.session_state.recommendations = recs
                
                st.rerun()
    
    with col3:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.profile = None
            st.session_state.last_log = None
            st.session_state.learning_history = []
            st.session_state.recommendations = []
            st.rerun()
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────────────────
    # 결과 표시
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.profile is None:
        st.info("👆 '학습자 프로필 생성' 버튼을 클릭하여 시작하세요.")
    else:
        profile = st.session_state.profile
        
        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs([
            "👤 학습자 프로필", 
            "📊 학습 결과", 
            "🎯 다음 유니트 추천",
            "📋 전체 데이터"
        ])
        
        # ─────────────────────────────────────────────────────────────────────
        # 탭 1: 학습자 프로필
        # ─────────────────────────────────────────────────────────────────────
        with tab1:
            st.header(f"👤 {profile.name}")
            st.caption(f"ID: {profile.learner_id} | 상태벡터: v{profile.state_version} | 완료: {len(profile.completed_units)}개")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 성향축 (합계 100)")
                st.plotly_chart(create_personality_radar(profile), use_container_width=True)
                
                # 성향 수치
                p = profile.personality
                cols = st.columns(4)
                cols[0].metric("탐험형", f"{p.탐험형}%")
                cols[1].metric("성취형", f"{p.성취형}%")
                cols[2].metric("경쟁형", f"{p.경쟁형}%")
                cols[3].metric("창조형", f"{p.창조형}%")
            
            with col2:
                st.subheader("📺 미디어 선호도")
                st.plotly_chart(create_media_bar(profile), use_container_width=True)
            
            st.divider()
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.subheader("⚡ 난이도 반응")
                st.write(f"**도전 선호도:** {profile.도전_선호도}")
                st.write(f"**실패 인내도:** {profile.실패_인내도}")
            
            with col4:
                st.subheader("🎮 몰입·이탈 특성")
                st.write(f"**평균 집중 시간:** {profile.평균_집중_지속시간_초}초")
                st.write(f"**지루함 임계치:** {profile.지루함_임계치_초}초")
                st.write(f"**이탈 임계치:** {profile.이탈_임계치_실패횟수}회 실패")
            
            with col5:
                st.subheader("🔄 행동 성향")
                st.write(f"**재도전 확률:** {profile.재도전_확률}%")
                st.write(f"**확장 선택 확률:** {profile.확장_선택_확률}%")
                st.write(f"**휴식 수용도:** {profile.휴식_수용도}")
        
        # ─────────────────────────────────────────────────────────────────────
        # 탭 2: 학습 결과
        # ─────────────────────────────────────────────────────────────────────
        with tab2:
            if st.session_state.last_log:
                log = st.session_state.last_log
                
                st.header("📊 최근 학습 결과")
                st.caption(f"유니트: {log.unit_id}")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("체류시간", f"{log.체류시간_초}초")
                col2.metric("실패횟수", f"{log.실패횟수}회")
                col3.metric("이탈", "❌" if log.이탈_여부 else "✅")
                col4.metric("재도전", "✅" if log.재도전_여부 else "❌")
                
                st.divider()
                
                col5, col6 = st.columns(2)
                
                with col5:
                    st.subheader("🎁 보상반응")
                    st.info(f"**{log.보상반응}**에 반응")
                
                with col6:
                    st.subheader("📺 미디어 반응 점수")
                    for k, v in log.선호미디어_반응점수.items():
                        st.progress(v, text=f"{k}: {v:.2f}")
                
                st.divider()
                
                # 학습 히스토리 차트
                if len(st.session_state.learning_history) > 1:
                    st.subheader("📈 학습 히스토리")
                    fig = create_learning_history_chart(st.session_state.learning_history)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("아직 학습 기록이 없습니다. '유니트 학습 시뮬레이션' 버튼을 클릭하세요.")
        
        # ─────────────────────────────────────────────────────────────────────
        # 탭 3: 다음 유니트 추천
        # ─────────────────────────────────────────────────────────────────────
        with tab3:
            st.header("🎯 다음 유니트 추천")
            
            # 현재 추천 계산
            sim = st.session_state.simulator
            recs = sim.recommend_next_units(profile, st.session_state.last_log, top_n=5)
            
            if recs:
                for i, (unit, score) in enumerate(recs):
                    with st.expander(f"**{i+1}위: {unit.unit_id}** ({unit.unit_type}, 난이도 {unit.difficulty}) - 점수: {score.total_score:.3f}", expanded=(i==0)):
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.write("**유니트 정보**")
                            st.write(f"- 과목: {unit.subject}")
                            st.write(f"- 단원: {unit.chapter}")
                            st.write(f"- 추천 미디어: {unit.recommended_media}")
                            st.write(f"- 예상 시간: {unit.estimated_time_sec}초")
                            st.write(f"- 실패 허용: {unit.fail_allow}회")
                        
                        with col2:
                            st.write("**5가지 적합성 점수**")
                            st.plotly_chart(create_score_radar(score), use_container_width=True)
            else:
                st.warning("추천 가능한 유니트가 없습니다.")
        
        # ─────────────────────────────────────────────────────────────────────
        # 탭 4: 전체 데이터
        # ─────────────────────────────────────────────────────────────────────
        with tab4:
            st.header("📋 전체 데이터 (JSON)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("학습자 프로필")
                st.json(profile.to_dict())
            
            with col2:
                st.subheader("최근 생성정보")
                if st.session_state.last_log:
                    st.json(st.session_state.last_log.to_dict())
                else:
                    st.info("학습 기록 없음")


if __name__ == "__main__":
    main()
