/*
 * TypeScript types used by the users feature area.
 */
export type UserRole = "admin" | "analyst";

// Defines the Create User Payload data shape used by this frontend module.
export type CreateUserPayload = {
  username: string;
  password: string;
  full_name?: string;
  role: UserRole;
};

// Defines the User Record data shape used by this frontend module.
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

// Defines the Create User Response data shape used by this frontend module.
export type CreateUserResponse = {
  user: UserRecord;
  message: string;
};