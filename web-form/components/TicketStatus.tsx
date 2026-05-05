"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Loader2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowLeft,
  MessageSquare,
  User,
  Tag,
  Calendar,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface TicketStatusData {
  ticket_id: string;
  status: string;
  category: string | null;
  priority: string | null;
  created_at: string;
  last_updated: string | null;
  message_count: number;
  last_message_preview: string | null;
  escalated: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
  open: {
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    icon: <Clock className="w-4 h-4" />,
    label: "Open",
  },
  processing: {
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
    icon: <Loader2 className="w-4 h-4 animate-spin" />,
    label: "Processing",
  },
  resolved: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
    icon: <CheckCircle2 className="w-4 h-4" />,
    label: "Resolved",
  },
  escalated: {
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
    icon: <AlertTriangle className="w-4 h-4" />,
    label: "Escalated",
  },
  closed: {
    color: "text-gray-400",
    bg: "bg-gray-500/10 border-gray-500/20",
    icon: <CheckCircle2 className="w-4 h-4" />,
    label: "Closed",
  },
};

export default function TicketStatus({ onBack }: { onBack?: () => void }) {
  const [ticketId, setTicketId] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "found" | "not_found" | "error">("idle");
  const [ticket, setTicket] = useState<TicketStatusData | null>(null);
  const [error, setError] = useState("");

  const handleSearch = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!ticketId.trim()) return;

      setStatus("loading");
      setError("");

      try {
        const response = await fetch(`${API_URL}/support/ticket/${ticketId.trim()}`);

        if (!response.ok) {
          if (response.status === 404) {
            setStatus("not_found");
            return;
          }
          throw new Error("Failed to fetch ticket status");
        }

        const data: TicketStatusData = await response.json();
        setTicket(data);
        setStatus("found");
      } catch {
        setError("Unable to connect to the server. Please try again.");
        setStatus("error");
      }
    },
    [ticketId]
  );

  const statusConfig = ticket ? STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open : null;

  return (
    <div className="relative w-full max-w-xl mx-auto">
      <AnimatePresence mode="wait">
        {status === "found" && ticket ? (
          <motion.div
            key="ticket-found"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="glass-strong rounded-2xl sm:rounded-3xl overflow-hidden"
          >
            {/* Gradient top border */}
            <div className="h-1 bg-gradient-to-r from-indigo-500 via-cyan-500 to-purple-500" />

            <div className="p-6 sm:p-8">
              {/* Back button */}
              {onBack && (
                <button
                  onClick={onBack}
                  className="flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-6 transition-colors group"
                >
                  <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                  Back to search
                </button>
              )}

              {/* Status badge */}
              {statusConfig && (
                <div className="flex items-center gap-3 mb-6">
                  <div
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-full border",
                      statusConfig.bg
                    )}
                  >
                    {statusConfig.icon}
                    <span className={cn("text-sm font-medium", statusConfig.color)}>
                      {statusConfig.label}
                    </span>
                  </div>
                  {ticket.escalated && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20">
                      <AlertTriangle className="w-3 h-3 text-red-400" />
                      <span className="text-xs text-red-400 font-medium">Escalated</span>
                    </div>
                  )}
                </div>
              )}

              {/* Ticket ID */}
              <div className="mb-6">
                <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">
                  Ticket ID
                </div>
                <code className="text-lg font-mono font-bold text-indigo-400">
                  {ticket.ticket_id.slice(0, 8).toUpperCase()}
                </code>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                {ticket.category && (
                  <div className="p-3 rounded-xl bg-white/5">
                    <div className="flex items-center gap-2 text-gray-400 mb-1">
                      <Tag className="w-3.5 h-3.5" />
                      <span className="text-xs">Category</span>
                    </div>
                    <span className="text-sm font-medium text-white capitalize">
                      {ticket.category.replace("_", " ")}
                    </span>
                  </div>
                )}
                {ticket.priority && (
                  <div className="p-3 rounded-xl bg-white/5">
                    <div className="flex items-center gap-2 text-gray-400 mb-1">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span className="text-xs">Priority</span>
                    </div>
                    <span
                      className={cn(
                        "text-sm font-medium capitalize",
                        ticket.priority === "high"
                          ? "text-red-400"
                          : ticket.priority === "medium"
                            ? "text-amber-400"
                            : "text-blue-400"
                      )}
                    >
                      {ticket.priority}
                    </span>
                  </div>
                )}
                <div className="p-3 rounded-xl bg-white/5">
                  <div className="flex items-center gap-2 text-gray-400 mb-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span className="text-xs">Created</span>
                  </div>
                  <span className="text-sm text-white">
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-white/5">
                  <div className="flex items-center gap-2 text-gray-400 mb-1">
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span className="text-xs">Messages</span>
                  </div>
                  <span className="text-sm text-white">{ticket.message_count}</span>
                </div>
              </div>

              {/* Last message preview */}
              {ticket.last_message_preview && (
                <div className="p-4 rounded-xl bg-gradient-to-br from-gray-900/50 to-gray-800/50 border border-gray-700/30 mb-6">
                  <div className="flex items-center gap-2 text-gray-400 mb-2">
                    <User className="w-3.5 h-3.5" />
                    <span className="text-xs">Latest Activity</span>
                  </div>
                  <p className="text-sm text-gray-300 line-clamp-3">
                    {ticket.last_message_preview}
                  </p>
                </div>
              )}

              {/* Progress indicator */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Progress</span>
                  <span>
                    {ticket.status === "resolved" || ticket.status === "closed"
                      ? "Complete"
                      : ticket.status === "escalated"
                        ? "Escalated to human agent"
                        : "In progress"}
                  </span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{
                      width:
                        ticket.status === "resolved" || ticket.status === "closed"
                          ? "100%"
                          : ticket.status === "escalated"
                            ? "75%"
                            : ticket.status === "processing"
                              ? "50%"
                              : "25%",
                    }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={cn(
                      "h-full rounded-full",
                      ticket.status === "resolved" || ticket.status === "closed"
                        ? "bg-gradient-to-r from-emerald-500 to-teal-500"
                        : ticket.status === "escalated"
                          ? "bg-gradient-to-r from-red-500 to-orange-500"
                          : "bg-gradient-to-r from-indigo-500 to-cyan-500"
                    )}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="search"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="glass-strong rounded-2xl sm:rounded-3xl overflow-hidden"
          >
            <div className="h-1 bg-gradient-to-r from-indigo-500 via-cyan-500 to-purple-500" />

            <div className="p-6 sm:p-8">
              {/* Header */}
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 border border-indigo-500/20">
                  <Search className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Track Your Request</h3>
                  <p className="text-sm text-gray-400">
                    Enter your ticket ID to check status
                  </p>
                </div>
              </div>

              {/* Search Form */}
              <form onSubmit={handleSearch} className="space-y-4">
                <div className="relative">
                  <input
                    type="text"
                    value={ticketId}
                    onChange={(e) => {
                      setTicketId(e.target.value);
                      if (status !== "idle") setStatus("idle");
                    }}
                    placeholder="Enter ticket ID (e.g., abc12345-...)"
                    className="w-full px-4 py-3.5 pl-12 rounded-xl bg-gray-900/50 border border-gray-700/50 text-white placeholder-gray-500 input-focus outline-none transition-all duration-300 hover:border-gray-600 font-mono text-sm"
                  />
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                </div>

                <button
                  type="submit"
                  disabled={status === "loading" || !ticketId.trim()}
                  className={cn(
                    "w-full py-3.5 rounded-xl font-medium text-white transition-all duration-300 flex items-center justify-center gap-2",
                    status === "loading" || !ticketId.trim()
                      ? "bg-gray-700 cursor-not-allowed"
                      : "bg-gradient-to-r from-indigo-500 to-cyan-500 hover:shadow-lg hover:shadow-indigo-500/25"
                  )}
                >
                  {status === "loading" ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4" />
                      Check Status
                    </>
                  )}
                </button>
              </form>

              {/* Status Messages */}
              <AnimatePresence>
                {status === "not_found" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-3"
                  >
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-amber-300 font-medium">Ticket not found</p>
                      <p className="text-xs text-amber-400/70 mt-1">
                        Please check the ticket ID and try again.
                      </p>
                    </div>
                  </motion.div>
                )}

                {status === "error" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20"
                  >
                    <p className="text-sm text-red-300">{error}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
