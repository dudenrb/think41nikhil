// frontend/src/components/MessageList.jsx
import React, { useRef, useEffect } from 'react';
import Message from './Message';
import './MessageList.css';

function MessageList({ messages, loading }) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="message-list">
      {messages.length === 0 && !loading && (
        <div className="empty-chat-message">
          Start a conversation! Type your question below.
        </div>
      )}
      {messages.map((msg, index) => (
        <Message key={index} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
      ))}
      {loading && (
        <div className="message assistant loading">
          <p>Thinking...</p>
          <span className="timestamp"></span>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;