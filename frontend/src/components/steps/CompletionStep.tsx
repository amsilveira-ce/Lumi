// components/steps/CompletionStep.tsx
import React from 'react';
import { StepProps } from './types';

export const CompletionStep: React.FC<StepProps> = ({ data }) => {
  const userProfile = data?.user_profile || {};

  const handleGetStarted = () => {
    // Navigate to main app or dashboard
    window.location.href = '/dashboard';
  };

  return (
    <div className="step completion-step">
      <div className="completion-content">
        {data?.celebration && (
          <div className="celebration-animation">
            🎉
          </div>
        )}

        <div className="completion-icon">✓</div>
        <h1>All Set!</h1>
        <p className="subtitle">Your profile has been created successfully</p>

        {Object.keys(userProfile).length > 0 && (
          <div className="profile-summary">
            <h3>Your Profile</h3>
            <div className="profile-grid">
              {Object.entries(userProfile).map(([step, stepData]: [string, any]) => (
                <div key={step} className="profile-section">
                  <h4>{step.replace('_', ' ').toUpperCase()}</h4>
                  {typeof stepData === 'object' && stepData !== null ? (
                    <ul>
                      {Object.entries(stepData).map(([key, value]) => (
                        <li key={key}>
                          <strong>{key.replace('_', ' ')}:</strong>{' '}
                          {Array.isArray(value) ? value.join(', ') : String(value)}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>{String(stepData)}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="completion-actions">
          <button
            className="btn-primary btn-large"
            onClick={handleGetStarted}
          >
            Get Started 🚀
          </button>
        </div>

        <div className="next-steps">
          <h3>What's Next?</h3>
          <div className="next-steps-list">
            <div className="next-step-item">
              <span className="step-number">1</span>
              <div>
                <h4>Explore the Dashboard</h4>
                <p>Familiarize yourself with all available features</p>
              </div>
            </div>
            <div className="next-step-item">
              <span className="step-number">2</span>
              <div>
                <h4>Complete Your First Task</h4>
                <p>Put your skills to practice</p>
              </div>
            </div>
            <div className="next-step-item">
              <span className="step-number">3</span>
              <div>
                <h4>Invite Team Members</h4>
                <p>Collaboration makes everything better</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
