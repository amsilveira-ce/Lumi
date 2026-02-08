// components/steps/PreferencesStep.tsx
import React, { useState } from 'react';
import { StepProps, Field } from './types';
import { DynamicForm } from '../DynamicForm';

export const PreferencesStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  onValidate,
  errors,
  isLoading
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});

  const defaultFields: Field[] = data?.fields || [
    {
      name: 'interests',
      label: 'What are you interested in?',
      type: 'multiselect',
      options: ['Technology', 'Design', 'Business', 'Health', 'Education', 'Entertainment'],
      required: true
    },
    {
      name: 'communication_preference',
      label: 'How should we communicate with you?',
      type: 'select',
      options: ['Email', 'SMS', 'Push Notifications', 'All of the above'],
      required: true
    },
    {
      name: 'theme',
      label: 'Preferred Theme',
      type: 'select',
      options: ['Light', 'Dark', 'Auto'],
      required: false
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleFieldChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));

    if (onValidate) {
      onValidate(name, value);
    }
  };

  return (
    <div className="step preferences-step">
      <div className="step-header">
        <h2>{data?.title || 'Customize your experience'}</h2>
        {data?.description && <p className="step-description">{data.description}</p>}
      </div>

      <form onSubmit={handleSubmit}>
        <DynamicForm
          fields={defaultFields}
          values={formData}
          onChange={handleFieldChange}
          errors={errors || {}}
        />

        <button
          type="submit"
          className="btn-primary btn-large"
          disabled={isLoading}
        >
          {isLoading ? 'Processing...' : 'Continue →'}
        </button>
      </form>
    </div>
  );
};
