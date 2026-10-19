interface DateClient {
  rpc: (name: string, parameters: Record<string, unknown>) => PromiseLike<{
    data: unknown;
    error: { message: string } | null;
  }>;
}

export async function loadArchiveDates(client: DateClient, name: string): Promise<string[]> {
  const dates: string[] = [];
  const pageSize = 100;
  for (let offset = 0; ; offset += pageSize) {
    const { data, error } = await client.rpc(name, { page_offset: offset, page_size: pageSize });
    if (error || !data) throw new Error("발행 아카이브 날짜를 불러오지 못했습니다.");
    const rows = data as { publication_date: string | null }[];
    dates.push(...rows.flatMap((row) => row.publication_date ? [row.publication_date] : []));
    if (rows.length < pageSize) return [...new Set(dates)];
  }
}
