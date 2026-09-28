import React from "react";

interface DigitalTwinCanvasProps {
  distanceA: number;
  speedA: number;
  distanceB: number;
  speedB: number;
  sideAAction: string;
  sideBAction: string;
  finalRisk: string;
}

export const DigitalTwinCanvas: React.FC<DigitalTwinCanvasProps> = ({
  distanceA,
  speedA,
  distanceB,
  speedB,
  sideAAction,
  sideBAction,
  finalRisk,
}) => {
  // Clamp distance between 10cm (at stopline) and 150cm (far approach)
  const clampA = Math.min(Math.max(distanceA, 10), 150);
  const clampB = Math.min(Math.max(distanceB, 10), 150);

  // Side A vertical position:
  // 150cm -> Y=60 (top), 10cm -> Y=195 (at intersection stopline)
  const normA = (clampA - 10) / (150 - 10);
  const carAY = 195 - normA * 135; // 60 to 195

  // Side B horizontal position:
  // 150cm -> X=60 (far left), 10cm -> X=210 (at intersection stopline)
  const normB = (clampB - 10) / (150 - 10);
  const carBX = 210 - normB * 150; // 60 to 210

  const isCollision = finalRisk === "COLLISION_RISK";
  const isHighRisk = finalRisk === "HIGH_RISK";
  const isCaution = finalRisk === "CAUTION";

  const sigAGreen = !isCollision && sideAAction.includes("PROCEED");
  const sigBGreen = !isCollision && sideBAction.includes("PROCEED");

  return (
    <div className="w-full space-y-2.5">
      <div className="relative w-full aspect-[16/10] bg-[#070b14] rounded-xl border border-slate-800/90 overflow-hidden flex items-center justify-center p-3">
      <svg viewBox="0 0 540 340" className="w-full h-full select-none">
        <defs>
          {/* Subtle grid */}
          <pattern id="twinGrid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#131c2e" strokeWidth="0.5" />
          </pattern>
          {/* Obstruction hatching */}
          <pattern id="obstructionHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="8" stroke="#1c2638" strokeWidth="1" />
          </pattern>
          {/* Conflict Zone Yellow-Box Junction Hatching */}
          <pattern id="junctionHatch" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="10" stroke="#f59e0b" strokeWidth="0.9" opacity="0.32" />
          </pattern>
        </defs>

        <rect width="540" height="340" fill="url(#twinGrid)" />

        {/* ================= ROADS ================= */}
        {/* SIDE A ROAD (Vertical Lane from top down into intersection) */}
        <rect x="250" y="10" width="80" height="260" fill="#151d2d" stroke="#253248" strokeWidth="1.5" />
        {/* Road A Centerline */}
        <line x1="290" y1="10" x2="290" y2="210" stroke="#475569" strokeWidth="1.5" strokeDasharray="6 6" />

        {/* SIDE B ROAD (Horizontal Lane from left into intersection) */}
        <rect x="20" y="210" width="310" height="80" fill="#151d2d" stroke="#253248" strokeWidth="1.5" />
        {/* Road B Centerline */}
        <line x1="20" y1="250" x2="250" y2="250" stroke="#475569" strokeWidth="1.5" strokeDasharray="6 6" />

        {/* Stop Lines */}
        <line x1="250" y1="210" x2="330" y2="210" stroke={sigAGreen ? "#10b981" : "#ef4444"} strokeWidth="3" />
        <line x1="250" y1="210" x2="250" y2="290" stroke={sigBGreen ? "#10b981" : "#ef4444"} strokeWidth="3" />

        {/* ================= INTERSECTION CONFLICT ZONE (NEVER BLANK) ================= */}
        {/* Intersection Box */}
        <rect
          x="250"
          y="210"
          width="80"
          height="80"
          fill={
            isCollision
              ? "rgba(239, 68, 68, 0.22)"
              : isHighRisk
              ? "rgba(249, 115, 22, 0.16)"
              : isCaution
              ? "rgba(245, 158, 11, 0.12)"
              : "rgba(16, 185, 129, 0.08)"
          }
          stroke={isCollision ? "#ef4444" : isHighRisk ? "#f97316" : isCaution ? "#f59e0b" : "#3b82f6"}
          strokeWidth="1.5"
          strokeDasharray="4 4"
        />

        {/* Real-World Conflict Zone Yellow-Box Pavement Markings */}
        <rect x="251" y="211" width="78" height="78" fill="url(#junctionHatch)" />

        {/* Dynamic Road Passage Flow Chevrons */}
        {sigBGreen && !isCollision && (
          <g opacity="0.8">
            <path d="M 256 250 L 267 250 M 263 246 L 267 250 L 263 254" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M 313 250 L 324 250 M 320 246 L 324 250 L 320 254" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </g>
        )}
        {sigAGreen && !isCollision && (
          <g opacity="0.8">
            <path d="M 290 216 L 290 227 M 286 223 L 290 227 L 294 223" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M 290 273 L 290 284 M 286 280 L 290 284 L 294 280" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </g>
        )}

        {/* 1-Line Instruction HUD Badge Inside Intersection Box */}
        <g transform="translate(290, 250)">
          {/* Glassmorphic backdrop badge */}
          <rect
            x="-44"
            y="-22"
            width="88"
            height="44"
            rx="6"
            fill={
              isCollision
                ? "rgba(69, 10, 10, 0.94)"
                : isHighRisk
                ? "rgba(67, 20, 7, 0.92)"
                : sigBGreen || sigAGreen
                ? "rgba(6, 78, 59, 0.92)"
                : "rgba(8, 47, 73, 0.92)"
            }
            stroke={
              isCollision
                ? "#ef4444"
                : isHighRisk
                ? "#f97316"
                : sigBGreen || sigAGreen
                ? "#10b981"
                : "#38bdf8"
            }
            strokeWidth="1.4"
          />

          {/* Micro Top Tag */}
          <rect
            x="-40"
            y="-19"
            width="80"
            height="9"
            rx="2.5"
            fill="rgba(15, 23, 42, 0.85)"
          />
          <circle
            cx="-32"
            cy="-14.5"
            r="2"
            fill={isCollision ? "#ef4444" : "#10b981"}
          />
          <text
            x="-26"
            y="-12"
            fill={isCollision ? "#fca5a5" : "#38bdf8"}
            fontSize="5"
            fontWeight="900"
            letterSpacing="0.08em"
          >
            {isCollision ? "SAFETY OVERRIDE" : "AI CONFLICT DISPATCH"}
          </text>

          {/* 1-LINE INSTRUCTION TO BOTH VEHICLES (CLIENT-ATTRACTIVE) */}
          <text
            x="0"
            y="2"
            fill="#ffffff"
            fontSize="6.2"
            fontWeight="900"
            textAnchor="middle"
            letterSpacing="0.01em"
          >
            {isCollision
              ? "🛑 ALL VEHICLES STOP 🛑"
              : sigBGreen
              ? "➔ B: PROCEED | 🛑 A: WAIT"
              : sigAGreen
              ? "➔ A: PROCEED | 🛑 B: WAIT"
              : "✔ PROCEED WITH CAUTION"}
          </text>

          {/* Subline explanation */}
          <text
            x="0"
            y="13"
            fill={isCollision ? "#fca5a5" : "#6ee7b7"}
            fontSize="4.8"
            fontWeight="bold"
            textAnchor="middle"
            letterSpacing="0.04em"
          >
            {isCollision
              ? "COLLISION PREVENTED"
              : sigBGreen
              ? "SIDE B RIGHT-OF-WAY"
              : sigAGreen
              ? "SIDE A RIGHT-OF-WAY"
              : "CORRIDOR CLEAR"}
          </text>
        </g>

        {/* ================= BLIND OBSTRUCTION CORNER ================= */}
        {/* Top-Left Quadrant Obstruction Wall */}
        <rect x="50" y="30" width="180" height="160" rx="6" fill="#0d1424" stroke="#25354e" strokeWidth="1.5" />
        <rect x="52" y="32" width="176" height="156" rx="4" fill="url(#obstructionHatch)" />

        <text x="140" y="105" fill="#94a3b8" fontSize="11" fontWeight="bold" textAnchor="middle" letterSpacing="0.08em">
          BLIND OBSTRUCTION
        </text>
        <text x="140" y="125" fill="#64748b" fontSize="9" textAnchor="middle">
          (Zero Direct Line of Sight Between Lanes)
        </text>

        {/* Laser Sight Lines / Occlusion Line */}
        <line
          x1={carBX + 30}
          y1="250"
          x2="230"
          y2="190"
          stroke="#ef4444"
          strokeWidth="1"
          strokeDasharray="3 3"
          opacity="0.7"
        />
        <line
          x1="230"
          y1="190"
          x2="290"
          y2={carAY + 25}
          stroke="#ef4444"
          strokeWidth="1"
          strokeDasharray="3 3"
          opacity="0.7"
        />

        {/* Road Labels */}
        <text x="290" y="26" fill="#64748b" fontSize="8" fontWeight="bold" textAnchor="middle" letterSpacing="0.05em">
          SIDE A ROAD
        </text>
        <text x="70" y="222" fill="#64748b" fontSize="8" fontWeight="bold" textAnchor="start" letterSpacing="0.05em">
          SIDE B ROAD
        </text>

        {/* ================= SENSORS ================= */}
        {/* Sensor A (Right of Side A road) */}
        <g transform="translate(345, 95)">
          <rect x="-14" y="-12" width="28" height="24" rx="4" fill="#0c1626" stroke="#0ea5e9" strokeWidth="1.5" />
          <circle cx="-6" cy="0" r="4.5" fill="#0284c7" stroke="#38bdf8" strokeWidth="1" />
          <circle cx="6" cy="0" r="4.5" fill="#0284c7" stroke="#38bdf8" strokeWidth="1" />
          <text x="0" y="-16" fill="#38bdf8" fontSize="8" fontWeight="bold" textAnchor="middle">
            SENSOR A
          </text>
        </g>

        {/* Sensor B (Below Side B road) */}
        <g transform="translate(145, 305)">
          <rect x="-12" y="-14" width="24" height="28" rx="4" fill="#0c1626" stroke="#0ea5e9" strokeWidth="1.5" />
          <circle cx="0" cy="-6" r="4.5" fill="#0284c7" stroke="#38bdf8" strokeWidth="1" />
          <circle cx="0" cy="6" r="4.5" fill="#0284c7" stroke="#38bdf8" strokeWidth="1" />
          <text x="0" y="23" fill="#38bdf8" fontSize="8" fontWeight="bold" textAnchor="middle">
            SENSOR B
          </text>
        </g>

        {/* ================= TRAFFIC LIGHTS ================= */}
        {/* SIG A (Next to stopline A) */}
        <g transform="translate(342, 205)">
          <rect x="-7" y="-14" width="14" height="28" rx="3" fill="#0b1120" stroke="#334155" strokeWidth="1" />
          <circle cx="0" cy="-6" r="3.5" fill={sigAGreen ? "#1e293b" : "#ef4444"} />
          <circle cx="0" cy="6" r="3.5" fill={sigAGreen ? "#10b981" : "#1e293b"} />
          <text x="12" y="2" fill="#94a3b8" fontSize="8" fontWeight="bold" textAnchor="start">
            SIG A
          </text>
        </g>

        {/* SIG B (Next to stopline B) */}
        <g transform="translate(242, 298)">
          <rect x="-14" y="-7" width="28" height="14" rx="3" fill="#0b1120" stroke="#334155" strokeWidth="1" />
          <circle cx="-6" cy="0" r="3.5" fill={sigBGreen ? "#1e293b" : "#ef4444"} />
          <circle cx="6" cy="0" r="3.5" fill={sigBGreen ? "#10b981" : "#1e293b"} />
          <text x="0" y="16" fill="#94a3b8" fontSize="8" fontWeight="bold" textAnchor="middle">
            SIG B
          </text>
        </g>

        {/* ================= VEHICLES ================= */}
        {/* Vehicle A (Blue Car traveling down) */}
        <g transform={`translate(290, ${carAY})`}>
          {/* Distance Tag */}
          <rect x="-24" y="-22" width="48" height="13" rx="2" fill="#082f49" stroke="#0284c7" strokeWidth="1" />
          <text x="0" y="-13" fill="#38bdf8" fontSize="9" fontWeight="bold" textAnchor="middle">
            A: {distanceA.toFixed(0)}cm
          </text>
          {/* Car Body */}
          <rect x="-14" y="-7" width="28" height="42" rx="5" fill="#0284c7" stroke="#38bdf8" strokeWidth="1.5" />
          {/* Windshield */}
          <rect x="-10" y="14" width="20" height="8" rx="2" fill="#bae6fd" />
          {/* Headlights */}
          <circle cx="-8" cy="32" r="2.5" fill="#fef08a" />
          <circle cx="8" cy="32" r="2.5" fill="#fef08a" />
        </g>

        {/* Vehicle B (Green Car traveling right) */}
        <g transform={`translate(${carBX}, 250)`}>
          {/* Distance Tag */}
          <rect x="-24" y="-30" width="48" height="13" rx="2" fill="#064e3b" stroke="#059669" strokeWidth="1" />
          <text x="0" y="-21" fill="#34d399" fontSize="9" fontWeight="bold" textAnchor="middle">
            B: {distanceB.toFixed(0)}cm
          </text>
          {/* Car Body */}
          <rect x="-21" y="-14" width="42" height="28" rx="5" fill="#059669" stroke="#34d399" strokeWidth="1.5" />
          {/* Windshield */}
          <rect x="8" y="-10" width="8" height="20" rx="2" fill="#a7f3d0" />
          {/* Headlights */}
          <circle cx="18" cy="-8" r="2.5" fill="#fef08a" />
          <circle cx="18" cy="8" r="2.5" fill="#fef08a" />
        </g>

        {/* ================= BUZZER ACTIVE BADGE (when Collision Risk) ================= */}
        {isCollision && (
          <g transform="translate(455, 30)">
            <rect x="-65" y="-12" width="130" height="24" rx="12" fill="#450a0a" stroke="#ef4444" strokeWidth="1.5" />
            <circle cx="-50" cy="0" r="4.5" fill="#ef4444" />
            <circle cx="-50" cy="0" r="3" fill="#ffffff" />
            <text x="-40" y="3.5" fill="#fca5a5" fontSize="8.5" fontWeight="900" letterSpacing="0.05em">
              BUZZER ACTIVE (2000Hz)
            </text>
          </g>
        )}

        {/* ================= COLLISION IMPACT ZONE HALO ================= */}
        {isCollision && (
          <g transform="translate(290, 250)">
            <circle cx="0" cy="0" r="38" fill="rgba(239, 68, 68, 0.3)" stroke="#ef4444" strokeWidth="2" strokeDasharray="4 4" />
          </g>
        )}
      </svg>
    </div>

    {/* 1-Line Client-Attracting Instruction Banner */}
    <div
      className={`w-full px-3.5 py-2.5 rounded-xl border flex items-center justify-between shadow-lg transition-all ${
        isCollision
          ? "bg-rose-950/60 border-rose-500/70 text-rose-200 shadow-rose-950/40"
          : sigBGreen || sigAGreen
          ? "bg-emerald-950/50 border-emerald-500/60 text-emerald-200 shadow-emerald-950/30"
          : "bg-[#0b1324] border-slate-700/80 text-slate-300"
      }`}
    >
      <div className="flex items-center gap-2.5 overflow-hidden">
        <span
          className={`w-2.5 h-2.5 rounded-full shrink-0 ${
            isCollision ? "bg-rose-500 animate-ping" : "bg-emerald-400 animate-pulse"
          }`}
        />
        <span className="text-[10px] font-black uppercase tracking-wider text-slate-400 shrink-0">
          Live Vehicle Directive:
        </span>
        <span className="text-xs sm:text-sm font-black tracking-wide truncate">
          {isCollision
            ? "🛑 CRITICAL: BOTH VEHICLES MUST STOP & HOLD AT STOPLINE"
            : sigBGreen
            ? "➔ VEHICLE B: PROCEED SAFELY | 🛑 VEHICLE A: WAIT AT STOPLINE"
            : sigAGreen
            ? "➔ VEHICLE A: PROCEED SAFELY | 🛑 VEHICLE B: WAIT AT STOPLINE"
            : "✔ ALL CLEAR: PROCEED WITH CAUTION (20 KM/H)"}
        </span>
      </div>
      <span
        className={`text-[9px] font-black font-mono px-2 py-0.5 rounded border uppercase tracking-wider shrink-0 ${
          isCollision
            ? "bg-rose-900/80 border-rose-500/60 text-rose-300"
            : "bg-emerald-900/80 border-emerald-500/60 text-emerald-300"
        }`}
      >
        {isCollision ? "HAZARD AVOIDED" : "AI ARBITRATED"}
      </span>
    </div>
  </div>
  );
};
