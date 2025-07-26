// frontend/script.js

const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// --- Global variables to manage chat state ---
let currentSessionId = null; // Stores the session ID for the ongoing conversation
const userId = "web_user_123"; // A static user ID for this frontend. In a real app, this would come from a login system.
const backendUrl = 'http://127.0.0.1:8000/api/chat'; // Your FastAPI backend endpoint

// --- Event Listeners ---
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function(e) {
    // Send message on Enter key press
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// --- Helper Functions ---

/**
 * Displays a message in the chat interface.
 * @param {string} role - 'user' or 'assistant'
 * @param {string} message - The message content
 */
function displayMessage(role, message) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);

    const messageP = document.createElement('p');
    messageP.textContent = message;
    messageDiv.appendChild(messageP);

    const timestampSpan = document.createElement('span');
    timestampSpan.classList.add('timestamp');
    timestampSpan.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    messageDiv.appendChild(timestampSpan);

    chatMessages.appendChild(messageDiv);
    // Scroll to the bottom to show the latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Sends the user's message to the backend and handles the response.
 */
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return; // Don't send empty messages

    displayMessage('user', message); // Display user's message immediately
    userInput.value = ''; // Clear input field

    try {
        const payload = {
            user_id: userId,
            message: message,
            session_id: currentSessionId // Send null for the first message of a new session
        };

        const response = await fetch(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) { // Check for HTTP errors (e.g., 4xx, 5xx)
            const errorText = await response.text(); // Get raw error response
            console.error('Backend responded with an error:', response.status, errorText);
            displayMessage('assistant', `Error: Could not connect to the chatbot or an issue occurred. Please try again. (${response.status})`);
            return;
        }

        const data = await response.json();
        
        // Update the session ID for subsequent messages in this conversation
        currentSessionId = data.session_id; 

        displayMessage('assistant', data.assistant_response);

    } catch (error) {
        console.error('Network or parsing error:', error);
        displayMessage('assistant', 'Oops! It seems I lost connection. Please check the backend server or try again.');
    } finally {
        // Re-enable input and button if they were disabled (optional for future enhancements)
        sendBtn.disabled = false;
        userInput.disabled = false;
        userInput.focus(); // Keep input focused
    }
}

// Optional: Initial focus on input when page loads
document.addEventListener('DOMContentLoaded', () => {
    userInput.focus();
});