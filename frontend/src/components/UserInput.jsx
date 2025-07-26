// frontend/src/components/UserInput.jsx
import React, { useState } from 'react';
import './UserInput.css';

function UserInput({ onSendMessage, loading }) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !loading) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <form className="chat-input-area" onSubmit={handleSubmit}>
      <input
        type="text"
        id="user-input"
        placeholder={loading ? "Waiting for response..." : "Type your message here..."}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        disabled={loading}
      />
      <button
        id="send-btn"
        type="submit"
        disabled={loading}
      >
        {loading ? 'Sending...' : 'Send'}
      </button>
    </form>
  );
}

export default UserInput;