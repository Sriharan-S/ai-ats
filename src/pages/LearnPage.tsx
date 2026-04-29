import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Search, Book } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/common/Card";
import { TextInput } from "../components/common/TextInput";
import { GlowCard } from "../components/common/GlowCard";

interface RoadmapDef {
  slug: string;
  name: string;
  category: string;
  topicsCount: number;
  description: string;
}

export default function LearnPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [roadmaps, setRoadmaps] = useState<RoadmapDef[]>([]);

  useEffect(() => {
    fetch("/api/roadmaps").then(r => r.json()).then(setRoadmaps);
  }, []);

  const filtered = roadmaps.filter(r => 
    (filter === "All" || r.category === filter) &&
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Roadmap Library</h1>
        <p className="text-slate-500 dark:text-slate-400 max-w-lg mx-auto">Browse role-based and skill-based learning paths designed to cover everything you need to know.</p>
      </div>

      <div className="mb-8">
        <div className="relative max-w-xl mx-auto mb-6">
          <Search className="absolute left-3 top-2.5 text-slate-400" size={20} />
          <TextInput 
            placeholder="Search roadmaps..." 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
            className="pl-10"
          />
        </div>
        
        <div className="flex flex-wrap justify-center gap-2">
          {["All", "Role Based", "Skill Based", "Recommended"].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                filter === f 
                  ? 'bg-slate-900 text-white' 
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:bg-slate-700'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-20 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 border-dashed">
          <Book size={48} className="mx-auto text-slate-300 mb-4" />
          <h2 className="text-xl font-medium mb-2">No roadmaps found</h2>
          <p className="text-slate-500 dark:text-slate-400">Try adjusting your search or filters.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
          {filtered.map((r, i) => (
            <Link key={r.slug} to={`/learn/${r.slug}`} className="block group">
              <GlowCard customSize className="h-full border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900" glowColor={["blue", "purple", "green", "orange"][i % 4] as any}>
                <div className="mb-4">
                  <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded">
                    {r.category}
                  </span>
                </div>
                <h3 className="font-bold text-lg mb-2 group-hover:text-indigo-600 transition-colors">{r.name}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 line-clamp-2">{r.description}</p>
                
                <div className="flex items-center text-xs font-medium text-slate-400 mt-auto">
                  <Book size={14} className="mr-1.5" /> {r.topicsCount} Topics
                </div>
              </GlowCard>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
