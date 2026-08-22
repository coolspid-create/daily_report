import { getAdminUser } from "@/lib/auth/admin-session";
import { mutationError } from "@/features/admin-review/server/route-response";
import { approveReviewBatch } from "@/features/admin-review/server/review-service";
import { requestPublicationRefresh } from "@/features/admin-review/server/publication-refresh";

export async function POST(request: Request) {
  const user = await getAdminUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });
  try {
    const count = await approveReviewBatch(await request.json(), user);
    const refresh = await requestPublicationRefresh();
    return Response.json({ status: "APPROVED", count, refresh });
  } catch (error) {
    return mutationError(error);
  }
}
