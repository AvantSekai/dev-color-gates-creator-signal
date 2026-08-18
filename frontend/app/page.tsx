import Link from "next/link";

import { fetchSummary } from "@/lib/api";

const DISPLAY_LIMIT = 50;

export default async function SummaryPage() {
  const { meta, creators } = await fetchSummary();
  const shown = creators.slice(0, DISPLAY_LIMIT);

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Creator Signal</h1>
        <Link href="/chat" className="text-sm underline">
          Ask a question &rarr;
        </Link>
      </div>

      <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        Sample data only &mdash; {meta.date_range[0]} to {meta.date_range[1]}. Not live/current
        trending data; this is a methodology demo, not a real-time feed.
      </div>

      <dl className="mb-8 grid grid-cols-3 gap-4">
        <StatTile label="Creators evaluated" value={meta.total_creators} />
        <StatTile label="Promising pool" value={meta.promising_count} />
        <StatTile label="Showing top" value={shown.length} />
      </dl>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-300 text-left">
              <th className="py-2 pr-4">#</th>
              <th className="py-2 pr-4">Creator</th>
              <th className="py-2 pr-4">Total views</th>
              <th className="py-2 pr-4">Engagement rate</th>
              <th className="py-2 pr-4">Videos</th>
              <th className="py-2">Sample caption</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((c, i) => (
              <tr key={c.handle} className="border-b border-gray-100">
                <td className="py-2 pr-4 text-gray-500">{i + 1}</td>
                <td className="py-2 pr-4 font-medium">
                  {c.handle}
                  {c.verified && (
                    <span className="ml-1 text-blue-600" title="Verified">
                      ✓
                    </span>
                  )}
                </td>
                <td className="py-2 pr-4">{c.total_views.toLocaleString()}</td>
                <td className="py-2 pr-4">{(c.engagement_rate * 100).toFixed(1)}%</td>
                <td className="py-2 pr-4">{c.video_count}</td>
                <td className="max-w-xs truncate py-2 text-gray-600">
                  {c.sample_caption ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-gray-200 px-4 py-3">
      <dt className="text-xs tracking-wide text-gray-500 uppercase">{label}</dt>
      <dd className="text-2xl font-semibold">{value.toLocaleString()}</dd>
    </div>
  );
}
