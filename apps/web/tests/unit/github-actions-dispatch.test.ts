import { generateKeyPairSync, verify } from "node:crypto";
import { describe, expect, it, vi } from "vitest";
import { hasValidCronSecret } from "@/features/automation/server/cron-auth";
import {
  dispatchCollectorWorkflow,
  readGitHubDispatchSettings,
} from "@/features/automation/server/github-actions-dispatch";

describe("Vercel Cron collector dispatch", () => {
  it("accepts only the configured cron authorization header", () => {
    expect(hasValidCronSecret(new Request("https://example.test", { headers: { authorization: "Bearer secret" } }), "secret")).toBe(true);
    expect(hasValidCronSecret(new Request("https://example.test"), "secret")).toBe(false);
  });

  it("dispatches the configured GitHub workflow on main", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    const settings = readGitHubDispatchSettings({
      GITHUB_ACTIONS_DISPATCH_TOKEN: "token",
      GITHUB_REPOSITORY: "coolspid-create/daily_report",
    });
    await dispatchCollectorWorkflow(settings, "scheduled", fetcher);
    expect(fetcher).toHaveBeenCalledWith(
      "https://api.github.com/repos/coolspid-create/daily_report/actions/workflows/collector.yml/dispatches",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ ref: "main", inputs: { scheduled_run: "true", run_mode: "scheduled" } }),
      }),
    );
  });

  it("dispatches a publish-only refresh after an admin approval", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    const settings = readGitHubDispatchSettings({ GITHUB_ACTIONS_DISPATCH_TOKEN: "token", GITHUB_REPOSITORY: "coolspid-create/daily_report" });
    await dispatchCollectorWorkflow(settings, "refresh", fetcher);
    expect(fetcher).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({
      body: JSON.stringify({ ref: "main", inputs: { scheduled_run: "false", run_mode: "refresh" } }),
    }));
  });

  it("dispatches the delayed press collection without enabling Telegram delivery", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    const settings = readGitHubDispatchSettings({ GITHUB_ACTIONS_DISPATCH_TOKEN: "token", GITHUB_REPOSITORY: "coolspid-create/daily_report" });
    await dispatchCollectorWorkflow(settings, "press", fetcher);
    expect(fetcher).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({
      body: JSON.stringify({ ref: "main", inputs: { scheduled_run: "false", run_mode: "press" } }),
    }));
  });

  it("fails closed when dispatch credentials are absent", () => {
    expect(() => readGitHubDispatchSettings({ GITHUB_REPOSITORY: "coolspid-create/daily_report" })).toThrow();
  });

  it("uses a short-lived GitHub App token limited to the collector repository", async () => {
    const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
    const settings = readGitHubDispatchSettings({
      GITHUB_REPOSITORY: "owner/collector",
      GITHUB_ACTIONS_DISPATCH_TOKEN: "old-token",
      GITHUB_COLLECTOR_APP_ID: "123",
      GITHUB_COLLECTOR_INSTALLATION_ID: "456",
      GITHUB_COLLECTOR_APP_PRIVATE_KEY_BASE64: Buffer.from(privateKey.export({ type: "pkcs8", format: "pem" })).toString("base64"),
    });
    const fetcher = vi.fn()
      .mockResolvedValueOnce(Response.json({ token: "installation-token" }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    await dispatchCollectorWorkflow(settings, "scheduled", fetcher, true);
    const [[tokenUrl, tokenRequest], [dispatchUrl, dispatchRequest]] = fetcher.mock.calls;
    expect(tokenUrl).toBe("https://api.github.com/app/installations/456/access_tokens");
    expect(JSON.parse(tokenRequest.body)).toEqual({ repositories: ["collector"], permissions: { actions: "write" } });
    const [header, claims, signature] = tokenRequest.headers.Authorization.slice(7).split(".");
    expect(verify("RSA-SHA256", Buffer.from(`${header}.${claims}`), publicKey, Buffer.from(signature, "base64url"))).toBe(true);
    expect(dispatchUrl).toBe("https://api.github.com/repos/owner/collector/actions/workflows/collector.yml/dispatches");
    expect(dispatchRequest.headers.Authorization).toBe("Bearer installation-token");
    expect(JSON.parse(dispatchRequest.body).inputs.automatic).toBe("true");
  });
});
