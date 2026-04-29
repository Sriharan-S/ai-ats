import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Activity, BookOpen, Layers, Menu, Settings, Shield, X } from "lucide-react";

const navItems = [
  { to: "/track", label: "Track", icon: Activity },
  { to: "/ats", label: "Assess", icon: Layers },
  { to: "/learn", label: "Learn", icon: BookOpen },
  { to: "/privacy", label: "Privacy", icon: Shield },
];

function navLinkClass({ isActive }: { isActive: boolean }) {
  return [
    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
    isActive
      ? "bg-slate-800 text-white"
      : "text-slate-300 hover:bg-slate-800 hover:text-white",
  ].join(" ");
}

export default function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-200 flex flex-col overflow-hidden">
      <header className="bg-slate-900 border-b border-slate-700 text-white shrink-0">
        <div className="max-w-7xl mx-auto h-16 px-4 flex items-center justify-between">
          <NavLink to="/" className="text-xl font-semibold tracking-tight flex items-center gap-2" onClick={() => setMobileOpen(false)}>
            <div className="w-8 h-8 bg-indigo-500 rounded flex items-center justify-center font-bold text-xl">A</div>
            AIATS <span className="text-slate-400 font-normal hidden sm:inline">| Intelligence Tracking</span>
          </NavLink>

          <nav className="hidden md:flex gap-2 items-center">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={navLinkClass}>
                <Icon size={16} /> {label}
              </NavLink>
            ))}
            <NavLink to="/settings" className={navLinkClass} aria-label="Settings">
              <Settings size={16} /> Settings
            </NavLink>
          </nav>

          <button
            type="button"
            className="md:hidden inline-flex items-center justify-center rounded-lg p-2 text-slate-300 hover:bg-slate-800 hover:text-white"
            aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((open) => !open)}
          >
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {mobileOpen && (
          <nav className="md:hidden border-t border-slate-800 px-4 py-3 space-y-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={navLinkClass} onClick={() => setMobileOpen(false)}>
                <Icon size={16} /> {label}
              </NavLink>
            ))}
            <NavLink to="/settings" className={navLinkClass} onClick={() => setMobileOpen(false)}>
              <Settings size={16} /> Settings
            </NavLink>
          </nav>
        )}
      </header>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>

      <footer className="h-auto md:h-12 bg-slate-100 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-center px-4 py-2 justify-between text-[10px] font-medium text-slate-400 shrink-0 uppercase tracking-widest">
        <div className="flex items-center gap-4">
          <NavLink to="/privacy" className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">Privacy</NavLink>
          <NavLink to="/contact" className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">Contact</NavLink>
        </div>
        <div className="mt-2 md:mt-0">&copy; {new Date().getFullYear()} AIATS Research Laboratory</div>
      </footer>
    </div>
  );
}
