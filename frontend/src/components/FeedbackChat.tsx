import React, { useState, useRef, useEffect } from 'react';
import { useOnboardingAgent } from '../hooks/useOnboardingAgent';
import './FeedbackChat.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface FeedbackChatProps {
  onUIUpdate: (updates: any) => void;
}

export const FeedbackChat: React.FC<FeedbackChatProps> = ({ onUIUpdate }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm here to help. You can tell me things like:\n• \"Text is too small\"\n• \"Make buttons bigger\"\n• \"I need more contrast\"\n\nI'll adjust the interface for you!",
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendAction } = useOnboardingAgent();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (role: 'user' | 'assistant', content: string) => {
    const newMessage: Message = {
      id: `msg_${Date.now()}`,
      role,
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSendFeedback = async () => {
    if (!inputText.trim() || isProcessing) return;

    const userMessage = inputText.trim();
    setInputText('');
    addMessage('user', userMessage);
    setIsProcessing(true);

    try {
      // Send feedback to agent
      const response = await sendAction('ui_feedback', {
        feedback: userMessage,
        current_context: 'onboarding'
      });

      // Add agent response
      if (response.text) {
        addMessage('assistant', response.text);
      }

      // Apply UI updates
      if (response.ui_commands) {
        response.ui_commands.forEach(cmd => {
          if (cmd.action === 'update_ui_settings') {
            onUIUpdate(cmd.props);
          }
        });
      }
    } catch (error) {
      addMessage('assistant', 'Sorry, I had trouble processing that. Could you try rephrasing?');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendFeedback();
    }
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        className="feedback-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle feedback chat"
      >
        💬 {isOpen ? 'Close' : 'Feedback'}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="feedback-chat">
          <div className="feedback-header">
            <h3>💬 Help & Feedback</h3>
            <button
              className="close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          <div className="feedback-messages">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`message ${msg.role}`}
              >
                <div className="message-content">
                  {msg.content}
                </div>
                <div className="message-time">
                  {msg.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="message assistant">
                <div className="message-content typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="feedback-input-container">
            <textarea
              className="feedback-input"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Tell me what needs adjustment..."
              rows={2}
              disabled={isProcessing}
            />
            <button
              className="send-btn"
              onClick={handleSendFeedback}
              disabled={!inputText.trim() || isProcessing}
              aria-label="Send feedback"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
};
