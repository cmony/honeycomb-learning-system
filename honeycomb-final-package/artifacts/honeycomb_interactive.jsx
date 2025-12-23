import React, { useState, useCallback } from 'react';

const generateHexagonCenters = (numRings = 4) => {
  const centers = [];
  let cellNum = 1;
  const size = 32;
  const h = size * Math.sqrt(3);
  
  centers.push({ x: 280, y: 280, num: cellNum++ });
  
  for (let ring = 1; ring <= numRings; ring++) {
    const directions = [
      { dx: 1.5 * size, dy: -h / 2 },
      { dx: 0, dy: -h },
      { dx: -1.5 * size, dy: -h / 2 },
      { dx: -1.5 * size, dy: h / 2 },
      { dx: 0, dy: h },
      { dx: 1.5 * size, dy: h / 2 },
    ];
    
    let x = 280;
    let y = 280 + ring * h;
    
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

const hexPath = (cx, cy, size = 30) => {
  const points = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 6) + (i * Math.PI / 3);
    points.push(`${cx + size * Math.cos(angle)},${cy + size * Math.sin(angle)}`);
  }
  return `M ${points.join(' L ')} Z`;
};

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
      <text x={x} y={y + 4} textAnchor="middle" fill={color.text} fontSize="11" fontWeight="bold">
        {num}
      </text>
    </g>
  );
};

const generateProfile = () => {
  const names = ['김민준', '이서연', '박지호', '최유나', '정현우', '강수아'];
  const raw = [Math.random(), Math.random(), Math.random(), Math.random()];
  const total = raw.reduce((a, b) => a + b, 0);
  const norm = raw.map(r => Math.round(r / total * 100));
  norm[0] += 100 - norm.reduce((a, b) => a + b, 0);
  
  return {
    name: names[Math.floor(Math.random() * names.length)],
    탐험형: norm[0], 성취형: norm[1], 경쟁형: norm[2], 창조형: norm[3],
    도전선호: ['낮음', '중간', '높음'][Math.floor(Math.random() * 3)],
    이탈임계: Math.floor(Math.random() * 3) + 2,
  };
};

const getAdjacent = (num) => {
  if (num === 1) return [2, 3, 4, 5, 6, 7];
  if (num <= 7) return [1, num === 2 ? 7 : num - 1, num === 7 ? 2 : num + 1, num + 6, num + 5];
  if (num <= 19) {
    const base = [num - 6, num - 7].filter(n => n > 1);
    return [...base, num - 1, num + 1].filter(n => n > 0 && n <= 61);
  }
  return [num - 1, Math.max(1, num - 12), Math.max(1, num - 11)].filter(n => n > 0);
};

