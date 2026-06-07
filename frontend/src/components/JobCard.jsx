import HiringScoreBadge from './HiringScoreBadge';
import './JobCard.css';

export default function JobCard({ job, onClick, index }) {
  return (
    <div
      className="job-card card animate-fade-in"
      onClick={onClick}
      style={{ animationDelay: `${index * 80}ms` }}
      id={`job-card-${index}`}
    >
      <div className="job-card-main">
        <div className="job-card-info">
          <h3 className="job-card-title">{job.position_title}</h3>
          <p className="job-card-org">{job.organization_name}</p>
          <div className="job-card-meta">
            <span className="job-card-location">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              {job.location}
            </span>
          </div>
        </div>
        {job.hiring_score != null && (
          <div className="job-card-score">
            <HiringScoreBadge score={job.hiring_score} size="sm" />
          </div>
        )}
      </div>
      <p className="job-card-summary">
        {job.job_summary?.slice(0, 180)}{job.job_summary?.length > 180 ? '...' : ''}
      </p>
      <div className="job-card-footer">
        <span className="job-card-cta">
          View analysis & cover letter →
        </span>
      </div>
    </div>
  );
}
