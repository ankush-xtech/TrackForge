import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <nav className="flex items-center justify-between px-8 py-4 max-w-7xl mx-auto">
        <div className="text-2xl font-bold text-primary-700">WebWork</div>
        <div className="flex gap-4">
          <Link
            href="/auth/login"
            className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-primary-600 transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/auth/register"
            className="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-8 pt-20 pb-32">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-5xl font-bold text-slate-900 leading-tight mb-6">
            Track Employee Activity.
            <br />
            <span className="text-primary-600">Boost Productivity.</span>
          </h1>
          <p className="text-xl text-slate-600 mb-10 leading-relaxed">
            Monitor time, take screenshots, track applications, generate
            reports, and manage projects — all in one self-hosted platform your
            team controls.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/auth/register"
              className="px-8 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 shadow-lg shadow-primary-200 transition-all"
            >
              Start Free Trial
            </Link>
            <Link
              href="/docs"
              className="px-8 py-3 bg-white text-slate-700 font-semibold rounded-lg border border-slate-200 hover:border-primary-300 transition-all"
            >
              View Documentation
            </Link>
          </div>
        </div>

        {/* Feature highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24">
          {[
            {
              title: "Time Tracking",
              desc: "Automatic and manual time tracking with desktop agent. Know exactly how time is spent.",
              icon: "⏱️",
            },
            {
              title: "Activity Monitoring",
              desc: "Screenshots, app usage, and activity levels. Real-time dashboard for managers.",
              icon: "📊",
            },
            {
              title: "Self-Hosted",
              desc: "Your data stays on your servers. Full control, full privacy, no third-party access.",
              icon: "🔒",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="bg-white p-8 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="text-3xl mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
