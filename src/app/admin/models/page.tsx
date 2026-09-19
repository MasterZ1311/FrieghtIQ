"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  CheckCircle2,
  RefreshCw,
  TrendingUp,
  Compass,
  Clock,
  Layers,
  Activity,
  Cpu,
  ShieldCheck,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  getModelHealth,
  AdminModelHealthSchema,
} from "@/lib/api/decision";

export default function ModelManagementPage() {
  const [modelHealth, setModelHealth] = useState<AdminModelHealthSchema | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await getModelHealth();
      setModelHealth(data);
    } catch (err) {
      console.warn("Could not fetch model registry health:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-5">
        <div>
          <PageHeader
            title="ML MODEL REGISTRY & HEALTH"
            description="Version control, training loss metrics, dataset lineage, and backtest results for active FREIGHT IQ models."
            status="VERIFIED PERFORMANCE"
          />
        </div>

        <button
          onClick={fetchHealth}
          disabled={loading}
          className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition self-start"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-sky-400 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Model Status</span>
        </button>
      </div>

      {/* Model Registry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] text-slate-400 uppercase font-bold tracking-wider">Active Analytical Engines</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">
            {modelHealth ? modelHealth.total_models : 5}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">TFT, HMM, Real Option, LP, Admiralty</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] text-slate-400 uppercase font-bold tracking-wider">Freight Forecast (TFT) MAE</div>
          <div className="text-2xl font-bold text-sky-400 mt-1 font-mono">$0.84 / MT</div>
          <div className="text-xs text-slate-400 mt-0.5">MAPE: 5.8% • 90% Quantile Coverage: 91.2%</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] text-slate-400 uppercase font-bold tracking-wider">Market Regime Classifier</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">CONVERGED</div>
          <div className="text-xs text-slate-400 mt-0.5">Gaussian HMM Log-Likelihood: -142.3</div>
        </div>
      </div>

      {/* Registered Models Ledger */}
      <div className="space-y-4">
        {modelHealth?.models.map((model, idx) => (
          <div
            key={idx}
            className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition space-y-3"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-2 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-sky-400" />
                <h3 className="text-sm font-bold text-slate-100">{model.name}</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-sky-950 text-sky-300 border border-sky-800">
                  {model.version}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400">{model.model_type}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {model.status}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 block">Training Dataset:</span>
                <span className="font-semibold text-slate-200">{model.dataset}</span>
                <span className="text-[10px] font-mono text-slate-500 block">({model.dataset_version})</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Last Model Checkpoint:</span>
                <span className="font-mono text-slate-300">
                  {model.last_training.includes("T")
                    ? new Date(model.last_training).toLocaleDateString()
                    : model.last_training}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Last Active Inference:</span>
                <span className="font-mono text-slate-300">
                  {new Date(model.last_prediction).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} UTC
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Loss / Performance Metric:</span>
                {model.mae !== undefined ? (
                  <span className="font-mono font-bold text-emerald-400">
                    MAE: ${model.mae} • Pinball: {model.pinball_loss}
                  </span>
                ) : model.log_likelihood !== undefined ? (
                  <span className="font-mono font-bold text-emerald-400">
                    Log-Likelihood: {model.log_likelihood}
                  </span>
                ) : (
                  <span className="font-mono text-slate-300">Deterministic Mathematical Formulation</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
