import { useState } from 'react';
import MatchScoreRing from './MatchScoreRing';
import StatusBadge from './StatusBadge';
import VettingQuestions from './VettingQuestions';
import client from '../../api/client';
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
  const [showResumeModal, setShowResumeModal] = useState(false);
  const { candidate } = result;

  const handleDownload = async () => {
    try {
      const response = await client.get(`/hr/candidates/${candidate.id}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', candidate.resume_filename || 'resume.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error('Failed to download resume:', err);
      alert('Failed to download resume file.');
    }
  };

  return (
    <div className={`screening-card card ${showResumeModal ? 'active-modal' : ''}`} id={`screening-card-${result.id}`}>
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

        <button
          className="btn btn-secondary screening-card__resume-btn"
          onClick={() => setShowResumeModal(true)}
          id={`resume-view-${result.id}`}
        >
          📄 View Resume
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

      {/* Resume modal overlay */}
      {showResumeModal && (
        <div className="resume-modal-overlay" onClick={() => setShowResumeModal(false)}>
          <div className="resume-modal" onClick={(e) => e.stopPropagation()}>
            <div className="resume-modal__header">
              <h3>{candidate.name}'s Resume</h3>
              <div className="resume-modal__header-actions">
                <button className="btn btn-secondary resume-modal__download-btn" onClick={handleDownload}>
                  📥 Download PDF
                </button>
                <button className="resume-modal__close" onClick={() => setShowResumeModal(false)}>
                  &times;
                </button>
              </div>
            </div>
            <div className="resume-modal__body">
              <pre className="resume-modal__text">{candidate.resume_text || 'No resume content available.'}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
