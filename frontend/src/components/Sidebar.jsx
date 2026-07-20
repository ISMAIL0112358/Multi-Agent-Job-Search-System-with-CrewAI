import { useState, useEffect } from 'react';
import client from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import './Sidebar.css';

export default function Sidebar({ activeId, onSelect, onNew }) {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchConversations = async () => {
    try {
      const res = await client.get('/conversations');
      setConversations(res.data);
    } catch (err) {
      console.error('Failed to fetch conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [activeId]);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    try {
      await client.delete(`/conversations/${id}`);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeId === id) onSelect(null);
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  };

  return (
    <aside className="sidebar" id="sidebar">
      <div className="sidebar-header">
        <h2 className="sidebar-title">
          Conversations{' '}
          <span style={{ fontSize: '0.8rem', opacity: 0.6, fontWeight: 'normal' }}>
            ({user?.conversations_count || 0} / {user?.max_conversations || 10} used)
          </span>
        </h2>
        <button className="btn btn-primary sidebar-new-btn" onClick={onNew} id="new-conversation-button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New
        </button>
      </div>

      <div className="sidebar-list">
        {loading ? (
          <div className="sidebar-loading">
            {[1, 2, 3].map(i => (
              <div key={i} className="sidebar-skeleton" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="sidebar-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <p>No conversations yet</p>
            <span>Start a new search!</span>
          </div>
        ) : (
          conversations.map((convo, index) => (
            <div
              key={convo.id}
              className={`sidebar-item ${activeId === convo.id ? 'active' : ''}`}
              onClick={() => onSelect(convo.id)}
              style={{ animationDelay: `${index * 50}ms` }}
              id={`conversation-${convo.id}`}
            >
              <div className="sidebar-item-content">
                <span className="sidebar-item-title">{convo.title}</span>
                <span className="sidebar-item-meta">
                  {convo.resume_filename && (
                    <span className="sidebar-item-badge">📄 Resume</span>
                  )}
                  {formatDate(convo.updated_at)}
                </span>
              </div>
              <button
                className="sidebar-item-delete"
                onClick={(e) => handleDelete(e, convo.id)}
                title="Delete conversation"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
