// frontend/src/App.jsx
import React, { useState } from 'react'; // useState will be used in M7
import MessageList from './components/MessageList'; // Import MessageList
import UserInput from './components/UserInput';     // Import UserInput
import './App.css'; // Component-specific CSS for ChatWindow

/**
 * The main ChatWindow component that orchestrates the entire chat interface.
 * For Milestone 6, this sets up the basic layout and includes sub-components.
 * State management and API calls will be fully implemented in Milestone 7.
 */
function App() {
  // Placeholder for messages state (will be properly used in Milestone 7)
  // For M6, we'll just have a couple of dummy messages to show the UI.
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hello! I'm ShopAssist, your e-commerce chatbot. How can I help you today?", timestamp: new Date() },
    { role: 'user', content: "Hi there!", timestamp: new Date() },
  ]);

  // Placeholder for loading state (will be properly used in Milestone 7)
  const [loading, setLoading] = useState(false);

  // Placeholder for sendMessage function (will be properly implemented in Milestone 7)
  // For M6, this just logs the message and adds a dummy assistant response.
  const handleSendMessage = (messageContent) => {
    console.log("User sent message (M6 placeholder):", messageContent);
    setMessages((prevMessages) => [
      ...prevMessages,
      { role: 'user', content: messageContent, timestamp: new Date() },
      { role: 'assistant', content: `Echoing: "${messageContent}" (M6 Placeholder)`, timestamp: new Date() },
    ]);
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h1>ShopAssist Chatbot</h1>
        {/* History toggle button placeholder (for Milestone 8) */}
        <button className="history-toggle-btn">Show History</button>
      </div>

      <div className="chat-content">
        {/* MessageList component displays the conversation history */}
        <MessageList messages={messages} loading={loading} />
      </div>

      {/* UserInput component for typing and sending messages */}
      <UserInput onSendMessage={handleSendMessage} loading={loading} />
    </div>
  );
}

export default App;