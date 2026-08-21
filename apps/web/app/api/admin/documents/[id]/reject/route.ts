import { getAdminUser } from "@/lib/auth/admin-session";
import { mutationError } from "@/features/admin-review/server/route-response";
import { rejectReview } from "@/features/admin-review/server/review-service";

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const user = await getAdminUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });
  try {
    const { id } = await params;
    await rejectReview(id, await request.json(), user);
    return Response.json({ status: "REJECTED" });
  } catch (error) { return mutationError(error); }
}
