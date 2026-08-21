export function hasValidCronSecret(request: Request, secret: string | undefined): boolean {
  return Boolean(secret) && request.headers.get("authorization") === `Bearer ${secret}`;
}
