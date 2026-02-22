import { useState, useRef, useEffect } from "react";
import { LogOut, Send, Loader2, ClipboardList, MessageSquare, ChevronRight, X } from "lucide-react";

const API_BASE_URL = "http://localhost:8000";

export default function App() {
  const [page, setPage] = useState("landing");
  const [user, setUser] = useState(null);

  const handleLogin = (data) => {
    setUser({ name: data.name || "User", email: data.email });
    setPage("dashboard");
  };

  const handleLogout = () => {
    setUser(null);
    setPage("landing");
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* NAVBAR */}
      <nav className="fixed top-0 w-full bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6 z-50">
        <h1 className="font-bold text-lg cursor-pointer" onClick={() => setPage("landing")}>
          Scheme <span className="text-indigo-600">Sathi</span>
        </h1>
        {user ? (
          <div className="flex items-center gap-3">
            <span className="font-semibold text-sm">{user.name}</span>
            <button onClick={handleLogout} className="p-2 hover:bg-slate-100 rounded-full">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button onClick={() => setPage("auth")}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold">
            Sign In
          </button>
        )}
      </nav>

      <div className="pt-24 px-6">
        {page === "landing"   && <LandingPage setPage={setPage} user={user} />}
        {page === "auth"      && <AuthPage onLogin={handleLogin} />}
        {page === "dashboard" && <Dashboard setPage={setPage} />}
        {page === "form"      && <FormPage />}
        {page === "chat"      && <ChatPage />}
      </div>
    </div>
  );
}

/* ─── LANDING ──────────────────────────────────────────────── */

function LandingPage({ setPage, user }) {
  return (
    <div className="text-center mt-20 max-w-2xl mx-auto">
      <h2 className="text-4xl font-bold mb-4 text-slate-900">
        Your Intelligent <span className="text-indigo-600">Scheme Navigator</span>
      </h2>
      <p className="text-slate-500 mb-8 text-lg">
        Find government schemes you're eligible for — instantly.
      </p>
      <button
        onClick={() => user ? setPage("dashboard") : setPage("auth")}
        className="px-8 py-4 bg-indigo-600 text-white rounded-xl text-lg font-semibold hover:bg-indigo-700 transition-all">
        Get Started
      </button>
    </div>
  );
}

/* ─── AUTH ─────────────────────────────────────────────────── */

function AuthPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm]             = useState({ name: "", email: "", password: "" });
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Authentication failed");
      }
      const data = await res.json();
      onLogin(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-xl shadow-lg">
      <h2 className="text-2xl font-bold mb-6">{isRegister ? "Register" : "Login"}</h2>
      {error && <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        {isRegister && (
          <input type="text" placeholder="Full Name" required
            className="w-full border p-3 rounded-lg text-sm"
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
        )}
        <input type="email" placeholder="Email" required
          className="w-full border p-3 rounded-lg text-sm"
          onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input type="password" placeholder="Password" required
          className="w-full border p-3 rounded-lg text-sm"
          onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button disabled={loading}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg flex items-center justify-center gap-2 font-semibold hover:bg-indigo-700 transition-all">
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          {isRegister ? "Create Account" : "Login"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-500">
        {isRegister ? "Already have an account?" : "New here?"}
        <button onClick={() => { setIsRegister(!isRegister); setError(""); }}
          className="ml-1 text-indigo-600 font-semibold hover:underline">
          {isRegister ? "Login" : "Register"}
        </button>
      </p>
    </div>
  );
}

/* ─── DASHBOARD ────────────────────────────────────────────── */

function Dashboard({ setPage }) {
  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-3xl font-bold mb-8">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <button onClick={() => setPage("form")}
          className="p-8 bg-white border border-slate-200 rounded-2xl text-left hover:border-indigo-400 hover:shadow-lg transition-all">
          <ClipboardList className="w-10 h-10 text-emerald-600 mb-4" />
          <h3 className="text-xl font-bold mb-2">Profile-Based Matching</h3>
          <p className="text-slate-500 text-sm mb-4">Fill a form and get matched to eligible schemes instantly.</p>
          <div className="flex items-center text-emerald-600 font-semibold text-sm">
            Open Form <ChevronRight className="w-4 h-4 ml-1" />
          </div>
        </button>

        <button onClick={() => setPage("chat")}
          className="p-8 bg-white border border-slate-200 rounded-2xl text-left hover:border-indigo-400 hover:shadow-lg transition-all">
          <MessageSquare className="w-10 h-10 text-indigo-600 mb-4" />
          <h3 className="text-xl font-bold mb-2">Chat with Sathi AI</h3>
          <p className="text-slate-500 text-sm mb-4">Talk naturally and discover schemes through conversation.</p>
          <div className="flex items-center text-indigo-600 font-semibold text-sm">
            Start Chat <ChevronRight className="w-4 h-4 ml-1" />
          </div>
        </button>
      </div>
    </div>
  );
}

/* ─── KNOW MORE MODAL ──────────────────────────────────────── */

