import { getAdminUser } from "@/lib/auth/admin-session";
import { mutationError } from "@/features/admin-review/server/route-response";
import { approveReview } from "@/features/admin-review/server/review-service";

export async function POST(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const user = await getAdminUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });
  try {
    const { id } = await params;
    await approveReview(id, user);
    return Response.json({ status: "APPROVED" });
  } catch (error) { return mutationError(error); }
}
