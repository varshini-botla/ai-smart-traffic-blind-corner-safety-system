import React, { useState, useEffect } from "react";
import { HistoryEventItem } from "../types/traffic";
import { getHistory, clearHistory } from "../services/api";
import {
  Clock,
  RotateCcw,
  Trash2,
  Download,
  Search,
  Filter,
  AlertTriangle,
  ShieldCheck,
  AlertOctagon,
  ChevronRight,
  Database,
} from "lucide-react";

interface CompleteHistorySectionProps {
  onRefreshTrigger?: number;
}

export const CompleteHistorySection: React.FC<CompleteHistorySectionProps> = ({ onRefreshTrigger = 0 }) => {
  const [events, setEvents] = useState<HistoryEventItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [notification, setNotification] = useState<string | null>(null);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const res = await getHistory(100, 0, riskFilter === "ALL" ? undefined : riskFilter, searchQuery || undefined);
      setEvents(res.events);
      setTotalCount(res.total);
    } catch (err: any) {
      console.error("Failed to load history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [riskFilter, onRefreshTrigger]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEvents();
  };

  const handleClear = async () => {
    if (!window.confirm("Are you sure you want to clear all recorded traffic analysis history events?")) {
      return;
    }
    try {
      await clearHistory();
      setEvents([]);
      setTotalCount(0);
      setNotification("History cleared successfully.");
      setTimeout(() => setNotification(null), 3000);
    } catch (err: any) {
      setNotification("Failed to clear history.");
      setTimeout(() => setNotification(null), 3000);
    }
  };

  const handleExportCSV = () => {
    if (events.length === 0) {
      alert("No events available to export.");
      return;
    }

    const headers = [
      "ID",
      "Timestamp",
      "Source",
      "Distance_A_cm",
      "Speed_A_cms",
      "Vehicles_A",
      "TTC_A_sec",
      "Distance_B_cm",
      "Speed_B_cms",
      "Vehicles_B",
      "TTC_B_sec",
      "Traffic_Density",
      "AI_Predicted_Risk",
      "Final_Safety_Risk",
      "Side_A_Action",
      "Side_B_Action",
      "Recommendation",
      "Explanation",
    ];

    const rows = events.map((ev) => [
      ev.id,
      `"${ev.timestamp}"`,
      `"${ev.source}"`,
      ev.distance_a,
      ev.speed_a,
      ev.vehicle_count_a,
      ev.ttc_a ?? "",
      ev.distance_b,
      ev.speed_b,
      ev.vehicle_count_b,
      ev.ttc_b ?? "",
      `"${ev.traffic_density}"`,
      `"${ev.ai_risk}"`,
      `"${ev.final_risk}"`,
      `"${ev.side_a_action}"`,
      `"${ev.side_b_action}"`,
      `"${ev.recommendation.replace(/"/g, '""')}"`,
      `"${ev.explanation.replace(/"/g, '""')}"`,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `blind_corner_traffic_history_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case "COLLISION_RISK":
        return "bg-rose-950 text-rose-300 border-rose-500/60 font-black";
      case "HIGH_RISK":
        return "bg-orange-950 text-orange-300 border-orange-500/60 font-bold";
      case "CAUTION":
        return "bg-amber-950 text-amber-300 border-amber-500/60 font-bold";
      default:
        return "bg-emerald-950 text-emerald-300 border-emerald-500/60 font-medium";
    }
  };

  const getActionBadge = (action: string) => {
    if (action.includes("WAIT")) {
      return "bg-rose-950 text-rose-300 border border-rose-500/40";
    }
    if (action.includes("CAUTION")) {
      return "bg-amber-950 text-amber-300 border border-amber-500/40";
    }
    return "bg-emerald-950 text-emerald-300 border border-emerald-500/40";
  };

  return (
    <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-6 space-y-5">
      {/* Header and Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-950 text-cyan-400 border border-cyan-500/30">
              Persistent SQLite Storage
            </span>
            <span className="text-xs text-slate-400">Total Recorded: {totalCount} events</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
            <Database className="w-6 h-6 text-cyan-400" />
            Complete Telemetry & Risk Analysis History Log
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full audit log of physical measurements, AI classification confidence, safety overrides, and signal decisions.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchEvents}
            disabled={loading}
            className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={handleExportCSV}
            className="px-3 py-2 rounded-xl bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-600/50 text-xs font-semibold text-cyan-300 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>

          <button
            type="button"
            onClick={handleClear}
            className="px-3 py-2 rounded-xl bg-rose-950/70 hover:bg-rose-900 border border-rose-600/40 text-xs font-semibold text-rose-300 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-3 bg-cyan-950/80 border border-cyan-500/40 rounded-xl text-xs font-semibold text-cyan-300 text-center animate-fade-in">
          {notification}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#080d19] p-3 rounded-xl border border-slate-800">
        {/* Risk Level Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-slate-400 font-semibold mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Filter:
          </span>
          {["ALL", "SAFE", "CAUTION", "HIGH_RISK", "COLLISION_RISK"].map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRiskFilter(r)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer border ${
                riskFilter === r
                  ? "bg-cyan-600 text-white border-cyan-500 shadow-sm"
                  : "bg-slate-900/80 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
              }`}
            >
              {r.replace("_", " ")}
            </button>
          ))}
        </div>

        {/* Search input */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-all cursor-pointer"
          >
            Search
          </button>
        </form>
      </div>

      {/* Full Event Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800/90 bg-[#070b14]">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#0f172a] text-slate-400 uppercase font-bold text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-3.5">Time & ID</th>
              <th className="py-3 px-3.5">Side A Approach</th>
              <th className="py-3 px-3.5">Side B Approach</th>
              <th className="py-3 px-3.5">Density</th>
              <th className="py-3 px-3.5">AI Inference</th>
              <th className="py-3 px-3.5">Final Safety Risk</th>
              <th className="py-3 px-3.5">Signal Directives</th>
              <th className="py-3 px-3.5 min-w-[200px]">Recommendation Directive</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
            {events.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-400 font-sans text-xs">
                  {loading ? "Loading historical traffic events..." : "No recorded events matching the selected criteria."}
                </td>
              </tr>
            ) : (
              events.map((ev) => {
                const timeStr = new Date(ev.timestamp).toLocaleTimeString();
                const isOverridden = ev.raw_features?.override_applied;

                return (
                  <tr key={ev.id} className="hover:bg-slate-900/60 transition-colors">
                    {/* Timestamp & ID */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <div className="font-bold text-slate-200">#{ev.id}</div>
                      <div className="text-[10px] text-slate-400 font-sans">{timeStr}</div>
                    </td>

                    {/* Side A Telemetry */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <div className="font-bold text-cyan-400">{ev.distance_a.toFixed(1)} cm</div>
                      <div className="text-[10px] text-slate-400">
                        {ev.speed_a.toFixed(1)} cm/s | TTC: {ev.ttc_a !== null ? `${ev.ttc_a}s` : "None"}
                      </div>
                    </td>

                    {/* Side B Telemetry */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <div className="font-bold text-purple-400">{ev.distance_b.toFixed(1)} cm</div>
                      <div className="text-[10px] text-slate-400">
                        {ev.speed_b.toFixed(1)} cm/s | TTC: {ev.ttc_b !== null ? `${ev.ttc_b}s` : "None"}
                      </div>
                    </td>

                    {/* Traffic Density */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {ev.traffic_density}
                      </span>
                    </td>

                    {/* AI Inference */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] border ${getRiskBadge(ev.ai_risk)}`}>
                        {ev.ai_risk}
                      </span>
                      {ev.raw_features?.confidence_score && (
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {(ev.raw_features.confidence_score * 100).toFixed(0)}% conf
                        </div>
                      )}
                    </td>

                    {/* Final Safety Risk */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className={`px-2.5 py-0.5 rounded text-[10px] border ${getRiskBadge(ev.final_risk)}`}>
                          {ev.final_risk}
                        </span>
                        {isOverridden && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-950 text-rose-300 border border-rose-500/50">
                            OVERRIDE
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Signal Directives */}
                    <td className="py-3 px-3.5 whitespace-nowrap font-sans">
                      <div className="flex items-center gap-1.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getActionBadge(ev.side_a_action)}`}>
                          A: {ev.side_a_action}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getActionBadge(ev.side_b_action)}`}>
                          B: {ev.side_b_action}
                        </span>
                      </div>
                    </td>

                    {/* Recommendation Directive */}
                    <td className="py-3 px-3.5 font-sans">
                      <div className="font-bold text-slate-200 text-xs">{ev.recommendation}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">{ev.explanation}</div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
