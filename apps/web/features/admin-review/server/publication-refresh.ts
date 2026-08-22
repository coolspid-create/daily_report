import {
  dispatchCollectorWorkflow,
  readGitHubDispatchSettings,
} from "@/features/automation/server/github-actions-dispatch";

export type PublicationRefreshResult =
  | { status: "QUEUED" }
  | { status: "FAILED"; message: string };

export async function requestPublicationRefresh(): Promise<PublicationRefreshResult> {
  try {
    await dispatchCollectorWorkflow(readGitHubDispatchSettings(), "refresh");
    return { status: "QUEUED" };
  } catch (error) {
    const message = error instanceof Error ? error.message : "재발행 요청에 실패했습니다.";
    return { status: "FAILED", message };
  }
}
