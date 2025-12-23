import React, { useState, useCallback } from 'react';

// 벌집 좌표 생성
const generateHexagonCenters = (numRings = 4) => {
  const centers = [];
  let cellNum = 1;
  const size = 40;
  const h = size * Math.sqrt(3);
  
  // 중앙
  centers.push({ x: 350, y: 350, num: cellNum++ });
  
  // 각 링
  for (let ring = 1; ring <= numRings; ring++) {
    const directions = [
      { dx: 1.5 * size, dy: -h / 2 },
      { dx: 0, dy: -h },
      { dx: -1.5 * size, dy: -h / 2 },
      { dx: -1.5 * size, dy: h / 2 },
      { dx: 0, dy: h },
      { dx: 1.5 * size, dy: h / 2 },
    ];
    
    let x = 350;
    let y = 350 + ring * h;
    
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

// 육각형 SVG 패스
const hexPath = (cx, cy, size = 38) => {
  const points = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 6) + (i * Math.PI / 3);
    points.push(`${cx + size * Math.cos(angle)},${cy + size * Math.sin(angle)}`);
  }
  return `M ${points.join(' L ')} Z`;
};

// 단일 육각형 컴포넌트
const Hexagon = ({ x, y, num, status, onClick, isSelected }) => {
  const colors = {
    completed: { fill: '#2ecc71', stroke: '#27ae60', text: 'white' },
    current: { fill: '#f39c12', stroke: '#e67e22', text: 'white' },
    available: { fill: '#3498db', stroke: '#2980b9', text: 'white' },
    locked: { fill: '#ecf0f1', stroke: '#bdc3c7', text: '#7f8c8d' },
  };
  
  const color = colors[status] || colors.locked;
  
  return (
    <g 
      onClick={() => onClick(num)}
      style={{ cursor: status !== 'locked' ? 'pointer' : 'default' }}
    >
      <path
        d={hexPath(x, y)}
        fill={color.fill}
        stroke={isSelected ? '#e74c3c' : color.stroke}
        strokeWidth={isSelected ? 3 : 2}
      />
      <text
        x={x}
        y={y + 5}
        textAnchor="middle"
        fill={color.text}
        fontSize="14"
        fontWeight="bold"
      >
        {num}
      </text>
    </g>
  );
};

// 학습자 프로필 생성
const generateProfile = () => {
  const names = ['김민준', '이서연', '박지호', '최유나', '정현우', '강수아'];
  const raw = [Math.random(), Math.random(), Math.random(), Math.random()];
  const total = raw.reduce((a, b) => a + b, 0);
  const norm = raw.map(r => Math.round(r / total * 100));
  norm[0] += 100 - norm.reduce((a, b) => a + b, 0);
  
  return {
    name: names[Math.floor(Math.random() * names.length)],
    탐험형: norm[0],
    성취형: norm[1],
    경쟁형: norm[2],
    창조형: norm[3],
    도전선호: ['낮음', '중간', '높음'][Math.floor(Math.random() * 3)],
    실패인내: ['낮음', '중간', '높음'][Math.floor(Math.random() * 3)],
  };
};

