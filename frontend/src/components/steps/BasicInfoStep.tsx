// components/steps/BasicInfoStep.tsx
import React, { useState } from 'react';
import { StepProps, Field } from './types';
import { DynamicForm } from '../DynamicForm';

export const BasicInfoStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  onValidate,
  errors,
  isLoading
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});

  const defaultFields: Field[] = data?.fields || [
    {
      name: 'full_name',
      label: 'Full Name',
      type: 'text',
      required: true,
      placeholder: 'John Doe'
    },
    {
      name: 'email',
      label: 'Email Address',
      type: 'email',
      required: true,
      placeholder: 'john@example.com'
    },
    {
      name: 'phone',
      label: 'Phone Number',
      type: 'tel',
      required: false,
      placeholder: '+1 (555) 000-0000'
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleFieldChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));

    // Real-time validation
    if (onValidate) {
      onValidate(name, value);
    }
  };

  return (
    <div className="step basic-info-step">
      <div className="step-header">
        <h2>{data?.title || 'Tell us about yourself'}</h2>
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
