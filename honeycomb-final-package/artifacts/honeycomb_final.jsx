import React, { useState, useCallback, useMemo } from 'react';

// ════════════════════════════════════════════════════════════════════════════
// 벌집 좌표 계산
// ════════════════════════════════════════════════════════════════════════════
const generateHexagonCenters = (numRings = 4) => {
  const centers = [];
  let cellNum = 1;
  const size = 28;
  const h = size * Math.sqrt(3);
  
  centers.push({ x: 240, y: 240, num: cellNum++ });
  
  for (let ring = 1; ring <= numRings; ring++) {
    const directions = [
      { dx: 1.5 * size, dy: -h / 2 },
      { dx: 0, dy: -h },
      { dx: -1.5 * size, dy: -h / 2 },
      { dx: -1.5 * size, dy: h / 2 },
      { dx: 0, dy: h },
      { dx: 1.5 * size, dy: h / 2 },
    ];
    
    let x = 240;
    let y = 240 + ring * h;
    
    for (let dirIdx = 0; dirIdx < 6; dirIdx++) {
      for (let step = 0; step < ring; step++) {
        centers.push({ x, y, num: cellNum++ });
        x += directions[dirIdx].dx;
        y += directions[dirIdx].dy;
      }
    }
  }
  
  return centers.filter(c => c.num <= 61);
};

const hexPath = (cx, cy, size = 26) => {
  const points = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 6) + (i * Math.PI / 3);
    points.push(`${cx + size * Math.cos(angle)},${cy + size * Math.sin(angle)}`);
  }
  return `M ${points.join(' L ')} Z`;
};

const getRing = (cellId) => {
  if (cellId === 1) return 0;
  let total = 1, ring = 1;
  while (total < cellId) {
    total += 6 * ring;
    if (cellId <= total) return ring;
    ring++;
  }
  return ring;
};

const getAdjacent = (num) => {
  if (num === 1) return [2, 3, 4, 5, 6, 7];
  const ring = getRing(num);
  const ringStart = 2 + Array.from({length: ring - 1}, (_, i) => 6 * (i + 1)).reduce((a, b) => a + b, 0);
  const ringEnd = ringStart + 6 * ring - 1;
  
  const adj = [num > ringStart ? num - 1 : ringEnd, num < ringEnd ? num + 1 : ringStart];
  
  if (ring > 1) {
    const prevStart = 2 + Array.from({length: ring - 2}, (_, i) => 6 * (i + 1)).reduce((a, b) => a + b, 0);
    const offset = num - ringStart;
    const prevCell = prevStart + Math.floor(offset * (ring - 1) / ring);
    if (prevCell > 0 && prevCell <= 61) adj.push(prevCell);
  } else {
    adj.push(1);
  }
  
  if (ring < 4) {
    const nextStart = 2 + Array.from({length: ring}, (_, i) => 6 * (i + 1)).reduce((a, b) => a + b, 0);
    const offset = num - ringStart;
    const nextCell = nextStart + Math.floor(offset * (ring + 1) / ring);
    if (nextCell <= 61) {
      adj.push(nextCell);
      if (nextCell + 1 <= 61) adj.push(nextCell + 1);
    }
  }
  
  return [...new Set(adj.filter(a => a > 0 && a <= 61 && a !== num))];
};

// ════════════════════════════════════════════════════════════════════════════
// 데이터 생성
// ════════════════════════════════════════════════════════════════════════════
const SUBJECTS = ['수학', '과학', '언어', '사회', '예술', '체육', '코딩'];
const UNIT_TYPES = ['개념', '보조', '실전', '탐색'];
const MEDIA_TYPES = ['이미지', '텍스트', '숫자', '영상', '혼합'];
const NAMES = ['김민준', '이서연', '박지호', '최유나', '정현우', '강수아', '조예린', '윤시우'];

