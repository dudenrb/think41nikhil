// frontend/src/App.jsx
import React, { useState, useEffect } from 'react'; // Import useEffect for side effects
import MessageList from './components/MessageList';
import UserInput from './components/UserInput';
// Import ChatHistoryPanel here if you want to keep the M8 placeholder,
// otherwise, we can add it back when we reach Milestone 8 specifically.
// import ChatHistoryPanel from './components/ChatHistoryPanel';
import './App.css';

// A static user ID for this frontend. In a real app, this would come from a login system.
// This is important as your backend links conversations to user_id.
const USER_ID = "frontend_user_react_123";

function App() {
  // Milestone 7: Client-Side State Management Implementation

  // State for the list of messages in the current conversation
  // Each message object will have { role: 'user' | 'assistant', content: string, timestamp: Date }
  const [messages, setMessages] = useState([]);

  // State to indicate if an API call is in progress (e.g., waiting for AI response)
  const [loading, setLoading] = useState(false);

  // State to store the ID of the currently active conversation session.
  // This is crucial for maintaining context with the backend.
  const [currentSessionId, setCurrentSessionId] = useState(null);

  // (Placeholder for Milestone 8) State to control visibility of the history panel
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);

  // useEffect to initialize chat or load default history (optional for initial load)
  // For a fresh start, you might just want an initial assistant message
  useEffect(() => {
      // Add an initial welcome message from the assistant when the component mounts
      // This ensures a greeting even before the first user message.
      if (messages.length === 0 && !loading) {
          setMessages([
              { role: 'assistant', content: "Hello! I'm ShopAssist, your e-commerce chatbot. How can I help you today?", timestamp: new Date() }
          ]);
      }
  }, []); // Empty dependency array means this effect runs only once after the initial render

  /**
   * Handles sending a user message to the backend.
   * Updates local state (messages, loading) and performs the API call.
   * @param {string} userMessageContent - The text content of the user's message.
   */
  const handleSendMessage = async (userMessageContent) => {
    // Prevent sending empty messages or multiple messages while loading
    if (!userMessageContent.trim() || loading) {
      return;
    }

    // 1. Add user's message to local state immediately for instant feedback
    const newUserMessage = {
      role: 'user',
      content: userMessageContent,
      timestamp: new Date(), // Use Date object for easier formatting later
    };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setLoading(true); // Set loading state to true (disables input/button)

    try {
      // Prepare the payload for the backend API call
      const payload = {
        user_id: USER_ID,
        message: userMessageContent,
        session_id: currentSessionId, // Pass the current session ID (null for new session)
      };

      // Make the POST request to your FastAPI backend
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        // If the HTTP response is not OK (e.g., 400, 500), throw an error
        const errorData = await response.json(); // Try to parse error details
        throw new Error(`Backend error: ${errorData.detail || response.statusText}`);
      }

      const data = await response.json();
      console.log("Backend response for chat:", data);

      // 2. Update current session ID with the one received from the backend
      // This is essential for subsequent messages to continue the same conversation.
      if (data.session_id) {
        setCurrentSessionId(data.session_id);
      }

      // 3. Update the messages state with the full conversation history from the backend.
      // This ensures that our frontend state is always synchronized with the backend's record,
      // including backend-generated timestamps for assistant messages.
      // Convert timestamp strings from backend to Date objects for consistent handling.
      setMessages(data.conversation_history.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      })));

    } catch (error) {
      console.error('Error sending message or processing response:', error);
      // 4. Add an error message to the chat history if something goes wrong
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: 'assistant',
          content: 'Oops! Something went wrong while getting my response. Please try again. ' + (error.message || ''),
          timestamp: new Date(),
        },
      ]);
    } finally {
      // 5. Always set loading state back to false after the API call completes
      setLoading(false);
    }
  };

  // (Placeholder for Milestone 8) Function to load a past conversation
  const loadPastConversation = (sessionId) => {
    // This function will be fully implemented in Milestone 8.
    console.log("Loading past conversation (M7 placeholder):", sessionId);
    // For now, reset messages and loading state to simulate.
    setMessages([
        { role: 'assistant', content: `Simulating load of session ${sessionId}.`, timestamp: new Date() }
    ]);
    setCurrentSessionId(sessionId);
    setShowHistoryPanel(false); // Hide panel after "loading"
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h1>ShopAssist Chatbot</h1>
        {/* History toggle button placeholder (for Milestone 8) */}
        <button className="history-toggle-btn" /* onClick={() => setShowHistoryPanel(!showHistoryPanel)} */>
          {showHistoryPanel ? 'Hide History' : 'Show History'}
        </button>
      </div>

      <div className="chat-content">
        {/* ChatHistoryPanel placeholder for Milestone 8 */}
        {/* {showHistoryPanel && (
          <ChatHistoryPanel
            userId={USER_ID}
            onSelectConversation={loadPastConversation}
            currentSessionId={currentSessionId}
          />
        )} */}
        {/* MessageList component displays the conversation history */}
        {/* Pass the messages state and loading state to MessageList */}
        <MessageList messages={messages} loading={loading} />
      </div>

      {/* UserInput component for typing and sending messages */}
      {/* Pass the handleSendMessage function and loading state to UserInput */}
      <UserInput onSendMessage={handleSendMessage} loading={loading} />
    </div>
  );
}

export default App;