import * as React from "react";
import { useRef, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/common/Button";
import { GlowCard } from "../components/common/GlowCard";
import { HyperText } from "../components/common/HyperText";
import { Activity, Layers, BookOpen, BrainCircuit, ArrowRight } from "lucide-react";
import { motion, useMotionValue, useMotionTemplate, useAnimationFrame } from "motion/react";

const GridPattern = ({ offsetX, offsetY }: { offsetX: any, offsetY: any }) => {
  return (
    <svg className="w-full h-full">
      <defs>
        <motion.pattern
          id="grid-pattern"
          width="40"
          height="40"
          patternUnits="userSpaceOnUse"
          x={offsetX}
          y={offsetY}
        >
          <path
            d="M 40 0 L 0 0 0 40"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
            className="text-slate-900 dark:text-white" 
          />
        </motion.pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid-pattern)" />
    </svg>
  );
};

export default function HomePage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const words = ["Profile.", "Resume.", "Portfolio.", "Career.", "Skillset."];
  const [wordIndex, setWordIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % words.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const { left, top } = containerRef.current.getBoundingClientRect();
    mouseX.set(e.clientX - left);
    mouseY.set(e.clientY - top);
  };

  const gridOffsetX = useMotionValue(0);
  const gridOffsetY = useMotionValue(0);

  const speedX = 0.5; 
  const speedY = 0.5;

  useAnimationFrame(() => {
    const currentX = gridOffsetX.get();
    const currentY = gridOffsetY.get();
    gridOffsetX.set((currentX + speedX) % 40);
    gridOffsetY.set((currentY + speedY) % 40);
  });

  const maskImage = useMotionTemplate`radial-gradient(300px circle at ${mouseX}px ${mouseY}px, black, transparent)`;

  return (
    <div className="flex flex-col gap-16 pb-16">
      {/* Hero Section */}
      <section 
        ref={containerRef}
        onMouseMove={handleMouseMove}
        className="relative w-full min-h-[85vh] flex flex-col items-center justify-center overflow-hidden bg-slate-50 dark:bg-slate-950 px-4 pt-16 pb-12 box-border"
      >
        {/* Background Effects */}
        <div className="absolute inset-0 z-0 opacity-[0.03]">
          <GridPattern offsetX={gridOffsetX} offsetY={gridOffsetY} />
        </div>
        <motion.div 
          className="absolute inset-0 z-0 opacity-[0.15]"
          style={{ maskImage, WebkitMaskImage: maskImage }}
        >
          <GridPattern offsetX={gridOffsetX} offsetY={gridOffsetY} />
        </motion.div>

        <div className="absolute inset-0 pointer-events-none z-0">
          <div className="absolute right-[-10%] top-[-10%] w-[40%] h-[50%] rounded-full bg-indigo-500/20 blur-[120px]" />
          <div className="absolute left-[-10%] bottom-[-10%] w-[40%] h-[50%] rounded-full bg-emerald-500/20 blur-[120px]" />
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto text-center flex flex-col items-center pointer-events-none">
          <div className="pointer-events-auto inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800 text-sm mb-8 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            AIATS Phase II Live
          </div>
          <h1 className="pointer-events-auto text-5xl md:text-7xl font-bold tracking-tight mb-6 max-w-5xl mx-auto text-slate-900 dark:text-white drop-shadow-sm leading-tight">
            Supercharge your technical{" "}
            <HyperText text={words[wordIndex]} className="text-indigo-600 dark:text-indigo-400 inline-flex font-bold" />
          </h1>
          <p className="pointer-events-auto text-xl text-slate-600 dark:text-slate-400 mb-10 max-w-2xl mx-auto font-medium">
            AIATS analyzes your resume, GitHub commits, and LeetCode activity to build an explainable profile that matches actual job requirements.
          </p>
          <div className="pointer-events-auto flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/ats">
              <Button size="lg" className="w-full sm:w-auto shadow-md">
                Assess Resume <ArrowRight className="ml-2" size={20} />
              </Button>
            </Link>
            <Link to="/track">
              <Button variant="outline" size="lg" className="w-full sm:w-auto shadow-sm bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm hover:bg-white/80 dark:bg-slate-900/80">
                Track Profile <Activity className="ml-2" size={20} />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Overview */}
      <section className="px-4 max-w-7xl mx-auto w-full relative z-10">
        <h2 className="text-3xl font-bold mb-8 text-center text-slate-900 dark:text-white">Platform Capabilities</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <GlowCard customSize className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800" glowColor="blue">
            <div>
              <Activity className="w-10 h-10 text-slate-700 dark:text-slate-300 mb-4" />
              <h3 className="font-bold text-lg mb-2 text-slate-900 dark:text-white">Profile Tracking</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
                Connect GitHub, LeetCode, and Codeforces to showcase your coding consistency and capabilities.
              </p>
            </div>
            <Link to="/track" className="text-sm font-medium text-indigo-600 hover:underline mt-auto">Track Progress &rarr;</Link>
          </GlowCard>
          <GlowCard customSize className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800" glowColor="purple">
            <div>
              <Layers className="w-10 h-10 text-slate-700 dark:text-slate-300 mb-4" />
              <h3 className="font-bold text-lg mb-2 text-slate-900 dark:text-white">ATS Assessment</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
                Match your resume and public profiles against real job descriptions to identify missing skills.
              </p>
            </div>
            <Link to="/ats" className="text-sm font-medium text-indigo-600 hover:underline mt-auto">Try ATS &rarr;</Link>
          </GlowCard>
          <GlowCard customSize className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800" glowColor="green">
            <div>
              <BrainCircuit className="w-10 h-10 text-slate-700 dark:text-slate-300 mb-4" />
              <h3 className="font-bold text-lg mb-2 text-slate-900 dark:text-white">Explainable AI</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
                Understand exactly why your score changed with transparent SHAP feature breakdowns.
              </p>
            </div>
            <Link to="/privacy" className="text-sm font-medium text-indigo-600 hover:underline mt-auto">See Analysis &rarr;</Link>
          </GlowCard>
          <GlowCard customSize className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800" glowColor="orange">
            <div>
              <BookOpen className="w-10 h-10 text-slate-700 dark:text-slate-300 mb-4" />
              <h3 className="font-bold text-lg mb-2 text-slate-900 dark:text-white">Learning Roadmaps</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
                Turn skill gaps into action with concrete learning roadmaps explicitly tied to job roles.
              </p>
            </div>
            <Link to="/learn" className="text-sm font-medium text-indigo-600 hover:underline mt-auto">Browse Roadmaps &rarr;</Link>
          </GlowCard>
        </div>
      </section>

      {/* Architecture */}
      <section className="px-4 max-w-5xl mx-auto w-full text-center mt-4 bg-slate-900 text-white rounded-3xl p-12 shadow-xl border border-slate-800 relative z-10">
        <h2 className="text-3xl font-bold mb-4">How it works</h2>
        <p className="text-slate-400 mb-12 max-w-2xl mx-auto">Our transparent scoring pipeline turns your artifacts into actionable insights.</p>
        
        <div className="grid sm:grid-cols-3 gap-8">
          <div>
            <div className="text-4xl font-bold mb-2 text-indigo-400">1</div>
            <h4 className="font-bold mb-2">Connect</h4>
            <p className="text-sm text-slate-400">Upload resume and connect GitHub to build your initial feature profile.</p>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2 text-emerald-400">2</div>
            <h4 className="font-bold mb-2">Analyze</h4>
            <p className="text-sm text-slate-400">Our model scores your profile against job descriptions and calculates SHAP values.</p>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2 text-amber-400">3</div>
            <h4 className="font-bold mb-2">Improve</h4>
            <p className="text-sm text-slate-400">Follow personalized roadmaps to close your skill gaps and raise your score.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
