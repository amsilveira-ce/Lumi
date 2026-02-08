// components/OnboardingFlow.tsx
import React, { useState, useEffect } from 'react';
import { useOnboardingAgent, AgentResponse, UICommand } from '../hooks/useOnboardingAgent';
import { WelcomeStep } from './steps/WelcomeStep';
import { BasicInfoStep } from './steps/BasicInfoStep';
import { PreferencesStep } from './steps/PreferencesStep';
import { GoalsStep } from './steps/GoalsStep';
import { CompletionStep } from './steps/CompletionStep';
import { CognitiveComfortStep } from './steps/CognitiveComfortStep';
import { PersonalityStep } from './steps/PersonalityStep';
import { TonePreferencesStep } from './steps/TonePreferencesStep';
import { EmergencyContactsStep } from './steps/EmergencyContactsStep';
import { DailyRoutinesStep } from './steps/DailyRoutinesStep';
import { ProgressBar } from './ProgressBar';
import { FeedbackChat } from './FeedbackChat';
import './OnboardingFlow.css';

export interface StepData {
  [key: string]: any;
}

export const OnboardingFlow: React.FC = () => {
  const { sendAction, isLoading, error } = useOnboardingAgent();
  const [currentStep, setCurrentStep] = useState<string>('welcome');
  const [stepData, setStepData] = useState<StepData>({});
  const [progress, setProgress] = useState<number>(0);
  const [agentMessage, setAgentMessage] = useState<string>('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [uiSettings, setUiSettings] = useState<any>({});

  const initOnboarding = async () => {
    try {
      const response = await sendAction('init');
      processAgentResponse(response);
    } catch (err) {
      console.error('Failed to initialize onboarding:', err);
    }
  };

  useEffect(() => {
    // Initialize onboarding
    initOnboarding();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const processAgentResponse = (response: AgentResponse) => {
    setAgentMessage(response.text);
    setProgress(response.onboarding_state.progress);

    // Process UI commands
    response.ui_commands.forEach((command: UICommand) => {
      handleUICommand(command);
    });
  };

  const handleUICommand = (command: UICommand) => {
    switch (command.action) {
      case 'navigate':
        setCurrentStep(command.props.step);
        setStepData(command.props.data || {});
        setErrors({});
        break;

      case 'show_error':
        const newErrors: Record<string, string> = {};
        command.props.errors?.forEach((error: string) => {
          newErrors['general'] = error;
        });
        setErrors(newErrors);
        break;

      case 'validate':
        if (command.props.valid) {
          setErrors(prev => {
            const updated = { ...prev };
            delete updated[command.component];
            return updated;
          });
        } else {
          setErrors(prev => ({
            ...prev,
            [command.component]: command.props.message
          }));
        }
        break;

      case 'update':
        setStepData(prev => ({
          ...prev,
          ...command.props
        }));
        break;
    }
  };

  const handleStepSubmit = async (data: Record<string, any>) => {
    try {
      const response = await sendAction('submit_step', data);
      processAgentResponse(response);
    } catch (err) {
      console.error('Failed to submit step:', err);
    }
  };

  const handleFieldValidation = async (field: string, value: any) => {
    try {
      const response = await sendAction('validate', { field, value });
      processAgentResponse(response);
    } catch (err) {
      console.error('Field validation failed:', err);
    }
  };

  const handleNavigation = async (direction: 'back' | 'next') => {
    try {
      const response = await sendAction('navigate', { direction });
      processAgentResponse(response);
    } catch (err) {
      console.error('Navigation failed:', err);
    }
  };

  const handleUIUpdate = (updates: any) => {
    setUiSettings((prev: any) => ({ ...prev, ...updates }));
    console.log('UI Settings Updated:', updates);
  };

  const renderStep = () => {
    const commonProps = {
      data: stepData,
      onSubmit: handleStepSubmit,
      onValidate: handleFieldValidation,
      errors,
      isLoading
    };

    switch (currentStep) {
      case 'welcome':
        return <WelcomeStep {...commonProps} />;
      case 'cognitive_comfort':
        return <CognitiveComfortStep {...commonProps} />;
      case 'personality_traits':
        return <PersonalityStep {...commonProps} />;
      case 'tone_preferences':
        return <TonePreferencesStep {...commonProps} />;
      case 'emergency_contacts':
        return <EmergencyContactsStep {...commonProps} />;
      case 'daily_routines':
        return <DailyRoutinesStep {...commonProps} />;
      case 'basic_info':
        return <BasicInfoStep {...commonProps} />;
      case 'preferences':
        return <PreferencesStep {...commonProps} />;
      case 'goals':
        return <GoalsStep {...commonProps} />;
      case 'complete':
      case 'confirmation':
        return <CompletionStep {...commonProps} />;
      default:
        return <div>Unknown step: {currentStep}</div>;
    }
  };

  // Apply UI settings as CSS variables
  const containerStyle = {
    '--font-size-base': uiSettings.fontSize?.base || '18px',
    '--font-size-title': uiSettings.fontSize?.title || '32px',
    '--font-size-button': uiSettings.fontSize?.button || '20px',
    '--button-height': uiSettings.buttonSize?.height || '80px',
    '--button-padding': uiSettings.buttonSize?.padding || '24px 32px',
    '--container-padding': uiSettings.spacing?.padding || '40px 20px',
    '--element-gap': uiSettings.spacing?.gap || '20px',
  } as React.CSSProperties;

  return (
    <div className="onboarding-flow" style={containerStyle}>
      <div className="onboarding-container">
        {currentStep !== 'complete' && (
          <ProgressBar progress={progress} />
        )}

        {agentMessage && (
          <div className="agent-message">
            <div className="agent-avatar">🤖</div>
            <p>{agentMessage}</p>
          </div>
        )}

        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <p>{error}</p>
          </div>
        )}

        <div className="step-container">
          {renderStep()}
        </div>

        {currentStep !== 'welcome' && currentStep !== 'complete' && (
          <div className="navigation-buttons">
            <button
              className="btn-secondary"
              onClick={() => handleNavigation('back')}
              disabled={isLoading}
            >
              ← Back
            </button>
          </div>
        )}
      </div>

      {/* Feedback Chat for real-time UI adjustments */}
      <FeedbackChat onUIUpdate={handleUIUpdate} />
    </div>
  );
};
