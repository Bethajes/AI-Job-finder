import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import axios from "axios";
import type { User } from "@/types";

const ACCESS_TOKEN_COOKIE = "accessToken";

/**
 * Server-side guard for admin routes.
 *
 * The access token is mirrored into a cookie at login (see lib/api.ts), so
 * the RSC layer can verify the session without exposing tokens to markup.
 * Redirects unauthenticated users to login and non-admins to the dashboard.
 */
export async function requireAdmin(): Promise<User> {
  const token = (await cookies()).get(ACCESS_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/admin");
  }

  let user: User;
  try {
    const res = await axios.get<User>(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/me`,
      { headers: { Authorization: `Bearer ${token}` }, timeout: 10_000 }
    );
    user = res.data;
  } catch {
    // Invalid/expired token or unreachable API – send to login.
    redirect("/login?next=/admin");
  }

  if (user.role !== "admin") {
    redirect("/dashboard");
  }
  return user;
}
