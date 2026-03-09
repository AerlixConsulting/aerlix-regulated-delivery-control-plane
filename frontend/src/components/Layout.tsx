import { Outlet, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Shield,
  Package,
  GitBranch,
  AlertTriangle,
  FileDown,
  Link,
} from "lucide-react";
import clsx from "clsx";

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Overview" },
  { to: "/requirements", icon: FileText, label: "Requirements" },
  { to: "/controls", icon: Shield, label: "Controls & Evidence" },
  { to: "/supply-chain", icon: Package, label: "Supply Chain" },
  { to: "/release-gates", icon: GitBranch, label: "Release Gates" },
  { to: "/traceability", icon: Link, label: "Traceability" },
  { to: "/incidents", icon: AlertTriangle, label: "Incidents & Exceptions" },
  { to: "/audit", icon: FileDown, label: "Audit Export" },
];

export default function Layout() {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield size={16} className="text-white" />
            </div>
            <div>
              <div className="text-sm font-bold text-white">Aerlix</div>
              <div className="text-xs text-slate-400">Control Plane</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800">
          <div className="text-xs text-slate-500">
            <div className="font-medium text-slate-400">Aerlix Consulting</div>
            <div>v0.1.0 — NIST 800-53 Rev5</div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
