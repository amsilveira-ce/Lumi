import React, { useState } from 'react';
import './MoodSelector.css';

interface Mood {
  emoji: string;
  label: string;
  color: string;
}

const MOODS: Mood[] = [
  { emoji: '😊', label: 'Happy', color: '#48bb78' },
  { emoji: '😢', label: 'Sad', color: '#4299e1' },
  { emoji: '😌', label: 'Calm', color: '#9f7aea' },
  { emoji: '😰', label: 'Anxious', color: '#ed8936' },
  { emoji: '😴', label: 'Tired', color: '#718096' },
  { emoji: '😡', label: 'Frustrated', color: '#f56565' }
];

export const MoodSelector: React.FC = () => {
  const [selectedMood, setSelectedMood] = useState<string | null>(null);

  const handleMoodSelect = (label: string) => {
    setSelectedMood(label);
    // In a real app, this would send the mood to the backend
    console.log('Mood selected:', label);
  };

  return (
    <div className="mood-selector widget">
      <h3 className="widget-title">😊 How are you feeling?</h3>
      <p className="widget-subtitle">Let me know your mood</p>

      <div className="mood-grid">
        {MOODS.map((mood) => (
          <button
            key={mood.label}
            className={`mood-button ${selectedMood === mood.label ? 'selected' : ''}`}
            onClick={() => handleMoodSelect(mood.label)}
            style={{
              borderColor: selectedMood === mood.label ? mood.color : undefined
            }}
          >
            <span className="mood-emoji">{mood.emoji}</span>
            <span className="mood-label">{mood.label}</span>
          </button>
        ))}
      </div>

      {selectedMood && (
        <div className="mood-feedback">
          <p>Thank you for sharing! I understand you're feeling {selectedMood.toLowerCase()}.</p>
        </div>
      )}
    </div>
  );
};
