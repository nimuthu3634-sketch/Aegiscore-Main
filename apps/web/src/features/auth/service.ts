import { loginWithPassword } from "../../lib/api";

export async function authenticateOperator(username: string, password: string) {
  return loginWithPassword(username, password);
}
