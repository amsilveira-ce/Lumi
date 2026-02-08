// components/steps/GoalsStep.tsx
import React, { useState } from 'react';
import { StepProps, Field } from './types';
import { DynamicForm } from '../DynamicForm';

export const GoalsStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  onValidate,
  errors,
  isLoading
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});

  const defaultFields: Field[] = data?.fields || [
    {
      name: 'primary_goal',
      label: 'What is your main goal?',
      type: 'textarea',
      required: true,
      placeholder: 'Tell us what you hope to achieve...'
    },
    {
      name: 'timeline',
      label: 'When do you want to achieve this?',
      type: 'select',
      options: ['This week', 'This month', 'This quarter', 'This year', 'Long term'],
      required: true
    },
    {
      name: 'experience_level',
      label: 'What is your experience level?',
      type: 'select',
      options: ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
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
    <div className="step goals-step">
      <div className="step-header">
        <h2>{data?.title || 'What brings you here?'}</h2>
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
          {isLoading ? 'Processing...' : 'Complete Setup →'}
        </button>
      </form>
    </div>
  );
};
