import StatusBadge from './StatusBadge';
import './CandidateCard.css';

const STATUS_OPTIONS = ['new', 'screening', 'shortlisted', 'interview', 'hired', 'closed'];

export default function CandidateCard({ candidate, onStatusChange, onDelete }) {
  return (
    <div className="candidate-card card" id={`candidate-card-${candidate.id}`}>
      <div className="candidate-card__header">
        <div className="candidate-card__avatar">
          {candidate.name?.charAt(0)?.toUpperCase() || '?'}
        </div>
        <div className="candidate-card__info">
          <h3 className="candidate-card__name">{candidate.name}</h3>
          {candidate.email && (
            <span className="candidate-card__email">{candidate.email}</span>
          )}
          {candidate.phone && (
            <span className="candidate-card__phone">{candidate.phone}</span>
          )}
        </div>
        <StatusBadge status={candidate.status} />
      </div>

      <div className="candidate-card__meta">
        <span className="candidate-card__file">📄 {candidate.resume_filename}</span>
        {candidate.created_at && (
          <span className="candidate-card__date">
            {new Date(candidate.created_at).toLocaleDateString()}
          </span>
        )}
      </div>

      <div className="candidate-card__actions">
        <select
          className="input candidate-card__status-select"
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
        <button
          className="btn btn-danger btn-sm"
          onClick={() => onDelete?.(candidate.id)}
          id={`delete-candidate-${candidate.id}`}
        >
          ✕
        </button>
      </div>
    </div>
  );
}