function KnowMoreModal({ scheme, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-6"
      onClick={onClose}>
      <div className="bg-white rounded-2xl p-8 max-w-xl w-full max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1 pr-4">
            <h2 className="text-xl font-bold text-slate-900 mb-1">{scheme.title}</h2>
            <span className="text-xs font-semibold px-2 py-1 bg-indigo-50 text-indigo-600 rounded-full">
              {scheme.category}
            </span>
          </div>
          <button onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-full flex-shrink-0">
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Description */}
        {scheme.summary && (
          <p className="text-slate-600 text-sm leading-relaxed mb-6">{scheme.summary}</p>
        )}

        {/* Documents Required */}
        {scheme.documents?.length > 0 && (
          <div className="mb-6">
            <h3 className="font-bold text-slate-800 mb-3 flex items-center gap-2">
              <span className="text-lg">📄</span> Documents Required
            </h3>
            <ul className="space-y-2">
              {scheme.documents.map((doc, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="text-green-500 font-bold mt-0.5 flex-shrink-0">✓</span>
                  {doc}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* How to Apply */}
        {scheme.steps?.length > 0 && (
          <div className="mb-6">
            <h3 className="font-bold text-slate-800 mb-3 flex items-center gap-2">
              <span className="text-lg">📋</span> How to Apply
            </h3>
            <ol className="space-y-3">
              {scheme.steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-slate-600">
                  <span className="w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-2 border-t border-slate-100">
          <a href={scheme.source} target="_blank" rel="noreferrer"
            className="flex-1 text-center py-3 bg-indigo-600 text-white font-semibold rounded-xl text-sm hover:bg-indigo-700 transition-all">
            Apply on Official Portal →
          </a>
          <button onClick={onClose}
            className="px-6 py-3 border border-slate-200 rounded-xl text-sm font-semibold hover:bg-slate-50 transition-all">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── FORM PAGE ────────────────────────────────────────────── */

function FormPage() {
  const [form, setForm]           = useState({ name: "", occupation: "", caste: "", income: "500000" });
  const [schemes, setSchemes]     = useState([]);
  const [loading, setLoading]     = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/schemes/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("Matching failed");
      const data = await res.json();
      setSchemes(data.schemes || []);
      setSubmitted(true);
    } catch {
      alert("Could not fetch schemes. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Matched Schemes for {form.name}</h2>
          <p className="text-slate-500 text-sm mt-1">{schemes.length} scheme{schemes.length !== 1 ? "s" : ""} found</p>
        </div>
        <button onClick={() => { setSubmitted(false); setSchemes([]); }}
          className="text-sm text-indigo-600 underline font-semibold">
          Search again
        </button>
      </div>

      {schemes.length === 0 ? (
        <div className="bg-white p-10 rounded-xl text-center text-slate-500 border border-slate-200">
          <p className="text-lg font-semibold mb-2">No schemes matched your profile</p>
          <p className="text-sm">Try adjusting your occupation or category.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {schemes.map((s) => (
            <div key={s.id}
              className="bg-white p-6 rounded-xl border border-slate-200 hover:shadow-md transition-all">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-slate-900 mb-2">{s.title}</h3>
                  <p className="text-slate-500 text-sm mb-4 line-clamp-2">{s.summary}</p>
                </div>
              </div>
              <div className="flex gap-3 flex-wrap">
                <button onClick={() => setSelectedScheme(s)}
                  className="px-5 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-all">
                  Know More
                </button>
                <a href={s.source} target="_blank" rel="noreferrer"
                  className="px-5 py-2 border border-indigo-200 text-indigo-600 text-sm font-semibold rounded-lg hover:bg-indigo-50 transition-all">
                  Official Portal →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedScheme && (
        <KnowMoreModal scheme={selectedScheme} onClose={() => setSelectedScheme(null)} />
      )}
    </div>
  );

  return (
    <div className="max-w-lg mx-auto bg-white p-8 rounded-xl shadow-lg">
      <h2 className="text-2xl font-bold mb-6">Find Your Schemes</h2>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-semibold mb-1">Full Name</label>
          <input type="text" required placeholder="e.g. Rahul Sharma"
            className="w-full border p-3 rounded-lg text-sm"
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1">Occupation</label>
          <select className="w-full border p-3 rounded-lg text-sm"
            onChange={(e) => setForm({ ...form, occupation: e.target.value })}>
            <option value="">Select...</option>
            {["Student", "Farmer", "Worker", "Professional", "Unemployed"].map(o => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1">Category</label>
          <select className="w-full border p-3 rounded-lg text-sm"
            onChange={(e) => setForm({ ...form, caste: e.target.value })}>
            <option value="">Select...</option>
            {["General", "OBC", "SC", "ST"].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold mb-2">
            Annual Income: ₹{Number(form.income).toLocaleString()}
          </label>
          <input type="range" min="0" max="2000000" step="50000"
            value={form.income}
            className="w-full accent-indigo-600"
            onChange={(e) => setForm({ ...form, income: e.target.value })} />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>₹0</span><span>₹20 lakh</span>
          </div>
        </div>
        <button disabled={loading}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-indigo-700 transition-all">
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          Find Matching Schemes
        </button>
      </form>
    </div>
  );
}

/* ─── CHAT PAGE ────────────────────────────────────────────── */

function ChatPage() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! I'm Sathi. What's your name?" }
  ]);
  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep]       = useState(0);
  const [profile, setProfile] = useState({});
  const bottomRef             = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, current_step: step, profile }),
      });
      if (!res.ok) throw new Error("Chat failed");
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", text: data.response }]);
      setStep(data.next_step);
      if (data.profile) setProfile(data.profile);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        text: "Sorry, I couldn't connect to the server. Make sure the backend is running."
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto flex flex-col h-[75vh] bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-3">
        <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
        <span className="font-bold">Sathi AI Assistant</span>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm font-medium ${
              m.role === "user"
                ? "bg-indigo-600 text-white rounded-tr-none"
                : "bg-slate-100 text-slate-800 rounded-tl-none"
            }`}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 px-4 py-3 rounded-2xl rounded-tl-none">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-4 border-t border-slate-200 flex gap-3">
        <input
          className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend} disabled={loading}
          className="px-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all disabled:opacity-50">
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
