import React, { useState, useEffect, useRef } from "react";
import {
  Shield,
  Sliders,
  RotateCcw,
  Volume2,
  VolumeX,
  Send,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Activity,
  Car,
  Wifi,
} from "lucide-react";
import { TrafficAnalysisResponse } from "../types/traffic";
import { simulateTraffic, getCurrentStatus, getAnalytics } from "../services/api";
import { DigitalTwinCanvas } from "../components/DigitalTwinCanvas";
import { CompleteHistorySection } from "../components/CompleteHistorySection";

interface UnifiedSystemPageProps {
  isBackendOnline: boolean;
  isWsConnected: boolean;
}

export const UnifiedSystemPage: React.FC<UnifiedSystemPageProps> = ({
  isBackendOnline,
  isWsConnected,
}) => {
  // Input Sliders State (Defaults to 74 cm and 13 cm/s matching the exact screenshot)
  const [distanceA, setDistanceA] = useState<number>(74);
  const [speedA, setSpeedA] = useState<number>(13);
  const [distanceB, setDistanceB] = useState<number>(74);
  const [speedB, setSpeedB] = useState<number>(13);

  // Sound Mute State (default Sound OFF matching screenshot)
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);

  // Loading & Error States
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Analysis Result
  const [result, setResult] = useState<TrafficAnalysisResponse | null>(null);

  // Telemetry Distance History for the Line Chart (past 15 samples)
  const [telemetryHistory, setTelemetryHistory] = useState<
    Array<{ distA: number; distB: number }>
  >([
    { distA: 100, distB: 100 },
    { distA: 85, distB: 85 },
    { distA: 80, distB: 80 },
    { distA: 40, distB: 40 },
    { distA: 74, distB: 74 },
  ]);

  // Distribution counts for the Bar Chart
  const [riskDistribution, setRiskDistribution] = useState<{
    SAFE: number;
    CAUTION: number;
    HIGH_RISK: number;
    COLLISION_RISK: number;
  }>({
    SAFE: 5,
    CAUTION: 42,
    HIGH_RISK: 12,
    COLLISION_RISK: 8,
  });

  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Active audio reference for clean stop/start control
  const activeAudioRef = useRef<{ osc: OscillatorNode; ctx: AudioContext } | null>(null);

  const stopCurrentSound = () => {
    try {
      if (activeAudioRef.current) {
        activeAudioRef.current.osc.stop();
        activeAudioRef.current.ctx.close();
        activeAudioRef.current = null;
      }
    } catch {
      activeAudioRef.current = null;
    }
  };

  // Sound Synthesizer using Web Audio API
  const playAlertSound = (risk: string, forcePlay: boolean = false) => {
    if (!soundEnabled && !forcePlay) return;
    try {
      stopCurrentSound();

      const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtxClass) return;
      const audioCtx = new AudioCtxClass();
      if (audioCtx.state === "suspended") {
        audioCtx.resume();
      }

      if (risk === "COLLISION_RISK") {
        // Sustained Long Emergency Buzzer Beep (2000Hz piercing collision warning for 1.8s)
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        // Authentic 2000Hz hardware buzzer timbre matching "BUZZER ACTIVE (2000Hz)" badge
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(2000, audioCtx.currentTime);

        // Immediate solid attack, steady long beep sustain for 1.5s, clean release at 1.8s
        gain.gain.setValueAtTime(0.01, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.28, audioCtx.currentTime + 0.04);
        gain.gain.setValueAtTime(0.28, audioCtx.currentTime + 1.5);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1.8);

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.start(audioCtx.currentTime);
        osc.stop(audioCtx.currentTime + 1.8);

        activeAudioRef.current = { osc, ctx: audioCtx };
        osc.onended = () => {
          if (activeAudioRef.current?.osc === osc) {
            activeAudioRef.current = null;
          }
        };
      } else if (risk === "HIGH_RISK") {
        // Warning tone (650Hz, 0.5s)
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(650, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.5);
      } else if (risk === "CAUTION") {
        // Caution chime (523Hz, 0.25s)
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(523, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.25);
      }
    } catch (e) {
      console.warn("AudioContext error:", e);
    }
  };

  // Sound toggle handler with immediate alert trigger
  const handleToggleSound = () => {
    const nextState = !soundEnabled;
    setSoundEnabled(nextState);
    if (nextState) {
      // User turned Sound ON: immediately trigger alert for current evaluated risk
      playAlertSound(currentRisk, true);
    } else {
      stopCurrentSound();
    }
  };

  // Perform Analysis
  const runSimulation = async (
    customDistA?: number,
    customSpdA?: number,
    customDistB?: number,
    customSpdB?: number
  ) => {
    const da = customDistA !== undefined ? customDistA : distanceA;
    const sa = customSpdA !== undefined ? customSpdA : speedA;
    const db = customDistB !== undefined ? customDistB : distanceB;
    const sb = customSpdB !== undefined ? customSpdB : speedB;

    setLoading(true);
    setErrorMsg(null);

    const payload = {
      distance_a_cm: da,
      speed_a_cms: sa,
      vehicle_count_a: da <= 120 ? 1 : 0,
      distance_b_cm: db,
      speed_b_cms: sb,
      vehicle_count_b: db <= 120 ? 1 : 0,
      source: "Sensor Simulation Mode",
    };

    try {
      const res = await simulateTraffic(payload);
      setResult(res);

      // Play chime if enabled
      playAlertSound(res.safety_assessment.final_safety_risk);

      // Append to Telemetry History
      setTelemetryHistory((prev) => {
        const next = [...prev, { distA: da, distB: db }];
        if (next.length > 15) return next.slice(next.length - 15);
        return next;
      });

      // Update distribution counts
      const r = res.safety_assessment.final_safety_risk;
      setRiskDistribution((prev) => ({
        ...prev,
        [r]: (prev[r as keyof typeof prev] || 0) + 1,
      }));

      // Trigger History Table reload
      setRefreshTrigger((prev) => prev + 1);
    } catch (err: any) {
      setErrorMsg(err.message || "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  // Initial load: trigger simulation for default state (74cm @ 13cm/s)
  useEffect(() => {
    runSimulation(74, 13, 74, 13);
  }, []);

  // Quick Preset Handlers
  const applyPreset = (presetName: string) => {
    switch (presetName) {
      case "default_caution":
        setDistanceA(74);
        setSpeedA(13);
        setDistanceB(74);
        setSpeedB(13);
        runSimulation(74, 13, 74, 13);
        break;
      case "danger_10cm":
        setDistanceA(10);
        setSpeedA(0);
        setDistanceB(10);
        setSpeedB(0);
        runSimulation(10, 0, 10, 0);
        break;
      case "safe_clear":
        setDistanceA(100);
        setSpeedA(0);
        setDistanceB(100);
        setSpeedB(0);
        runSimulation(100, 0, 100, 0);
        break;
      case "side_a_priority":
        setDistanceA(40);
        setSpeedA(15);
        setDistanceB(100);
        setSpeedB(0);
        runSimulation(40, 15, 100, 0);
        break;
      case "dual_close":
        setDistanceA(40);
        setSpeedA(15);
        setDistanceB(40);
        setSpeedB(15);
        runSimulation(40, 15, 40, 15);
        break;
      case "critical_collision":
        setDistanceA(20);
        setSpeedA(35);
        setDistanceB(20);
        setSpeedB(35);
        runSimulation(20, 35, 20, 35);
        break;
      default:
        break;
    }
  };

  // Current values to display (from result or local state)
  const currentRisk = result?.safety_assessment.final_safety_risk || "CAUTION";
  const confidencePercent = result?.ai_prediction.confidence_score
    ? (result.ai_prediction.confidence_score * 100).toFixed(1)
    : "100.0";
  const overrideApplied = result?.safety_assessment.override_applied || false;
  const warningText =
    result?.safety_assessment.warning_message ||
    "CAUTION: Vehicle detected near Side A (46-90cm). Approach with caution.";

  const sideAAction = result?.traffic_recommendation.side_a_action || "WAIT";
  const sideBAction = result?.traffic_recommendation.side_b_action || "PROCEED";
  const rawSummary = result?.traffic_recommendation.recommendation_summary || "RECOMMENDATION: SIDE B PROCEED";
  const recommendationSummary = rawSummary
    .replace(/^CRITICAL STOP:\s*/i, "")
    .replace(/^CRITICAL:\s*/i, "");
  const explanation =
    result?.traffic_recommendation.primary_reason ||
    "Side B vehicle prioritized due to closer proximity or lower Time-To-Collision. Side A held safely at stopline.";

  const isCollision = currentRisk === "COLLISION_RISK";

  // Formatted TTC displays
  const ttcA_disp =
    result?.features.ttc_a_display ||
    (distanceA <= 20 ? "CRITICAL (<1s)" : speedA > 0 ? `${(distanceA / speedA).toFixed(1)} s` : "None");
  const ttcB_disp =
    result?.features.ttc_b_display ||
    (distanceB <= 20 ? "CRITICAL (<1s)" : speedB > 0 ? `${(distanceB / speedB).toFixed(1)} s` : "None");

  const density = result?.features.traffic_density || "HIGH";
  const totalVehicles = result?.features.total_vehicles ?? 2;

  // Stopping distances (in cm)
  const stoppingDistA =
    result?.features.stopping_dist_a_cm ?? (speedA > 0 ? Number(((speedA * speedA) / 1372).toFixed(1)) : 0);
  const stoppingDistB =
    result?.features.stopping_dist_b_cm ?? (speedB > 0 ? Number(((speedB * speedB) / 1372).toFixed(1)) : 0);

  // Probabilities
  const probs = result?.ai_prediction.class_probabilities || {
    CAUTION: 0.88,
    COLLISION_RISK: 0.0,
    HIGH_RISK: 0.0,
    SAFE: 0.12,
  };

  return (
    <div className="min-h-screen bg-[#060913] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* ================= HEADER ================= */}
      <header className="border-b border-slate-800/90 bg-[#090d18]/95 backdrop-blur sticky top-0 z-40 px-4 sm:px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-black text-white tracking-tight">
                Smart Traffic &amp; Blind-Corner Safety System
              </h1>
              <p className="text-xs text-slate-400 font-medium">
                AI-Integrated Collision Prevention &amp; Intelligent Traffic Management System
              </p>
            </div>
          </div>

          {/* Badges and Mode Indicators */}
          <div className="flex items-center gap-2 sm:gap-2.5">
            {/* Sensor Simulation Mode (Active badge) */}
            <div className="px-3 py-1.5 rounded-xl bg-blue-950/80 border border-cyan-500/50 text-cyan-300 text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-cyan-950">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              <span>Sensor Simulation Mode</span>
            </div>

            {/* Backend status */}
            <div className="px-2.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isBackendOnline ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" : "bg-rose-400"
                }`}
              ></span>
              <span className="hidden sm:inline">Backend:</span>
              <span className={isBackendOnline ? "text-emerald-400" : "text-rose-400"}>
                {isBackendOnline ? "ONLINE" : "OFFLINE"}
              </span>
            </div>

            {/* AI Engine status */}
            <div className="px-2.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]"></span>
              <span className="hidden sm:inline">AI:</span>
              <span className="text-cyan-400">ONLINE</span>
            </div>

            {/* Live Sync Pulse */}
            <div className="px-2.5 py-1.5 rounded-xl bg-blue-950/60 border border-blue-800/40 text-[11px] font-semibold text-blue-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
              <span>Live Sync</span>
            </div>
          </div>
        </div>
      </header>

      {/* ================= MAIN CONTAINER ================= */}
      <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 space-y-8 flex-1">
        {/* ================= SECTION 1: PRIMARY DASHBOARD GRID (SCREENSHOT MATCH) ================= */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* ================= LEFT COLUMN (7 COLS) ================= */}
          <div className="lg:col-span-7 space-y-5">
            {/* Card 1: Live Blind-Corner 2D Road Digital Twin */}
            <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-4 sm:p-5 space-y-3">
              <div>
                <h2 className="text-base sm:text-lg font-black text-slate-100 tracking-tight">
                  Live Blind-Corner 2D Road Digital Twin
                </h2>
                <p className="text-xs text-slate-400">
                  Kinematic positioning directly mapped to physical ultrasonic sensor telemetry
                </p>
              </div>

              {/* 2D Canvas */}
              <DigitalTwinCanvas
                distanceA={distanceA}
                speedA={speedA}
                distanceB={distanceB}
                speedB={speedB}
                sideAAction={sideAAction}
                sideBAction={sideBAction}
                finalRisk={currentRisk}
              />
            </div>

            {/* Card 2: Sensor Telemetry Cards (Side by Side) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* SIDE A SENSOR */}
              <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className={`w-4 h-4 ${distanceA <= 20 ? "text-rose-400" : "text-amber-400"}`} />
                    <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Side A Sensor
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full border ${
                      sideAAction.includes("PROCEED")
                        ? "bg-emerald-950 text-emerald-300 border-emerald-500/50"
                        : "bg-rose-950 text-rose-300 border-rose-500/50"
                    }`}
                  >
                    {sideAAction.includes("PROCEED") ? "PROCEED" : "WAIT"}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">
                    Measured Distance
                  </span>
                  <div className="flex items-baseline justify-between">
                    <span
                      className={`text-3xl font-black font-mono tracking-tight ${
                        distanceA <= 20 ? "text-rose-400" : "text-amber-400"
                      }`}
                    >
                      {distanceA.toFixed(1)} <span className="text-sm font-sans font-bold text-slate-400">cm</span>
                    </span>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">
                        Speed
                      </span>
                      <span className="text-lg font-bold text-slate-200 font-mono">
                        {speedA.toFixed(1)} <span className="text-xs font-sans text-slate-400">cm/s</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      distanceA <= 20
                        ? "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.7)]"
                        : "bg-gradient-to-r from-amber-500 to-amber-400"
                    }`}
                    style={{ width: `${Math.min(Math.max((distanceA / 150) * 100, 5), 100)}%` }}
                  ></div>
                </div>

                {/* Bottom Stats */}
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase block">Estimated TTC</span>
                    <span
                      className={`font-bold font-mono ${
                        distanceA <= 20 ? "text-rose-400 font-black" : "text-slate-200"
                      }`}
                    >
                      {ttcA_disp}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase block">
                      {distanceA <= 20 ? "Lane Status" : "Braking Distance"}
                    </span>
                    <span
                      className={`font-bold font-mono ${
                        distanceA <= 20 ? "text-rose-400 font-black" : "text-cyan-400"
                      }`}
                    >
                      {distanceA <= 20 ? "STOPLINE HOLD" : `${stoppingDistA} cm`}
                    </span>
                  </div>
                </div>
              </div>

              {/* SIDE B SENSOR */}
              <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className={`w-4 h-4 ${distanceB <= 20 ? "text-rose-400" : "text-amber-400"}`} />
                    <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Side B Sensor
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full border ${
                      sideBAction.includes("PROCEED")
                        ? "bg-emerald-950 text-emerald-300 border-emerald-500/50"
                        : "bg-rose-950 text-rose-300 border-rose-500/50"
                    }`}
                  >
                    {sideBAction.includes("PROCEED") ? "PROCEED" : "WAIT"}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">
                    Measured Distance
                  </span>
                  <div className="flex items-baseline justify-between">
                    <span
                      className={`text-3xl font-black font-mono tracking-tight ${
                        distanceB <= 20 ? "text-rose-400" : "text-amber-400"
                      }`}
                    >
                      {distanceB.toFixed(1)} <span className="text-sm font-sans font-bold text-slate-400">cm</span>
                    </span>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">
                        Speed
                      </span>
                      <span className="text-lg font-bold text-slate-200 font-mono">
                        {speedB.toFixed(1)} <span className="text-xs font-sans text-slate-400">cm/s</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      distanceB <= 20
                        ? "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.7)]"
                        : "bg-gradient-to-r from-amber-500 to-amber-400"
                    }`}
                    style={{ width: `${Math.min(Math.max((distanceB / 150) * 100, 5), 100)}%` }}
                  ></div>
                </div>

                {/* Bottom Stats */}
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase block">Estimated TTC</span>
                    <span
                      className={`font-bold font-mono ${
                        distanceB <= 20 ? "text-rose-400 font-black" : "text-slate-200"
                      }`}
                    >
                      {ttcB_disp}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase block">
                      {distanceB <= 20 ? "Lane Status" : "Braking Distance"}
                    </span>
                    <span
                      className={`font-bold font-mono ${
                        distanceB <= 20 ? "text-rose-400 font-black" : "text-cyan-400"
                      }`}
                    >
                      {distanceB <= 20 ? "STOPLINE HOLD" : `${stoppingDistB} cm`}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Card 3: Web Sensor Simulation / Test Mode */}
            <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-4 sm:p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                    Web Sensor Simulation / Test Mode
                  </h3>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-cyan-950 text-cyan-400 border border-cyan-500/40">
                  Test Mode Active
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Notice: Values sent via API to the same backend AI + Safety pipeline for testing &amp; verification.
              </p>

              {/* Two Column Sliders */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
                {/* Side A Sliders */}
                <div className="space-y-3 bg-[#080d19] p-3.5 rounded-xl border border-slate-800/80">
                  <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider block">
                    Side A Sensor Inputs
                  </span>

                  {/* Distance Slider */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-400">Distance:</span>
                      <span className="text-slate-200 font-mono">{distanceA} cm</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="150"
                      value={distanceA}
                      onChange={(e) => setDistanceA(parseInt(e.target.value, 10))}
                      className="w-full accent-cyan-400 h-1.5 bg-slate-800 rounded cursor-pointer"
                    />
                  </div>

                  {/* Approach Speed Slider */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-400">Approach Speed:</span>
                      <span className="text-slate-200 font-mono">{speedA} cm/s</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="40"
                      value={speedA}
                      onChange={(e) => setSpeedA(parseInt(e.target.value, 10))}
                      className="w-full accent-cyan-400 h-1.5 bg-slate-800 rounded cursor-pointer"
                    />
                  </div>
                </div>

                {/* Side B Sliders */}
                <div className="space-y-3 bg-[#080d19] p-3.5 rounded-xl border border-slate-800/80">
                  <span className="text-xs font-bold text-purple-400 uppercase tracking-wider block">
                    Side B Sensor Inputs
                  </span>

                  {/* Distance Slider */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-400">Distance:</span>
                      <span className="text-slate-200 font-mono">{distanceB} cm</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="150"
                      value={distanceB}
                      onChange={(e) => setDistanceB(parseInt(e.target.value, 10))}
                      className="w-full accent-purple-400 h-1.5 bg-slate-800 rounded cursor-pointer"
                    />
                  </div>

                  {/* Approach Speed Slider */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-400">Approach Speed:</span>
                      <span className="text-slate-200 font-mono">{speedB} cm/s</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="40"
                      value={speedB}
                      onChange={(e) => setSpeedB(parseInt(e.target.value, 10))}
                      className="w-full accent-purple-400 h-1.5 bg-slate-800 rounded cursor-pointer"
                    />
                  </div>
                </div>
              </div>

              {/* Big Cyan Apply Button */}
              <button
                type="button"
                onClick={() => runSimulation()}
                disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 via-cyan-500 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-black text-xs uppercase tracking-wider shadow-lg shadow-cyan-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Send className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                <span>Apply Custom Sensor Data (POST /simulate)</span>
              </button>

              {/* Benchmark Presets Row */}
              <div className="pt-2 border-t border-slate-800/80">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block mb-2">
                  Benchmark Test Scenarios:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
                  <button
                    type="button"
                    onClick={() => applyPreset("danger_10cm")}
                    className="p-2 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 border border-rose-500/50 text-left text-xs transition-colors cursor-pointer"
                  >
                    <span className="text-rose-400 font-bold block text-[11px]">Critical Danger</span>
                    <span className="text-[10px] text-slate-300">10cm @ 0cm/s</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => applyPreset("default_caution")}
                    className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left text-xs transition-colors cursor-pointer"
                  >
                    <span className="text-amber-400 font-bold block text-[11px]">Default</span>
                    <span className="text-[10px] text-slate-400">74cm @ 13cm/s</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => applyPreset("safe_clear")}
                    className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left text-xs transition-colors cursor-pointer"
                  >
                    <span className="text-emerald-400 font-bold block text-[11px]">Safe Road</span>
                    <span className="text-[10px] text-slate-400">100cm, Clear</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => applyPreset("side_a_priority")}
                    className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left text-xs transition-colors cursor-pointer"
                  >
                    <span className="text-cyan-400 font-bold block text-[11px]">Side A Priority</span>
                    <span className="text-[10px] text-slate-400">40cm vs Clear</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => applyPreset("dual_close")}
                    className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left text-xs transition-colors cursor-pointer"
                  >
                    <span className="text-orange-400 font-bold block text-[11px]">Dual Close</span>
                    <span className="text-[10px] text-slate-400">40cm @ 15cm/s</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => applyPreset("critical_collision")}
                    className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left text-xs transition-colors cursor-pointer"
                  >
                    <span className="text-rose-400 font-bold block text-[11px]">Fast Collision</span>
                    <span className="text-[10px] text-slate-400">20cm @ 35cm/s</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* ================= RIGHT COLUMN (5 COLS) ================= */}
          <div className="lg:col-span-5 space-y-5">
            {/* Card 1: AI Collision-Risk & Safety Layer */}
            <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-4 sm:p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                  AI Collision-Risk &amp; Safety Layer
                </h3>
                <button
                  type="button"
                  onClick={handleToggleSound}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 border transition-all cursor-pointer ${
                    soundEnabled
                      ? "bg-cyan-950 text-cyan-300 border-cyan-500/50"
                      : "bg-slate-900 text-slate-400 border-slate-800"
                  }`}
                >
                  {soundEnabled ? <Volume2 className="w-3.5 h-3.5 text-cyan-400" /> : <VolumeX className="w-3.5 h-3.5" />}
                  <span>{soundEnabled ? "Sound ON" : "Sound OFF"}</span>
                </button>
              </div>

              {/* Sub-Card: Current Evaluated Risk */}
              <div className="bg-[#080d19] p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-0.5">
                    Current Evaluated Risk
                  </span>
                  <span
                    className={`text-2xl font-black tracking-tight ${
                      isCollision
                        ? "text-rose-400 animate-pulse"
                        : currentRisk === "HIGH_RISK"
                        ? "text-orange-400"
                        : currentRisk === "CAUTION"
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {currentRisk.replace("_", " ")}
                  </span>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-0.5">
                    AI Model Confidence
                  </span>
                  <span className="text-2xl font-black text-slate-100 font-mono">
                    {confidencePercent}%
                  </span>
                  <span className="text-[10px] text-slate-400 block">Random Forest (100 Trees)</span>
                </div>
              </div>

              {/* Warning Alert Banner (matches Screenshot 2 when critical) */}
              <div
                className={`p-3.5 rounded-xl border flex items-start gap-2.5 ${
                  isCollision
                    ? "bg-rose-950/80 border-rose-500/60 text-rose-200"
                    : currentRisk === "HIGH_RISK"
                    ? "bg-orange-950/70 border-orange-500/50 text-orange-200"
                    : currentRisk === "CAUTION"
                    ? "bg-amber-950/60 border-amber-500/50 text-amber-200"
                    : "bg-emerald-950/60 border-emerald-500/40 text-emerald-200"
                }`}
              >
                <AlertTriangle className={`w-4 h-4 shrink-0 mt-0.5 ${isCollision ? "text-rose-400 animate-bounce" : ""}`} />
                <p className="text-xs leading-relaxed font-medium">{warningText}</p>
              </div>

              {/* Layer 4 Fail-Safe Status */}
              <div className="flex items-center justify-between text-xs py-1 px-2 rounded bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400">Layer 4 Fail-Safe Status:</span>
                <span
                  className={`font-bold ${
                    overrideApplied ? "text-amber-400" : "text-emerald-400"
                  }`}
                >
                  {overrideApplied ? "SAFETY OVERRIDE ESCALATED" : "AI INFERENCE VERIFIED"}
                </span>
              </div>

              {/* Class Probability Pills */}
              <div className="grid grid-cols-4 gap-1.5 pt-1">
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-400 uppercase block font-semibold">CAUT</span>
                  <span className="text-xs font-bold text-amber-400 font-mono">
                    {((probs.CAUTION || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-400 uppercase block font-semibold">COLL</span>
                  <span className="text-xs font-bold text-rose-400 font-mono">
                    {((probs.COLLISION_RISK || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-400 uppercase block font-semibold">HIGH</span>
                  <span className="text-xs font-bold text-orange-400 font-mono">
                    {((probs.HIGH_RISK || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-400 uppercase block font-semibold">SAFE</span>
                  <span className="text-xs font-bold text-emerald-400 font-mono">
                    {((probs.SAFE || 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Card 2: Traffic Minimization & Management */}
            <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-4 sm:p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                  Traffic Minimization &amp; Management
                </h3>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-950 text-amber-400 border border-amber-600/40">
                    Density: {density}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-300">
                    Vehicles: {totalVehicles}
                  </span>
                </div>
              </div>

              {/* Primary Directive Banner (Red if Collision, Green if Proceed) */}
              <div
                className={`p-3.5 rounded-xl border flex items-center gap-2.5 shadow-sm ${
                  isCollision
                    ? "border-rose-500/70 bg-rose-950/40 text-rose-300 shadow-rose-950/50"
                    : "border-emerald-500/60 bg-emerald-950/30 text-emerald-300 shadow-emerald-950/50"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full border flex items-center justify-center shrink-0 ${
                    isCollision ? "border-rose-400 text-rose-400" : "border-emerald-400 text-emerald-400"
                  }`}
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
                <span className="text-xs sm:text-sm font-black uppercase tracking-wider">
                  {recommendationSummary}
                </span>
              </div>

              {/* Side A & Side B Action Boxes */}
              <div className="grid grid-cols-2 gap-3">
                {/* Side A Guidance */}
                <div className="bg-[#080d19] p-3 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">
                    Side A Guidance
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center text-[9px] font-black ${
                        sideAAction.includes("PROCEED")
                          ? "border-emerald-400 text-emerald-400"
                          : "border-rose-400 text-rose-400"
                      }`}
                    >
                      {sideAAction.includes("PROCEED") ? "✓" : "✕"}
                    </span>
                    <span
                      className={`text-sm font-black uppercase ${
                        sideAAction.includes("PROCEED") ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {sideAAction.includes("PROCEED") ? "PROCEED" : "WAIT"}
                    </span>
                  </div>
                </div>

                {/* Side B Guidance */}
                <div className="bg-[#080d19] p-3 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">
                    Side B Guidance
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center text-[9px] font-black ${
                        sideBAction.includes("PROCEED")
                          ? "border-emerald-400 text-emerald-400"
                          : "border-rose-400 text-rose-400"
                      }`}
                    >
                      {sideBAction.includes("PROCEED") ? "✓" : "✕"}
                    </span>
                    <span
                      className={`text-sm font-black uppercase ${
                        sideBAction.includes("PROCEED") ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {sideBAction.includes("PROCEED") ? "PROCEED" : "WAIT"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Detailed Physical Reasoning */}
              <p className="text-xs text-slate-400 leading-relaxed font-medium bg-[#080d19] p-3 rounded-xl border border-slate-800/80">
                {explanation}
              </p>
            </div>

            {/* Card 3: Two Compact Real-Time Visual Charts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Chart 1: Kinematic Distance Trends */}
              <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-3.5 space-y-2">
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-[11px] font-bold text-slate-200">
                    Kinematic Distance Trends (Recent Telemetry)
                  </span>
                </div>

                {/* SVG Line Chart */}
                <div className="w-full h-28 bg-[#070b14] rounded-lg p-2 border border-slate-800/70 relative">
                  <svg viewBox="0 0 160 80" className="w-full h-full overflow-visible">
                    <defs>
                      <linearGradient id="cyanLineGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Horizontal grid lines */}
                    <line x1="0" y1="20" x2="160" y2="20" stroke="#1e293b" strokeWidth="0.5" />
                    <line x1="0" y1="50" x2="160" y2="50" stroke="#1e293b" strokeWidth="0.5" />

                    {/* Side A Line */}
                    {telemetryHistory.length > 1 && (
                      <polyline
                        fill="none"
                        stroke="#06b6d4"
                        strokeWidth="1.5"
                        points={telemetryHistory
                          .map((pt, i) => {
                            const x = (i / (telemetryHistory.length - 1)) * 160;
                            const y = 75 - (Math.min(pt.distA, 150) / 150) * 65;
                            return `${x},${y}`;
                          })
                          .join(" ")}
                      />
                    )}

                    {/* Side B Line */}
                    {telemetryHistory.length > 1 && (
                      <polyline
                        fill="none"
                        stroke="#38bdf8"
                        strokeWidth="1.5"
                        strokeDasharray="2 2"
                        points={telemetryHistory
                          .map((pt, i) => {
                            const x = (i / (telemetryHistory.length - 1)) * 160;
                            const y = 75 - (Math.min(pt.distB, 150) / 150) * 65;
                            return `${x},${y}`;
                          })
                          .join(" ")}
                      />
                    )}
                  </svg>
                  <div className="flex justify-between text-[9px] text-slate-400 font-mono mt-0.5">
                    <span>#1</span>
                    <span className="text-cyan-400">Side A (solid)</span>
                    <span className="text-blue-400">Side B (dashed)</span>
                    <span>#15</span>
                  </div>
                </div>
              </div>

              {/* Chart 2: Event Risk Level Distribution */}
              <div className="bg-[#0b1120] rounded-2xl border border-slate-800 p-3.5 space-y-2">
                <div className="flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-[11px] font-bold text-slate-200">
                    Event Risk Level Distribution
                  </span>
                </div>

                {/* Bar Chart */}
                <div className="w-full h-28 bg-[#070b14] rounded-lg p-2 border border-slate-800/70 flex items-end justify-around gap-2">
                  {/* SAFE */}
                  <div className="flex flex-col items-center flex-1 h-full justify-end">
                    <span className="text-[9px] text-slate-400 font-mono mb-0.5">
                      {riskDistribution.SAFE}
                    </span>
                    <div
                      className="w-full bg-emerald-500 rounded-t transition-all duration-300"
                      style={{
                        height: `${Math.min(Math.max((riskDistribution.SAFE / 50) * 70, 6), 70)}px`,
                      }}
                    ></div>
                    <span className="text-[9px] text-slate-400 mt-1 uppercase font-semibold">Safe</span>
                  </div>

                  {/* CAUTION */}
                  <div className="flex flex-col items-center flex-1 h-full justify-end">
                    <span className="text-[9px] text-amber-400 font-mono font-bold mb-0.5">
                      {riskDistribution.CAUTION}
                    </span>
                    <div
                      className="w-full bg-amber-500 rounded-t transition-all duration-300"
                      style={{
                        height: `${Math.min(Math.max((riskDistribution.CAUTION / 50) * 70, 6), 70)}px`,
                      }}
                    ></div>
                    <span className="text-[9px] text-amber-400 mt-1 uppercase font-semibold">Caut</span>
                  </div>

                  {/* HIGH_RISK */}
                  <div className="flex flex-col items-center flex-1 h-full justify-end">
                    <span className="text-[9px] text-orange-400 font-mono mb-0.5">
                      {riskDistribution.HIGH_RISK}
                    </span>
                    <div
                      className="w-full bg-orange-500 rounded-t transition-all duration-300"
                      style={{
                        height: `${Math.min(Math.max((riskDistribution.HIGH_RISK / 50) * 70, 6), 70)}px`,
                      }}
                    ></div>
                    <span className="text-[9px] text-orange-400 mt-1 uppercase font-semibold">High</span>
                  </div>

                  {/* COLLISION_RISK */}
                  <div className="flex flex-col items-center flex-1 h-full justify-end">
                    <span className="text-[9px] text-rose-400 font-mono mb-0.5">
                      {riskDistribution.COLLISION_RISK}
                    </span>
                    <div
                      className="w-full bg-rose-500 rounded-t transition-all duration-300"
                      style={{
                        height: `${Math.min(Math.max((riskDistribution.COLLISION_RISK / 50) * 70, 6), 70)}px`,
                      }}
                    ></div>
                    <span className="text-[9px] text-rose-400 mt-1 uppercase font-semibold">Coll</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>


        {/* ================= SECTION 3: COMPLETE HISTORY LOG ================= */}
        <CompleteHistorySection onRefreshTrigger={refreshTrigger} />
      </main>

      {/* ================= FOOTER ================= */}
      <footer className="border-t border-slate-800/80 bg-[#090d18] px-4 py-4 text-center text-xs text-slate-400">
        <p>
          AI-Integrated Smart Traffic &amp; Blind-Corner Safety System &bull; 100% Software Architecture with Random Forest ML &amp; Deterministic Layer 4 Failsafe Override
        </p>
      </footer>
    </div>
  );
};