const generateUnits = () => {
  const units = {};
  for (let i = 1; i <= 61; i++) {
    const ring = getRing(i);
    const difficulty = Math.min(12, ring * 3 + Math.floor(Math.random() * 3)) || 1;
    const utype = ring === 0 ? '개념' : ring === 1 ? ['개념', '보조'][Math.floor(Math.random() * 2)] 
                : ring === 2 ? ['보조', '실전'][Math.floor(Math.random() * 2)] : ['실전', '탐색'][Math.floor(Math.random() * 2)];
    
    units[i] = {
      cellId: i,
      unitType: utype,
      difficulty,
      subject: SUBJECTS[(i - 1) % 7],
      media: MEDIA_TYPES[Math.floor(Math.random() * 5)],
      failAllow: Math.max(1, 5 - Math.floor(difficulty / 3)),
      adjacent: getAdjacent(i),
      isCompleted: false,
      isLocked: i !== 1,
      score: 0,
    };
  }
  return units;
};

const generateProfile = () => {
  const raw = [Math.random(), Math.random(), Math.random(), Math.random()];
  const total = raw.reduce((a, b) => a + b, 0);
  const norm = raw.map(r => Math.round(r / total * 100));
  norm[0] += 100 - norm.reduce((a, b) => a + b, 0);
  
  return {
    name: NAMES[Math.floor(Math.random() * NAMES.length)],
    탐험형: norm[0], 성취형: norm[1], 경쟁형: norm[2], 창조형: norm[3],
    도전선호: ['낮음', '중간', '높음'][Math.floor(Math.random() * 3)],
    실패인내: ['낮음', '중간', '높음'][Math.floor(Math.random() * 3)],
    이탈임계: Math.floor(Math.random() * 3) + 2,
    미디어: { 이미지: Math.random() * 0.6 + 0.2, 텍스트: Math.random() * 0.6 + 0.2, 숫자: Math.random() * 0.6 + 0.2, 영상: Math.random() * 0.6 + 0.2 },
    집중시간: Math.floor(Math.random() * 120) + 120,
    재도전확률: Math.floor(Math.random() * 50) + 30,
    version: 0,
    completed: [],
  };
};

// ════════════════════════════════════════════════════════════════════════════
// 5가지 적합성 점수 계산
// ════════════════════════════════════════════════════════════════════════════
const calculateMatchScores = (profile, units, lastLog) => {
  const available = Object.values(units).filter(u => !u.isCompleted && !u.isLocked);
  
  return available.map(unit => {
    // 1. 난이도 적합성
    let idealDiff = 6;
    if (lastLog) {
      if (lastLog.실패횟수 > 2) idealDiff -= 1;
      if (!lastLog.이탈 && lastLog.실패횟수 <= 1) idealDiff += 1;
    }
    if (profile.도전선호 === '높음') idealDiff += 2;
    if (profile.도전선호 === '낮음') idealDiff -= 1;
    const 난이도적합 = Math.max(0, 1 - Math.abs(unit.difficulty - idealDiff) * 0.12);
    
    // 2. 학습타입 적합성
    let typeScore = 0.5;
    if (lastLog?.이탈 && (unit.unitType === '보조' || unit.unitType === '탐색')) typeScore += 0.25;
    if (lastLog?.재도전 && unit.unitType === '실전') typeScore += 0.2;
    typeScore += (unit.unitType === '탐색' ? profile.탐험형 : unit.unitType === '실전' ? profile.성취형 : profile.창조형) * 0.003;
    const 학습타입적합 = Math.min(1, typeScore);
    
    // 3. 미디어 궁합
    const 미디어궁합 = profile.미디어[unit.media] || 0.5;
    
    // 4. 선행조건 충족도
    const prereqs = unit.adjacent.filter(a => a < unit.cellId);
    const met = prereqs.filter(p => profile.completed.includes(p)).length;
    const 선행조건 = prereqs.length ? 0.6 + (met / prereqs.length) * 0.4 : 0.8;
    
    // 5. 성향 방향성
    let 성향 = 0.5;
    if (unit.unitType === '탐색') 성향 += profile.탐험형 * 0.004;
    if (unit.unitType === '실전') 성향 += (profile.성취형 + profile.경쟁형) * 0.003;
    if (unit.unitType === '개념') 성향 += profile.창조형 * 0.003;
    성향 = Math.min(1, 성향);
    
    // 총점 (가중치: 난이도 25%, 학습타입 20%, 미디어 15%, 선행조건 25%, 성향 15%)
    const total = 난이도적합 * 0.25 + 학습타입적합 * 0.20 + 미디어궁합 * 0.15 + 선행조건 * 0.25 + 성향 * 0.15;
    
    return { cellId: unit.cellId, total, 난이도적합, 학습타입적합, 미디어궁합, 선행조건, 성향, unit };
  }).sort((a, b) => b.total - a.total);
};

