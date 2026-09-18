export type UserRole =
  | 'production_operator'
  | 'quality_engineer'
  | 'manufacturing_engineer'
  | 'maintenance_engineer'
  | 'quality_manager'
  | 'supplier_quality_engineer'
  | 'system_administrator'
  | 'agent_orchestrator';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  user_id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}