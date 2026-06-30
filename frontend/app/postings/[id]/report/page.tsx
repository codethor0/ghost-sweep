import { ReportForm } from "@/components/reports/ReportForm";

interface ReportPageProps {
  params: Promise<{ id: string }>;
}

export default async function ReportPage({ params }: ReportPageProps) {
  const { id } = await params;
  return <ReportForm jobPostingId={id} />;
}
