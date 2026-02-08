// components/steps/types.ts
export interface Field {
  name: string;
  label: string;
  type: 'text' | 'email' | 'tel' | 'select' | 'multiselect' | 'textarea' | 'number';
  required?: boolean;
  options?: string[];
  placeholder?: string;
  min?: number;
  max?: number;
}

export interface StepProps {
  data: Record<string, any>;
  onSubmit: (data: Record<string, any>) => void;
  onValidate?: (field: string, value: any) => void;
  errors?: Record<string, string>;
  isLoading?: boolean;
}
