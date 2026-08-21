interface ArchiveSelectorProps {
  activeDate: string | null;
  dates: string[];
  onChange: (date: string) => void;
}

function label(date: string): string {
  const [year, month, day] = date.split("-");
  return `${year}.${month}.${day} 발행본`;
}

export function ArchiveSelector({ activeDate, dates, onChange }: ArchiveSelectorProps) {
  if (dates.length < 2 || !activeDate) return null;

  return (
    <label className="archive-selector">
      <span>일일 아카이브</span>
      <select aria-label="일일 아카이브 날짜" value={activeDate} onChange={(event) => onChange(event.target.value)}>
        {dates.map((date) => <option key={date} value={date}>{label(date)}</option>)}
      </select>
    </label>
  );
}
