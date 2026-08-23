import { PublicFeed } from "@/features/public-feed/components/public-feed";
import { parseInitialSelection } from "@/features/public-feed/lib/initial-selection";
import { getFallbackSnapshot, getPublicArchive } from "@/features/public-feed/server/get-public-snapshots";
import { getLatestPressReleases } from "@/features/public-feed/server/get-press-releases";

export const revalidate = 60;

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function HomePage({ searchParams }: PageProps) {
  const query = await searchParams;
  const selection = parseInitialSelection(query);
  const [archive, pressReleases] = await Promise.all([
    getPublicArchive(selection.archiveDate),
    getLatestPressReleases(),
  ]);
  return (
    <PublicFeed
      archive={archive}
      fallbackSnapshot={getFallbackSnapshot()}
      initialSelection={selection}
      pressReleases={pressReleases}
    />
  );
}
