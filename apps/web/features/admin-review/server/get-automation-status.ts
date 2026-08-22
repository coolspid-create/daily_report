import { createServiceClient } from "@/lib/database/service-client";
import type { AutomationStatus } from "../types/admin-review";

export async function getAutomationStatus(): Promise<AutomationStatus | null> {
  const client = createServiceClient();
  const { data: run, error } = await client
    .from("automation_runs")
    .select("*")
    .order("scheduled_for", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw new Error("자동 발행 상태를 불러오지 못했습니다.");
  if (!run) return null;
  const publicationDate = formatPublicationDate(String(run.scheduled_for));
  const { data: publication } = await client
    .from("daily_publications")
    .select("id")
    .eq("publication_date", publicationDate)
    .eq("range_key", "7d")
    .order("published_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  const { data: delivery } = publication ? await client
    .from("telegram_deliveries")
    .select("id,status,last_error")
    .eq("publication_id", publication.id)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle() : { data: null };
  return {
    id: String(run.id),
    status: run.status as AutomationStatus["status"],
    stage: String(run.stage),
    scheduledFor: String(run.scheduled_for),
    scheduledForLabel: formatScheduledFor(String(run.scheduled_for)),
    collectedCount: Number(run.collected_count),
    autoApprovedCount: Number(run.approved_count),
    exceptionCount: Number(run.exception_count),
    publishedCount: Number(run.published_count),
    errorMessage: run.error_message ? String(run.error_message) : null,
    telegramDeliveryId: delivery?.id ? String(delivery.id) : null,
    telegramStatus: delivery?.status as AutomationStatus["telegramStatus"] ?? null,
    telegramError: delivery?.last_error ? String(delivery.last_error) : null,
  };
}

function formatScheduledFor(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function formatPublicationDate(value: string): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date(value));
  const part = (type: Intl.DateTimeFormatPartTypes) => parts.find((item) => item.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")}`;
}
