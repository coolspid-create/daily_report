import { sign } from "node:crypto";

type Environment = Record<string, string | undefined>;

type GitHubAppSettings = {
  id: string;
  installationId: string;
  privateKey: string;
};

export type GitHubDispatchSettings = {
  repository: string;
  workflow: string;
  ref: string;
} & ({ app: GitHubAppSettings; token?: never } | { app?: never; token: string });

export type CollectorRunMode = "scheduled" | "press" | "refresh";
type DispatchInputs = Record<string, string>;
const watchdogWorkflow = "press-collection-watchdog.yml";

export function readGitHubDispatchSettings(environment: Environment = process.env): GitHubDispatchSettings {
  const repository = environment.GITHUB_REPOSITORY;
  if (!repository) throw new Error("자동 수집 저장소가 설정되지 않았습니다.");
  const settings = {
    repository,
    workflow: environment.GITHUB_COLLECTOR_WORKFLOW ?? "collector.yml",
    ref: environment.GITHUB_COLLECTOR_REF ?? "main",
  };
  const id = environment.GITHUB_COLLECTOR_APP_ID;
  const installationId = environment.GITHUB_COLLECTOR_INSTALLATION_ID;
  const key = environment.GITHUB_COLLECTOR_APP_PRIVATE_KEY_BASE64;
  if (id || installationId || key) {
    if (!id || !installationId || !key) throw new Error("수집용 GitHub App 설정이 일부 누락되었습니다.");
    return { ...settings, app: { id, installationId, privateKey: Buffer.from(key, "base64").toString("utf8") } };
  }
  const token = environment.GITHUB_ACTIONS_DISPATCH_TOKEN;
  if (!token) throw new Error("자동 수집 실행 환경변수가 설정되지 않았습니다.");
  return { ...settings, token };
}

function githubHeaders(token: string) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

async function installationToken(app: GitHubAppSettings, repository: string, request: typeof fetch): Promise<string> {
  const now = Math.floor(Date.now() / 1_000);
  const encode = (value: object) => Buffer.from(JSON.stringify(value)).toString("base64url");
  const payload = `${encode({ alg: "RS256", typ: "JWT" })}.${encode({ iss: app.id, iat: now - 60, exp: now + 540 })}`;
  const signature = sign("RSA-SHA256", Buffer.from(payload), app.privateKey).toString("base64url");
  const response = await request(
    `https://api.github.com/app/installations/${encodeURIComponent(app.installationId)}/access_tokens`,
    {
      method: "POST",
      headers: githubHeaders(`${payload}.${signature}`),
      body: JSON.stringify({ repositories: [repository.split("/")[1]], permissions: { actions: "write" } }),
      signal: AbortSignal.timeout(10_000),
    },
  );
  if (!response.ok) throw new Error(`수집용 GitHub App 인증에 실패했습니다. (${response.status})`);
  const { token } = await response.json() as { token?: string };
  if (!token) throw new Error("GitHub App 설치 토큰이 응답에 없습니다.");
  return token;
}

export async function dispatchCollectorWorkflow(
  settings: GitHubDispatchSettings,
  mode: CollectorRunMode = "scheduled",
  request: typeof fetch = fetch,
  automatic = false,
): Promise<void> {
  const inputs: DispatchInputs = { scheduled_run: String(mode === "scheduled"), run_mode: mode };
  if (automatic) inputs.automatic = "true";
  await dispatchWorkflow(settings, settings.workflow, inputs, request);
}

export async function dispatchCollectionWatchdog(
  settings: GitHubDispatchSettings,
  mode: Exclude<CollectorRunMode, "refresh">,
) {
  await dispatchWorkflow(settings, watchdogWorkflow, { run_mode: mode }, fetch);
}

async function dispatchWorkflow(settings: GitHubDispatchSettings, workflow: string, inputs: DispatchInputs, request: typeof fetch) {
  const token = settings.app ? await installationToken(settings.app, settings.repository, request) : settings.token;
  const endpoint = `https://api.github.com/repos/${settings.repository}/actions/workflows/${encodeURIComponent(workflow)}/dispatches`;
  const response = await request(endpoint, {
    method: "POST",
    headers: githubHeaders(token),
    body: JSON.stringify({ ref: settings.ref, inputs }),
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`GitHub Actions 실행 요청이 실패했습니다. (${response.status})`);
}
