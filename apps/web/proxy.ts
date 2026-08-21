import type { NextRequest } from "next/server";
import { updateSession } from "@/lib/auth/update-session";

export async function proxy(request: NextRequest) {
  return updateSession(request);
}

export const proxyConfig = {
  matcher: ["/admin/:path*", "/api/admin/:path*"],
};
