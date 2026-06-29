import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <section className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-3xl font-bold text-ink">Log in</h1>
      <p className="mt-2 text-sm text-slate">Sign in with your email or username.</p>
      <div className="mt-8">
        <LoginForm />
      </div>
    </section>
  );
}
