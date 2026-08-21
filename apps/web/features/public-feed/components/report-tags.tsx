interface ReportTagsProps {
  tags: string[];
}

export function ReportTags({ tags }: ReportTagsProps) {
  return (
    <ul className="report-tags" aria-label="핵심 키워드">
      {tags.slice(0, 3).map((tag) => <li key={tag}>{tag}</li>)}
    </ul>
  );
}
