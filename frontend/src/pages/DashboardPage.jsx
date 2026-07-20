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
        <main className="dashboard-main">
          <ChatWindow conversationId={activeConversationId} />
        </main>
      </div>
    </div>
  );
}
