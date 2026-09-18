import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';

const ROLES_THAT_CAN_CREATE_INCIDENTS = ['production_operator', 'quality_engineer'];

export function NavBar() {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between p-4">
        <Link to="/" className="text-lg font-bold">
          ForgeSight AI
        </Link>
        <nav className="flex items-center gap-4">
          {user && ROLES_THAT_CAN_CREATE_INCIDENTS.includes(user.role) && (
            <Link to="/incidents/new" className="text-sm font-medium text-blue-700 hover:underline">
              New Incident
            </Link>
          )}
          {user && (
            <span className="text-sm text-slate-600">
              {user.full_name} <span className="text-slate-400">· {user.role.replace(/_/g, ' ')}</span>
            </span>
          )}
          <Button variant="ghost" onClick={logout}>
            Log out
          </Button>
        </nav>
      </div>
    </header>
  );
}