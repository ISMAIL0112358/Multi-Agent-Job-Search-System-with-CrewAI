import { useState } from 'react';
import './VettingQuestions.css';

const DIFFICULTY_COLORS = {
  basic: { bg: 'rgba(16, 185, 129, 0.12)', color: '#34d399' },
  intermediate: { bg: 'rgba(245, 158, 11, 0.12)', color: '#fbbf24' },
  advanced: { bg: 'rgba(239, 68, 68, 0.12)', color: '#f87171' },
};

export default function VettingQuestions({ questions }) {
  const [expanded, setExpanded] = useState({});

  if (!questions || questions.length === 0) return null;

  const toggleAnswer = (idx) => {
    setExpanded((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="vetting-questions" id="vetting-questions-panel">
      <h4 className="vetting-questions__title">🔍 Vetting Questions</h4>
      <div className="vetting-questions__list">
        {questions.map((q, idx) => {
          const diffStyle = DIFFICULTY_COLORS[q.difficulty] || DIFFICULTY_COLORS.basic;
          return (
            <div key={idx} className="vetting-q card" id={`vetting-q-${idx}`}>
              <div className="vetting-q__header" onClick={() => toggleAnswer(idx)}>
                <div className="vetting-q__badges">
                  <span className="vetting-q__skill">{q.skill_area}</span>
                  <span
                    className="vetting-q__difficulty"
                    style={{ background: diffStyle.bg, color: diffStyle.color }}
                  >
                    {q.difficulty}
                  </span>
                </div>
                <span className="vetting-q__toggle">{expanded[idx] ? '▼' : '▶'}</span>
              </div>

              <p className="vetting-q__question">Q{idx + 1}: {q.question}</p>

              <div className={`vetting-q__answer ${expanded[idx] ? 'expanded' : ''}`}>
                <div className="vetting-q__answer-content">
                  <span className="vetting-q__answer-label">Expected Answer / Key Points:</span>
                  <p>{q.expected_answer}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
