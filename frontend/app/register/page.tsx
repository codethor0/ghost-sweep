import { RegisterForm } from "@/components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <section className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-3xl font-bold text-ink">Create account</h1>
      <p className="mt-2 text-sm text-slate">Register for a ghost-sweep account.</p>
      <div className="mt-8">
        <RegisterForm />
      </div>
    </section>
  );
}
