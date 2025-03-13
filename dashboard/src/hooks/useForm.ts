import { useState, ChangeEvent, FormEvent } from 'react';

interface ValidationRules {
  [key: string]: {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    validate?: (value: any, formValues: any) => boolean | string;
  };
}

interface ValidationErrors {
  [key: string]: string;
}

interface UseFormReturn<T> {
  values: T;
  errors: ValidationErrors;
  touched: Record<keyof T, boolean>;
  isValid: boolean;
  isDirty: boolean;
  handleChange: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  handleBlur: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  handleSubmit: (onSubmit: (values: T) => void) => (e: FormEvent) => void;
  setFieldValue: (name: keyof T, value: any) => void;
  reset: () => void;
}

function useForm<T extends Record<string, any>>(
  initialValues: T,
  validationRules: ValidationRules = {}
): UseFormReturn<T> {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [touched, setTouched] = useState<Record<keyof T, boolean>>({} as Record<keyof T, boolean>);
  const [isDirty, setIsDirty] = useState(false);

  // Validate a single field
  const validateField = (name: string, value: any): string => {
    const rules = validationRules[name];
    if (!rules) return '';

    if (rules.required && (!value || (typeof value === 'string' && value.trim() === ''))) {
      return 'This field is required';
    }

    if (rules.minLength && typeof value === 'string' && value.length < rules.minLength) {
      return `Must be at least ${rules.minLength} characters`;
    }

    if (rules.maxLength && typeof value === 'string' && value.length > rules.maxLength) {
      return `Must be no more than ${rules.maxLength} characters`;
    }

    if (rules.pattern && !rules.pattern.test(value)) {
      return 'Invalid format';
    }

    if (rules.validate) {
      const result = rules.validate(value, values);
      if (typeof result === 'string') return result;
      if (result === false) return 'Invalid value';
    }

    return '';
  };

  // Validate all fields
  const validateForm = (): ValidationErrors => {
    const newErrors: ValidationErrors = {};
    
    Object.keys(validationRules).forEach((key) => {
      const error = validateField(key, values[key]);
      if (error) {
        newErrors[key] = error;
      }
    });
    
    return newErrors;
  };

  // Handle input change
  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    // Handle different input types
    const inputValue = type === 'checkbox' 
      ? (e.target as HTMLInputElement).checked 
      : value;
    
    setValues((prev) => ({ ...prev, [name]: inputValue }));
    setIsDirty(true);
    
    // Validate field if it's been touched
    if (touched[name as keyof T]) {
      const error = validateField(name, inputValue);
      setErrors((prev) => ({ ...prev, [name]: error }));
    }
  };

  // Handle input blur
  const handleBlur = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    // Mark field as touched
    setTouched((prev) => ({ ...prev, [name]: true }));
    
    // Validate field
    const error = validateField(name, value);
    setErrors((prev) => ({ ...prev, [name]: error }));
  };

  // Handle form submission
  const handleSubmit = (onSubmit: (values: T) => void) => (e: FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched
    const allTouched = Object.keys(values).reduce((acc, key) => {
      acc[key as keyof T] = true;
      return acc;
    }, {} as Record<keyof T, boolean>);
    
    setTouched(allTouched);
    
    // Validate all fields
    const formErrors = validateForm();
    setErrors(formErrors);
    
    // Submit if no errors
    if (Object.keys(formErrors).length === 0) {
      onSubmit(values);
    }
  };

  // Set a field value programmatically
  const setFieldValue = (name: keyof T, value: any) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    setIsDirty(true);
    
    if (touched[name]) {
      const error = validateField(name as string, value);
      setErrors((prev) => ({ ...prev, [name]: error }));
    }
  };

  // Reset form to initial values
  const reset = () => {
    setValues(initialValues);
    setErrors({});
    setTouched({} as Record<keyof T, boolean>);
    setIsDirty(false);
  };

  return {
    values,
    errors,
    touched,
    isValid: Object.keys(errors).length === 0,
    isDirty,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    reset,
  };
}

export default useForm; 