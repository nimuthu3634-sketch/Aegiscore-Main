import { loginWithPassword, type LoginResult } from "../../lib/api";

export function authenticateOperator(
  username: string,
  password: string
): Promise<LoginResult> {
  return loginWithPassword(username, password);
}
