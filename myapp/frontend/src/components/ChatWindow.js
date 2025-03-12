import React, { useState } from 'react';
import './ChatWindow.css';

function ChatWindow({ isOpen, onClose }) {
  // State array of user messages
  const [messages, setMessages] = useState([]);
  // Current text typed
  const [inputValue, setInputValue] = useState('');

  // Called when the user hits "Send"
  const handleSendClick = () => {
    if (inputValue.trim() === '') return;

    // Add the new message to our list
    setMessages([...messages, inputValue]);

    // Clear the input field
    setInputValue('');
  };

  return (
    <div className={`slide-chat-window ${isOpen ? 'open' : ''}`}>
      <div className="chat-header">
        <span>AI Chat</span>
        <button className="close-btn" onClick={onClose}>
          ✕
        </button>
      </div>

      <div className="chat-content">
        {/* Static welcome message at the top */}
        <div className="chat-welcome">
          <p>Welcome to your AI Chat!</p>
          <p>Type your questions or requests here.</p>
        </div>

        {/* Render each user-typed message */}
        {messages.map((msg, idx) => (
          <div key={idx} className="chat-message">
            {msg}
          </div>
        ))}
      </div>

      <div className="chat-footer">
        <input
          type="text"
          className="chat-input"
          placeholder="Type your message..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />
        <button className="send-btn" onClick={handleSendClick}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;
