import { z } from "zod";
import { getAdminUser } from "@/lib/auth/admin-session";
import { mutationError } from "@/features/admin-review/server/route-response";
import { requestPublicationBuild } from "@/features/admin-review/server/publication-request-service";

const schema = z.object({ publicationDate: z.iso.date(), rangeKey: z.enum(["today", "1d", "7d"]) });

export async function POST(request: Request) {
  if (!(await getAdminUser())) return Response.json({ error: "unauthorized" }, { status: 401 });
  try {
    const value = schema.parse(await request.json());
    return Response.json(await requestPublicationBuild(value.publicationDate, value.rangeKey), { status: 202 });
  } catch (error) { return mutationError(error); }
}
