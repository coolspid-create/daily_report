import { z } from "zod";
import { getAdminUser } from "@/lib/auth/admin-session";
import { mutationError } from "@/features/admin-review/server/route-response";
import { requestDigestBuild } from "@/features/admin-review/server/publication-request-service";

const schema = z.object({ publicationId: z.uuid(), topicId: z.string().min(1) });

export async function POST(request: Request) {
  if (!(await getAdminUser())) return Response.json({ error: "unauthorized" }, { status: 401 });
  try {
    const value = schema.parse(await request.json());
    return Response.json(await requestDigestBuild(value.publicationId, value.topicId), { status: 202 });
  } catch (error) { return mutationError(error); }
}
