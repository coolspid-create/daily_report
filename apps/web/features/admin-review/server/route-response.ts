import { ZodError } from "zod";

export function mutationError(error: unknown): Response {
  if (error instanceof ZodError) {
    return Response.json({ error: "입력값이 올바르지 않습니다.", issues: error.issues }, { status: 400 });
  }
  const message = error instanceof Error ? error.message : "요청 처리에 실패했습니다.";
  return Response.json({ error: message }, { status: 500 });
}
