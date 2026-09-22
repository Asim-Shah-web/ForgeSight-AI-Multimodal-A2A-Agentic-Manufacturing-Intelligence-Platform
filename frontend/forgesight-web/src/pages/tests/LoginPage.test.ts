import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '../LoginPage';
import { AuthProvider } from '@/contexts/AuthContext';
import * as authApi from '@/api/endpoints/auth';

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('LoginPage', () => {
  it('shows the exact backend error message on invalid credentials', async () => {
    vi.spyOn(authApi, 'login').mockRejectedValue({
      status: 401,
      detail: 'Incorrect username or password',
      requestId: null,
    });

    renderLogin();
    await userEvent.type(screen.getByLabelText('Username'), 'baduser');
    await userEvent.type(screen.getByLabelText('Password'), 'badpass');
    await userEvent.click(screen.getByText('Sign in'));

    await waitFor(() => {
      expect(screen.getByText('Incorrect username or password')).toBeInTheDocument();
    });
  });
});