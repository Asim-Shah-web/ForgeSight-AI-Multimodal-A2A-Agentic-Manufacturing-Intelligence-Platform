import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/types/auth';
import { EmptyState } from '@/components/ui/EmptyState';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

/** Hides UI the role can't meaningfully use — a UX convenience, never the
 * actual security boundary. The backend enforces every mutation regardless. */
export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isInitializing, user } = useAuth();

  if (isInitializing) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div className="p-6">
        <EmptyState
          title="You don't have access to this page"
          description={`This page is available to: ${allowedRoles.join(', ')}.`}
        />
      </div>
    );
  }

  return <>{children}</>;
}