// ════════════════════════════════════════════════════════════════════════════
// 학습 시뮬레이션 (생성정보 6개 필드)
// ════════════════════════════════════════════════════════════════════════════
const simulateLearning = (profile, unit) => {
  // 1. 체류시간
  const baseTime = profile.집중시간;
  const diffFactor = (unit.difficulty - 6) * 8;
  const 체류시간 = Math.max(30, Math.floor(baseTime + diffFactor + (Math.random() - 0.5) * 50));
  
  // 2. 실패횟수
  let baseFail = Math.max(0, Math.floor((unit.difficulty - 5) / 2)) + Math.floor(Math.random() * 3);
  if (profile.도전선호 === '높음') baseFail += 1;
  if (profile.실패인내 === '높음') baseFail = Math.max(0, baseFail - 1);
  const 실패횟수 = Math.min(baseFail, 8);
  
  // 3. 이탈 여부
  const 이탈 = 실패횟수 >= profile.이탈임계 && Math.random() < 0.5;
  
  // 4. 재도전 여부
  const 재도전 = !이탈 && 실패횟수 > 0 && Math.random() * 100 < profile.재도전확률;
  
  // 5. 보상반응
  const weights = { 칭찬: profile.성취형 + 10, 개방: profile.탐험형 + profile.창조형, 시각효과: profile.창조형 + profile.경쟁형 };
  const totalW = Object.values(weights).reduce((a, b) => a + b, 0);
  let r = Math.random() * totalW, cum = 0, 보상반응 = '칭찬';
  for (const [k, w] of Object.entries(weights)) { cum += w; if (r <= cum) { 보상반응 = k; break; } }
  
  // 6. 미디어 반응점수
  const 미디어반응 = {};
  ['이미지', '텍스트', '숫자', '영상'].forEach(m => {
    미디어반응[m] = Math.max(0, Math.min(1, profile.미디어[m] + (Math.random() - 0.5) * 0.3));
  });
  if (미디어반응[unit.media]) 미디어반응[unit.media] = Math.min(1, 미디어반응[unit.media] + 0.2);
  
  // 성취도
  const 성취도 = 이탈 ? Math.random() * 0.4 : 실패횟수 > unit.failAllow ? 0.4 + Math.random() * 0.3 : 0.7 + Math.random() * 0.3;
  
  return { cellId: unit.cellId, 체류시간, 실패횟수, 재도전, 이탈, 보상반응, 미디어반응, 성취도: Math.round(성취도 * 100) };
};

// ════════════════════════════════════════════════════════════════════════════
// 컴포넌트
// ════════════════════════════════════════════════════════════════════════════
const Hexagon = ({ x, y, num, status, onClick, isSelected }) => {
  const colors = {
    completed: { fill: '#2ecc71', stroke: '#27ae60', text: 'white' },
    current: { fill: '#f39c12', stroke: '#e67e22', text: 'white' },
    recommended: { fill: '#9b59b6', stroke: '#8e44ad', text: 'white' },
    available: { fill: '#3498db', stroke: '#2980b9', text: 'white' },
    locked: { fill: '#ecf0f1', stroke: '#bdc3c7', text: '#7f8c8d' },
  };
  const c = colors[status] || colors.locked;
  
  return (
    <g onClick={() => onClick(num)} style={{ cursor: status !== 'locked' ? 'pointer' : 'default' }}>
      <path d={hexPath(x, y)} fill={c.fill} stroke={isSelected ? '#e74c3c' : c.stroke} strokeWidth={isSelected ? 3 : 1.5} />
      <text x={x} y={y + 3} textAnchor="middle" fill={c.text} fontSize="10" fontWeight="bold">{num}</text>
    </g>
  );
};

