import { getAdminUser } from "@/lib/auth/admin-session";
import { createServiceClient } from "@/lib/database/service-client";

export async function POST(_: Request, context: { params: Promise<{ id: string }> }) {
  const user = await getAdminUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });
  const { id } = await context.params;
  const { error } = await createServiceClient()
    .from("telegram_deliveries")
    .update({ status: "PENDING", last_error: null, updated_at: new Date().toISOString() })
    .eq("id", id)
    .eq("status", "FAILED");
  if (error) return Response.json({ error: "retry_failed" }, { status: 500 });
  return Response.json({ status: "PENDING" });
}
