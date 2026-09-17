import { apiClient } from '../client';
import { TokenResponse, UserResponse } from '@/types/auth';

export async function login(username: string, password: string): Promise<TokenResponse> {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const response = await apiClient.post<TokenResponse>('/auth/token', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
}

export async function getCurrentUser(): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>('/users/me');
  return response.data;
}