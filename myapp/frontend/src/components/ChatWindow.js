import React, { useState, useRef, useEffect } from 'react';
import { sendChatQuery, createChatSession, getChatHistory } from '../api/api';
import './ChatWindow.css';

function ChatWindow({ isOpen, onClose, onFilterMap }) {
  // State for messages - each message has type (user/ai) and content
  const [messages, setMessages] = useState([]);
  // Current text typed
  const [inputValue, setInputValue] = useState('');
  // Loading state for AI response
  const [isLoading, setIsLoading] = useState(false);
  // Session ID for chat memory
  const [sessionId, setSessionId] = useState(null);
  // Loading state for chat history
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  
  const messagesEndRef = useRef(null);

  // Reference to the textarea element
  const textareaRef = useRef(null);
  
  // Function to strip markdown formatting
  const stripMarkdown = (text) => {
    if (!text) return '';
    
    return text
      // Remove bold/italic formatting
      .replace(/\*\*(.*?)\*\*/g, '$1') // Bold
      .replace(/\*(.*?)\*/g, '$1')     // Italic
      .replace(/__(.*?)__/g, '$1')     // Bold
      .replace(/_(.*?)_/g, '$1')       // Italic
      
      // Remove headers
      .replace(/#{1,6}\s+/g, '')
      
      // Remove links
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      
      // Remove list markers
      .replace(/^[\*\-+]\s+/gm, '')
      .replace(/^\d+\.\s+/gm, '')
      
      // Remove code blocks and inline code
      .replace(/```[a-z]*\n([\s\S]*?)```/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      
      // Remove blockquotes
      .replace(/^>\s+/gm, '');
  };
  
  // Initialize session or load existing session
  useEffect(() => {
    const loadSession = async () => {
      try {
        // Check for existing session in localStorage
        const storedSessionId = localStorage.getItem('chatSessionId');
        
        if (storedSessionId) {
          setSessionId(storedSessionId);
          await loadChatHistory(storedSessionId);
        } else {
          // Create a new session if none exists
          const session = await createChatSession();
          setSessionId(session.session_id);
          localStorage.setItem('chatSessionId', session.session_id);
        }
      } catch (error) {
        console.error('Error initializing chat session:', error);
      }
    };
    
    loadSession();
  }, []);
  
  // Load chat history for a session
  const loadChatHistory = async (sessionId) => {
    if (!sessionId) return;
    
    setIsLoadingHistory(true);
    try {
      const history = await getChatHistory(sessionId);
      if (history && history.messages && history.messages.length > 0) {
        // Convert from server format to component format
        const formattedMessages = history.messages.map(msg => ({
          type: msg.message_type,
          content: stripMarkdown(msg.content) // Strip markdown from stored messages
        }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      // If we can't load history, likely the session is invalid or expired
      // Create a new session
      try {
        const session = await createChatSession();
        setSessionId(session.session_id);
        localStorage.setItem('chatSessionId', session.session_id);
        setMessages([]);
      } catch (sessionError) {
        console.error('Error creating new session:', sessionError);
      }
    } finally {
      setIsLoadingHistory(false);
    }
  };
  
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

  // Function to scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  // This will run whenever the chat window opens or when conversations change
  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [isOpen, messages]);

  // Handle input change
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  // Create a new chat session
  const handleNewChat = async () => {
    try {
      if (isLoading) return; // Prevent creating new chat while loading
      
      const confirmNewChat = window.confirm("Start a new chat? This will clear the current conversation.");
      if (!confirmNewChat) return;
      
      const session = await createChatSession();
      setSessionId(session.session_id);
      localStorage.setItem('chatSessionId', session.session_id);
      setMessages([]);
      setInputValue('');
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
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
    
    // Show loading indicator
    setIsLoading(true);
    
    try {
      // Send the message to the API
      const response = await sendChatQuery(inputValue, sessionId);
      
      // Update session ID if returned from server (for first message)
      if (response.session_id && (!sessionId || response.session_id !== sessionId)) {
        setSessionId(response.session_id);
        localStorage.setItem('chatSessionId', response.session_id);
      }
      
      // Check if this is a show query with filter IDs
      if (response.is_show_query && response.filter_ids && response.filter_ids.length > 0) {
        // Call the filter map function with the IDs
        onFilterMap(response.filter_ids, response.filter_ids.length);
      }
      
      // Add the AI response to our list
      const aiMessage = {
        type: 'ai',
        content: stripMarkdown(response.response) // Strip markdown from AI response
      };
      setMessages(prevMessages => [...prevMessages, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      const errorMessage = {
        type: 'ai',
        content: 'Sorry, I encountered an error processing your request.'
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key for sending
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
        <div className="chat-header-actions">
          <button className="new-chat-btn" onClick={handleNewChat} disabled={isLoading}>
            New Chat
          </button>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>
      </div>

      <div className="chat-content">
        {/* Static welcome message at the top */}
        {messages.length === 0 && !isLoadingHistory && (
          <div className="chat-welcome">
            <p>Welcome to your AI Chat!</p>
            <p>Ask me questions about water mains in Kitchener.</p>
            <p>For example: "How many kilometers of water mains are there in Kitchener?"</p>
          </div>
        )}
        
        {/* Loading history indicator */}
        {isLoadingHistory && (
          <div className="chat-loading-history">
            <p>Loading chat history...</p>
          </div>
        )}

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
        
        {/* This empty div will be scrolled into view */}
        <div ref={messagesEndRef} />
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
          disabled={isLoading || isLoadingHistory}
        />
        <button 
          className="send-btn" 
          onClick={handleSendClick}
          disabled={isLoading || isLoadingHistory || inputValue.trim() === ''}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;
