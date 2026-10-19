import { beforeEach, describe, expect, it, vi } from "vitest";
const { client } = vi.hoisted(() => ({ client: { from: vi.fn(), rpc: vi.fn() } }));
vi.mock("@/lib/database/service-client", () => ({ createServiceClient: () => client }));
import { getPublicPressArchive, getPublicPressArchiveDate } from "@/features/public-feed/server/get-press-releases";

function row(index: number) {
  return {
    id: `press-${index}`, canonical_title: "과거 보도자료", institution: "정부기관",
    published_at: "2026-08-20", content_tag: "보도자료", why_it_matters: null,
    primary_source_url: "https://example.go.kr/press", delivery_mode: "OFFICIAL_PAGE_ONLY",
    created_at: "2026-08-20T00:00:00Z", updated_at: "2026-08-21T00:00:00Z",
    document_analysis: null, document_files: null,
  };
}

function query() {
  const q = {
    select: vi.fn(), in: vi.fn(), eq: vi.fn(), or: vi.fn(), order: vi.fn(), range: vi.fn(),
  };
  for (const name of ["select", "in", "eq", "or", "order"] as const) q[name].mockReturnValue(q);
  client.from.mockReturnValue(q);
  return q;
}

beforeEach(() => vi.clearAllMocks());

describe("press archive database queries", () => {
  it("loads the chosen old date, including every document beyond 250", async () => {
    client.rpc.mockResolvedValue({ data: [
      { publication_date: "2026-10-19" }, { publication_date: "2026-08-20" },
    ], error: null });
    const q = query();
    q.range.mockResolvedValueOnce({ data: Array.from({ length: 250 }, (_, i) => row(i)), error: null })
      .mockResolvedValueOnce({ data: [row(250)], error: null });
    const archive = await getPublicPressArchive("2026-08-20");
    expect(archive.loadedDate).toBe("2026-08-20");
    expect(archive.reports).toHaveLength(251);
    expect(q.eq).toHaveBeenCalledWith("document_sources.sources.content_type", "PRESS_RELEASE");
    expect(q.select.mock.calls[0][0]).toContain("document_sources!inner(sources!inner(content_type))");
    expect(q.or.mock.calls[0][0]).toContain("published_at.eq.2026-08-20");
    expect(q.range).toHaveBeenLastCalledWith(250, 499);
  });

  it("returns no archive for an empty date and rejects invalid calendar dates", async () => {
    const q = query();
    q.range.mockResolvedValue({ data: [], error: null });
    expect(await getPublicPressArchiveDate("2026-08-20")).toBeNull();
    client.from.mockClear();
    expect(await getPublicPressArchiveDate("2026-02-31")).toBeNull();
    expect(client.from).not.toHaveBeenCalled();
  });
});
