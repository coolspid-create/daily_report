import { getAdminUser } from "@/lib/auth/admin-session";
import { getReviewItems } from "@/features/admin-review/server/get-review-items";

export async function GET() {
  if (!(await getAdminUser())) return Response.json({ error: "unauthorized" }, { status: 401 });
  return Response.json(await getReviewItems());
}
