import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ArchiveSelector } from "@/features/public-feed/components/archive-selector";
import { loadArchiveDates } from "@/features/public-feed/server/load-archive-dates";

const dates = Array.from({ length: 45 }, (_, index) =>
  new Date(Date.UTC(2026, 9, 19 - index)).toISOString().slice(0, 10));

describe("archive date pagination", () => {
  it("reaches old dates and returns to the newest dates", () => {
    const onChange = vi.fn();
    render(<ArchiveSelector label="리포트 아카이브" activeDate={dates[0]} dates={dates} onChange={onChange} />);
    expect(screen.getByRole("button", { name: "최근 날짜" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "이전 날짜" }));
    expect(screen.getByRole("option", { name: `${dates[14].replaceAll("-", ".")} 발행본` })).toBeVisible();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: dates[14] } });
    expect(onChange).toHaveBeenCalledWith(dates[14]);
    fireEvent.click(screen.getByRole("button", { name: "이전 날짜" }));
    fireEvent.click(screen.getByRole("button", { name: "이전 날짜" }));
    expect(screen.getByRole("button", { name: "이전 날짜" })).toBeDisabled();
    expect(screen.getByText("4 / 4")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "최근 날짜" }));
    expect(screen.getByText("3 / 4")).toBeVisible();
  });

  it("opens the correct page for a deep-linked date", () => {
    render(<ArchiveSelector label="리포트 아카이브" activeDate={dates[32]} dates={dates} onChange={vi.fn()} />);
    expect(screen.getByRole("combobox")).toHaveValue(dates[32]);
    expect(screen.getByText("3 / 4")).toBeVisible();
  });

  it("reads all metadata pages beyond the database page size", async () => {
    const rows = Array.from({ length: 101 }, (_, i) => ({ publication_date: `date-${i}` }));
    const rpc = vi.fn().mockResolvedValueOnce({ data: rows.slice(0, 100), error: null })
      .mockResolvedValueOnce({ data: rows.slice(100), error: null });
    expect(await loadArchiveDates({ rpc }, "public_archive_dates_page")).toHaveLength(101);
    expect(rpc).toHaveBeenLastCalledWith("public_archive_dates_page", { page_offset: 100, page_size: 100 });
  });
});
