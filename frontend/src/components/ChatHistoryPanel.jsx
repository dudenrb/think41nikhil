// frontend/src/components/ChatHistoryPanel.jsx
import React, { useState, useEffect } from 'react';
import './ChatHistoryPanel.css'; // Component-specific CSS

/**
 * Renders a side panel displaying a list of past conversation sessions for a user.
 * Allows users to select a session to load its history into the main chat.
 *
 * @param {object} props - The component's props.
 * @param {string} props.userId - The ID of the current user.
 * @param {function(string): void} props.onSelectConversation - Callback to load a selected conversation's history.
 * @param {string | null} props.currentSessionId - The session ID of the currently active conversation.
 */
function ChatHistoryPanel({ userId, onSelectConversation, currentSessionId }) {
  const [pastConversations, setPastConversations] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [errorHistory, setErrorHistory] = useState(null);

  // useEffect to fetch past conversations when the component mounts or userId changes.
  // It also re-fetches if currentSessionId changes, to update the 'active' highlight and ensure the list is fresh.
  useEffect(() => {
    const fetchPastConversations = async () => {
      setLoadingHistory(true);
      setErrorHistory(null); // Clear previous errors
      try {
        // Fetch all conversations for the given userId from your backend
        const response = await fetch(`http://127.0.0.1:8000/api/conversations/${userId}`);

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`Failed to fetch history: ${errorData.detail || response.statusText}`);
        }

        const data = await response.json();
        // Sort conversations by creation date (most recent first)
        const sortedConversations = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setPastConversations(sortedConversations);
      } catch (error) {
        console.error("Error fetching past conversations:", error);
        setErrorHistory("Failed to load conversation history. " + error.message);
      } finally {
        setLoadingHistory(false);
      }
    };

    // Call the fetch function
    fetchPastConversations();

    // Optional: Set up an interval to periodically refresh history in a real-time app,
    // but for now, we rely on the currentSessionId dependency.
    // const interval = setInterval(fetchPastConversations, 30000); // refresh every 30 seconds
    // return () => clearInterval(interval); // Cleanup interval on unmount
  }, [userId, currentSessionId]); // Dependencies: Re-run when userId or currentSessionId changes

  return (
    <div className="chat-history-panel">
      <h3>Past Conversations</h3>

      {loadingHistory && <div className="loading-history">Loading history...</div>}
      {errorHistory && <div className="error-history">{errorHistory}</div>}

      {!loadingHistory && !errorHistory && pastConversations.length === 0 && (
        <div className="no-history-message">No past conversations found.</div>
      )}

      <ul className="conversation-list">
        {pastConversations.map((conv) => (
          <li
            key={conv.session_id} // Use session_id as a unique key for list items
            // Add 'active' class if this is the currently loaded conversation
            className={`conversation-item ${conv.session_id === currentSessionId ? 'active' : ''}`}
            onClick={() => onSelectConversation(conv.session_id)} // Call parent's callback on click
          >
            {/* Display conversation date/time */}
            <span className="conversation-date">
              {new Date(conv.created_at).toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' })}
            </span>
            {/* Display a preview of the first message's content */}
            <p className="conversation-preview">
              {conv.messages && conv.messages.length > 0
                ? conv.messages[0].content.substring(0, 50) + (conv.messages[0].content.length > 50 ? '...' : '')
                : 'Empty conversation'}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ChatHistoryPanel;