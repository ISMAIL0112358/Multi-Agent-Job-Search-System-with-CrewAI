import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../contexts/AuthContext';
import client from '../api/client';
import './ProfilePage.css';

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();

  // Personal Info State
  const [name, setName] = useState(user?.name || '');
  const [pictureUrl, setPictureUrl] = useState(user?.picture_url || '');
  const [skillsTags, setSkillsTags] = useState(user?.skills ? user.skills.split(',').map(s => s.trim()).filter(s => s) : []);
  const [skillInput, setSkillInput] = useState('');
  const [savingInfo, setSavingInfo] = useState(false);
  const [infoMessage, setInfoMessage] = useState(null);

  // Resumes State
  const [resumes, setResumes] = useState([]);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [resumeError, setResumeError] = useState(null);

  useEffect(() => {
    if (user?.role === 'hr') {
      navigate('/hr', { replace: true });
      return;
    }
    fetchResumes();
  }, [user, navigate]);

  const fetchResumes = async () => {
    setLoadingResumes(true);
    try {
      const res = await client.get('/user-resumes');
      setResumes(res.data);
    } catch (err) {
      console.error('Failed to load resumes:', err);
    } finally {
      setLoadingResumes(false);
    }
  };

  const handleSaveInfo = async (e) => {
    e.preventDefault();
    setSavingInfo(true);
    setInfoMessage(null);
    try {
      const skills = skillsTags.join(', ');
      await updateUser({ name, picture_url: pictureUrl, skills });
      setInfoMessage({ type: 'success', text: 'Profile updated successfully!' });
    } catch (err) {
      console.error(err);
      setInfoMessage({ type: 'error', text: 'Failed to update profile.' });
    } finally {
      setSavingInfo(false);
    }
  };

  const handleSkillKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const newSkill = skillInput.trim();
      if (newSkill && !skillsTags.includes(newSkill)) {
        setSkillsTags([...skillsTags, newSkill]);
      }
      setSkillInput('');
    } else if (e.key === 'Backspace' && !skillInput && skillsTags.length > 0) {
      setSkillsTags(skillsTags.slice(0, -1));
    }
  };

  const removeSkillTag = (indexToRemove) => {
    setSkillsTags(skillsTags.filter((_, idx) => idx !== indexToRemove));
  };

  const onDropResume = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploadingResume(true);
    setResumeError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await client.post('/user-resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchResumes();
    } catch (err) {
      setResumeError(err.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setUploadingResume(false);
    }
  }, []);

  const handleDeleteResume = async (filename) => {
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;
    
    try {
      await client.delete(`/user-resumes/${encodeURIComponent(filename)}`);
      fetchResumes();
    } catch (err) {
      console.error('Failed to delete resume:', err);
      setResumeError(err.response?.data?.detail || 'Failed to delete resume');
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onDropResume,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploadingResume,
  });

  return (
    <div className="profile-page">
      <Navbar />
      <div className="profile-body">
        <div className="profile-container glass animate-fade-in">
          <div className="profile-header">
            <button className="btn btn-ghost profile-back-btn" onClick={() => navigate(-1)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              Back
            </button>
            <h1 className="profile-title">Profile & Resume Management</h1>
          </div>

          <div className="profile-content">
            {/* Personal Info Section */}
            <section className="profile-section">
              <h2>Personal Information</h2>
              <form onSubmit={handleSaveInfo} className="profile-form">
                <div className="form-group">
                  <label>Name</label>
                  <input 
                    type="text" 
                    className="input" 
                    value={name} 
                    onChange={e => setName(e.target.value)} 
                    required 
                  />
                </div>
                
                <div className="form-group">
                  <label>Profile Image URL</label>
                  <input 
                    type="url" 
                    className="input" 
                    value={pictureUrl} 
                    onChange={e => setPictureUrl(e.target.value)} 
                    placeholder="https://example.com/avatar.jpg"
                  />
                </div>

                <div className="form-group">
                  <label>Skills</label>
                  <div className="skills-tags-container input">
                    {skillsTags.map((tag, idx) => (
                      <span key={idx} className="skill-tag">
                        {tag}
                        <button type="button" className="skill-tag-remove" onClick={() => removeSkillTag(idx)}>
                          &times;
                        </button>
                      </span>
                    ))}
                    <input 
                      type="text" 
                      className="skill-tag-input" 
                      value={skillInput} 
                      onChange={e => setSkillInput(e.target.value)} 
                      onKeyDown={handleSkillKeyDown}
                      placeholder={skillsTags.length === 0 ? "Type a skill and press Enter..." : ""}
                    />
                  </div>
                  <small className="form-hint">Press Enter or comma to add a skill. Our AI will refer to these skills when tweaking your resume.</small>
                </div>

                {infoMessage && (
                  <div className={`profile-message ${infoMessage.type}`}>
                    {infoMessage.text}
                  </div>
                )}

                <div className="profile-actions">
                  <button type="submit" className="btn btn-primary" disabled={savingInfo}>
                    {savingInfo ? 'Saving...' : 'Save Info'}
                  </button>
                </div>
              </form>
            </section>

            {/* Resume Management Section */}
            <section className="profile-section">
              <h2>My Resumes</h2>
              
              <div className="profile-resumes-list">
                {loadingResumes ? (
                  <p className="profile-muted">Loading resumes...</p>
                ) : resumes.length === 0 ? (
                  <p className="profile-muted">No resumes uploaded yet.</p>
                ) : (
                  <ul>
                    {resumes.map((doc, idx) => (
                      <li key={idx} className="profile-resume-item">
                        <svg className="profile-resume-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                          <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        <span className="profile-resume-name">{doc.filename}</span>
                        <span className="profile-resume-date">
                          {new Date(doc.modified).toLocaleDateString()}
                        </span>
                        <button 
                          className="btn btn-ghost profile-resume-delete" 
                          onClick={() => handleDeleteResume(doc.filename)}
                          title="Delete resume"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 6h18"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                          </svg>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div
                {...getRootProps()}
                className={`profile-dropzone ${isDragActive ? 'dragging' : ''} ${uploadingResume ? 'uploading' : ''}`}
              >
                <input {...getInputProps()} />
                {uploadingResume ? (
                  <div className="profile-dropzone-status">
                    <div className="profile-spinner" />
                    <p>Uploading and analyzing PDF...</p>
                  </div>
                ) : (
                  <>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ marginBottom: '8px', color: 'var(--color-primary)' }}>
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    <p>{isDragActive ? 'Drop new resume here...' : 'Drag & drop a new resume PDF here'}</p>
                    <span className="profile-dropzone-hint">or click to browse</span>
                  </>
                )}
              </div>
              
              {resumeError && <div className="profile-error">{resumeError}</div>}
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
