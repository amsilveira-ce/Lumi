// components/steps/WelcomeStep.tsx
import React from 'react';
import { StepProps } from './types';

export const WelcomeStep: React.FC<StepProps> = ({ data, onSubmit, isLoading }) => {
  const handleStart = () => {
    onSubmit({});
  };

  return (
    <div className="step welcome-step">
      <div className="welcome-content">
        <div className="welcome-icon">👋</div>
        <h1>{data?.title || 'Welcome!'}</h1>
        <p className="subtitle">{data?.subtitle || 'Let\'s get you started'}</p>

        {data?.features && (
          <div className="features-list">
            {data.features.map((feature: string, index: number) => (
              <div key={index} className="feature-item">
                <span className="checkmark">✓</span>
                <span>{feature}</span>
              </div>
            ))}
          </div>
        )}

        <button
          className="btn-primary btn-large"
          onClick={handleStart}
          disabled={isLoading}
        >
          {data?.cta_text || 'Get Started'} →
        </button>
      </div>
    </div>
  );
};
