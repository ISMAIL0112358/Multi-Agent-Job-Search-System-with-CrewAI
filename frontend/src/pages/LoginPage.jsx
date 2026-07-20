import GoogleLoginButton from '../components/GoogleLoginButton';
import './LoginPage.css';

export default function LoginPage() {
  return (
    <div className="login-page">
      <div className="bg-ambient" />

      <div className="login-container animate-fade-in">
        {/* Hero */}
        <div className="login-hero">
          <div className="login-logo">
            <svg width="56" height="56" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="8" fill="url(#login-gradient)"/>
              <path d="M8 14L12 18L20 10" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <defs>
                <linearGradient id="login-gradient" x1="0" y1="0" x2="28" y2="28">
                  <stop stopColor="#6366f1"/>
                  <stop offset="1" stopColor="#06b6d4"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 className="login-title">AI Job Hunt & Recruitment Assistant (Beta)</h1>
          <p className="login-subtitle">
            An AI-driven job hunt and talent recruitment platform using cooperative CrewAI agents to assist both candidates and HR personnel.
          </p>
        </div>

        {/* Dual Login Cards */}
        <div className="login-cards">
          {/* Job Seeker Card */}
          <div className="login-card login-card--seeker" id="login-card-seeker">
            <div className="login-card__icon">🔍</div>
            <h2 className="login-card__title">Job Seeker</h2>
            <ul className="login-card__features">
              <li>
                <span className="login-card__bullet">📄</span>
                Upload your resume for AI analysis
              </li>
              <li>
                <span className="login-card__bullet">🎯</span>
                Get hiring match scores for jobs
              </li>
              <li>
                <span className="login-card__bullet">✍️</span>
                AI-crafted cover letters &amp; resume tweaks
              </li>
            </ul>
            <div className="login-card__action">
              <GoogleLoginButton
                role="job_seeker"
                label="Sign in as Job Seeker"
                className="login-btn--seeker"
              />
            </div>
          </div>

          {/* HR / Hiring Manager Card */}
          <div className="login-card login-card--hr" id="login-card-hr">
            <div className="login-card__icon">🏢</div>
            <h2 className="login-card__title">HR / Hiring Manager</h2>
            <ul className="login-card__features">
              <li>
                <span className="login-card__bullet">📋</span>
                Screen candidates against Job Descriptions
              </li>
              <li>
                <span className="login-card__bullet">📊</span>
                AI-powered Top-N candidate matching
              </li>
              <li>
                <span className="login-card__bullet">🔍</span>
                Generate vetting Q&amp;As for interviews
              </li>
            </ul>
            <div className="login-card__action">
              <GoogleLoginButton
                role="hr"
                label="Sign in as HR Manager"
                className="login-btn--hr"
              />
            </div>
          </div>
        </div>

        <p className="login-disclaimer">
          Sign in securely with your Google account • Same account can be used for both roles
        </p>

        <div style={{ marginTop: '24px', fontSize: '0.85rem', opacity: 0.8 }}>
          Created by <a href="https://www.linkedin.com/in/ismailtaibani/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary, #6366f1)', textDecoration: 'underline', fontWeight: 'bold' }}>Ismail Taibani</a> (<a href="https://www.linkedin.com/in/ismailtaibani/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary, #6366f1)', textDecoration: 'underline' }}>About Me</a>)
        </div>
      </div>

      {/* Floating orbs for visual depth */}
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />
      <div className="login-orb login-orb-3" />

      {/* Developer Profile Link Badge */}
      <a 
        href="https://www.linkedin.com/in/ismailtaibani/" 
        target="_blank" 
        rel="noopener noreferrer" 
        className="dev-badge glass"
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 20px',
          borderRadius: '50px',
          fontSize: '0.85rem',
          fontWeight: '600',
          color: '#ffffff',
          textDecoration: 'none',
          zIndex: 1000,
          border: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.2)',
          transition: 'all 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)';
          e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" style={{ transition: 'transform 0.3s ease' }}>
          <polyline points="16 18 22 12 16 6"/>
          <polyline points="8 6 2 12 8 18"/>
        </svg>
        <span>About Developer</span>
      </a>
    </div>
  );
}
