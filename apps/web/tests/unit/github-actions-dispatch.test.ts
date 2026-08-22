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

  it("fails closed when dispatch credentials are absent", () => {
    expect(() => readGitHubDispatchSettings({ GITHUB_REPOSITORY: "coolspid-create/daily_report" })).toThrow();
  });
});
