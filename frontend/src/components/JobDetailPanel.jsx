import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import client from '../api/client';
import HiringScoreBadge from './HiringScoreBadge';
import Loader from './Loader';
import './JobDetailPanel.css';

export default function JobDetailPanel({ job, conversationId, messages = [], onClose }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  
  // Chat state
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Check for existing analysis
  useEffect(() => {
    const existingMsg = messages
      .slice()
      .reverse()
      .find(
        m => m.metadata_?.type === 'job_analysis' && 
             m.metadata_?.job_title === job.position_title
      );
    
    if (existingMsg && existingMsg.content) {
      try {
        const parsed = JSON.parse(existingMsg.content);
        setAnalysis(parsed);
        setActiveTab('resume');
      } catch (err) {
        console.error("Failed to parse cached analysis", err);
      }
    }
  }, [job, messages]);

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

  const sendChatMessage = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;

    const userMsg = chatMessage.trim();
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);

    try {
      const res = await client.post(`/conversations/${conversationId}/chat`, {
        message: userMsg,
        job_context: {
          position_title: job.position_title,
          organization_name: job.organization_name,
          job_summary: analysis?.jd_summary || job.job_summary || 'Unknown',
        }
      });
      setChatHistory(prev => [...prev, { role: 'assistant', content: res.data.reply }]);
    } catch (err) {
      console.error(err);
      setChatHistory(prev => [...prev, { role: 'assistant', content: "Sorry, I couldn't answer that right now." }]);
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, chatLoading]);

  const tabs = [
    { id: 'summary', label: 'JD Summary' },
    { id: 'resume', label: 'Resume Tweaks' },
    { id: 'cover', label: 'Cover Letter' },
    { id: 'company', label: 'Company Profile' },
    { id: 'interview', label: 'Interview Prep' },
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
              Get AI-powered resume tweaks, a tailored cover letter, company profiling, and interview prep for this position.
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
            submessage="Analyzing JD • Tweaking resume • Writing cover letter • Researching Company • Preparing Interview"
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
              {activeTab === 'company' && (
                <div className="job-detail-markdown animate-fade-in">
                  <ReactMarkdown>{analysis.company_profile}</ReactMarkdown>
                </div>
              )}
              {activeTab === 'interview' && (
                <div className="job-detail-markdown animate-fade-in">
                  <ReactMarkdown>{analysis.interview_prep}</ReactMarkdown>
                </div>
              )}
            </div>

            {analysis.hiring_score_reasoning && (
              <div className="job-detail-reasoning">
                <h4>Match Assessment</h4>
                <ReactMarkdown>{analysis.hiring_score_reasoning}</ReactMarkdown>
              </div>
            )}
            
            {/* Follow-up Chat Interface */}
            <div className="job-detail-chat">
              <h4 className="job-detail-chat-title">Ask Follow-up Questions</h4>
              
              <div className="job-detail-chat-history">
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`chat-message ${msg.role}`}>
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      <p>{msg.content}</p>
                    )}
                  </div>
                ))}
                {chatLoading && (
                  <div className="chat-message assistant loading">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              
              <form onSubmit={sendChatMessage} className="job-detail-chat-form">
                <input
                  type="text"
                  placeholder="Ask a question about this job..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  disabled={chatLoading}
                />
                <button type="submit" className="btn btn-primary btn-icon" disabled={!chatMessage.trim() || chatLoading}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              </form>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
