import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import rawSnapshots from "@/data/public-snapshots.json";
import { PublicFeed } from "@/features/public-feed/components/public-feed";
import { validatePublicSnapshot } from "@/features/public-feed/server/validate-public-snapshot";
import type { PublicArchive } from "@/features/public-feed/types/public-feed";
import { TOPIC_STORAGE_KEY } from "@/features/public-feed/lib/topic-storage";

function archive(): PublicArchive {
  const current = validatePublicSnapshot({ ...rawSnapshots["1d"], range: "7d" });
  const previous = validatePublicSnapshot({ ...rawSnapshots.today, generatedAt: "2026-08-20T00:00:00Z", range: "7d" });
  return {
    currentDate: "2026-08-21",
    dates: ["2026-08-21", "2026-08-20"],
    snapshotsByDate: { "2026-08-21": current, "2026-08-20": previous },
  };
}

describe("public feed", () => {
  it("filters an already-loaded snapshot without navigation", () => {
    render(
      <PublicFeed
        archive={archive()} fallbackSnapshot={validatePublicSnapshot({ ...rawSnapshots["1d"], range: "7d" })}
        initialSelection={{ topic: "all", archiveDate: null, topicFromQuery: false }}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "법·외교·안보" }));
    expect(screen.getByText("「자살예방법」은 무엇을 놓치고 있는가")).toBeVisible();
    expect(screen.queryByText("유통시장의 환경 변화와 경제적 영향에 관한 연구")).not.toBeInTheDocument();
    expect(window.location.search).toBe("?topic=law-security");
  });

  it("restores the stored topic", async () => {
    localStorage.setItem(TOPIC_STORAGE_KEY, "economy");
    render(
      <PublicFeed
        archive={archive()} fallbackSnapshot={validatePublicSnapshot({ ...rawSnapshots["1d"], range: "7d" })}
        initialSelection={{ topic: "all", archiveDate: null, topicFromQuery: false }}
      />,
    );
    await waitFor(() => expect(screen.getByRole("button", { name: "경제·금융" })).toHaveAttribute("aria-pressed", "true"));
    expect(screen.getByText("유통시장의 환경 변화와 경제적 영향에 관한 연구")).toBeVisible();
  });

  it("gives an explicit query topic precedence over local storage", () => {
    localStorage.setItem(TOPIC_STORAGE_KEY, "economy");
    render(
      <PublicFeed
        archive={archive()} fallbackSnapshot={validatePublicSnapshot({ ...rawSnapshots["1d"], range: "7d" })}
        initialSelection={{ topic: "all", archiveDate: null, topicFromQuery: true }}
      />,
    );
    expect(screen.getByRole("button", { name: "전체" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("switches the already-loaded daily archive without a page transition", () => {
    render(
      <PublicFeed
        archive={archive()} fallbackSnapshot={validatePublicSnapshot({ ...rawSnapshots["1d"], range: "7d" })}
        initialSelection={{ topic: "all", archiveDate: null, topicFromQuery: false }}
      />,
    );
    fireEvent.change(screen.getByLabelText("일일 아카이브 날짜"), { target: { value: "2026-08-20" } });
    expect(screen.getByText("최근 7일 꼭 볼 자료 3건")).toBeVisible();
    expect(window.location.search).toBe("?date=2026-08-20");
  });
});
