import * as yup from 'yup';

export const PASSWORD_MIN_LENGTH = 8;

export const loginSchema = yup.object({
  email: yup
    .string()
    .trim()
    .email('Enter a valid email address')
    .required('Email is required'),
  password: yup
    .string()
    .min(
      PASSWORD_MIN_LENGTH,
      `Password must be at least ${PASSWORD_MIN_LENGTH} characters`,
    )
    .required('Password is required'),
});

const phoneSchema = yup
  .string()
  .trim()
  .transform((value) =>
    typeof value === 'string' && value.trim() === '' ? undefined : value,
  )
  .matches(/^(?:\+251|0)?9\d{8}$/, 'Enter a valid Ethiopian phone number')
  .optional();

export const registerSchema = yup.object({
  first_name: yup
    .string()
    .trim()
    .min(2, 'First name is too short')
    .max(100, 'First name is too long')
    .required('First name is required'),
  last_name: yup
    .string()
    .trim()
    .min(2, 'Last name is too short')
    .max(100, 'Last name is too long')
    .required('Last name is required'),
  email: yup
    .string()
    .trim()
    .email('Enter a valid email address')
    .required('Email is required'),
  phone: phoneSchema,
  password: yup
    .string()
    .min(
      PASSWORD_MIN_LENGTH,
      `Password must be at least ${PASSWORD_MIN_LENGTH} characters`,
    )
    .max(128, 'Password must be at most 128 characters')
    .required('Password is required'),
  confirmPassword: yup
    .string()
    .oneOf([yup.ref('password')], 'Passwords do not match')
    .required('Please confirm your password'),
  role: yup
    .mixed<'job_seeker' | 'employer'>()
    .oneOf(['job_seeker', 'employer'], 'Choose how you will use the app')
    .required('Choose how you will use the app'),
});

export type LoginFormValues = yup.InferType<typeof loginSchema>;
export type RegisterFormValues = yup.InferType<typeof registerSchema>;
