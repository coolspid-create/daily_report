type Environment = Record<string, string | undefined>;

export type GitHubDispatchSettings = {
  repository: string;
  workflow: string;
  ref: string;
  token: string;
};

export type CollectorRunMode = "scheduled" | "refresh";

export function readGitHubDispatchSettings(environment: Environment = process.env): GitHubDispatchSettings {
  const token = environment.GITHUB_ACTIONS_DISPATCH_TOKEN;
  const repository = environment.GITHUB_REPOSITORY;
  if (!token || !repository) throw new Error("자동 수집 실행 환경변수가 설정되지 않았습니다.");
  return {
    token,
    repository,
    workflow: environment.GITHUB_COLLECTOR_WORKFLOW ?? "collector.yml",
    ref: environment.GITHUB_COLLECTOR_REF ?? "main",
  };
}

export async function dispatchCollectorWorkflow(
  settings: GitHubDispatchSettings,
  mode: CollectorRunMode = "scheduled",
  request: typeof fetch = fetch,
): Promise<void> {
  const endpoint = `https://api.github.com/repos/${settings.repository}/actions/workflows/${encodeURIComponent(settings.workflow)}/dispatches`;
  const response = await request(endpoint, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${settings.token}`,
      "Content-Type": "application/json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({
      ref: settings.ref,
      inputs: { scheduled_run: String(mode === "scheduled"), run_mode: mode },
    }),
  });
  if (!response.ok) throw new Error(`GitHub Actions 실행 요청이 실패했습니다. (${response.status})`);
}
