export type UserRole = "admin" | "analyst";

export type CreateUserPayload = {
  username: string;
  password: string;
  full_name?: string;
  role: UserRole;
};

export type UserRecord = {
  id: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  role: {
    id: string;
    name: UserRole;
  };
};

export type CreateUserResponse = {
  user: UserRecord;
  message: string;
};