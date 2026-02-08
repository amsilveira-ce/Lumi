// components/DynamicForm.tsx
import React from 'react';
import { Field } from './steps/types';
import './DynamicForm.css';

interface DynamicFormProps {
  fields: Field[];
  values: Record<string, any>;
  onChange: (name: string, value: any) => void;
  errors: Record<string, string>;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({
  fields,
  values,
  onChange,
  errors
}) => {
  const renderField = (field: Field) => {
    const value = values[field.name] || '';
    const error = errors[field.name];
    const hasError = !!error;

    const commonProps = {
      id: field.name,
      name: field.name,
      required: field.required,
      className: hasError ? 'form-input error' : 'form-input',
      'aria-invalid': hasError,
      'aria-describedby': hasError ? `${field.name}-error` : undefined
    };

    switch (field.type) {
      case 'text':
      case 'email':
      case 'tel':
      case 'number':
        return (
          <input
            {...commonProps}
            type={field.type}
            value={value}
            onChange={(e) => onChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            min={field.min}
            max={field.max}
          />
        );

      case 'textarea':
        return (
          <textarea
            {...commonProps}
            value={value}
            onChange={(e) => onChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            rows={4}
          />
        );

      case 'select':
        return (
          <select
            {...commonProps}
            value={value}
            onChange={(e) => onChange(field.name, e.target.value)}
          >
            <option value="">Select an option</option>
            {field.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      case 'multiselect':
        return (
          <div className="multiselect-container">
            {field.options?.map((option) => {
              const selectedValues = Array.isArray(value) ? value : [];
              const isChecked = selectedValues.includes(option);

              return (
                <label key={option} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={(e) => {
                      const newValues = e.target.checked
                        ? [...selectedValues, option]
                        : selectedValues.filter((v) => v !== option);
                      onChange(field.name, newValues);
                    }}
                  />
                  <span>{option}</span>
                </label>
              );
            })}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="dynamic-form">
      {fields.map((field) => (
        <div key={field.name} className="form-field">
          <label htmlFor={field.name} className="form-label">
            {field.label}
            {field.required && <span className="required">*</span>}
          </label>

          {renderField(field)}

          {errors[field.name] && (
            <div
              id={`${field.name}-error`}
              className="field-error"
              role="alert"
            >
              {errors[field.name]}
            </div>
          )}
        </div>
      ))}

      {errors.general && (
        <div className="form-error" role="alert">
          {errors.general}
        </div>
      )}
    </div>
  );
};
