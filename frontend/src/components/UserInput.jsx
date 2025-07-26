// frontend/src/components/UserInput.jsx
import React, { useState } from 'react';
import './UserInput.css'; // Component-specific CSS

/**
 * Renders the user input field and send button for the chat.
 * @param {object} props - The component's props.
 * @param {function(string): void} props.onSendMessage - Callback function to send the message.
 * @param {boolean} props.loading - Indicates if a message is currently being processed (disables input).
 */
function UserInput({ onSendMessage, loading }) {
  // State to manage the value of the input field
  const [inputValue, setInputValue] = useState('');

  /**
   * Handles the form submission (either by clicking send button or pressing Enter).
   * @param {Event} e - The form submission event.
   */
  const handleSubmit = (e) => {
    e.preventDefault(); // Prevent the default form submission behavior (page reload)

    // Only send message if input is not empty and not currently loading
    if (inputValue.trim() && !loading) {
      onSendMessage(inputValue); // Call the parent component's message sending function
      setInputValue(''); // Clear the input field after sending
    }
  };

  return (
    // A form element is used to handle both button click and Enter key press
    <form className="chat-input-area" onSubmit={handleSubmit}>
      <input
        type="text"
        id="user-input"
        // Placeholder text changes based on loading state
        placeholder={loading ? "Waiting for response..." : "Type your message here..."}
        value={inputValue} // Makes this a controlled component
        onChange={(e) => setInputValue(e.target.value)} // Update state on every input change
        disabled={loading} // Disable input while loading to prevent multiple submissions
      />
      <button
        id="send-btn"
        type="submit" // Type 'submit' makes it trigger the form's onSubmit
        disabled={loading} // Disable button while loading
      >
        {loading ? 'Sending...' : 'Send'} {/* Button text changes based on loading state */}
      </button>
    </form>
  );
}

export default UserInput;