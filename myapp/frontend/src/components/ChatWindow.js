import React, { useState, useRef, useEffect } from 'react';
import { sendChatQuery } from '../api/api';
import ReactMarkdown from 'react-markdown';
import './ChatWindow.css';

function ChatWindow({ isOpen, onClose }) {
  // State for messages - each message has type (user/ai) and content
  const [messages, setMessages] = useState([]);
  // Current text typed
  const [inputValue, setInputValue] = useState('');
  // Loading state for AI response
  const [isLoading, setIsLoading] = useState(false);

  // Reference to the textarea element
  const textareaRef = useRef(null);
  
  // Auto-resize function
  const autoResizeTextarea = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    // Reset height to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Set the height based on scrollHeight (content height)
    textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
  };
  
  // Call resize when input value changes
  useEffect(() => {
    autoResizeTextarea();
  }, [inputValue]);

  // Handle input change
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  // Called when the user hits "Send"
  const handleSendClick = async () => {
    if (inputValue.trim() === '') return;

    // Add the new user message to our list
    const userMessage = {
      type: 'user',
      content: inputValue
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Clear the input field
    setInputValue('');
    
    // Show loading state
    setIsLoading(true);
    
    try {
      // Send the message to the backend
      const response = await sendChatQuery(userMessage.content);
      
      // Add AI response to messages
      const aiMessage = {
        type: 'ai',
        content: response.response,
        data: response.data
      };
      setMessages(prevMessages => [...prevMessages, aiMessage]);
    } catch (error) {
      console.error('Error getting AI response:', error);
      // Add error message
      const errorMessage = {
        type: 'ai',
        content: 'Sorry, I encountered an error while processing your request.'
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendClick();
    }
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
          <p>Ask me questions about water mains in Kitchener.</p>
          <p>For example: "How many kilometers of water mains are there in Kitchener?"</p>
        </div>

        {/* Render messages with different styling based on type */}
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.type}`}>
            <div className="message-header">
              {msg.type === 'user' ? 'You' : 'AI Assistant'}
            </div>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="chat-message ai loading">
            <div className="message-header">AI Assistant</div>
            <div className="message-content">
              <div className="loading-dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-footer">
        <textarea
          ref={textareaRef}
          className="chat-input"
          placeholder="Type your message..."
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          rows="1"
        />
        <button 
          className="send-btn" 
          onClick={handleSendClick}
          disabled={isLoading || inputValue.trim() === ''}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;
