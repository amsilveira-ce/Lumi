import React, { useState } from 'react';
import { StepProps } from './types';
import './TonePreferencesStep.css';

export const TonePreferencesStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  isLoading,
  errors
}) => {
  const [tone, setTone] = useState<string>('');
  const [pace, setPace] = useState<string>('');

  const title = data.title || 'How would you like us to communicate?';
  const subtitle = data.subtitle || 'We want you to feel comfortable';

  const toneOptions = [
    { value: 'formal', label: 'Formal and polite', icon: '🎩' },
    { value: 'casual', label: 'Casual and friendly', icon: '😊' }
  ];

  const paceOptions = [
    { value: 'slow', label: 'Take it slow', icon: '🐢' },
    { value: 'medium', label: 'Normal pace', icon: '🚶' },
    { value: 'fast', label: "Let's move quickly", icon: '🚀' }
  ];

  const handleSubmit = () => {
    if (!tone || !pace) {
      return;
    }

    onSubmit({
      tone_preferences: {
        tone,
        pace
      }
    });
  };

  return (
    <div className="tone-preferences-step">
      <div className="step-header">
        <h1 className="step-title">{title}</h1>
        {subtitle && <p className="step-subtitle">{subtitle}</p>}
      </div>

      {/* Tone Selection */}
      <div className="preference-section">
        <h2 className="section-title">Communication Style</h2>
        <div className="preference-options">
          {toneOptions.map((option) => (
            <button
              key={option.value}
              className={`preference-option ${tone === option.value ? 'selected' : ''}`}
              onClick={() => setTone(option.value)}
              disabled={isLoading}
            >
              <span className="option-icon">{option.icon}</span>
              <span className="option-label">{option.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Pace Selection */}
      <div className="preference-section">
        <h2 className="section-title">Interaction Pace</h2>
        <div className="preference-options">
          {paceOptions.map((option) => (
            <button
              key={option.value}
              className={`preference-option ${pace === option.value ? 'selected' : ''}`}
              onClick={() => setPace(option.value)}
              disabled={isLoading}
            >
              <span className="option-icon">{option.icon}</span>
              <span className="option-label">{option.label}</span>
            </button>
          ))}
        </div>
      </div>

      {errors?.general && (
        <div className="error-message" role="alert">
          {errors.general}
        </div>
      )}

      <div className="step-actions">
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!tone || !pace || isLoading}
        >
          {isLoading ? 'Processing...' : 'Continue'}
        </button>
      </div>
    </div>
  );
};
