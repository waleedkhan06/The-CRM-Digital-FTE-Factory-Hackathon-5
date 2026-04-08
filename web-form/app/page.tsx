"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { LifeBuoy, Search, ArrowRight, Sparkles, Shield, Zap, Clock } from "lucide-react";
import Header from "@/components/Header";
import AnimatedBackground from "@/components/AnimatedBackground";
import SupportForm from "@/components/SupportForm";
import TicketStatus from "@/components/TicketStatus";

type View = "home" | "submit" | "track";

export default function Home() {
  const [currentView, setCurrentView] = useState<View>("home");

  const stats = [
    { icon: Zap, value: "< 5 min", label: "Avg Response Time", gradient: "from-amber-400 to-orange-500" },
    { icon: Clock, value: "24/7", label: "Always Available", gradient: "from-cyan-400 to-blue-500" },
    { icon: Shield, value: "99.9%", label: "Uptime SLA", gradient: "from-emerald-400 to-teal-500" },
    { icon: Sparkles, value: "AI + Human", label: "Smart Escalation", gradient: "from-purple-400 to-pink-500" },
  ];

  const channels = [
    {
      icon: "💬",
      name: "Web Form",
      desc: "Instant AI response",
      status: "Active",
      color: "from-indigo-500 to-cyan-500",
    },
    {
      icon: "📧",
      name: "Email",
      desc: "support@techcorp.io",
      status: "Active",
      color: "from-blue-500 to-indigo-500",
    },
    {
      icon: "📱",
      name: "WhatsApp",
      desc: "Chat with our AI",
      status: "Active",
      color: "from-emerald-500 to-teal-500",
    },
  ];

  return (
    <div className="relative min-h-screen">
      {/* Background */}
      <AnimatedBackground />

      {/* Content */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Header */}
        <Header />

        {/* Main Content */}
        <main className="flex-1 flex flex-col">
          {currentView === "home" ? (
            <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-12 sm:py-20">
              {/* Hero Section */}
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="text-center max-w-4xl mx-auto mb-16"
              >
                {/* Badge */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 }}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-6"
                >
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm font-medium text-indigo-300">
                    AI-Powered Support — Available 24/7
                  </span>
                </motion.div>

                {/* Headline */}
                <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
                  <span className="text-white">Need Help?</span>
                  <br />
                  <span className="gradient-text">We&apos;re On It.</span>
                </h1>

                {/* Subheadline */}
                <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                  Our AI-powered support team resolves your issues in minutes, not hours.
                  When things get complex, our human experts step in seamlessly.
                </p>

                {/* CTA Buttons */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="flex flex-col sm:flex-row gap-4 justify-center"
                >
                  <button
                    onClick={() => setCurrentView("submit")}
                    className="group px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-500 via-indigo-600 to-cyan-500 text-white font-semibold text-lg hover:shadow-2xl hover:shadow-indigo-500/25 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-3 btn-shine"
                  >
                    <LifeBuoy className="w-5 h-5" />
                    Submit a Request
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                  <button
                    onClick={() => setCurrentView("track")}
                    className="px-8 py-4 rounded-xl glass text-white font-semibold text-lg hover:bg-white/10 transition-all duration-300 flex items-center justify-center gap-3 group"
                  >
                    <Search className="w-5 h-5 group-hover:scale-110 transition-transform" />
                    Track Request
                  </button>
                </motion.div>
              </motion.div>

              {/* Stats Grid */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-16 w-full px-4"
              >
                {stats.map(({ icon: Icon, value, label, gradient }) => (
                  <div
                    key={label}
                    className="glass rounded-2xl p-5 text-center hover:bg-white/[0.07] transition-all duration-300 group"
                  >
                    <div
                      className={`w-10 h-10 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:scale-110 transition-transform duration-300`}
                    >
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">{value}</div>
                    <div className="text-xs text-gray-500 uppercase tracking-wider">{label}</div>
                  </div>
                ))}
              </motion.div>

              {/* Channels */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 }}
                className="max-w-3xl mx-auto w-full px-4"
              >
                <h3 className="text-center text-sm font-medium text-gray-500 uppercase tracking-widest mb-6">
                  Available Channels
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {channels.map((ch) => (
                    <div
                      key={ch.name}
                      className="glass rounded-2xl p-5 hover:bg-white/[0.07] transition-all duration-300 group cursor-pointer"
                      onClick={() => ch.name === "Web Form" && setCurrentView("submit")}
                    >
                      <div className="text-3xl mb-3">{ch.icon}</div>
                      <div className="font-semibold text-white mb-1">{ch.name}</div>
                      <div className="text-xs text-gray-400 mb-3">{ch.desc}</div>
                      <div className="flex items-center gap-1.5">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                        </span>
                        <span className="text-xs text-emerald-400 font-medium">{ch.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* How it works */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="max-w-3xl mx-auto w-full px-4 mt-16 mb-12"
              >
                <h3 className="text-center text-sm font-medium text-gray-500 uppercase tracking-widest mb-8">
                  How It Works
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  {[
                    {
                      step: "01",
                      title: "Describe Your Issue",
                      desc: "Fill out the support form with details about your problem",
                    },
                    {
                      step: "02",
                      title: "AI Responds Instantly",
                      desc: "Our AI analyzes your request and provides a solution in minutes",
                    },
                    {
                      step: "03",
                      title: "Human Escalation If Needed",
                      desc: "Complex issues are seamlessly escalated to our expert team",
                    },
                  ].map((item) => (
                    <div key={item.step} className="relative">
                      <div className="text-5xl font-bold text-indigo-500/20 mb-3">{item.step}</div>
                      <div className="font-semibold text-white mb-2">{item.title}</div>
                      <div className="text-sm text-gray-400">{item.desc}</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>
          ) : currentView === "submit" ? (
            <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-12">
              {/* Back to home */}
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => setCurrentView("home")}
                className="self-start mb-8 flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors group"
              >
                <ArrowRight className="w-4 h-4 rotate-180 group-hover:-translate-x-1 transition-transform" />
                Back to Home
              </motion.button>

              <SupportForm />
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-12">
              {/* Back to home */}
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => setCurrentView("home")}
                className="self-start mb-8 flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors group"
              >
                <ArrowRight className="w-4 h-4 rotate-180 group-hover:-translate-x-1 transition-transform" />
                Back to Home
              </motion.button>

              <TicketStatus onBack={() => setCurrentView("home")} />
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-800/50 py-8 px-4">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-500">
              &copy; {new Date().getFullYear()} TechCorp Solutions Inc. All rights reserved.
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <a href="/privacy" className="hover:text-gray-300 transition-colors">
                Privacy
              </a>
              <a href="/terms" className="hover:text-gray-300 transition-colors">
                Terms
              </a>
              <a href="/status" className="hover:text-gray-300 transition-colors flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                Status
              </a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
