"use client";

import { useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Mail,
  Phone,
  LifeBuoy,
  Sparkles,
  ArrowRight,
  Copy,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ─────────────────────────────────────────────────────────────────

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

interface FormErrors {
  [key: string]: string | undefined;
}

interface SubmitResponse {
  ticket_id: string;
  message: string;
  estimated_response_time: string;
  ai_response?: string;
  escalated?: boolean;
  escalation_reason?: string;
}

// ─── Constants ─────────────────────────────────────────────────────────────

const CATEGORIES = [
  { value: "general", label: "General Question", icon: "💬", color: "from-blue-500 to-indigo-500" },
  { value: "technical", label: "Technical Support", icon: "🔧", color: "from-orange-500 to-red-500" },
  { value: "billing", label: "Billing Inquiry", icon: "💳", color: "from-emerald-500 to-teal-500" },
  { value: "bug_report", label: "Bug Report", icon: "🐛", color: "from-pink-500 to-rose-500" },
  { value: "feedback", label: "Feedback", icon: "⭐", color: "from-amber-500 to-yellow-500" },
];

const PRIORITIES = [
  { value: "low", label: "Low", desc: "Not urgent", color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
  { value: "medium", label: "Medium", desc: "Need help soon", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  { value: "high", label: "High", desc: "Urgent issue", color: "text-red-400 bg-red-500/10 border-red-500/20" },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

// ─── Main Component ────────────────────────────────────────────────────────

export default function SupportForm() {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    email: "",
    subject: "",
    category: "general",
    priority: "medium",
    message: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [responseMessage, setResponseMessage] = useState("");
  const [estimatedTime, setEstimatedTime] = useState("");
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [escalated, setEscalated] = useState(false);
  const [activeField, setActiveField] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // ─── Validation ───────────────────────────────────────────────────────

  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim() || formData.name.trim().length < 2) {
      newErrors.name = "Name must be at least 2 characters";
    }
    if (!formData.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }
    if (!formData.subject.trim() || formData.subject.trim().length < 5) {
      newErrors.subject = "Subject must be at least 5 characters";
    }
    if (!formData.message.trim() || formData.message.trim().length < 10) {
      newErrors.message = "Please describe your issue in detail (at least 10 characters)";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  // ─── Handlers ─────────────────────────────────────────────────────────

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { name, value } = e.target;
      setFormData((prev) => ({ ...prev, [name]: value }));
      // Clear error on change
      if (errors[name]) {
        setErrors((prev) => {
          const next = { ...prev };
          delete next[name];
          return next;
        });
      }
    },
    [errors]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validate()) return;

      setStatus("submitting");

      try {
        const response = await fetch(`${API_URL}/support/submit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || "Submission failed. Please try again.");
        }

        const data: SubmitResponse = await response.json();
        setTicketId(data.ticket_id);
        setResponseMessage(data.message);
        setEstimatedTime(data.estimated_response_time);
        setAiResponse(data.ai_response || null);
        setEscalated(data.escalated || false);
        setStatus("success");
      } catch (err) {
        setErrors({ form: err instanceof Error ? err.message : "An unexpected error occurred" });
        setStatus("error");
      }
    },
    [formData, validate]
  );

  const copyTicketId = useCallback(() => {
    if (ticketId) {
      navigator.clipboard.writeText(ticketId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [ticketId]);

  const resetForm = useCallback(() => {
    setFormData({
      name: "",
      email: "",
      subject: "",
      category: "general",
      priority: "medium",
      message: "",
    });
    setErrors({});
    setStatus("idle");
    setTicketId(null);
    setResponseMessage("");
    setEstimatedTime("");
    setAiResponse(null);
    setEscalated(false);
  }, []);

  // ─── Character count ──────────────────────────────────────────────────

  const messageLength = useMemo(() => formData.message.length, [formData.message]);
  const messageLimit = 1000;
  const messagePercent = useMemo(
    () => Math.min((messageLength / messageLimit) * 100, 100),
    [messageLength]
  );

  // ─── Selected category/priority info ──────────────────────────────────

  const selectedCategory = useMemo(
    () => CATEGORIES.find((c) => c.value === formData.category),
    [formData.category]
  );
  const selectedPriority = useMemo(
    () => PRIORITIES.find((p) => p.value === formData.priority),
    [formData.priority]
  );

  // ─── Render ───────────────────────────────────────────────────────────

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <AnimatePresence mode="wait">
        {/* ─── Success State ──────────────────────────────────────────── */}
        {status === "success" ? (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
            className="glass-strong rounded-2xl sm:rounded-3xl p-6 sm:p-10 text-center"
          >
            {/* Animated checkmark */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200, damping: 15 }}
              className="relative mx-auto w-20 h-20 mb-6"
            >
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 opacity-20 animate-ping" />
              <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-2xl shadow-emerald-500/30">
                <CheckCircle2 className="w-10 h-10 text-white" />
              </div>
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-2xl sm:text-3xl font-bold mb-3 bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent"
            >
              Request Submitted!
            </motion.h2>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-gray-400 mb-8 max-w-md mx-auto"
            >
              {responseMessage}
            </motion.p>

            {/* Ticket ID Card */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-gradient-to-br from-gray-900/80 to-gray-800/80 rounded-2xl p-6 mb-8 border border-indigo-500/20 max-w-sm mx-auto"
            >
              <div className="text-xs text-gray-500 uppercase tracking-widest mb-2 font-medium">
                Your Ticket ID
              </div>
              <div className="flex items-center justify-center gap-3">
                <code className="text-xl sm:text-2xl font-mono font-bold text-indigo-400 tracking-wider">
                  {ticketId?.slice(0, 8).toUpperCase()}
                </code>
                <button
                  onClick={copyTicketId}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group"
                  title="Copy ticket ID"
                >
                  {copied ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                  )}
                </button>
              </div>
              <div className="mt-3 text-xs text-gray-500">
                Full ID: {ticketId}
              </div>
            </motion.div>

            {/* AI Response */}
            {aiResponse && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="text-left bg-gradient-to-br from-indigo-950/60 to-cyan-950/40 border border-indigo-500/20 rounded-2xl p-5 mb-6 max-w-lg mx-auto"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-semibold text-indigo-400 uppercase tracking-widest">AI Response</span>
                  {escalated && (
                    <span className="ml-auto text-xs bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full">
                      Escalated to Human
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{aiResponse}</p>
              </motion.div>
            )}

            {/* ETA */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
              className="flex items-center justify-center gap-2 text-sm text-gray-400 mb-8"
            >
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>{estimatedTime}</span>
            </motion.div>

            {/* Actions */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="flex flex-col sm:flex-row gap-3 justify-center"
            >
              <button
                onClick={resetForm}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-500 text-white font-medium hover:shadow-lg hover:shadow-indigo-500/25 transition-all duration-300 flex items-center justify-center gap-2 group"
              >
                Submit Another Request
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </motion.div>

            {/* Other channels */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="mt-8 pt-6 border-t border-gray-800"
            >
              <p className="text-xs text-gray-500 mb-3">Need faster help? Try other channels:</p>
              <div className="flex justify-center gap-4">
                <div className="flex items-center gap-1.5 text-xs text-gray-400 px-3 py-1.5 rounded-full bg-white/5">
                  <Mail className="w-3.5 h-3.5" />
                  support@techcorp.io
                </div>
                <div className="flex items-center gap-1.5 text-xs text-gray-400 px-3 py-1.5 rounded-full bg-white/5">
                  <Phone className="w-3.5 h-3.5" />
                  WhatsApp
                </div>
              </div>
            </motion.div>
          </motion.div>
        ) : (
          /* ─── Form State ───────────────────────────────────────────── */
          <motion.div
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
          >
            {/* Form Card */}
            <div className="glass-strong rounded-2xl sm:rounded-3xl overflow-hidden">
              {/* Gradient top border */}
              <div className="h-1 bg-gradient-to-r from-indigo-500 via-cyan-500 to-purple-500" />

              <div className="p-6 sm:p-10">
                {/* Header */}
                <div className="mb-8">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 border border-indigo-500/20">
                      <LifeBuoy className="w-6 h-6 text-indigo-400" />
                    </div>
                    <div>
                      <h2 className="text-xl sm:text-2xl font-bold text-white">
                        Contact Support
                      </h2>
                      <p className="text-sm text-gray-400">
                        Our AI assistant responds in under 5 minutes
                      </p>
                    </div>
                  </div>
                </div>

                {/* Error Alert */}
                {errors.form && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3"
                  >
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-300">{errors.form}</p>
                  </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5" noValidate>
                  {/* Name & Email Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    {/* Name */}
                    <div className="space-y-2">
                      <label
                        htmlFor="name"
                        className="block text-sm font-medium text-gray-300"
                      >
                        Full Name <span className="text-red-400">*</span>
                      </label>
                      <div className="relative">
                        <input
                          id="name"
                          name="name"
                          type="text"
                          value={formData.name}
                          onChange={handleChange}
                          onFocus={() => setActiveField("name")}
                          onBlur={() => setActiveField(null)}
                          placeholder="John Doe"
                          className={cn(
                            "w-full px-4 py-3 rounded-xl bg-gray-900/50 border text-white placeholder-gray-500 input-focus outline-none transition-all duration-300",
                            errors.name
                              ? "border-red-500/50 focus:border-red-500"
                              : activeField === "name"
                                ? "border-indigo-500/50"
                                : "border-gray-700/50 hover:border-gray-600"
                          )}
                          aria-invalid={!!errors.name}
                          aria-describedby={errors.name ? "name-error" : undefined}
                        />
                        {formData.name && !errors.name && (
                          <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400" />
                        )}
                      </div>
                      {errors.name && (
                        <p id="name-error" className="text-xs text-red-400 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          {errors.name}
                        </p>
                      )}
                    </div>

                    {/* Email */}
                    <div className="space-y-2">
                      <label
                        htmlFor="email"
                        className="block text-sm font-medium text-gray-300"
                      >
                        Email Address <span className="text-red-400">*</span>
                      </label>
                      <div className="relative">
                        <input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleChange}
                          onFocus={() => setActiveField("email")}
                          onBlur={() => setActiveField(null)}
                          placeholder="john@example.com"
                          className={cn(
                            "w-full px-4 py-3 rounded-xl bg-gray-900/50 border text-white placeholder-gray-500 input-focus outline-none transition-all duration-300",
                            errors.email
                              ? "border-red-500/50 focus:border-red-500"
                              : activeField === "email"
                                ? "border-indigo-500/50"
                                : "border-gray-700/50 hover:border-gray-600"
                          )}
                          aria-invalid={!!errors.email}
                          aria-describedby={errors.email ? "email-error" : undefined}
                        />
                        {formData.email && !errors.email && (
                          <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-400" />
                        )}
                      </div>
                      {errors.email && (
                        <p id="email-error" className="text-xs text-red-400 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          {errors.email}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Subject */}
                  <div className="space-y-2">
                    <label
                      htmlFor="subject"
                      className="block text-sm font-medium text-gray-300"
                    >
                      Subject <span className="text-red-400">*</span>
                    </label>
                    <input
                      id="subject"
                      name="subject"
                      type="text"
                      value={formData.subject}
                      onChange={handleChange}
                      onFocus={() => setActiveField("subject")}
                      onBlur={() => setActiveField(null)}
                      placeholder="Brief description of your issue"
                      className={cn(
                        "w-full px-4 py-3 rounded-xl bg-gray-900/50 border text-white placeholder-gray-500 input-focus outline-none transition-all duration-300",
                        errors.subject
                          ? "border-red-500/50 focus:border-red-500"
                          : activeField === "subject"
                            ? "border-indigo-500/50"
                            : "border-gray-700/50 hover:border-gray-600"
                      )}
                      aria-invalid={!!errors.subject}
                    />
                    {errors.subject && (
                      <p className="text-xs text-red-400 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.subject}
                      </p>
                    )}
                  </div>

                  {/* Category & Priority Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    {/* Category */}
                    <div className="space-y-2">
                      <label
                        htmlFor="category"
                        className="block text-sm font-medium text-gray-300"
                      >
                        Category <span className="text-red-400">*</span>
                      </label>
                      <div className="relative">
                        <select
                          id="category"
                          name="category"
                          value={formData.category}
                          onChange={handleChange}
                          className="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-700/50 text-white input-focus outline-none appearance-none cursor-pointer transition-all duration-300 hover:border-gray-600"
                        >
                          {CATEGORIES.map((cat) => (
                            <option key={cat.value} value={cat.value}>
                              {cat.icon} {cat.label}
                            </option>
                          ))}
                        </select>
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </div>
                      </div>
                    </div>

                    {/* Priority */}
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        Priority
                      </label>
                      <div className="flex gap-2">
                        {PRIORITIES.map((pri) => (
                          <button
                            key={pri.value}
                            type="button"
                            onClick={() =>
                              setFormData((prev) => ({ ...prev, priority: pri.value }))
                            }
                            className={cn(
                              "flex-1 px-3 py-2.5 rounded-xl border text-xs font-medium transition-all duration-200",
                              formData.priority === pri.value
                                ? `${pri.color} shadow-lg`
                                : "text-gray-500 bg-white/5 border-gray-700/30 hover:border-gray-600 hover:text-gray-300"
                            )}
                          >
                            <div className="font-semibold">{pri.label}</div>
                            <div className="text-[10px] opacity-70 mt-0.5 hidden sm:block">
                              {pri.desc}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Message */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label
                        htmlFor="message"
                        className="block text-sm font-medium text-gray-300"
                      >
                        How can we help? <span className="text-red-400">*</span>
                      </label>
                      <span
                        className={cn(
                          "text-xs font-mono tabular-nums",
                          messageLength > messageLimit * 0.9
                            ? "text-red-400"
                            : messageLength > messageLimit * 0.7
                              ? "text-amber-400"
                              : "text-gray-500"
                        )}
                      >
                        {messageLength}/{messageLimit}
                      </span>
                    </div>

                    <div className="relative">
                      <textarea
                        id="message"
                        name="message"
                        value={formData.message}
                        onChange={handleChange}
                        onFocus={() => setActiveField("message")}
                        onBlur={() => setActiveField(null)}
                        rows={6}
                        placeholder="Please describe your issue or question in detail..."
                        className={cn(
                          "w-full px-4 py-3 rounded-xl bg-gray-900/50 border text-white placeholder-gray-500 input-focus outline-none resize-none transition-all duration-300",
                          errors.message
                            ? "border-red-500/50 focus:border-red-500"
                            : activeField === "message"
                              ? "border-indigo-500/50"
                              : "border-gray-700/50 hover:border-gray-600"
                        )}
                        maxLength={messageLimit}
                        aria-invalid={!!errors.message}
                      />
                      {/* Progress bar */}
                      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-800 rounded-b-xl overflow-hidden">
                        <div
                          className={cn(
                            "h-full transition-all duration-300 rounded-r-full",
                            messagePercent > 90
                              ? "bg-red-500"
                              : messagePercent > 70
                                ? "bg-amber-500"
                                : "bg-indigo-500"
                          )}
                          style={{ width: `${messagePercent}%` }}
                        />
                      </div>
                    </div>
                    {errors.message && (
                      <p className="text-xs text-red-400 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {errors.message}
                      </p>
                    )}
                  </div>

                  {/* Category Preview */}
                  {selectedCategory && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-gray-900/50 to-gray-800/50 border border-gray-700/30"
                    >
                      <div
                        className={cn(
                          "w-8 h-8 rounded-lg bg-gradient-to-br flex items-center justify-center text-sm",
                          selectedCategory.color
                        )}
                      >
                        {selectedCategory.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-200">
                          {selectedCategory.label}
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              "text-[10px] px-2 py-0.5 rounded-full border",
                              selectedPriority?.color
                            )}
                          >
                            {selectedPriority?.label} Priority
                          </span>
                        </div>
                      </div>
                      <MessageSquare className="w-4 h-4 text-gray-500" />
                    </motion.div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={status === "submitting"}
                    className={cn(
                      "w-full py-4 px-6 rounded-xl font-semibold text-white transition-all duration-300 flex items-center justify-center gap-2.5 group relative overflow-hidden",
                      status === "submitting"
                        ? "bg-gray-700 cursor-not-allowed"
                        : "bg-gradient-to-r from-indigo-500 via-indigo-600 to-cyan-500 hover:shadow-xl hover:shadow-indigo-500/25 hover:scale-[1.01] active:scale-[0.99] btn-shine"
                    )}
                  >
                    {status === "submitting" ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Submitting your request...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                        <span>Submit Support Request</span>
                        <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                      </>
                    )}
                  </button>

                  {/* Footer */}
                  <p className="text-center text-xs text-gray-500">
                    By submitting, you agree to our{" "}
                    <a href="/privacy" className="text-indigo-400 hover:text-indigo-300 hover:underline transition-colors">
                      Privacy Policy
                    </a>
                  </p>
                </form>
              </div>
            </div>

            {/* Trust indicators */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mt-8 grid grid-cols-3 gap-4"
            >
              {[
                { value: "< 5 min", label: "Avg. Response", icon: "⚡" },
                { value: "24/7", label: "Availability", icon: "🌐" },
                { value: "98%", label: "Satisfaction", icon: "💎" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="text-center p-4 rounded-xl glass hover:bg-white/[0.07] transition-colors duration-200"
                >
                  <div className="text-xl mb-1">{stat.icon}</div>
                  <div className="text-lg font-bold text-white">{stat.value}</div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider">
                    {stat.label}
                  </div>
                </div>
              ))}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
