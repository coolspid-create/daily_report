import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const origin = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  return [{ url: origin, changeFrequency: "daily", priority: 1 }];
}
