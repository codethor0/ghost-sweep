interface DeferredNoticeProps {
  title: string;
  children: React.ReactNode;
}

export function DeferredNotice({ title, children }: DeferredNoticeProps) {
  return (
    <aside className="rounded-xl border border-alert/30 bg-white p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-alert">{title}</h2>
      <div className="mt-2 text-sm leading-6 text-slate">{children}</div>
    </aside>
  );
}
