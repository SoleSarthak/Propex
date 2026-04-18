import {
  ShieldAlert,
  Package,
  Globe,
  AlertTriangle
} from "lucide-react";

const StatCard = ({ title, value, icon: Icon, trend }: any) => (
  <div className="p-6 bg-card border rounded-xl shadow-sm hover:shadow-md transition-shadow">
    <div className="flex items-center justify-between mb-4">
      <div className="p-2 bg-primary/10 rounded-lg text-primary">
        <Icon size={24} />
      </div>
      {trend && (
        <span className={`text-xs font-medium px-2 py-1 rounded-full ${
          trend > 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
        }`}>
          {trend > 0 ? '+' : ''}{trend}%
        </span>
      )}
    </div>
    <p className="text-sm text-muted-foreground">{title}</p>
    <h3 className="text-2xl font-bold mt-1">{value}</h3>
  </div>
);

function App() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Security Overview</h1>
        <p className="text-muted-foreground">Monitor vulnerability propagation across your dependency graph.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Active CVEs" value="1,284" icon={ShieldAlert} trend={12} />
        <StatCard title="Affected Packages" value="8,432" icon={Package} trend={-3} />
        <StatCard title="Monitored Repos" value="452" icon={Globe} trend={5} />
        <StatCard title="Critical Risks" value="42" icon={AlertTriangle} trend={0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="p-6 bg-card border rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-6">Recent Propagation Events</h3>
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-4">
                <div className="mt-1">
                  <div className="w-2 h-2 rounded-full bg-rose-500" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium">CVE-2024-1234 detected in @fastify/core</p>
                  <p className="text-xs text-muted-foreground">Propagated to 14 downstream packages • 2m ago</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 bg-card border rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-6">Security Health</h3>
          <div className="flex items-end gap-2 h-32">
            {[40, 60, 45, 90, 85, 100, 95].map((h, i) => (
              <div
                key={i}
                className="flex-1 bg-primary/20 rounded-t-sm hover:bg-primary/40 transition-colors"
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
          <div className="flex justify-between mt-4 text-xs text-muted-foreground">
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
            <span>Sun</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
