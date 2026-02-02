import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Network, Settings } from 'lucide-react';

const AdminLayout = ({ children }) => {
  const location = useLocation();

  const NavItem = ({ to, icon: Icon, label }) => {
    const isActive = location.pathname === to;
    return (
      <Link 
        to={to} 
        className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-bold uppercase tracking-wider ${
          isActive 
            ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30' 
            : 'text-neutral-500 hover:bg-neutral-800 hover:text-white'
        }`}
      >
        <Icon size={18} />
        <span>{label}</span>
      </Link>
    );
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-black pt-20">
      
      {/* SIDEBAR */}
      <aside className="w-full lg:w-64 p-4 border-r border-neutral-800 lg:min-h-[80vh]">
        <div className="mb-6 px-4">
            <h2 className="text-white font-black text-xl tracking-tighter">COMMAND DECK</h2>
            <p className="text-[10px] text-neutral-500 uppercase">System Admin</p>
        </div>
        <nav className="space-y-1">
          <NavItem to="/admin/dashboard" icon={LayoutDashboard} label="Overview" />
          <NavItem to="/admin/ip" icon={Network} label="IP Manager" />
          <NavItem to="/admin/settings" icon={Settings} label="Settings" />
        </nav>
      </aside>

      {/* CONTENT AREA */}
      <main className="flex-1 p-4 lg:p-8 overflow-x-auto relative">
        {children}
      </main>
    </div>
  );
};

export default AdminLayout;