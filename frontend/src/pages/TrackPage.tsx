import { useState, FormEvent } from "react";
import { requestJsonAllowNonOk } from "../api/client";
import { GitHubProfile, LeetCodeProfile, CodeforcesProfile, FetchStatus } from "../api/types";
import { Button } from "../components/common/Button";
import { TextInput } from "../components/common/TextInput";
import { StatCard } from "../components/common/StatCard";
import { Card, CardHeader, CardTitle, CardContent } from "../components/common/Card";
import { Search, Github, Code, Terminal, AlertTriangle, ExternalLink, RefreshCw, Activity } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from "recharts";

export default function TrackPage() {
  const [githubUser, setGithubUser] = useState("");
  const [leetcodeUser, setLeetcodeUser] = useState("");
  const [codeforcesUser, setCodeforcesUser] = useState("");

  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const [githubData, setGithubData] = useState<GitHubProfile | null>(null);
  const [leetcodeData, setLeetcodeData] = useState<LeetCodeProfile | null>(null);
  const [codeforcesData, setCodeforcesData] = useState<CodeforcesProfile | null>(null);

  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleFetch = async (e?: FormEvent) => {
    if (e) e.preventDefault();
    if (!githubUser && !leetcodeUser && !codeforcesUser) {
      setErrors({ form: "Please enter at least one username" });
      return;
    }

    setErrors({});
    setLoading(true);
    setHasSearched(true);

    setGithubData(null);
    setLeetcodeData(null);
    setCodeforcesData(null);

    const promises: Promise<unknown>[] = [];

    if (githubUser) {
      promises.push(
        requestJsonAllowNonOk<GitHubProfile>(`/api/track/github/${encodeURIComponent(githubUser)}`)
          .then(({ data }) => setGithubData(data))
          .catch(err => setErrors(prev => ({ ...prev, github: err instanceof Error ? err.message : "Network error" })))
      );
    }

    if (leetcodeUser) {
      promises.push(
        requestJsonAllowNonOk<LeetCodeProfile>(`/api/track/leetcode/${encodeURIComponent(leetcodeUser)}`)
          .then(({ data }) => setLeetcodeData(data))
          .catch(err => setErrors(prev => ({ ...prev, leetcode: err instanceof Error ? err.message : "Network error" })))
      );
    }

    if (codeforcesUser) {
      promises.push(
        requestJsonAllowNonOk<CodeforcesProfile>(`/api/track/codeforces/${encodeURIComponent(codeforcesUser)}`)
          .then(({ data }) => setCodeforcesData(data))
          .catch(err => setErrors(prev => ({ ...prev, codeforces: err instanceof Error ? err.message : "Network error" })))
      );
    }

    await Promise.all(promises);
    setLoading(false);
  };

  const renderStatusBadge = (loading: boolean, status: FetchStatus | undefined, networkError: string | undefined) => {
    if (loading) {
      return <span className="text-sm text-slate-500 dark:text-slate-400 px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded">Fetching...</span>;
    }
    if (networkError) {
      return <span className="text-sm text-rose-700 bg-rose-50 px-2 py-1 rounded font-medium border border-rose-200 flex items-center gap-1"><AlertTriangle size={14}/> Network error</span>;
    }
    switch (status) {
      case "success":
        return <span className="text-sm text-emerald-700 bg-emerald-50 px-2 py-1 rounded font-medium border border-emerald-200">Connected</span>;
      case "not_found":
        return <span className="text-sm text-amber-700 bg-amber-50 px-2 py-1 rounded font-medium border border-amber-200">User not found</span>;
      case "rate_limited":
        return <span className="text-sm text-amber-700 bg-amber-50 px-2 py-1 rounded font-medium border border-amber-200">Rate limited — try later</span>;
      case "unauthorized":
        return <span className="text-sm text-rose-700 bg-rose-50 px-2 py-1 rounded font-medium border border-rose-200">Auth required</span>;
      case "timeout":
        return <span className="text-sm text-amber-700 bg-amber-50 px-2 py-1 rounded font-medium border border-amber-200">Upstream timeout</span>;
      case "error":
        return <span className="text-sm text-rose-700 bg-rose-50 px-2 py-1 rounded font-medium border border-rose-200 flex items-center gap-1"><AlertTriangle size={14}/> Upstream error</span>;
      default:
        return null;
    }
  };

  const handleClear = () => {
    setGithubUser("");
    setLeetcodeUser("");
    setCodeforcesUser("");
    setGithubData(null);
    setLeetcodeData(null);
    setCodeforcesData(null);
    setHasSearched(false);
    setErrors({});
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#ffc658'];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Profile Tracker</h1>
        <p className="text-slate-500 dark:text-slate-400">Connect your public coding profiles to fetch powerful analytics.</p>
      </div>

      <Card className="mb-10 shadow-sm border-slate-200 dark:border-slate-800">
        <CardContent className="p-6">
          <form onSubmit={handleFetch} className="grid sm:grid-cols-3 gap-4">
            <TextInput 
              label="GitHub Username" 
              placeholder="e.g. torvalds" 
              value={githubUser} 
              onChange={e => setGithubUser(e.target.value)} 
            />
            <TextInput 
              label="LeetCode Username" 
              placeholder="e.g. neetcode" 
              value={leetcodeUser} 
              onChange={e => setLeetcodeUser(e.target.value)} 
            />
            <TextInput 
              label="Codeforces Handle" 
              placeholder="e.g. tourist" 
              value={codeforcesUser} 
              onChange={e => setCodeforcesUser(e.target.value)} 
            />
            {errors.form && <div className="sm:col-span-3 text-rose-500 text-sm">{errors.form}</div>}
            <div className="sm:col-span-3 flex gap-3 mt-2">
              <Button type="submit" isLoading={loading}>
                <Search size={18} className="mr-2" /> Fetch Profiles
              </Button>
              <Button type="button" variant="outline" onClick={handleClear} disabled={loading}>
                Clear
              </Button>
              <Button type="button" variant="ghost" className="ml-auto" onClick={() => {
                setGithubUser("sriharan2544");
                setLeetcodeUser("sriharan");
                setCodeforcesUser("sriharan");
              }}>
                Use Sample
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {!hasSearched && (
        <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 border-dashed">
          <Activity size={48} className="mx-auto text-slate-300 mb-4" />
          <h2 className="text-xl font-medium mb-2">Enter your platform usernames</h2>
          <p className="text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            Connect your GitHub, LeetCode, or Codeforces accounts to see your engineering activity in one dashboard.
          </p>
        </div>
      )}

      {hasSearched && (
        <div className="space-y-8 flex-col flex">
          {githubUser && (
            <section>
              <div className="flex items-center gap-3 mb-4">
                <Github size={24} />
                <h2 className="text-2xl font-bold">GitHub</h2>
                {renderStatusBadge(loading, githubData?.fetch_status, errors.github)}
              </div>

              {errors.github && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm mb-4">
                  {errors.github}
                </div>
              )}

              {githubData && githubData.fetch_status === "success" && (
                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  <StatCard label="Commits" value={githubData.total_commits} />
                  <StatCard label="Pull Requests" value={githubData.total_pull_requests} />
                  <StatCard label="Repositories" value={githubData.total_repos} />
                  <StatCard label="Languages" value={githubData.total_languages} />
                  
                  <Card className="md:col-span-4">
                    <CardHeader>
                      <CardTitle>Language Distribution</CardTitle>
                    </CardHeader>
                    <CardContent className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={Object.entries(githubData.language_stats).map(([name, value]) => ({ name, value }))} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                          <XAxis type="number" hide />
                          <YAxis dataKey="name" type="category" width={100} axisLine={false} tickLine={false} />
                          <RechartsTooltip cursor={{fill: '#f5f5f5'}} />
                          <Bar dataKey="value" fill="#171717" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              )}
            </section>
          )}

          {leetcodeUser && (
            <section>
              <div className="flex items-center gap-3 mb-4">
                <Code size={24} />
                <h2 className="text-2xl font-bold">LeetCode</h2>
                {renderStatusBadge(loading, leetcodeData?.fetch_status, errors.leetcode)}
              </div>

              {errors.leetcode && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm mb-4">
                  {errors.leetcode}
                </div>
              )}

              {leetcodeData && leetcodeData.fetch_status === "success" && (
                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  <div className="md:col-span-2 grid grid-cols-2 gap-4">
                    <StatCard label="Total Solved" value={leetcodeData.solved} />
                    <StatCard label="Ranking" value={`~${Math.round(leetcodeData.ranking/1000)}k`} />
                    <StatCard label="Easy" value={leetcodeData.easy} valueClassName="text-emerald-600" />
                    <StatCard label="Medium / Hard" value={`${leetcodeData.medium} / ${leetcodeData.hard}`} />
                  </div>
                  
                  <Card className="md:col-span-2">
                    <CardHeader>
                      <CardTitle>Difficulty Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Easy', value: leetcodeData.easy },
                              { name: 'Medium', value: leetcodeData.medium },
                              { name: 'Hard', value: leetcodeData.hard }
                            ]}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                            isAnimationActive={false}
                          >
                            <Cell fill="#00C49F" />
                            <Cell fill="#FFBB28" />
                            <Cell fill="#FF8042" />
                          </Pie>
                          <RechartsTooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              )}
            </section>
          )}

          {codeforcesUser && (
            <section>
              <div className="flex items-center gap-3 mb-4">
                <Terminal size={24} />
                <h2 className="text-2xl font-bold">Codeforces</h2>
                {renderStatusBadge(loading, codeforcesData?.fetch_status, errors.codeforces)}
              </div>

               {errors.codeforces && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm mb-4">
                  {errors.codeforces}
                </div>
              )}

              {codeforcesData && codeforcesData.fetch_status === "success" && (
                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  <StatCard label="Current Rating" value={codeforcesData.rating} />
                  <StatCard label="Max Rating" value={codeforcesData.max_rating} />
                  <StatCard label="Rank" value={<span className="capitalize">{codeforcesData.rank}</span>} />
                  <StatCard label="Contests" value={codeforcesData.contests} />
                  
                  <Card className="md:col-span-4">
                    <CardHeader>
                      <CardTitle>Rating History</CardTitle>
                    </CardHeader>
                    <CardContent className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={codeforcesData.contest_history} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                          <XAxis dataKey="name" hide />
                          <YAxis domain={['auto', 'auto']} axisLine={false} tickLine={false} />
                          <RechartsTooltip />
                          <Line type="monotone" dataKey="rating" stroke="#171717" strokeWidth={2} dot={{r: 4}} activeDot={{r: 6}} isAnimationActive={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              )}
            </section>
          )}

        </div>
      )}
    </div>
  );
}
