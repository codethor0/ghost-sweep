import { HomeHero } from "@/components/HomeHero";

interface HomePageProps {
  searchParams?: {
    posting_url?: string | string[];
  };
}

function resolvePostingUrl(value: string | string[] | undefined): string | undefined {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (Array.isArray(value) && value[0]?.trim()) {
    return value[0].trim();
  }
  return undefined;
}

export default function HomePage({ searchParams }: HomePageProps) {
  return (
    <HomeHero
      title="Expose ghost jobs. Restore hiring transparency."
      subtitle="ghost-sweep helps job seekers evaluate companies and postings using evidence-based reports, transparent risk signals, and employer response workflows."
      postingUrl={resolvePostingUrl(searchParams?.posting_url)}
    />
  );
}
