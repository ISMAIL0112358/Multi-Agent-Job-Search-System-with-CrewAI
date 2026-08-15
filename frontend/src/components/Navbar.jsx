import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="navbar" id="main-navbar">
      <div className="navbar-brand">
        <div className="navbar-logo">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="8" fill="url(#logo-gradient)"/>
            <path d="M8 14L12 18L20 10" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            <defs>
              <linearGradient id="logo-gradient" x1="0" y1="0" x2="28" y2="28">
                <stop stopColor="#6366f1"/>
                <stop offset="1" stopColor="#06b6d4"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 className="navbar-title">AI Job Hunt & Recruitment (Beta)</h1>
      </div>

      {user && (
        <div className="navbar-right">
          {/* Cumulative Token Metrics */}
          <div className="navbar-token-metrics glass">
            <div className="token-metric-badge generative" title="Cumulative Generative LLM Tokens Used">
              <span className="token-metric-icon">🤖</span>
              <span className="token-metric-label">Generative LLM:</span>
              <span className="token-metric-value">{(user.generative_tokens_count || 0).toLocaleString()}</span>
            </div>
            <div className="token-metric-divider" />
            <div className="token-metric-badge embedding" title="Cumulative Embedding Tokens Used">
              <span className="token-metric-icon">🧬</span>
              <span className="token-metric-label">Embedding:</span>
              <span className="token-metric-value">{(user.embedding_tokens_count || 0).toLocaleString()}</span>
            </div>
          </div>

          <div className="navbar-user">
            <div className="navbar-user-info">
              <span className="navbar-user-name">{user.name}</span>
              <span className="navbar-user-email">{user.email}</span>
            </div>
            {user.picture_url && (
              <img
                src={user.picture_url}
                alt={user.name}
                className="navbar-avatar"
                referrerPolicy="no-referrer"
              />
            )}
            {/* Show Profile button only for Job Seekers (not HR) */}
            {user.role !== 'hr' && (
              <button className="btn btn-secondary navbar-profile-btn" onClick={() => navigate('/profile')}>
                Profile
              </button>
            )}
            <button className="btn btn-ghost navbar-logout" onClick={logout} id="logout-button" title="Sign out">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
