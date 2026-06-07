import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import client from '../api/client';
import HiringScoreBadge from './HiringScoreBadge';
import Loader from './Loader';
import './JobDetailPanel.css';

export default function JobDetailPanel({ job, conversationId, onClose }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await client.post(`/conversations/${conversationId}/analyze-job`, {
        job_data: job.raw_data || job,
        user_bio: 'I am a professional looking for new opportunities.',
      });
      setAnalysis(res.data);
      setActiveTab('resume');
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'summary', label: 'JD Summary' },
    { id: 'resume', label: 'Resume Tweaks' },
    { id: 'cover', label: 'Cover Letter' },
  ];

  return (
    <div className="job-detail-overlay" onClick={onClose}>
      <div className="job-detail-panel glass animate-slide-up" onClick={e => e.stopPropagation()}>
        <div className="job-detail-header">
          <div className="job-detail-header-info">
            <h2 className="job-detail-title">{job.position_title}</h2>
            <p className="job-detail-org">{job.organization_name}</p>
            <span className="job-detail-location">📍 {job.location}</span>
          </div>
          <div className="job-detail-header-actions">
            {job.hiring_score != null && (
              <HiringScoreBadge score={job.hiring_score} size="md" />
            )}
            <button className="btn btn-ghost job-detail-close" onClick={onClose}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        {!analysis && !loading && (
          <div className="job-detail-cta">
            <p className="job-detail-cta-text">
              Get AI-powered resume tweaks and a tailored cover letter for this position.
            </p>
            <button className="btn btn-primary" onClick={runAnalysis} id="run-analysis-button">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              Analyze & Generate
            </button>
            {error && <p className="job-detail-error">{error}</p>}
          </div>
        )}

        {loading && (
          <Loader
            message="AI Agents are working..."
            submessage="Analyzing JD • Tweaking resume • Writing cover letter"
          />
        )}

        {analysis && (
          <div className="job-detail-results">
            <div className="job-detail-tabs">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  className={`job-detail-tab ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="job-detail-content">
              {activeTab === 'summary' && (
                <div className="job-detail-markdown animate-fade-in">
                  <ReactMarkdown>{analysis.jd_summary}</ReactMarkdown>
                </div>
              )}
              {activeTab === 'resume' && (
                <div className="job-detail-markdown animate-fade-in">
                  <ReactMarkdown>{analysis.resume_tweaks}</ReactMarkdown>
                </div>
              )}
              {activeTab === 'cover' && (
                <div className="job-detail-markdown animate-fade-in">
                  <ReactMarkdown>{analysis.cover_letter}</ReactMarkdown>
                  <button
                    className="btn btn-secondary job-detail-copy"
                    onClick={() => navigator.clipboard.writeText(analysis.cover_letter)}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                    Copy to Clipboard
                  </button>
                </div>
              )}
            </div>

            {analysis.hiring_score_reasoning && (
              <div className="job-detail-reasoning">
                <h4>Match Assessment</h4>
                <ReactMarkdown>{analysis.hiring_score_reasoning}</ReactMarkdown>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
