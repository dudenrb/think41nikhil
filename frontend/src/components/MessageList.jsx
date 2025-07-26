// frontend/src/components/MessageList.jsx
import React, { useRef, useEffect } from 'react';
import Message from './Message'; // Import the Message component
import './MessageList.css'; // Component-specific CSS for MessageList and Message styling

/**
 * Renders a scrollable list of chat messages.
 * @param {object} props - The component's props.
 * @param {Array<object>} props.messages - An array of message objects to display.
 * @param {boolean} props.loading - Boolean indicating if an AI response is currently being fetched.
 */
function MessageList({ messages, loading }) {
  // useRef hook to get a direct reference to the last element in the message list
  const messagesEndRef = useRef(null);

  // useEffect hook to scroll to the bottom of the chat when messages or loading state changes.
  // This ensures the latest message or loading indicator is always in view.
  useEffect(() => {
    // `scrollIntoView` method smoothly scrolls the element into the visible area of the browser window.
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]); // Dependencies: re-run effect when `messages` or `loading` changes.

  return (
    <div className="message-list">
      {/* Display a welcome/empty chat message if no messages and not loading */}
      {messages.length === 0 && !loading && (
        <div className="empty-chat-message">
          Start a conversation! Type your question below.
        </div>
      )}
      {/* Map through the messages array and render a Message component for each */}
      {messages.map((msg, index) => (
        // `key` prop is crucial for React's list rendering efficiency.
        // Using `index` as key is acceptable here since messages don't change order or get deleted.
        <Message key={index} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
      ))}
      {/* Display a 'Thinking...' loading indicator when `loading` is true */}
      {loading && (
        <div className="message assistant loading">
          <p>Thinking...</p>
          <span className="timestamp"></span> {/* Placeholder for timestamp when thinking */}
        </div>
      )}
      {/* Invisible div that the `messagesEndRef` points to, ensuring auto-scroll to the very bottom */}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;