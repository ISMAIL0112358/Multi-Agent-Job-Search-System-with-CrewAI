import GoogleLoginButton from '../components/GoogleLoginButton';
import './LoginPage.css';

export default function LoginPage() {
  return (
    <div className="login-page">
      <div className="bg-ambient" />

      <div className="login-container animate-fade-in">
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
          <h1 className="login-title">AI Job Hunt Assistant</h1>
          <p className="login-subtitle">
            Powered by multi-agent AI to find your perfect job, score your match,
            and craft winning resumes & cover letters.
          </p>
        </div>

        <div className="login-features">
          <div className="login-feature">
            <span className="login-feature-icon">📄</span>
            <div>
              <h3>Upload Resume</h3>
              <p>Upload your PDF resume for AI analysis</p>
            </div>
          </div>
          <div className="login-feature">
            <span className="login-feature-icon">🎯</span>
            <div>
              <h3>Hiring Score</h3>
              <p>Get match percentages for each job</p>
            </div>
          </div>
          <div className="login-feature">
            <span className="login-feature-icon">✍️</span>
            <div>
              <h3>Smart Applications</h3>
              <p>AI-crafted cover letters & resume tweaks</p>
            </div>
          </div>
        </div>

        <div className="login-action">
          <GoogleLoginButton />
          <p className="login-disclaimer">
            Sign in with your Google account to get started
          </p>
        </div>
      </div>

      {/* Floating orbs for visual depth */}
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />
      <div className="login-orb login-orb-3" />
    </div>
  );
}
