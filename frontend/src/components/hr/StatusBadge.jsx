import './StatusBadge.css';

const STATUS_CONFIG = {
  new: { label: 'New', className: 'status-new' },
  screening: { label: 'Screening', className: 'status-screening' },
  shortlisted: { label: 'Shortlisted', className: 'status-shortlisted' },
  interview: { label: 'Interview', className: 'status-interview' },
  hired: { label: 'Hired', className: 'status-hired' },
  closed: { label: 'Closed', className: 'status-closed' },
  open: { label: 'Open', className: 'status-open' },
};

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || { label: status, className: 'status-new' };

  return (
    <span className={`status-badge ${config.className}`} id={`status-badge-${status}`}>
      <span className="status-dot" />
      {config.label}
    </span>
  );
}
