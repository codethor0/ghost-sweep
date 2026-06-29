import { ReportForm } from "@/components/reports/ReportForm";

interface ReportPageProps {
  params: { id: string };
}

export default function ReportPage({ params }: ReportPageProps) {
  return <ReportForm jobPostingId={params.id} />;
}
