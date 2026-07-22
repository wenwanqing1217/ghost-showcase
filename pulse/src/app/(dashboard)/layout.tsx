import DashboardClient from './page.client';

export default function DashboardPage({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-slate-900 border-r border-blue-500/20 p-4">
        <h1 className="text-xl font-bold mb-8">DS Dashboard</h1>
        <nav className="space-y-2">
          <NavItem href="/(dashboard)" label="Overview" />
          <NavItem href="/(dashboard)/agents/content" label="Content Agent" />
          <NavItem href="/(dashboard)/agents/ads" label="Ads Agent" />
          <NavItem href="/(dashboard)/agents/cs" label="CS Agent" />
          <NavItem href="/(dashboard)/revenue" label="Revenue" />
          <NavItem href="/(dashboard)/alerts" label="Alerts" />
          <NavItem href="/(dashboard)/products" label="Products" />
          <NavItem href="/(dashboard)/orders" label="Orders" />
          <NavItem href="/(dashboard)/settings" label="Settings" />
        </nav>
      </aside>
      <main className="flex-1 p-8 overflow-auto">
        {children}
      </main>
    </div>
  );
}

function NavItem({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="block px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
    >
      {label}
    </a>
  );
}
