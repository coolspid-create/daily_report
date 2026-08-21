import { getAdminUser } from "@/lib/auth/admin-session";
import { mutationError } from "@/features/admin-review/server/route-response";
import { approveReviewBatch } from "@/features/admin-review/server/review-service";

export async function POST(request: Request) {
  const user = await getAdminUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });
  try {
    const count = await approveReviewBatch(await request.json(), user);
    return Response.json({ status: "APPROVED", count });
  } catch (error) {
    return mutationError(error);
  }
}
