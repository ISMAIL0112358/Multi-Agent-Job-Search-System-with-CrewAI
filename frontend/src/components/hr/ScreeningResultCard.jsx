import { useState } from 'react';
import MatchScoreRing from './MatchScoreRing';
import StatusBadge from './StatusBadge';
import VettingQuestions from './VettingQuestions';
import './ScreeningResultCard.css';

const STATUS_OPTIONS = ['new', 'screening', 'shortlisted', 'interview', 'hired', 'closed'];

export default function ScreeningResultCard({
  result,
  onStatusChange,
  onGenerateVetting,
  vettingLoading,
}) {
  const [showReason, setShowReason] = useState(false);
  const [showVetting, setShowVetting] = useState(false);
  const { candidate } = result;

  return (
    <div className="screening-card card" id={`screening-card-${result.id}`}>
      {/* Header with candidate info + score */}
      <div className="screening-card__header">
        <div className="screening-card__left">
          <div className="screening-card__avatar">
            {candidate.name?.charAt(0)?.toUpperCase() || '?'}
          </div>
          <div className="screening-card__info">
            <h3 className="screening-card__name">{candidate.name}</h3>
            <div className="screening-card__contact">
              {candidate.email && <span>✉ {candidate.email}</span>}
              {candidate.phone && <span>📞 {candidate.phone}</span>}
            </div>
          </div>
        </div>
        <MatchScoreRing score={result.match_score} />
      </div>

      {/* Action bar */}
      <div className="screening-card__actions">
        <button
          className={`btn btn-secondary screening-card__reason-btn ${showReason ? 'active' : ''}`}
          onClick={() => setShowReason(!showReason)}
          id={`reason-toggle-${result.id}`}
        >
          {showReason ? '▼ Hide Reason' : '▶ Show Reason'}
        </button>

        <button
          className={`btn btn-secondary screening-card__vetting-btn ${showVetting ? 'active' : ''}`}
          onClick={() => {
            if (!showVetting && !result.vetting_questions) {
              onGenerateVetting?.(candidate.id);
            }
            setShowVetting(!showVetting);
          }}
          disabled={vettingLoading}
          id={`vetting-toggle-${result.id}`}
        >
          {vettingLoading ? (
            <><span className="spinner" /> Generating...</>
          ) : showVetting ? (
            '▼ Hide Vetting Qs'
          ) : (
            '🔍 Generate Vetting Qs'
          )}
        </button>

        <div className="screening-card__status-control">
          <StatusBadge status={candidate.status} />
          <select
            className="input screening-card__status-select"
            value={candidate.status}
            onChange={(e) => onStatusChange?.(candidate.id, e.target.value)}
            id={`status-select-${candidate.id}`}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Reason accordion */}
      <div className={`screening-card__reason ${showReason ? 'expanded' : ''}`}>
        <div className="screening-card__reason-content">
          <h4>Match Justification</h4>
          <p>{result.match_justification || 'No justification available.'}</p>
        </div>
      </div>

      {/* Vetting questions accordion */}
      <div className={`screening-card__vetting ${showVetting ? 'expanded' : ''}`}>
        <VettingQuestions questions={result.vetting_questions} />
      </div>
    </div>
  );
}
