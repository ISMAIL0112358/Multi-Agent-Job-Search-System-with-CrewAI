import ReactMarkdown from 'react-markdown';
import './MessageBubble.css';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (message.metadata_?.type === 'job_analysis') {
    const jobTitle = message.metadata_?.job_title || 'Position';
    return (
      <div className="message-bubble assistant animate-fade-in">
        <div className="message-bubble-avatar">🤖</div>
        <div className="message-bubble-content">
          <p>✨ <strong>AI Analysis Ready: {jobTitle}</strong></p>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
            Resume tweaks, cover letter, company profile, and interview prep have been generated. Click on the job card to view the complete details.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`message-bubble ${message.role} animate-fade-in`}>
      <div className="message-bubble-avatar">
        {isUser ? '👤' : isSystem ? '⚙️' : '🤖'}
      </div>
      <div className="message-bubble-content">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
    </div>
  );
}
