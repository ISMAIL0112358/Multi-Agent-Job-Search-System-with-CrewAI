import { useEffect, useState } from 'react';
import './MatchScoreRing.css';

export default function MatchScoreRing({ score, size = 80 }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animatedScore / 100) * circumference;

  useEffect(() => {
    // Animate the score from 0 to target
    const timer = setTimeout(() => setAnimatedScore(score), 100);
    return () => clearTimeout(timer);
  }, [score]);

  const getColor = (s) => {
    if (s >= 70) return '#34d399'; // green
    if (s >= 40) return '#fbbf24'; // amber
    return '#f87171'; // red
  };

  const color = getColor(score);

  return (
    <div className="match-score-ring" id="match-score-ring" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="ring-svg">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="5"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="ring-progress"
          style={{
            filter: `drop-shadow(0 0 6px ${color}40)`,
          }}
        />
      </svg>
      <div className="ring-label" style={{ color }}>
        <span className="ring-value">{Math.round(animatedScore)}</span>
        <span className="ring-percent">%</span>
      </div>
    </div>
  );
}
