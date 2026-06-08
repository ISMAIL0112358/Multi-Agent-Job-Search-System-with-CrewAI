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
          <h1 className="login-title">AI Job Hunt Platform</h1>
          <p className="login-subtitle">
            Multi-agent AI for job seekers and hiring managers — powered by intelligent automation.
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
      </div>

      {/* Floating orbs for visual depth */}
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />
      <div className="login-orb login-orb-3" />
    </div>
  );
}
