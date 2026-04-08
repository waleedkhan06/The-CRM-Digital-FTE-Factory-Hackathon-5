"use client";

import { Shield, Headphones, Zap, Clock } from "lucide-react";
import Link from "next/link";

const features = [
  { icon: Zap, label: "AI-Powered", desc: "Instant smart responses" },
  { icon: Clock, label: "24/7 Available", desc: "Always here for you" },
  { icon: Shield, label: "Secure", desc: "Enterprise-grade privacy" },
  { icon: Headphones, label: "Human Backup", desc: "Escalation when needed" },
];

export default function Header() {
  return (
    <header className="relative z-10 border-b border-indigo-500/10">
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-transparent to-cyan-500/5" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative">
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:shadow-indigo-500/40 transition-shadow duration-300">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-indigo-400 to-cyan-400 opacity-0 group-hover:opacity-100 blur-md transition-opacity duration-300 -z-10" />
            </div>
            <div>
              <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                TechCorp
              </span>
              <span className="hidden sm:block text-[10px] text-gray-500 -mt-1 tracking-widest uppercase">
                Support Center
              </span>
            </div>
          </Link>

          {/* Features */}
          <nav className="hidden lg:flex items-center gap-6">
            {features.map(({ icon: Icon, label, desc }) => (
              <div
                key={label}
                className="flex items-center gap-2.5 text-gray-400 hover:text-gray-200 transition-colors duration-200 group"
              >
                <div className="p-1.5 rounded-lg bg-white/5 group-hover:bg-indigo-500/10 transition-colors duration-200">
                  <Icon className="w-4 h-4 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
                </div>
                <div className="text-xs">
                  <div className="font-medium text-gray-300 group-hover:text-white transition-colors">
                    {label}
                  </div>
                  <div className="text-gray-500 text-[10px]">{desc}</div>
                </div>
              </div>
            ))}
          </nav>

          {/* Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs font-medium text-emerald-400 hidden sm:inline">
              All Systems Operational
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
