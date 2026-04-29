import { Card, CardContent } from "../components/common/Card";
import { useTheme } from "../contexts/ThemeContext";
import { Monitor, Moon, Sun } from "lucide-react";
import { cn } from "../components/common/Button";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold mb-4 text-slate-900 dark:text-white">Settings</h1>
      <p className="text-slate-500 dark:text-slate-400 mb-8 max-w-lg">
        Manage your application preferences and settings.
      </p>

      <div className="space-y-6">
        <section>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Appearance</h2>
          <Card className="dark:bg-slate-900 dark:border-slate-800">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-slate-900 dark:text-white">Theme Preference</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Choose how AIATS looks to you.
                  </p>
                </div>
                <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                  <button
                    onClick={() => setTheme("light")}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                      theme === "light"
                        ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                        : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                    )}
                  >
                    <Sun size={16} /> Light
                  </button>
                  <button
                    onClick={() => setTheme("dark")}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                      theme === "dark"
                        ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                        : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                    )}
                  >
                    <Moon size={16} /> Dark
                  </button>
                  <button
                    onClick={() => setTheme("system")}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                      theme === "system"
                        ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                        : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                    )}
                  >
                    <Monitor size={16} /> System
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
