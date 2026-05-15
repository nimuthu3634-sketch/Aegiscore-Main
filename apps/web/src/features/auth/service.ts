/*
 * API helper functions for the auth feature area.
 */
import { loginWithPassword, type LoginResult } from "../../lib/api";

// Helper function for authenticate Operator logic in this file.
export function authenticateOperator(
  username: string,
  password: string
): Promise<LoginResult> {
  return loginWithPassword(username, password);
}
