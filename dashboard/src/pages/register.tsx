import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import useForm from '../hooks/useForm';

const Register = () => {
  const { register, error: authError, user } = useAuth();
  const router = useRouter();
  const [registerError, setRegisterError] = useState<string | null>(null);

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  const { values, errors, handleChange, handleBlur, handleSubmit, isValid } = useForm(
    {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
    {
      name: {
        required: true,
        minLength: 2,
      },
      email: {
        required: true,
        pattern: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
      },
      password: {
        required: true,
        minLength: 6,
      },
      confirmPassword: {
        required: true,
        validate: (value, formValues) => value === formValues.password || 'Passwords do not match',
      },
    }
  );

  const onSubmit = async () => {
    setRegisterError(null);
    try {
      const { confirmPassword, ...registerData } = values;
      await register(registerData);
    } catch (err: any) {
      setRegisterError(err.message || 'Registration failed. Please try again.');
    }
  };

  return (
    <>
      <Head>
        <title>Register | SMS Dashboard</title>
      </Head>
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">SMS Dashboard</h1>
            <p className="text-muted-foreground mt-2">Create a new account</p>
          </div>

          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            {(registerError || authError) && (
              <div className="bg-destructive/10 text-destructive p-3 rounded-md mb-4">
                {registerError || authError}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)}>
              <div className="mb-4">
                <label htmlFor="name" className="block text-sm font-medium mb-1">
                  Full Name
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  value={values.name}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  className={`w-full p-2 border rounded-md bg-background ${
                    errors.name ? 'border-destructive' : 'border-input'
                  }`}
                />
                {errors.name && <p className="mt-1 text-sm text-destructive">{errors.name}</p>}
              </div>

              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium mb-1">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={values.email}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  className={`w-full p-2 border rounded-md bg-background ${
                    errors.email ? 'border-destructive' : 'border-input'
                  }`}
                />
                {errors.email && <p className="mt-1 text-sm text-destructive">{errors.email}</p>}
              </div>

              <div className="mb-4">
                <label htmlFor="password" className="block text-sm font-medium mb-1">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  value={values.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  className={`w-full p-2 border rounded-md bg-background ${
                    errors.password ? 'border-destructive' : 'border-input'
                  }`}
                />
                {errors.password && (
                  <p className="mt-1 text-sm text-destructive">{errors.password}</p>
                )}
              </div>

              <div className="mb-6">
                <label htmlFor="confirmPassword" className="block text-sm font-medium mb-1">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  value={values.confirmPassword}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  className={`w-full p-2 border rounded-md bg-background ${
                    errors.confirmPassword ? 'border-destructive' : 'border-input'
                  }`}
                />
                {errors.confirmPassword && (
                  <p className="mt-1 text-sm text-destructive">{errors.confirmPassword}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={!isValid}
                className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Register
              </button>
            </form>

            <div className="mt-4 text-center">
              <p className="text-sm">
                Already have an account?{' '}
                <Link href="/login" className="text-primary hover:underline">
                  Sign In
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Register; 