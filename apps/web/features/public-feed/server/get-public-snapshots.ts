import { createClient } from "@supabase/supabase-js";
import fallbackData from "@/data/public-snapshots.json";
import type { PublicArchive, PublicFeedSnapshot } from "../types/public-feed";
import { validatePublicSnapshot } from "./validate-public-snapshot";

const ARCHIVE_LIMIT = 14;

interface ArchiveDateRow {
  publication_date: string | null;
}

interface ArchiveClient {
  rpc: (functionName: string, parameters: Record<string, unknown>) => Promise<{
    data: unknown;
    error: { message: string } | null;
  }>;
}

function client() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  return url && key ? createClient(url, key, { auth: { persistSession: false } }) : null;
}

export async function getPublicArchive(): Promise<PublicArchive> {
  const supabase = client() as ArchiveClient | null;
  if (!supabase) return { currentDate: null, dates: [], snapshotsByDate: {} };

  const { data, error } = await supabase.rpc("public_archive_dates", { maximum: ARCHIVE_LIMIT });
  if (error || !data) throw new Error("발행 아카이브를 불러오지 못했습니다.");
  const dates = (data as ArchiveDateRow[])
    .map((row) => row.publication_date)
    .filter((value): value is string => Boolean(value));
  const snapshots = await Promise.all(dates.map((date) => loadArchiveSnapshot(supabase, date)));
  const snapshotsByDate = Object.fromEntries(
    dates.flatMap((date, index) => snapshots[index] ? [[date, snapshots[index]]] : []),
  );
  return { currentDate: dates[0] ?? null, dates, snapshotsByDate };
}

async function loadArchiveSnapshot(
  supabase: ArchiveClient, date: string,
): Promise<PublicFeedSnapshot | null> {
  const { data, error } = await supabase.rpc("public_archive_snapshot", { target_date: date });
  if (error) throw new Error("발행본을 불러오지 못했습니다.");
  return data ? validatePublicSnapshot(data) : null;
}

export function getFallbackSnapshot(): PublicFeedSnapshot {
  return validatePublicSnapshot({ ...fallbackData["1d"], range: "7d" });
}
