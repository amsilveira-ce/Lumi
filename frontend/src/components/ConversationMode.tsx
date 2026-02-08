import React, { useState } from 'react';
import { useOnboardingAgent } from '../hooks/useOnboardingAgent';
import { ChatPanel } from './ChatPanel';
import { WidgetPanel } from './WidgetPanel';
import './ConversationMode.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Widget {
  id: string;
  type: string;
  props: any;
  visible: boolean;
}

interface ConversationModeProps {
  elderProfile: any;
}

export const ConversationMode: React.FC<ConversationModeProps> = ({ elderProfile }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome_conversation',
      role: 'assistant',
      content: `Hello! It's wonderful to see you again. I'm here to chat and help with anything you need. How are you feeling today?`,
      timestamp: new Date()
    }
  ]);
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const { sendAction, isLoading } = useOnboardingAgent();

  const handleSendMessage = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // Send to agent (conversation mode)
      const response = await sendAction('conversation', {
        message: text,
        elder_profile: elderProfile
      });

      // Add assistant response
      if (response.text) {
        const assistantMessage: Message = {
          id: `msg_${Date.now() + 1}`,
          role: 'assistant',
          content: response.text,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      }

      // Process widget commands
      if (response.ui_commands) {
        response.ui_commands.forEach((cmd: any) => {
          if (cmd.action === 'show') {
            const newWidget: Widget = {
              id: cmd.props.widget_id || `widget_${Date.now()}`,
              type: cmd.component,
              props: cmd.props,
              visible: true
            };
            setWidgets(prev => [...prev, newWidget]);
          } else if (cmd.action === 'hide') {
            setWidgets(prev =>
              prev.map(w =>
                w.id === cmd.props.widget_id ? { ...w, visible: false } : w
              )
            );
          }
        });
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: "I'm sorry, I had trouble understanding that. Could you try again?",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div className="conversation-mode">
      <div className="conversation-header">
        <h1>💬 Elder Companion</h1>
        <div className="profile-info">
          <span className="profile-label">Comfort Level:</span>
          <span className="profile-value">{elderProfile?.cognitive_comfort || 'N/A'}</span>
        </div>
      </div>

      <div className="conversation-container">
        <div className="chat-section">
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>

        <div className="widget-section">
          <WidgetPanel widgets={widgets.filter(w => w.visible)} />
        </div>
      </div>
    </div>
  );
};
