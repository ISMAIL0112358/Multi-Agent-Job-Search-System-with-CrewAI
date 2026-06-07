import './HiringScoreBadge.css';

export default function HiringScoreBadge({ score, size = 'md' }) {
  const radius = size === 'sm' ? 18 : 28;
  const stroke = size === 'sm' ? 3 : 4;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s) => {
    if (s >= 70) return 'var(--color-success)';
    if (s >= 40) return 'var(--color-warning)';
    return 'var(--color-danger)';
  };

  const color = getColor(score);
  const svgSize = (radius + stroke) * 2;

  return (
    <div className={`hiring-score-badge ${size}`} title={`${score}% match`}>
      <svg width={svgSize} height={svgSize} className="hiring-score-ring">
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={stroke}
        />
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="hiring-score-progress"
        />
      </svg>
      <span className="hiring-score-value" style={{ color }}>
        {score}%
      </span>
    </div>
  );
}
