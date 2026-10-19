import { useState } from "react";

interface ArchiveSelectorProps {
  label: string;
  activeDate: string | null;
  dates: string[];
  onChange: (date: string) => void;
}

function label(date: string): string {
  const [year, month, day] = date.split("-");
  return `${year}.${month}.${day} 발행본`;
}

export function ArchiveSelector({ label: selectorLabel, activeDate, dates, onChange }: ArchiveSelectorProps) {
  const pageSize = 14;
  const [pageOverride, setPageOverride] = useState<number | null>(null);
  const activePage = Math.floor(Math.max(0, dates.indexOf(activeDate ?? "")) / pageSize);
  const pageCount = Math.ceil(dates.length / pageSize);
  const page = Math.min(pageOverride ?? activePage, Math.max(0, pageCount - 1));
  const pageDates = dates.slice(page * pageSize, (page + 1) * pageSize);
  if (!activeDate || dates.length === 0) return null;

  if (dates.length === 1) {
    return <p className="archive-selector archive-selector-static">{selectorLabel} · {label(activeDate)}</p>;
  }

  return (
    <div className="archive-selector">
      <label>
        <span>{selectorLabel}</span>{" "}
        <select aria-label={`${selectorLabel} 날짜`} value={pageDates.includes(activeDate) ? activeDate : ""}
          onChange={(event) => onChange(event.target.value)}>
          {!pageDates.includes(activeDate) && <option value="" disabled>발행일 선택</option>}
          {pageDates.map((date) => <option key={date} value={date}>{label(date)}</option>)}
        </select>
      </label>
      {pageCount > 1 && (
        <nav aria-label={`${selectorLabel} 페이지`}>
          <button type="button" disabled={page === 0} onClick={() => setPageOverride(page - 1)}>최근 날짜</button>
          <span aria-live="polite"> {page + 1} / {pageCount} </span>
          <button type="button" disabled={page === pageCount - 1} onClick={() => setPageOverride(page + 1)}>이전 날짜</button>
        </nav>
      )}
    </div>
  );
}
