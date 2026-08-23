import { revalidatePath, revalidateTag } from "next/cache";
import { hasValidCronSecret } from "@/features/automation/server/cron-auth";

export const runtime = "nodejs";

export async function POST(request: Request) {
  if (!hasValidCronSecret(request, process.env.FEED_REVALIDATION_SECRET)) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  revalidateTag("public-feed", "max");
  revalidatePath("/");
  return Response.json({ revalidated: true });
}
