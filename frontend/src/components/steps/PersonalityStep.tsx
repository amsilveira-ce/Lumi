import React, { useState } from 'react';
import { StepProps } from './types';
import './PersonalityStep.css';

interface PersonalityOption {
  value: string;
  label: string;
  description: string;
  icon: string;
}

export const PersonalityStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  isLoading,
  errors
}) => {
  const [selected, setSelected] = useState<string>('');

  const title = data.title || 'How do you like to learn new things?';
  const subtitle = data.subtitle || 'Everyone has their own style';
  const options: PersonalityOption[] = data.options || [
    {
      value: 'independent',
      label: 'I like to explore on my own',
      description: 'I prefer discovering features at my own pace',
      icon: '🦸'
    },
    {
      value: 'needs_guidance',
      label: 'I prefer step-by-step guidance',
      description: 'I appreciate clear instructions and helpful tips',
      icon: '🤝'
    }
  ];

  const handleSelect = (value: string) => {
    setSelected(value);
  };

  const handleSubmit = () => {
    if (!selected) {
      return;
    }

    onSubmit({ personality_traits: selected });
  };

  return (
    <div className="personality-step">
      <div className="step-header">
        <h1 className="step-title">{title}</h1>
        {subtitle && <p className="step-subtitle">{subtitle}</p>}
      </div>

      <div className="personality-options">
        {options.map((option) => (
          <button
            key={option.value}
            className={`personality-option ${selected === option.value ? 'selected' : ''}`}
            onClick={() => handleSelect(option.value)}
            disabled={isLoading}
          >
            <span className="option-icon">{option.icon}</span>
            <div className="option-content">
              <div className="option-label">{option.label}</div>
              <div className="option-description">{option.description}</div>
            </div>
          </button>
        ))}
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
          disabled={!selected || isLoading}
        >
          {isLoading ? 'Processing...' : 'Continue'}
        </button>
      </div>
    </div>
  );
};
