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
  if (!activeDate || dates.length === 0) return null;

  if (dates.length === 1) {
    return <p className="archive-selector archive-selector-static">{selectorLabel} · {label(activeDate)}</p>;
  }

  return (
    <label className="archive-selector">
      <span>{selectorLabel}</span>
      <select aria-label={`${selectorLabel} 날짜`} value={activeDate} onChange={(event) => onChange(event.target.value)}>
        {dates.map((date) => <option key={date} value={date}>{label(date)}</option>)}
      </select>
    </label>
  );
}
