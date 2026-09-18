import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { LoginPage } from '@/pages/LoginPage';
import { IncidentListPage } from '@/pages/IncidentListPage';
import { CreateIncidentPage } from '@/pages/CreateIncidentPage';
import { IncidentDetailPage } from '@/pages/IncidentDetailPage';
import { InvestigationWorkspacePage } from '@/pages/InvestigationWorkspacePage';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<IncidentListPage />} />
              <Route
                path="/incidents/new"
                element={
                  <ProtectedRoute allowedRoles={['production_operator', 'quality_engineer']}>
                    <CreateIncidentPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
              <Route path="/incidents/:incidentId/investigation" element={<InvestigationWorkspacePage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}