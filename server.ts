import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import multer from "multer";

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT) || 3000;

  app.use(express.json());

  // API Routes
  
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok" });
  });

  app.get("/api/track/github/:username", (req, res) => {
    const { username } = req.params;
    // Mock user
    if (username.toLowerCase() === 'error') {
      return res.status(404).json({ error: "User not found or API failure" });
    }
    
    setTimeout(() => {
      res.json({
        total_commits: 1250,
        total_pull_requests: 45,
        total_repos: 28,
        total_languages: 6,
        languages: ["TypeScript", "Python", "HTML", "CSS", "JavaScript", "Rust"],
        language_stats: {
          TypeScript: 45,
          Python: 30,
          HTML: 10,
          CSS: 8,
          JavaScript: 5,
          Rust: 2
        },
        commit_timestamps: [],
        repos: ["aiats", "frontend-app", "scripts"]
      });
    }, 1000);
  });

  app.get("/api/track/leetcode/:username", (req, res) => {
    const { username } = req.params;
    if (username.toLowerCase() === 'error') {
      return res.status(404).json({ error: "User not found or API failure" });
    }
    setTimeout(() => {
      res.json({
        solved: 342,
        easy: 150,
        medium: 152,
        hard: 40,
        ranking: 85000,
        total_languages: 4,
        recent_submissions: []
      });
    }, 800);
  });

  app.get("/api/track/codeforces/:username", (req, res) => {
    const { username } = req.params;
    if (username.toLowerCase() === 'error') {
      return res.status(404).json({ error: "User not found or API failure" });
    }
    setTimeout(() => {
      res.json({
        rating: 1450,
        max_rating: 1520,
        rank: "specialist",
        max_rank: "specialist",
        contests: 24,
        contest_history: [
          { name: "Round 800", rating: 1300, rank: 4000 },
          { name: "Round 801", rating: 1400, rank: 3500 },
          { name: "Round 805", rating: 1450, rank: 3000 }
        ]
      });
    }, 1200);
  });

  app.get("/api/profile", (req, res) => {
    // For when they want to fetch a combined profile
    res.json({ status: "ok" });
  });

  app.post("/api/ats-analyze", upload.single('resume'), (req, res) => {
    // Check fields
    const { job_description, github, leetcode, codeforces } = req.body;
    
    // Simulate processing
    setTimeout(() => {
      res.json({
        score: 72,
        shap_values: {
          "resume_keyword_match": 15,
          "has_python_projects": 8,
          "github_commit_consistency": 5,
          "missing_cloud_experience": -6,
          "short_job_tenure": -4
        },
        top_positive: [
          ["resume_keyword_match", 15],
          ["has_python_projects", 8],
          ["github_commit_consistency", 5]
        ],
        top_negative: [
          ["missing_cloud_experience", -6],
          ["missing_docker", -5],
          ["short_job_tenure", -4]
        ],
        missing_keywords: ["Docker", "AWS", "Kubernetes", "CI/CD"],
        recommendations: {
          score: 72,
          summary: "Good match, but lacking specific cloud and modern deployment skills.",
          priority: "medium",
          total_gaps: 2,
          gaps: [
            {
              skill: "Docker",
              advice: "Learn how to containerize applications.",
              action: "Build a simple Docker image for a Python web app.",
              topic: "DevOps",
              shap_impact: -5,
              feature_label: "missing_docker",
              roadmap_available: true,
              roadmap_url: "/learn/docker"
            },
            {
              skill: "AWS",
              advice: "Understand basic cloud services (EC2, S3).",
              action: "Deploy a small app to AWS EC2.",
              topic: "Cloud",
              shap_impact: -6,
              feature_label: "missing_cloud_experience",
              roadmap_available: true,
              roadmap_url: "/learn/aws"
            }
          ]
        },
        platform_data: {
          github: {
            total_commits: 1250,
            total_repos: 28,
            languages: ["Python", "TypeScript"]
          },
          leetcode: {
            solved: 342,
            ranking: 85000
          },
          codeforces: {
            rating: 1450
          }
        }
      });
    }, 3000);
  });

  app.get("/api/roadmaps", (req, res) => {
    res.json([
      { slug: "frontend", name: "Frontend Developer", category: "Role Based", topicsCount: 24, description: "Learn React, Vue, HTML, CSS." },
      { slug: "backend", name: "Backend Developer", category: "Role Based", topicsCount: 18, description: "Learn Node, Python, DBs, APIs." },
      { slug: "devops", name: "DevOps Engineer", category: "Role Based", topicsCount: 30, description: "Learn Docker, K8s, CI/CD." },
      { slug: "docker", name: "Docker", category: "Skill Based", topicsCount: 8, description: "Containerization fundamentals." },
      { slug: "aws", name: "AWS Basics", category: "Skill Based", topicsCount: 12, description: "Cloud computing with Amazon." }
    ]);
  });

  app.get("/api/roadmaps/:slug", (req, res) => {
    const { slug } = req.params;
    res.json({
      title: slug.charAt(0).toUpperCase() + slug.slice(1) + " Learning Path",
      summary: "A comprehensive guide to mastering " + slug,
      topics: [
        {
          id: 1,
          title: "Introduction",
          status: "completed",
          description: "Understanding the basics and core concepts.",
          resources: [
            { title: "Official Docs", url: "#", type: "docs" },
            { title: "Crash Course", url: "#", type: "video" }
          ]
        },
        {
          id: 2,
          title: "Intermediate Concepts",
          status: "in-progress",
          description: "Diving deeper into advanced features.",
          resources: [
            { title: "Advanced Patterns", url: "#", type: "article" }
          ]
        },
        {
          id: 3,
          title: "Building Projects",
          status: "not-started",
          description: "Putting it all together.",
          resources: [
            { title: "Project Tutorial", url: "#", type: "video" }
          ]
        }
      ]
    });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    // Important: For Express v4, it's app.get('*', ...), but if we use v5, it's app.get('*all', ...).
    // package.json says express ^4.21.2, so app.get('*', ...) is correct.
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
