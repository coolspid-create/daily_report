interface FeedSectionSelectorProps {
  isPress: boolean;
  reportCount: number;
  pressCount: number;
  onReports: () => void;
  onPress: () => void;
}

export function FeedSectionSelector({ isPress, reportCount, pressCount, onReports, onPress }: FeedSectionSelectorProps) {
  return (
    <nav className="feed-section-nav" aria-label="자료 유형">
      <button type="button" className="pill feed-section-button" aria-pressed={!isPress} onClick={onReports}>
        공공리포트 <span className="topic-count" aria-hidden="true">{reportCount}</span>
      </button>
      <button type="button" className="pill feed-section-button pill-press-release" aria-pressed={isPress} onClick={onPress}>
        보도자료 <span className="topic-count" aria-hidden="true">{pressCount}</span>
      </button>
    </nav>
  );
}
