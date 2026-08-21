import { z } from "zod";
import { getAdminUser } from "@/lib/auth/admin-session";
import { mutationError } from "@/features/admin-review/server/route-response";
import { setSourceActive } from "@/features/source-health/server/source-status-service";

const schema = z.object({ active: z.boolean() });

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!(await getAdminUser())) return Response.json({ error: "unauthorized" }, { status: 401 });
  try {
    const [{ id }, body] = await Promise.all([params, request.json()]);
    const { active } = schema.parse(body);
    await setSourceActive(id, active);
    return Response.json({ active });
  } catch (error) { return mutationError(error); }
}
