import { fetchApiJson } from "../../lib/api";
import type { CreateUserPayload, CreateUserResponse } from "./types";

export async function createUser(
  payload: CreateUserPayload
): Promise<CreateUserResponse> {
  return fetchApiJson<CreateUserResponse>("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}