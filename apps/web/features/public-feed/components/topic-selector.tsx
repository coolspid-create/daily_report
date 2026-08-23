import { RESEARCH_TOPICS, type TopicId } from "../constants/topics";
import type { TopicSummary } from "../types/public-feed";

interface TopicSelectorProps {
  activeTopic: TopicId;
  topicSummaries?: TopicSummary[];
  pressReleaseCount?: number;
  onChange: (topic: TopicId) => void;
}

export function TopicSelector({
  activeTopic,
  topicSummaries,
  pressReleaseCount,
  onChange,
}: TopicSelectorProps) {
  const countMap = new Map((topicSummaries ?? []).map((t) => [t.id, t.count]));

  return (
    <div className="topic-bar-container" aria-label="관심 분야">
      <div className="topic-scroll">
        {RESEARCH_TOPICS.map((topic) => {
          const count = countMap.get(topic.id);
          return (
            <button
              className="pill"
              key={topic.id}
              type="button"
              aria-label={topic.label}
              aria-pressed={activeTopic === topic.id}
              onClick={() => onChange(topic.id)}
            >
              <span>{topic.label}</span>
              {count !== undefined && count > 0 && (
                <span className="topic-count" aria-hidden="true">
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div className="topic-press-release-tab">
        <button
          className="pill pill-press-release"
          type="button"
          aria-label="보도자료 (24H)"
          aria-pressed={activeTopic === "press-release"}
          onClick={() => onChange("press-release")}
        >
          <span className="press-tab-icon" aria-hidden="true">📰</span>
          <span>보도자료</span>
          <span className="press-24h-tag">24H</span>
          {pressReleaseCount !== undefined && pressReleaseCount > 0 && (
            <span className="topic-count" aria-hidden="true">
              {pressReleaseCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}