// 메인 앱
export default function HoneycombApp() {
  const [cells, setCells] = useState(() => {
    const initial = {};
    for (let i = 1; i <= 61; i++) {
      initial[i] = {
        status: i === 1 ? 'available' : 'locked',
        score: 0,
        adjacent: getAdjacent(i),
      };
    }
    return initial;
  });
  
  const [profile, setProfile] = useState(null);
  const [currentCell, setCurrentCell] = useState(null);
  const [history, setHistory] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  
  const centers = generateHexagonCenters(4);
  
  // 인접 셀 계산 (간략화)
  function getAdjacent(num) {
    if (num === 1) return [2, 3, 4, 5, 6, 7];
    if (num <= 7) return [1, num === 2 ? 7 : num - 1, num === 7 ? 2 : num + 1];
    const ring = Math.ceil((-3 + Math.sqrt(9 + 12 * (num - 2))) / 6);
    const prevStart = 2 + 3 * (ring - 1) * (ring);
    return [Math.max(1, num - 1), Math.max(1, prevStart + Math.floor((num - prevStart) / 2))];
  }
  
  // 학습자 생성
  const handleCreateProfile = useCallback(() => {
    const newProfile = generateProfile();
    setProfile(newProfile);
    setCells(prev => {
      const newCells = {};
      for (let i = 1; i <= 61; i++) {
        newCells[i] = { ...prev[i], status: i === 1 ? 'available' : 'locked', score: 0 };
      }
      return newCells;
    });
    setCurrentCell(1);
    setHistory([]);
    setLastResult(null);
  }, []);
  
  // 학습 시뮬레이션
  const handleLearn = useCallback(() => {
    if (!currentCell || !profile) return;
    
    const cell = cells[currentCell];
    if (cell.status !== 'available' && cell.status !== 'current') return;
    
    // 학습 결과 생성
    const 체류시간 = Math.floor(120 + Math.random() * 180);
    const 실패횟수 = Math.floor(Math.random() * 5);
    const 이탈 = 실패횟수 >= 3 && Math.random() < 0.4;
    const 성취도 = 이탈 ? Math.random() * 0.4 : 0.6 + Math.random() * 0.4;
    
    const result = {
      셀: currentCell,
      체류시간,
      실패횟수,
      이탈,
      재도전: !이탈 && 실패횟수 > 0 && Math.random() < 0.5,
      보상반응: ['칭찬', '개방', '시각효과'][Math.floor(Math.random() * 3)],
      성취도: Math.round(성취도 * 100),
    };
    
    setLastResult(result);
    setHistory(prev => [...prev, result]);
    
    // 셀 상태 업데이트
    setCells(prev => {
      const newCells = { ...prev };
      
      if (!이탈) {
        // 완료 처리
        newCells[currentCell] = { ...newCells[currentCell], status: 'completed', score: 성취도 };
        
        // 인접 셀 잠금 해제
        cell.adjacent.forEach(adj => {
          if (adj <= 61 && newCells[adj].status === 'locked') {
            newCells[adj] = { ...newCells[adj], status: 'available' };
          }
        });
      }
      
      return newCells;
    });
    
    // 다음 셀 찾기
    if (!이탈) {
      setTimeout(() => {
        setCells(prev => {
          const available = Object.entries(prev)
            .filter(([_, c]) => c.status === 'available')
            .map(([k]) => parseInt(k));
          
          if (available.length > 0) {
            const next = Math.min(...available);
            setCurrentCell(next);
          } else {
            setCurrentCell(null);
          }
          return prev;
        });
      }, 100);
    }
  }, [currentCell, profile, cells]);
  
  // 셀 클릭
  const handleCellClick = useCallback((num) => {
    if (cells[num].status === 'available' || cells[num].status === 'current') {
      setCurrentCell(num);
    }
  }, [cells]);
  
  // 진행률 계산
  const completed = Object.values(cells).filter(c => c.status === 'completed').length;
  
  return (
    <div className="p-4 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold text-center mb-4">🐝 벌집 구조 학습 시스템</h1>
      
      {/* 컨트롤 */}
      <div className="flex justify-center gap-4 mb-4">
        <button
          onClick={handleCreateProfile}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          🎲 학습자 생성
        </button>
        {profile && (
          <button
            onClick={handleLearn}
            disabled={!currentCell}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
          >
            📚 학습 시뮬레이션
          </button>
        )}
      </div>
      
      {/* 범례 */}
      <div className="flex justify-center gap-6 mb-4 text-sm">
        <span className="flex items-center gap-1"><span className="w-4 h-4 bg-green-500 rounded"></span> 완료</span>
        <span className="flex items-center gap-1"><span className="w-4 h-4 bg-yellow-500 rounded"></span> 현재</span>
        <span className="flex items-center gap-1"><span className="w-4 h-4 bg-blue-500 rounded"></span> 학습가능</span>
        <span className="flex items-center gap-1"><span className="w-4 h-4 bg-gray-200 rounded"></span> 잠김</span>
      </div>
      
      <div className="flex gap-4 justify-center">
        {/* 벌집 맵 */}
        <div className="bg-white rounded-lg shadow p-4">
          <svg width="700" height="700" viewBox="0 0 700 700">
            {centers.map(({ x, y, num }) => (
              <Hexagon
                key={num}
                x={x}
                y={y}
                num={num}
                status={num === currentCell ? 'current' : cells[num]?.status}
                onClick={handleCellClick}
                isSelected={num === currentCell}
              />
            ))}
          </svg>
        </div>
        
        {/* 정보 패널 */}
        <div className="w-64 space-y-4">
          {/* 진행 상황 */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-bold mb-2">📊 진행 상황</h3>
            <div className="text-2xl font-bold text-center">{completed}/61</div>
            <div className="w-full bg-gray-200 rounded h-2 mt-2">
              <div 
                className="bg-green-500 h-2 rounded" 
                style={{ width: `${(completed / 61) * 100}%` }}
              ></div>
            </div>
            {currentCell && (
              <div className="mt-2 text-center text-sm text-gray-600">
                현재 셀: #{currentCell}
              </div>
            )}
          </div>
          
          {/* 학습자 정보 */}
          {profile && (
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-bold mb-2">👤 {profile.name}</h3>
              <div className="text-xs space-y-1">
                <div className="flex justify-between">
                  <span>탐험형</span>
                  <span className="font-bold">{profile.탐험형}%</span>
                </div>
                <div className="flex justify-between">
                  <span>성취형</span>
                  <span className="font-bold">{profile.성취형}%</span>
                </div>
                <div className="flex justify-between">
                  <span>경쟁형</span>
                  <span className="font-bold">{profile.경쟁형}%</span>
                </div>
                <div className="flex justify-between">
                  <span>창조형</span>
                  <span className="font-bold">{profile.창조형}%</span>
                </div>
              </div>
            </div>
          )}
          
          {/* 최근 결과 */}
          {lastResult && (
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-bold mb-2">📋 최근 결과</h3>
              <div className="text-xs space-y-1">
                <div>셀 #{lastResult.셀}</div>
                <div>체류시간: {lastResult.체류시간}초</div>
                <div>실패: {lastResult.실패횟수}회</div>
                <div>성취도: {lastResult.성취도}%</div>
                <div>이탈: {lastResult.이탈 ? '❌' : '✅'}</div>
                <div>보상: {lastResult.보상반응}</div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {!profile && (
        <div className="text-center mt-4 text-gray-500">
          👆 '학습자 생성' 버튼을 클릭하여 시작하세요!
        </div>
      )}
    </div>
  );
}