const ScoreBar = ({ label, value, color }) => (
  <div className="flex items-center gap-2 text-xs">
    <span className="w-16">{label}</span>
    <div className="flex-1 bg-gray-200 rounded h-2">
      <div className="h-2 rounded" style={{ width: `${value * 100}%`, backgroundColor: color }}></div>
    </div>
    <span className="w-8 text-right">{(value * 100).toFixed(0)}%</span>
  </div>
);

// ════════════════════════════════════════════════════════════════════════════
// 메인 앱
// ════════════════════════════════════════════════════════════════════════════
export default function HoneycombApp() {
  const [units, setUnits] = useState(() => generateUnits());
  const [profile, setProfile] = useState(null);
  const [currentCell, setCurrentCell] = useState(null);
  const [history, setHistory] = useState([]);
  const [lastLog, setLastLog] = useState(null);
  const [scores, setScores] = useState([]);
  
  const centers = useMemo(() => generateHexagonCenters(4), []);
  const completed = Object.values(units).filter(u => u.isCompleted).length;
  const recommended = scores.slice(0, 3).map(s => s.cellId);

  const handleCreate = useCallback(() => {
    const newUnits = generateUnits();
    setUnits(newUnits);
    setProfile(generateProfile());
    setCurrentCell(1);
    setHistory([]);
    setLastLog(null);
    setScores([]);
  }, []);

  const handleLearn = useCallback(() => {
    if (!currentCell || !profile || !units[currentCell]) return;
    
    const unit = units[currentCell];
    const log = simulateLearning(profile, unit);
    
    setLastLog(log);
    setHistory(prev => [...prev, log]);
    
    // 프로필 업데이트
    const newProfile = { ...profile, version: profile.version + 1 };
    if (!log.이탈) {
      newProfile.completed = [...newProfile.completed, log.cellId];
      if (log.성취도 > 70) {
        if (newProfile.도전선호 === '낮음' && Math.random() < 0.2) newProfile.도전선호 = '중간';
      }
    } else {
      if (newProfile.도전선호 === '높음') newProfile.도전선호 = '중간';
    }
    setProfile(newProfile);
    
    // 유니트 업데이트
    setUnits(prev => {
      const newUnits = { ...prev };
      if (!log.이탈) {
        newUnits[currentCell] = { ...newUnits[currentCell], isCompleted: true, score: log.성취도 };
        unit.adjacent.forEach(adj => {
          if (newUnits[adj]?.isLocked) newUnits[adj] = { ...newUnits[adj], isLocked: false };
        });
      }
      
      // 5가지 적합성 점수 계산 및 다음 셀 추천
      const newScores = calculateMatchScores(newProfile, newUnits, log);
      setScores(newScores);
      
      if (newScores.length > 0 && !log.이탈) {
        setCurrentCell(newScores[0].cellId);
      }
      
      return newUnits;
    });
  }, [currentCell, profile, units]);

  const handleCellClick = useCallback((num) => {
    if (units[num] && !units[num].isLocked && !units[num].isCompleted) {
      setCurrentCell(num);
    }
  }, [units]);

  return (
    <div className="p-2 bg-gray-50 min-h-screen text-sm">
      <h1 className="text-lg font-bold text-center mb-2">🐝 벌집 구조 학습 시스템</h1>
      <p className="text-xs text-center text-gray-500 mb-2">5가지 적합성 점수 기반 추천 + 생성정보 6개 필드</p>
      
      <div className="flex justify-center gap-2 mb-2">
        <button onClick={handleCreate} className="px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600">
          🎲 학습자 생성
        </button>
        {profile && (
          <button onClick={handleLearn} disabled={!currentCell} className="px-3 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600 disabled:bg-gray-300">
            📚 학습 시뮬레이션
          </button>
        )}
      </div>

      <div className="flex justify-center gap-3 mb-2 text-xs">
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-500 rounded-full"></span>완료</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-yellow-500 rounded-full"></span>현재</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-purple-500 rounded-full"></span>추천</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-blue-500 rounded-full"></span>가능</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-gray-300 rounded-full"></span>잠김</span>
      </div>

      <div className="flex gap-2 justify-center flex-wrap">
        {/* 벌집 맵 */}
        <div className="bg-white rounded shadow p-1">
          <svg width="480" height="480" viewBox="0 0 480 480">
            {centers.map(({ x, y, num }) => (
              <Hexagon
                key={num}
                x={x} y={y} num={num}
                status={units[num]?.isCompleted ? 'completed' : num === currentCell ? 'current' : recommended.includes(num) ? 'recommended' : !units[num]?.isLocked ? 'available' : 'locked'}
                onClick={handleCellClick}
                isSelected={num === currentCell}
              />
            ))}
          </svg>
        </div>

        {/* 정보 패널 */}
        <div className="w-56 space-y-2">
          {/* 진행 */}
          <div className="bg-white rounded shadow p-2">
            <div className="font-bold text-xs mb-1">📊 진행: {completed}/61</div>
            <div className="w-full bg-gray-200 rounded h-2">
              <div className="bg-green-500 h-2 rounded transition-all" style={{ width: `${(completed / 61) * 100}%` }}></div>
            </div>
            {currentCell && <div className="text-xs text-gray-500 mt-1">현재: #{currentCell}</div>}
          </div>

          {/* 프로필 */}
          {profile && (
            <div className="bg-white rounded shadow p-2">
              <div className="font-bold text-xs mb-1">👤 {profile.name} (v{profile.version})</div>
              <div className="grid grid-cols-2 gap-1 text-xs">
                <div>탐험 {profile.탐험형}%</div>
                <div>성취 {profile.성취형}%</div>
                <div>경쟁 {profile.경쟁형}%</div>
                <div>창조 {profile.창조형}%</div>
              </div>
              <div className="border-t mt-1 pt-1 text-xs">
                <div>도전선호: {profile.도전선호}</div>
                <div>이탈임계: {profile.이탈임계}회</div>
              </div>
            </div>
          )}

          {/* 생성정보 6개 필드 */}
          {lastLog && (
            <div className="bg-white rounded shadow p-2">
              <div className="font-bold text-xs mb-1">📋 생성정보 (#{lastLog.cellId})</div>
              <div className="grid grid-cols-2 gap-1 text-xs">
                <div>체류시간: {lastLog.체류시간}초</div>
                <div>실패: {lastLog.실패횟수}회</div>
                <div>재도전: {lastLog.재도전 ? '✅' : '❌'}</div>
                <div>이탈: {lastLog.이탈 ? '❌' : '✅'}</div>
                <div>보상: {lastLog.보상반응}</div>
                <div>성취: {lastLog.성취도}%</div>
              </div>
            </div>
          )}

          {/* 5가지 적합성 점수 */}
          {scores.length > 0 && (
            <div className="bg-white rounded shadow p-2">
              <div className="font-bold text-xs mb-1">🎯 추천 Top3 (5가지 적합성)</div>
              {scores.slice(0, 3).map((s, i) => (
                <div key={s.cellId} className="mb-2 p-1 bg-gray-50 rounded">
                  <div className="font-semibold text-xs mb-1">
                    {i + 1}위: #{s.cellId} ({s.unit.unitType}) - {(s.total * 100).toFixed(0)}점
                  </div>
                  <ScoreBar label="난이도" value={s.난이도적합} color="#e74c3c" />
                  <ScoreBar label="학습타입" value={s.학습타입적합} color="#f39c12" />
                  <ScoreBar label="미디어" value={s.미디어궁합} color="#9b59b6" />
                  <ScoreBar label="선행조건" value={s.선행조건} color="#3498db" />
                  <ScoreBar label="성향" value={s.성향} color="#2ecc71" />
                </div>
              ))}
            </div>
          )}

          {/* 히스토리 */}
          {history.length > 0 && (
            <div className="bg-white rounded shadow p-2 max-h-32 overflow-y-auto">
              <div className="font-bold text-xs mb-1">📜 히스토리 ({history.length}회)</div>
              {history.slice(-5).reverse().map((h, i) => (
                <div key={i} className={`text-xs flex justify-between ${h.이탈 ? 'text-red-500' : 'text-green-600'}`}>
                  <span>#{h.cellId}</span>
                  <span>{h.성취도}%</span>
                  <span>{h.이탈 ? '이탈' : '완료'}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {!profile && <div className="text-center mt-3 text-gray-500 text-xs">👆 '학습자 생성' 버튼을 클릭하세요!</div>}
    </div>
  );
}
