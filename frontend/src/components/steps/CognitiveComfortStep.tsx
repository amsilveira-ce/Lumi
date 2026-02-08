import React, { useState } from 'react';
import { StepProps } from './types';
import './CognitiveComfortStep.css';

interface CognitiveOption {
  value: string;
  label: string;
  icon?: string;
}

export const CognitiveComfortStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  isLoading,
  errors
}) => {
  const [selected, setSelected] = useState<string>('');

  const title = data.title || 'How comfortable are you with technology?';
  const subtitle = data.subtitle || 'This helps us adjust the experience for you';
  const options: CognitiveOption[] = data.options || [
    { value: 'beginner', label: "I'm new to technology", icon: '📱' },
    { value: 'intermediate', label: "I'm somewhat comfortable", icon: '💻' },
    { value: 'advanced', label: "I'm tech-savvy", icon: '🚀' }
  ];

  const handleSelect = (value: string) => {
    setSelected(value);
  };

  const handleSubmit = () => {
    if (!selected) {
      return;
    }

    onSubmit({ cognitive_comfort: selected });
  };

  return (
    <div className="cognitive-comfort-step">
      <div className="step-header">
        <h1 className="step-title">{title}</h1>
        {subtitle && <p className="step-subtitle">{subtitle}</p>}
      </div>

      <div className="comfort-options">
        {options.map((option) => (
          <button
            key={option.value}
            className={`comfort-option ${selected === option.value ? 'selected' : ''}`}
            onClick={() => handleSelect(option.value)}
            disabled={isLoading}
          >
            {option.icon && <span className="option-icon">{option.icon}</span>}
            <span className="option-label">{option.label}</span>
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
