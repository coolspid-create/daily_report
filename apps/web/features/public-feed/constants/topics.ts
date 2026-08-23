export const TOPICS = [
  { id: "all", label: "전체" },
  { id: "economy", label: "경제·금융" },
  { id: "industry", label: "산업·통상" },
  { id: "ai-tech", label: "AI·과학기술" },
  { id: "labor-welfare", label: "노동·복지" },
  { id: "education-population", label: "교육·인구" },
  { id: "land-environment", label: "국토·환경" },
  { id: "law-security", label: "법·외교·안보" },
  { id: "press-release", label: "보도자료" },
] as const;

export const RESEARCH_TOPICS = TOPICS.filter((t) => t.id !== "press-release");
export const TOPIC_IDS = new Set(TOPICS.map((topic) => topic.id));
export type TopicId = (typeof TOPICS)[number]["id"];

