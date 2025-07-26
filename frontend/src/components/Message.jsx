// frontend/src/components/Message.jsx
import React from 'react';
// Note: No specific CSS file imported here.
// The styles for Message are defined in MessageList.css
// because MessageList is responsible for arranging and styling messages.
// This decision can be changed based on project scale and preference.

/**
 * Renders a single chat message.
 * @param {object} props - The component's props.
 * @param {'user' | 'assistant'} props.role - The role of the sender ('user' or 'assistant').
 * @param {string} props.content - The text content of the message.
 * @param {Date | string} props.timestamp - The timestamp of the message. Can be a Date object or an ISO string.
 */
function Message({ role, content, timestamp }) {
  // Format the timestamp for display
  const formattedTime = timestamp instanceof Date
    ? timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    : new Date(timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  return (
    // The class names 'message' and either 'user' or 'assistant' are used for styling.
    <div className={`message ${role}`}>
      <p>{content}</p> {/* Display the message content */}
      {/* Display timestamp if available */}
      {timestamp && <span className="timestamp">{formattedTime}</span>}
    </div>
  );
}

export default Message;