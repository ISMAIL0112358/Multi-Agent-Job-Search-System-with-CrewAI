import { useState, useEffect, useRef } from 'react';
import client from '../api/client';
import ResumeUpload from './ResumeUpload';
import JobCard from './JobCard';
import JobDetailPanel from './JobDetailPanel';
import MessageBubble from './MessageBubble';
import Loader from './Loader';
import './ChatWindow.css';

export default function ChatWindow({ conversationId }) {
  const [conversation, setConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [location, setLocation] = useState('');
  const [companyPreference, setCompanyPreference] = useState('');
  const [searching, setSearching] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!conversationId) return;
    fetchConversation();
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  const fetchConversation = async () => {
    setLoading(true);
    try {
      const res = await client.get(`/conversations/${conversationId}`);
      setConversation(res.data);
      // Restore jobs from messages if any
      const jobMsg = res.data.messages
        ?.slice()
        .reverse()
        .find(m => m.metadata_?.type === 'job_results');
      if (jobMsg?.metadata_?.jobs) {
        setJobs(jobMsg.metadata_.jobs);
      } else {
        setJobs([]);
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUploaded = (data) => {
    fetchConversation();
  };

  const handleSearchJobs = async (e) => {
    e.preventDefault();
    if (!keyword.trim()) return;

    setSearching(true);
    setJobs([]);
    try {
      const res = await client.post(`/conversations/${conversationId}/search-jobs`, {
        keyword: keyword.trim(),
        location: location.trim() || 'remote',
        company_preference: companyPreference.trim() || undefined,
        results_per_page: 5,
      });
      setJobs(res.data.jobs);
      fetchConversation();
    } catch (err) {
      console.error('Job search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  if (!conversationId) {
    return (
      <div className="chat-empty">
        <div className="chat-empty-content animate-fade-in">
          <div className="chat-empty-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
              <line x1="9" y1="9" x2="9.01" y2="9"/>
              <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
          </div>
          <h2>Welcome to AI Job Hunt</h2>
          <p>Select a conversation or create a new one to get started.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return <Loader message="Loading conversation..." />;
  }

  const hasResume = !!conversation?.resume_filename;

  return (
    <div className="chat-window" id="chat-window">
      {/* Messages History */}
      {conversation?.messages?.length > 0 && (
        <div className="chat-messages">
          {conversation.messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Step 1: Resume Upload */}
      {!hasResume && (
        <div className="chat-section">
          <div className="chat-section-header">
            <span className="chat-step-badge">Step 1</span>
            <h3>Upload Your Resume</h3>
            <p>Upload a PDF resume so our AI agents can analyze it.</p>
          </div>
          <ResumeUpload
            conversationId={conversationId}
            onUploadComplete={handleResumeUploaded}
          />
        </div>
      )}

      {/* Resume Uploaded Confirmation */}
      {hasResume && (
        <div className="chat-resume-info animate-fade-in">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <span>Resume loaded: <strong>{conversation.resume_filename}</strong></span>
        </div>
      )}

      {/* Step 2: Job Search */}
      {hasResume && (
        <div className="chat-section animate-fade-in">
          <div className="chat-section-header">
            <span className="chat-step-badge">Step 2</span>
            <h3>Search for Jobs</h3>
            <p>Find positions matching your skills and get hiring scores.</p>
          </div>
          <form className="chat-search-form" onSubmit={handleSearchJobs}>
            <div className="chat-search-inputs">
              <input
                type="text"
                className="input"
                placeholder="Job keyword (e.g. data analyst)"
                value={keyword}
                onChange={e => setKeyword(e.target.value)}
                id="job-keyword-input"
              />
              <input
                type="text"
                className="input"
                placeholder="Location (e.g. New York)"
                value={location}
                onChange={e => setLocation(e.target.value)}
                id="job-location-input"
              />
              <input
                type="text"
                className="input"
                placeholder="Ideal Company (e.g. startup, remote, fintech)"
                value={companyPreference}
                onChange={e => setCompanyPreference(e.target.value)}
                id="company-preference-input"
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={searching || !keyword.trim()}
              id="search-jobs-button"
            >
              {searching ? (
                <>
                  <div className="btn-spinner" />
                  Searching & Scoring...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  Search Jobs
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* Search in progress */}
      {searching && (
        <Loader
          message="Searching & scoring jobs..."
          submessage="Our AI is evaluating each job against your resume"
        />
      )}

      {/* Job Results */}
      {jobs.length > 0 && !searching && (
        <div className="chat-section">
          <div className="chat-section-header">
            <h3>Job Results ({jobs.length})</h3>
            <p>Click a job to get resume tweaks and a cover letter.</p>
          </div>
          <div className="chat-jobs-grid">
            {jobs.map((job, i) => (
              <JobCard
                key={i}
                job={job}
                index={i}
                onClick={() => setSelectedJob(job)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Job Detail Panel */}
      {selectedJob && (
        <JobDetailPanel
          job={selectedJob}
          conversationId={conversationId}
          messages={conversation?.messages || []}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </div>
  );
}
