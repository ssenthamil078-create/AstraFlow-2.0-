import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardShell from './DashboardShell.tsx';
import { LandingView } from './views/LandingView.tsx';
import { AuthView } from './views/AuthView.tsx';
import { OnboardingView } from './views/OnboardingView.tsx';

// A simple protected route wrapper
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('astra_token') : null;
  return token ? children : <Navigate to="/login" replace />;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingView />} />
        <Route path="/login" element={<AuthView />} />
        <Route path="/register" element={<AuthView />} />
        <Route path="/onboarding" element={<OnboardingView />} />
        
        {/* Dashboard Shell handles all the internal routes like /dashboard, /cash-flow, etc. */}
        <Route 
          path="/*" 
          element={
            <ProtectedRoute>
              <DashboardShell />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </BrowserRouter>
  );
}
