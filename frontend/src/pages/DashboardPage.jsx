import { useState } from 'react';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import { useAuth } from '../contexts/AuthContext';
import client from '../api/client';
import './DashboardPage.css';

export default function DashboardPage() {
  const { refreshUser } = useAuth();
  const [activeConversationId, setActiveConversationId] = useState(null);

  const handleNewConversation = async () => {
    try {
      const res = await client.post('/conversations', { title: 'New Conversation' });
      setActiveConversationId(res.data.id);
      refreshUser(); // Refresh the user limits count instantly
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  return (
    <div className="dashboard-page">
      <Navbar />
      <div className="dashboard-body">
        <Sidebar
          activeId={activeConversationId}
          onSelect={setActiveConversationId}
          onNew={handleNewConversation}
        />
        <main className="dashboard-main" style={{ display: 'flex', flexDirection: 'column' }}>
          {/* ── Beta Welcome / Info Banner ──────────────────── */}
          <div className="beta-banner glass" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 20px',
            borderRadius: '12px',
            marginBottom: '20px',
            background: 'rgba(99, 102, 241, 0.05)',
            border: '1px solid rgba(99, 102, 241, 0.15)',
            fontSize: '0.88rem',
            color: '#c7d2fe',
            fontWeight: '500',
            width: '100%',
            boxSizing: 'border-box'
          }}>
            <span style={{ fontSize: '1.2rem' }}>🚀</span>
            <span>
              <strong>Welcome to the Beta version!</strong> We have pre-configured a generous amount of free interactions for each feature on this site (listed below). If you're enjoying the platform and need to upgrade your limits, just connect at <a href="mailto:ismail.taibani786@gmail.com" style={{ color: '#818cf8', textDecoration: 'underline', fontWeight: '600' }}>ismail.taibani786@gmail.com</a>.
            </span>
          </div>

          <ChatWindow conversationId={activeConversationId} />
        </main>
      </div>
    </div>
  );
}
