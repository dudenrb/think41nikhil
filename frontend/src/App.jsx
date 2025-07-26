// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import MessageList from './components/MessageList';
import UserInput from './components/UserInput';
import ChatHistoryPanel from './components/ChatHistoryPanel'; // Import the new history panel
import './App.css'; // Main App CSS

// A static user ID for this frontend. In a real app, this would come from a login system.
const USER_ID = "frontend_user_react_123";

function App() {
  // State for the list of messages in the current conversation
  const [messages, setMessages] = useState([]);
  // State to indicate if an API call is in progress (for chat or history loading)
  const [loading, setLoading] = useState(false);
  // State to store the ID of the currently active conversation session
  const [currentSessionId, setCurrentSessionId] = useState(null);
  // State to control visibility of the history panel (Milestone 8)
  const [showHistoryPanel, setShowHistoryPanel] = useState(true); // Start visible for testing, change to false later

  // useEffect to initialize chat with a welcome message or load initial history.
  useEffect(() => {
      // Only add initial message if no messages are present and not already loading.
      if (messages.length === 0 && !loading && !currentSessionId) {
          setMessages([
              { role: 'assistant', content: "Hello! I'm ShopAssist, your e-commerce chatbot. How can I help you today?", timestamp: new Date() }
          ]);
      }
  }, [messages, loading, currentSessionId]); // Depend on these to prevent re-adding

  /**
   * Handles sending a user message to the backend.
   * Updates local state (messages, loading) and performs the API call.
   * @param {string} userMessageContent - The text content of the user's message.
   */
  const handleSendMessage = async (userMessageContent) => {
    if (!userMessageContent.trim() || loading) {
      return;
    }

    // Add user's message to local state immediately
    const newUserMessage = {
      role: 'user',
      content: userMessageContent,
      timestamp: new Date(),
    };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setLoading(true);

    try {
      const payload = {
        user_id: USER_ID,
        message: userMessageContent,
        session_id: currentSessionId, // Pass the current session ID
      };

      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Backend error: ${errorData.detail || response.statusText}`);
      }

      const data = await response.json();
      console.log("Backend response for chat:", data);

      setCurrentSessionId(data.session_id); // Update current session ID from backend

      // Update messages state with the full conversation history from backend
      setMessages(data.conversation_history.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp) // Convert ISO string to Date object
      })));

    } catch (error) {
      console.error('Error sending message or processing response:', error);
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: 'assistant',
          content: 'Oops! Something went wrong while getting my response. Please try again. ' + (error.message || ''),
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Loads a past conversation session into the main chat window.
   * @param {string} sessionId - The session ID of the conversation to load.
   */
  const loadPastConversation = async (sessionId) => {
    if (loading || sessionId === currentSessionId) return; // Prevent loading if already loading or same session

    setLoading(true);
    // Clear current messages and add a loading indicator
    setMessages([{ role: 'assistant', content: "Loading past conversation...", timestamp: new Date() }]);

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/conversation/${sessionId}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to load conversation: ${errorData.detail || response.statusText}`);
      }
      const data = await response.json();
      console.log("Loaded past conversation:", data);

      // Update messages with the loaded history
      setMessages(data.messages.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      })));
      setCurrentSessionId(data.session_id); // Set the loaded session as current
      setShowHistoryPanel(false); // Optionally hide panel after loading a session

    } catch (error) {
      console.error('Error loading past conversation:', error);
      setMessages((prevMessages) => [
        ...prevMessages.filter(msg => msg.content !== "Loading past conversation..."), // Remove temp loading msg
        {
          role: 'assistant',
          content: 'Failed to load past conversation: ' + (error.message || 'Unknown error'),
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="chat-window">
      <div className="chat-header">
        <h1>ShopAssist Chatbot</h1>
        {/* Toggle button for the history panel */}
        <button className="history-toggle-btn" onClick={() => setShowHistoryPanel(!showHistoryPanel)}>
          {showHistoryPanel ? 'Hide History' : 'Show History'}
        </button>
      </div>

      <div className="chat-content">
        {/* Conditionally render ChatHistoryPanel based on showHistoryPanel state */}
        {showHistoryPanel && (
          <ChatHistoryPanel 
            userId={USER_ID} 
            onSelectConversation={loadPastConversation} 
            currentSessionId={currentSessionId}
          />
        )}

        {/* MessageList component displays the conversation history */}
        <MessageList messages={messages} loading={loading} />
      </div>

      <UserInput onSendMessage={handleSendMessage} loading={loading} />
    </div>
  );
}

export default App;