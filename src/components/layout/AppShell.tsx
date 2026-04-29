import { Link, Outlet } from "react-router-dom";
import { Activity, BookOpen, Layers, Shield, Menu, Settings } from "lucide-react";
export default function AppShell() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-200 flex flex-col overflow-hidden">
      <header className="h-16 bg-slate-900 border-b border-slate-700 text-white flex items-center justify-between px-4 shrink-0">
        <div className="max-w-7xl mx-auto w-full flex items-center justify-between">
          <Link to="/" className="text-xl font-semibold tracking-tight flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-500 rounded flex items-center justify-center font-bold text-xl">A</div>
            AIATS <span className="text-slate-400 font-normal hidden sm:inline">| Intelligence Tracking</span>
          </Link>
          <nav className="hidden md:flex gap-6 items-center">
            <Link to="/track" className="text-sm font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1"><Activity size={16}/> Track</Link>
            <Link to="/ats" className="text-sm font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1"><Layers size={16}/> Assess</Link>
            <Link to="/learn" className="text-sm font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1"><BookOpen size={16}/> Learn</Link>
            <Link to="/privacy" className="text-sm font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1"><Shield size={16}/> Privacy</Link>
            <Link to="/settings" className="p-2 ml-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-colors">
              <Settings size={18} />
            </Link>
          </nav>
          <button className="md:hidden p-2 text-slate-300 hover:text-white flex gap-2 items-center">
             <Link to="/settings" className="p-2 mr-2 bg-slate-800 hover:bg-slate-700 rounded-lg"><Settings size={18} /></Link>
             <Menu size={24} />
          </button>
        </div>
      </header>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
      <footer className="h-auto md:h-12 bg-slate-100 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-center px-4 py-2 justify-between text-[10px] font-medium text-slate-400 shrink-0 uppercase tracking-widest">
        <div className="flex items-center gap-4">
          <Link to="/privacy" className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">Privacy</Link>
          <Link to="/contact" className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">Contact</Link>
        </div>
        <div className="mt-2 md:mt-0">&copy; {new Date().getFullYear()} AIATS RESEARCH LABORATORY</div>
      </footer>
    </div>
  );
}
