import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar';
import CandidateCard from '../components/hr/CandidateCard';
import JDForm from '../components/hr/JDForm';
import ScreeningResultCard from '../components/hr/ScreeningResultCard';
import StatusBadge from '../components/hr/StatusBadge';
import Loader from '../components/Loader';
import client from '../api/client';
import './HRDashboardPage.css';

export default function HRDashboardPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('candidates');
  const [stats, setStats] = useState({ total_candidates: 0, open_positions: 0, shortlisted: 0, hired: 0 });

  // Candidates state
  const [candidates, setCandidates] = useState([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // JD state
  const [jds, setJds] = useState([]);
  const [jdsLoading, setJdsLoading] = useState(false);
  const [jdCreating, setJdCreating] = useState(false);

  // Screening state
  const [selectedJdId, setSelectedJdId] = useState(null);
  const [screeningResults, setScreeningResults] = useState([]);
  const [screeningLoading, setScreeningLoading] = useState(false);
  const [topN, setTopN] = useState(10);
  const [vettingLoading, setVettingLoading] = useState({});

  // ── Fetch data ──────────────────────────────────────────────

  const fetchStats = useCallback(async () => {
    try {
      const res = await client.get('/hr/dashboard');
      setStats(res.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  const fetchCandidates = useCallback(async () => {
    setCandidatesLoading(true);
    try {
      const res = await client.get('/hr/candidates');
      setCandidates(res.data);
    } catch (err) {
      console.error('Failed to fetch candidates:', err);
    } finally {
      setCandidatesLoading(false);
    }
  }, []);

  const fetchJDs = useCallback(async () => {
    setJdsLoading(true);
    try {
      const res = await client.get('/hr/job-descriptions');
      setJds(res.data);
    } catch (err) {
      console.error('Failed to fetch JDs:', err);
    } finally {
      setJdsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchCandidates();
    fetchJDs();
  }, [fetchStats, fetchCandidates, fetchJDs]);

  // ── Candidate Actions ──────────────────────────────────────

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach((f) => formData.append('files', f));
      await client.post('/hr/candidates/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      fetchCandidates();
      fetchStats();
    } catch (err) {
      console.error('Upload failed:', err);
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleStatusChange = async (candidateId, newStatus) => {
    try {
      await client.patch(`/hr/candidates/${candidateId}/status`, { status: newStatus });
      setCandidates((prev) =>
        prev.map((c) => (c.id === candidateId ? { ...c, status: newStatus } : c))
      );
      // Also update screening results if they reference this candidate
      setScreeningResults((prev) =>
        prev.map((r) =>
          r.candidate.id === candidateId
            ? { ...r, candidate: { ...r.candidate, status: newStatus } }
            : r
        )
      );
      fetchStats();
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const handleDeleteCandidate = async (candidateId) => {
    if (!confirm('Delete this candidate permanently?')) return;
    try {
      await client.delete(`/hr/candidates/${candidateId}`);
      setCandidates((prev) => prev.filter((c) => c.id !== candidateId));
      fetchStats();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  // ── JD Actions ──────────────────────────────────────────────

  const handleCreateJD = async (data) => {
    setJdCreating(true);
    try {
      await client.post('/hr/job-descriptions', data);
      fetchJDs();
      fetchStats();
    } catch (err) {
      console.error('JD creation failed:', err);
      alert(err.response?.data?.detail || 'Failed to create JD');
    } finally {
      setJdCreating(false);
    }
  };

  const handleCloseJD = async (jdId) => {
    try {
      await client.patch(`/hr/job-descriptions/${jdId}`, { status: 'closed' });
      setJds((prev) => prev.map((j) => (j.id === jdId ? { ...j, status: 'closed' } : j)));
      fetchStats();
    } catch (err) {
      console.error('Close JD failed:', err);
    }
  };

  const handleDeleteJD = async (jdId) => {
    if (!confirm('Delete this Job Description and its screening results?')) return;
    try {
      await client.delete(`/hr/job-descriptions/${jdId}`);
      setJds((prev) => prev.filter((j) => j.id !== jdId));
      if (selectedJdId === jdId) {
        setSelectedJdId(null);
        setScreeningResults([]);
      }
      fetchStats();
    } catch (err) {
      console.error('Delete JD failed:', err);
    }
  };

  // ── Screening Actions ──────────────────────────────────────

  const handleScreenCandidates = async (jdId) => {
    setSelectedJdId(jdId);
    setScreeningLoading(true);
    setActiveTab('screening');
    try {
      const res = await client.post('/hr/screen', {
        job_description_id: jdId,
        top_n: topN,
      });
      setScreeningResults(res.data);
    } catch (err) {
      console.error('Screening failed:', err);
      alert(err.response?.data?.detail || 'Screening failed');
    } finally {
      setScreeningLoading(false);
    }
  };

  const handleLoadResults = async (jdId) => {
    setSelectedJdId(jdId);
    setScreeningLoading(true);
    setActiveTab('screening');
    try {
      const res = await client.get(`/hr/screening-results/${jdId}`);
      setScreeningResults(res.data);
    } catch (err) {
      console.error('Failed to load results:', err);
    } finally {
      setScreeningLoading(false);
    }
  };

  const handleGenerateVetting = async (candidateId) => {
    if (!selectedJdId) return;
    setVettingLoading((prev) => ({ ...prev, [candidateId]: true }));
    try {
      const res = await client.post('/hr/vetting-questions', {
        candidate_id: candidateId,
        job_description_id: selectedJdId,
      });
      setScreeningResults((prev) =>
        prev.map((r) =>
          r.candidate.id === candidateId
            ? { ...r, vetting_questions: res.data }
            : r
        )
      );
    } catch (err) {
      console.error('Vetting generation failed:', err);
    } finally {
      setVettingLoading((prev) => ({ ...prev, [candidateId]: false }));
    }
  };

  // ── Drag & Drop handlers ──────────────────────────────────

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFileUpload(e.dataTransfer.files);
  };

  // ── Fuzzy Search ──────────────────────────────────────────

  const fuzzyMatch = useCallback((text, query) => {
    if (!query) return 1;
    const t = text.toLowerCase();
    const q = query.toLowerCase();

    // Exact substring match → highest score
    if (t.includes(q)) return 1;

    // Fuzzy: walk through query chars in order within text
    let score = 0;
    let qi = 0;
    let lastMatchIdx = -1;
    for (let ti = 0; ti < t.length && qi < q.length; ti++) {
      if (t[ti] === q[qi]) {
        score += 1;
        // Bonus for consecutive matches
        if (lastMatchIdx === ti - 1) score += 0.5;
        // Bonus for match at word boundary
        if (ti === 0 || t[ti - 1] === ' ' || t[ti - 1] === '-' || t[ti - 1] === '_') score += 0.3;
        lastMatchIdx = ti;
        qi++;
      }
    }

    // All query chars must be found in order
    if (qi < q.length) return 0;
    return score / q.length;
  }, []);

  const filteredCandidates = useMemo(() => {
    if (!searchQuery.trim()) return candidates;

    const q = searchQuery.trim();
    const scored = candidates.map((c) => {
      const fields = [
        c.name || '',
        c.email || '',
        c.phone || '',
        c.status || '',
        c.resume_filename || '',
      ];
      const best = Math.max(...fields.map((f) => fuzzyMatch(f, q)));
      return { candidate: c, score: best };
    });

    return scored
      .filter((s) => s.score > 0.3)
      .sort((a, b) => b.score - a.score)
      .map((s) => s.candidate);
  }, [candidates, searchQuery, fuzzyMatch]);

  // ── Render ─────────────────────────────────────────────────

  const selectedJd = jds.find((j) => j.id === selectedJdId);

  return (
    <div className="hr-dashboard">
      <div className="bg-ambient" />
      <Navbar />
      <div className="hr-dashboard__content">
        {/* ── Stats Header ──────────────────── */}
        <div className="hr-stats">
          <div className="hr-stat-card glass">
            <span className="hr-stat-icon">👥</span>
            <div className="hr-stat-info">
              <span className="hr-stat-value">{stats.total_candidates}</span>
              <span className="hr-stat-label">Candidates</span>
            </div>
          </div>
          <div className="hr-stat-card glass">
            <span className="hr-stat-icon">📋</span>
            <div className="hr-stat-info">
              <span className="hr-stat-value">{stats.open_positions}</span>
              <span className="hr-stat-label">Open Positions</span>
            </div>
          </div>
          <div className="hr-stat-card glass">
            <span className="hr-stat-icon">⭐</span>
            <div className="hr-stat-info">
              <span className="hr-stat-value">{stats.shortlisted}</span>
              <span className="hr-stat-label">Shortlisted</span>
            </div>
          </div>
          <div className="hr-stat-card glass">
            <span className="hr-stat-icon">✅</span>
            <div className="hr-stat-info">
              <span className="hr-stat-value">{stats.hired}</span>
              <span className="hr-stat-label">Hired</span>
            </div>
          </div>
        </div>

        {/* ── Tab Navigation ──────────────── */}
        <div className="hr-tabs">
          <button
            className={`hr-tab ${activeTab === 'candidates' ? 'active' : ''}`}
            onClick={() => setActiveTab('candidates')}
            id="tab-candidates"
          >
            👥 Candidates
          </button>
          <button
            className={`hr-tab ${activeTab === 'jds' ? 'active' : ''}`}
            onClick={() => setActiveTab('jds')}
            id="tab-jds"
          >
            📋 Job Descriptions
          </button>
          <button
            className={`hr-tab ${activeTab === 'screening' ? 'active' : ''}`}
            onClick={() => setActiveTab('screening')}
            id="tab-screening"
          >
            🎯 Screening Results
          </button>
        </div>

        {/* ════════════════════════════════════ */}
        {/* TAB: Candidates                      */}
        {/* ════════════════════════════════════ */}
        {activeTab === 'candidates' && (
          <div className="hr-tab-content animate-fade-in">
            {/* Upload Zone */}
            <div
              className={`upload-zone glass ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              id="resume-upload-zone"
            >
              <div className="upload-zone__content">
                {uploading ? (
                  <>
                    <div className="upload-zone__spinner" />
                    <p>Uploading & processing resumes...</p>
                  </>
                ) : (
                  <>
                    <span className="upload-zone__icon">📄</span>
                    <p>Drag & drop resumes here, or</p>
                    <label className="btn btn-primary upload-zone__btn" htmlFor="file-input-upload">
                      Browse Files
                    </label>
                    <input
                      id="file-input-upload"
                      type="file"
                      accept=".pdf,.xlsx,.xls,.csv"
                      multiple
                      style={{ display: 'none' }}
                      onChange={(e) => handleFileUpload(e.target.files)}
                    />
                    <span className="upload-zone__hint">Supports PDF, Excel (.xlsx/.xls), and CSV • Bulk upload supported</span>
                  </>
                )}
              </div>
            </div>

            {/* Search Bar */}
            {candidates.length > 0 && (
              <div className="candidate-search glass" id="candidate-search">
                <div className="candidate-search__input-wrap">
                  <svg className="candidate-search__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  <input
                    className="candidate-search__input"
                    type="text"
                    placeholder="Search candidates by name, email, phone, status..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    id="candidate-search-input"
                  />
                  {searchQuery && (
                    <button
                      className="candidate-search__clear"
                      onClick={() => setSearchQuery('')}
                      id="candidate-search-clear"
                    >
                      ✕
                    </button>
                  )}
                </div>
                {searchQuery && (
                  <span className="candidate-search__count">
                    {filteredCandidates.length} of {candidates.length} candidate{candidates.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            )}

            {/* Candidate Grid */}
            {candidatesLoading ? (
              <Loader message="Loading candidates..." />
            ) : candidates.length === 0 ? (
              <div className="hr-empty-state">
                <span className="hr-empty-icon">📭</span>
                <p>No candidates yet. Upload resumes to get started.</p>
              </div>
            ) : filteredCandidates.length === 0 ? (
              <div className="hr-empty-state">
                <span className="hr-empty-icon">🔍</span>
                <p>No candidates match "{searchQuery}". Try a different search.</p>
              </div>
            ) : (
              <div className="candidates-grid">
                {filteredCandidates.map((c) => (
                  <CandidateCard
                    key={c.id}
                    candidate={c}
                    onStatusChange={handleStatusChange}
                    onDelete={handleDeleteCandidate}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════ */}
        {/* TAB: Job Descriptions                */}
        {/* ════════════════════════════════════ */}
        {activeTab === 'jds' && (
          <div className="hr-tab-content animate-fade-in">
            <JDForm onSubmit={handleCreateJD} loading={jdCreating} />

            {jdsLoading ? (
              <Loader message="Loading job descriptions..." />
            ) : jds.length === 0 ? (
              <div className="hr-empty-state">
                <span className="hr-empty-icon">📝</span>
                <p>No job descriptions yet. Create one above.</p>
              </div>
            ) : (
              <div className="jd-list">
                {jds.map((jd) => (
                  <div key={jd.id} className="jd-card card" id={`jd-card-${jd.id}`}>
                    <div className="jd-card__header">
                      <div className="jd-card__title-row">
                        <h3 className="jd-card__title">{jd.title}</h3>
                        <StatusBadge status={jd.status} />
                      </div>
                      {jd.department && (
                        <span className="jd-card__dept">{jd.department}</span>
                      )}
                    </div>
                    <p className="jd-card__desc">{jd.description.substring(0, 200)}...</p>
                    <div className="jd-card__actions">
                      <button
                        className="btn btn-primary"
                        onClick={() => handleScreenCandidates(jd.id)}
                        disabled={jd.status === 'closed' || candidates.length === 0}
                        id={`screen-btn-${jd.id}`}
                      >
                        🎯 Screen Candidates
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleLoadResults(jd.id)}
                        id={`load-results-${jd.id}`}
                      >
                        📊 View Results
                      </button>
                      {jd.status === 'open' && (
                        <button
                          className="btn btn-ghost"
                          onClick={() => handleCloseJD(jd.id)}
                          id={`close-jd-${jd.id}`}
                        >
                          Close Position
                        </button>
                      )}
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteJD(jd.id)}
                        id={`delete-jd-${jd.id}`}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════ */}
        {/* TAB: Screening Results               */}
        {/* ════════════════════════════════════ */}
        {activeTab === 'screening' && (
          <div className="hr-tab-content animate-fade-in">
            {/* JD selector + Top-N control */}
            <div className="screening-controls glass">
              <div className="screening-controls__jd-select">
                <label>Job Description</label>
                <select
                  className="input"
                  value={selectedJdId || ''}
                  onChange={(e) => {
                    if (e.target.value) handleLoadResults(e.target.value);
                  }}
                  id="screening-jd-select"
                >
                  <option value="">Select a Job Description...</option>
                  {jds.map((jd) => (
                    <option key={jd.id} value={jd.id}>
                      {jd.title} {jd.status === 'closed' ? '(Closed)' : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div className="screening-controls__topn">
                <label>Top N</label>
                <input
                  className="input"
                  type="number"
                  min={1}
                  max={50}
                  value={topN}
                  onChange={(e) => setTopN(parseInt(e.target.value) || 10)}
                  id="screening-topn-input"
                />
              </div>
              <button
                className="btn btn-primary"
                onClick={() => selectedJdId && handleScreenCandidates(selectedJdId)}
                disabled={!selectedJdId || screeningLoading}
                id="run-screening-btn"
              >
                {screeningLoading ? (
                  <><span className="spinner" /> Screening...</>
                ) : (
                  '🔄 Re-Screen'
                )}
              </button>
            </div>

            {/* Results */}
            {screeningLoading ? (
              <Loader message="AI is screening candidates... This may take a moment." />
            ) : screeningResults.length === 0 ? (
              <div className="hr-empty-state">
                <span className="hr-empty-icon">🎯</span>
                <p>
                  {selectedJdId
                    ? 'No screening results yet. Click "Screen Candidates" on a Job Description.'
                    : 'Select a Job Description to view or run screening.'}
                </p>
              </div>
            ) : (
              <div className="screening-results-list">
                {selectedJd && (
                  <div className="screening-results__header">
                    <h2>Results for: {selectedJd.title}</h2>
                    <span className="screening-results__count">
                      {screeningResults.length} candidate{screeningResults.length !== 1 ? 's' : ''} matched
                    </span>
                  </div>
                )}
                {screeningResults.map((result) => (
                  <ScreeningResultCard
                    key={result.id}
                    result={result}
                    onStatusChange={handleStatusChange}
                    onGenerateVetting={handleGenerateVetting}
                    vettingLoading={vettingLoading[result.candidate.id] || false}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