export default function HoneycombApp() {
  const [cells, setCells] = useState(() => {
    const initial = {};
    for (let i = 1; i <= 61; i++) {
      initial[i] = { status: i === 1 ? 'available' : 'locked', score: 0, adjacent: getAdjacent(i) };
    }
    return initial;
  });
  
  const [profile, setProfile] = useState(null);
  const [currentCell, setCurrentCell] = useState(null);
  const [history, setHistory] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  
  const centers = generateHexagonCenters(4);

  const handleCreateProfile = useCallback(() => {
    setProfile(generateProfile());
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

  const handleLearn = useCallback(() => {
    if (!currentCell || !profile) return;
    
    const 체류시간 = Math.floor(120 + Math.random() * 180);
    const 실패횟수 = Math.floor(Math.random() * 5);
    const 이탈 = 실패횟수 >= profile.이탈임계 && Math.random() < 0.4;
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
    
    const cell = cells[currentCell];
    
    setCells(prev => {
      const newCells = { ...prev };
      
      if (!이탈) {
        newCells[currentCell] = { ...newCells[currentCell], status: 'completed', score: 성취도 };
        
        cell.adjacent.forEach(adj => {
          if (adj <= 61 && newCells[adj]?.status === 'locked') {
            newCells[adj] = { ...newCells[adj], status: 'available' };
          }
        });
      }
      
      const available = Object.entries(newCells)
        .filter(([_, c]) => c.status === 'available')
        .map(([k]) => parseInt(k));
      
      if (available.length > 0 && !이탈) {
        setCurrentCell(Math.min(...available));
      } else if (이탈) {
        setCurrentCell(currentCell);
      }
      
      return newCells;
    });
  }, [currentCell, profile, cells]);

  const handleCellClick = useCallback((num) => {
    if (cells[num]?.status === 'available') {
      setCurrentCell(num);
    }
  }, [cells]);

  const completed = Object.values(cells).filter(c => c.status === 'completed').length;

  return (
    <div className="p-3 bg-gray-50 min-h-screen">
      <h1 className="text-xl font-bold text-center mb-3">🐝 벌집 구조 학습 시스템</h1>
      
      <div className="flex justify-center gap-3 mb-3">
        <button onClick={handleCreateProfile} className="px-3 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">
          🎲 학습자 생성
        </button>
        {profile && (
          <button onClick={handleLearn} disabled={!currentCell} className="px-3 py-1.5 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:bg-gray-300">
            📚 학습 시뮬레이션
          </button>
        )}
      </div>

      <div className="flex justify-center gap-4 mb-3 text-xs">
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded"></span> 완료</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-500 rounded"></span> 현재</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded"></span> 학습가능</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-gray-200 rounded"></span> 잠김</span>
      </div>

      <div className="flex gap-3 justify-center flex-wrap">
        <div className="bg-white rounded-lg shadow p-2">
          <svg width="560" height="560" viewBox="0 0 560 560">
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

        <div className="w-52 space-y-3">
          <div className="bg-white rounded-lg shadow p-3">
            <h3 className="font-bold text-sm mb-2">📊 진행 상황</h3>
            <div className="text-xl font-bold text-center">{completed}/61</div>
            <div className="w-full bg-gray-200 rounded h-2 mt-2">
              <div className="bg-green-500 h-2 rounded transition-all" style={{ width: `${(completed / 61) * 100}%` }}></div>
            </div>
            {currentCell && <div className="mt-2 text-center text-xs text-gray-600">현재 셀: #{currentCell}</div>}
          </div>

          {profile && (
            <div className="bg-white rounded-lg shadow p-3">
              <h3 className="font-bold text-sm mb-2">👤 {profile.name}</h3>
              <div className="text-xs space-y-1">
                <div className="flex justify-between"><span>탐험형</span><span className="font-bold">{profile.탐험형}%</span></div>
                <div className="flex justify-between"><span>성취형</span><span className="font-bold">{profile.성취형}%</span></div>
                <div className="flex justify-between"><span>경쟁형</span><span className="font-bold">{profile.경쟁형}%</span></div>
                <div className="flex justify-between"><span>창조형</span><span className="font-bold">{profile.창조형}%</span></div>
                <div className="border-t pt-1 mt-1">
                  <div className="flex justify-between"><span>도전선호</span><span>{profile.도전선호}</span></div>
                  <div className="flex justify-between"><span>이탈임계</span><span>{profile.이탈임계}회</span></div>
                </div>
              </div>
            </div>
          )}

          {lastResult && (
            <div className="bg-white rounded-lg shadow p-3">
              <h3 className="font-bold text-sm mb-2">📋 최근 결과</h3>
              <div className="text-xs space-y-1">
                <div className="flex justify-between"><span>셀</span><span>#{lastResult.셀}</span></div>
                <div className="flex justify-between"><span>체류시간</span><span>{lastResult.체류시간}초</span></div>
                <div className="flex justify-between"><span>실패</span><span>{lastResult.실패횟수}회</span></div>
                <div className="flex justify-between"><span>성취도</span><span className="font-bold">{lastResult.성취도}%</span></div>
                <div className="flex justify-between"><span>완료</span><span>{lastResult.이탈 ? '❌ 이탈' : '✅ 성공'}</span></div>
                <div className="flex justify-between"><span>보상반응</span><span>{lastResult.보상반응}</span></div>
              </div>
            </div>
          )}

          {history.length > 0 && (
            <div className="bg-white rounded-lg shadow p-3 max-h-40 overflow-y-auto">
              <h3 className="font-bold text-sm mb-2">📜 히스토리 ({history.length}회)</h3>
              <div className="text-xs space-y-1">
                {history.slice(-5).reverse().map((h, i) => (
                  <div key={i} className={`flex justify-between ${h.이탈 ? 'text-red-500' : 'text-green-600'}`}>
                    <span>#{h.셀}</span>
                    <span>{h.성취도}%</span>
                    <span>{h.이탈 ? '이탈' : '완료'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {!profile && (
        <div className="text-center mt-4 text-gray-500 text-sm">
          👆 '학습자 생성' 버튼을 클릭하여 시작하세요!
        </div>
      )}
    </div>
  );
}
