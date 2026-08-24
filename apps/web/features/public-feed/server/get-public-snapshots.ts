import { createClient } from "@supabase/supabase-js";
import { unstable_cache } from "next/cache";
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

export async function getPublicArchive(preferredDate?: string | null): Promise<PublicArchive> {
  const archive = await loadCachedArchive();
  if (!preferredDate || preferredDate === archive.currentDate || !archive.dates.includes(preferredDate)) {
    return archive;
  }
  return {
    ...archive,
    loadedDate: preferredDate,
    snapshot: await getPublicArchiveSnapshot(preferredDate),
  };
}

export async function getPublicArchiveSnapshot(date: string): Promise<PublicFeedSnapshot | null> {
  return loadCachedSnapshot(date);
}

const loadCachedArchive = unstable_cache(loadLatestArchive, ["public-feed-archive"], {
  revalidate: 60,
  tags: ["public-feed"],
});

async function loadLatestArchive(): Promise<PublicArchive> {
  const supabase = client() as ArchiveClient | null;
  if (!supabase) return { currentDate: null, dates: [], loadedDate: null, snapshot: null };

  const { data, error } = await supabase.rpc("public_archive_dates", { maximum: ARCHIVE_LIMIT });
  if (error || !data) throw new Error("발행 아카이브를 불러오지 못했습니다.");
  const dates = (data as ArchiveDateRow[])
    .map((row) => row.publication_date)
    .filter((value): value is string => Boolean(value));
  const currentDate = dates[0] ?? null;
  return {
    currentDate,
    dates,
    loadedDate: currentDate,
    snapshot: currentDate ? await loadArchiveSnapshot(supabase, currentDate) : null,
  };
}

function loadCachedSnapshot(date: string): Promise<PublicFeedSnapshot | null> {
  return unstable_cache(
    async () => loadSnapshotByDate(date),
    ["public-feed-snapshot", date],
    { revalidate: 60, tags: ["public-feed"] },
  )();
}

async function loadSnapshotByDate(date: string): Promise<PublicFeedSnapshot | null> {
  const supabase = client() as ArchiveClient | null;
  if (!supabase) return null;
  return loadArchiveSnapshot(supabase, date);
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
