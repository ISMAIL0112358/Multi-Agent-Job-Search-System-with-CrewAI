import ReactMarkdown from 'react-markdown';
import './MessageBubble.css';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

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
