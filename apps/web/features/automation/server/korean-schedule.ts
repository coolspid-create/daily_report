const KOREAN_WEEKEND = new Set(["Sat", "Sun"]);

export function isKoreanCollectionWeekday(now: Date): boolean {
  const weekday = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Seoul",
    weekday: "short",
  }).format(now);
  return !KOREAN_WEEKEND.has(weekday);
}
