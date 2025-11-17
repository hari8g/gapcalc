# dos_gap_closure_planner.py
# Run this in Jupyter or as a plain Python script.
# Output: dos_gap_closure_planner.html

import json, os

defaults = {
    "exit_arr_2025": 4200000,        # EUR
    "target_exit_arr_2026": 6500000, # EUR
    "customers_present_2025": 54,
    "median_mrpu": 7500,             # monthly EUR
    "median_mrpu_customers": 49,
    "max_mrpu": 30000,               # monthly EUR
    "max_mrpu_customers": 2,

    # Present (status-quo) funnel rates
    "reach_rate_present": 0.50,
    "meeting_rate_present": 0.25,
    "win_rate_present": 0.09,

    # ICP counts
    "ICP_2025": 1000,                # present ICP (2025)
    "ICP_2026": 300,                 # planned ICP (2026)
    "ICP_current_2026": 150,         # status-quo ICP already active in 2026

    # uplift weights (for distribution of uplift across reach/meet/win)
    "uplift_weight_reach": 1.0,
    "uplift_weight_meet": 1.0,
    "uplift_weight_win": 1.0,

    # unit economics inputs
    "ndr_target": 1.10,              # Net Dollar Retention target (e.g. 1.10 = 110%)
    "payback_months_2025": 14,       # current payback period in months (2025)
    "payback_months": 10,            # desired payback period in months (2026 / target)
    "ideal_customer_lifetime_years": 3.0,  # ideal customer lifetime in years

    # GM + revenue share + tier MRPUs
    "gm_2025": 0.07,                 # 7% gross margin 2025
    "gm_2026_anticipated": 0.10,     # 10% target GM 2026
    "rev_share_infra_2025": 0.95,    # 95% infra revenue share 2025
    "rev_share_managed_2025": 0.05,  # 5% managed share 2025
    "tier1_mrpu": 35000,             # high MRPU tier (monthly)
    "tier2_mrpu": 12500,             # mid MRPU tier (monthly)
    "tier3_mrpu": 6000,              # long tail tier (monthly)

    # Monte Carlo tuning for tier mix
    "gap_tolerance_pct": 0.07,       # ±7% band around gap MRR for "close"
    "mc_tier_iterations": 5000       # #iterations per grid cell
}

defaults_json = json.dumps(defaults, indent=2)

html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Region IN- D.OS Business equations</title>
  <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
  <style>
    body {
      font-family: Arial, Helvetica, sans-serif;
      margin: 14px;
      background: radial-gradient(circle at top left, #eef2ff, #f9fafb);
      color: #0f172a;
    }
    h2 {
      margin-bottom: 10px;
      font-size: 24px;
      color: #111827;
    }
    .layout {
      display:grid;
      grid-template-columns:420px 1fr;
      gap:14px;
      align-items:flex-start;
    }
    .panel {
      background:#ffffff;
      padding:12px 14px;
      border-radius:10px;
      box-shadow:0 10px 30px rgba(15,23,42,0.08);
      border:1px solid #e5e7eb;
      max-height:88vh;
      overflow:auto;
    }
    label {
      display:block;
      font-size:12px;
      margin-bottom:4px;
      color:#4b5563;
    }
    input[type=number] {
      width:100%;
      padding:6px 8px;
      border-radius:6px;
      border:1px solid #d1d5db;
      margin-bottom:8px;
      font-size:12px;
    }
    input[type=number]:focus {
      outline:none;
      border-color:#2563eb;
      box-shadow:0 0 0 1px rgba(37,99,235,0.2);
    }
    input[type=range] {
      width:100%;
    }
    .btn {
      background:#2563eb;
      color:#fff;
      padding:8px 14px;
      border-radius:18px;
      border:none;
      cursor:pointer;
      font-size:12px;
      font-weight:600;
      box-shadow:0 6px 14px rgba(37,99,235,0.35);
      transition:all 0.15s ease-out;
    }
    .btn:hover {
      transform:translateY(-1px);
      box-shadow:0 8px 18px rgba(37,99,235,0.45);
    }
    .btn:disabled {
      opacity:0.7;
      cursor:default;
      box-shadow:none;
      transform:none;
    }
    .kpi {
      display:flex;
      gap:10px;
      flex-wrap:wrap;
      margin-bottom:8px;
    }
    .kpi-card {
      flex:1 1 210px;
      background:linear-gradient(135deg,#ffffff,#f3f4ff);
      padding:10px 10px 8px;
      border-radius:10px;
      box-shadow:0 2px 10px rgba(15,23,42,0.08);
      border-left:4px solid #2563eb;
      text-align:left;
      transition:transform 0.12s ease-out, box-shadow 0.12s ease-out;
    }
    .kpi-card:hover {
      transform:translateY(-2px);
      box-shadow:0 6px 18px rgba(15,23,42,0.16);
    }
    /* Highlighted important KPI tiles */
    .kpi-important {
      background:linear-gradient(135deg,#fef3c7,#fde68a);
      border-left-color:#f97316;
      box-shadow:0 4px 14px rgba(249,115,22,0.25);
    }
    .muted {
      color:#6b7280;
      font-size:11px;
      margin-bottom:4px;
    }
    .big {
      font-weight:700;
      font-size:15px;
      color:#111827;
    }
    #debug {
      white-space:pre-wrap;
      font-family:monospace;
      background:#020617;
      color:#e5e7eb;
      padding:8px;
      border-radius:6px;
      max-height:180px;
      overflow:auto;
      font-size:11px;
      border:1px solid #111827;
    }
    .insight {
      background:#f8fafc;
      padding:10px 12px;
      border-radius:10px;
      margin-top:8px;
      font-size:13px;
      border:1px solid #e5edf7;
    }
    .insight-header {
      font-weight:700;
      margin-bottom:6px;
      font-size:14px;
      color:#0f172a;
    }
    .insight-section {
      margin-bottom:8px;
    }
    .insight-section-title {
      font-weight:600;
      margin-bottom:4px;
      font-size:13px;
      color:#111827;
    }
    .insight-row {
      display:flex;
      flex-wrap:wrap;
      gap:8px;
      margin-bottom:4px;
    }
    .pill {
      display:inline-block;
      padding:3px 8px;
      border-radius:999px;
      background:#e0edff;
      color:#1e40af;
      font-size:11px;
      font-weight:600;
    }
    .pill-critical {
      background:#fee2e2;
      color:#b91c1c;
    }
    .pill-okay {
      background:#dcfce7;
      color:#166534;
    }
    .pill-label {
      font-size:11px;
      margin-right:4px;
      color:#4b5563;
    }
    ul.insight-list {
      margin:4px 0 4px 18px;
      padding:0;
    }
    ul.insight-list li {
      margin-bottom:2px;
    }
    .weight-row {
      display:flex;
      align-items:center;
      gap:6px;
      margin-bottom:4px;
    }
    .weight-label {
      flex:0 0 180px;
      font-size:12px;
      color:#374151;
    }
    .weight-value {
      min-width:60px;
      text-align:right;
      font-size:11px;
      color:#4b5563;
    }
    .weights-caption {
      font-size:11px;
      color:#6b7280;
      margin-bottom:6px;
    }
    #tier_mix_heatmap { height:340px; }

    table.funnel-table {
      border-collapse: collapse;
      width: 100%;
      font-size: 12px;
      margin-top: 8px;
      background:#ffffff;
      border-radius:8px;
      overflow:hidden;
    }
    table.funnel-table th, table.funnel-table td {
      border: 1px solid #e5e7eb;
      padding: 4px 6px;
      text-align: right;
    }
    table.funnel-table th {
      background: #eff6ff;
      text-align: center;
      font-weight:600;
      color:#1f2937;
    }
    table.funnel-table td.stage {
      text-align: left;
      font-weight: 600;
      color:#111827;
    }

    .chart-title {
      font-size:16px;
      font-weight:700;
      margin-top:10px;
      margin-bottom:6px;
      color:#111827;
    }

    @media(max-width:1000px) {
      .layout { grid-template-columns:1fr; }
      .panel { max-height:none; }
    }
  </style>
</head>
<body>
  <h2>Region IN- D.OS Business equations — Gap closure & funnel uplift</h2>
  <div class="layout">
    <div class="panel">
      <div style="font-weight:700;margin-bottom:8px;font-size:14px;">Inputs (edit & Update)</div>
      <script> const DEFAULTS = REPLACE_DEFAULTS_HERE; </script>
      <div id="inputs"></div>

      <hr style="margin:10px 0; border:none; border-top:1px solid #e5e7eb;"/>
      <div style="font-weight:700;margin:8px 0 4px;font-size:14px;">Uplift distribution (weights)</div>
      <div class="weights-caption">
        Use sliders to decide where you want to push harder in 2026: reach, meetings, or win rate.
        We normalize these to a 100% uplift budget.
      </div>
      <div id="weights"></div>

      <div style="margin-top:8px;display:flex;gap:8px;">
        <button class="btn" id="btnUpdate">Update</button>
        <button class="btn" id="btnReset" style="background:#6b7280;box-shadow:none;">Reset</button>
      </div>

      <hr style="margin:10px 0; border:none; border-top:1px solid #e5e7eb;"/>
      <div style="font-weight:700;margin-bottom:6px;font-size:14px;">Debug / Log</div>
      <div id="debug">Logs will appear here.</div>
    </div>

    <div class="panel">
      <div style="font-weight:700;margin-bottom:8px;font-size:14px;">Gap closure, funnel, and unit economics</div>
      <div id="kpi_area" class="kpi"></div>
      <div class="insight" id="insights_area"></div>

      <div class="chart-title">Funnel volumes — 2025 present vs 2026 plan</div>
      <div id="funnel_chart" style="margin-top:4px;"></div>
      <!-- New table under funnel volumes chart -->
      <div id="funnel_chart_table" style="margin-top:6px;"></div>

      <div class="chart-title">2026 status — proposed vs status-quo funnel</div>
      <div id="funnel_status_chart" style="margin-top:4px;"></div>
      <div id="funnel_status_table" style="margin-top:6px;"></div>

      <div class="chart-title">Payback vs Gross Margin — 2025 vs 2026</div>
      <div id="payback_gm_chart" style="margin-top:4px;"></div>

      <div class="chart-title">Tier mix Monte Carlo — gap-closure probability</div>
      <div class="insight" id="tier_mix_summary" style="margin-top:4px;"></div>
      <div id="tier_mix_heatmap" style="margin-top:4px;"></div>
    </div>
  </div>

<script>
const DEFAULTS_JS = DEFAULTS;

/* ---------- Utilities ---------- */
function logDebug(msg){
  const d=document.getElementById("debug");
  const now=new Date().toISOString();
  if(d) d.textContent = now + " | " + msg + "\\n" + d.textContent;
  console.log("[GAP DEBUG]", msg);
}

function safeFloat(v, fallback=0){
  const n = parseFloat(v);
  return (isFinite(n) ? n : fallback);
}

function formatEuro(x){
  if(!isFinite(x)) return "—";
  return "€" + Math.round(x).toLocaleString();
}

function formatPct(x){
  if(!isFinite(x)) return "—";
  return (x*100).toFixed(1) + "%";
}

/* ---------- Inject input fields ---------- */
window.addEventListener("DOMContentLoaded", () => {
  const keys = [
    ["exit_arr_2025","Exit ARR 2025 (EUR)"],
    ["target_exit_arr_2026","Target exit ARR 2026 (EUR)"],
    ["customers_present_2025","Customers present (2025)"],
    ["median_mrpu","Median MRPU (monthly EUR)"],
    ["median_mrpu_customers","Number of customers at median MRPU"],
    ["max_mrpu","Maximum MRPU (monthly EUR)"],
    ["max_mrpu_customers","Number of customers at max MRPU"],
    ["reach_rate_present","Present reach rate (0–1)"],
    ["meeting_rate_present","Present meeting rate (0–1)"],
    ["win_rate_present","Present win rate (0–1)"],
    ["ICP_2025","Number of ICPs for 2025 (present)"],
    ["ICP_2026","Number of ICPs for 2026 (plan)"],
    ["ICP_current_2026","Number of ICPs currently active in 2026"],
    // unit economics
    ["ndr_target","Net Dollar Retention target (e.g. 1.10 = 110%)"],
    ["payback_months_2025","Current payback period 2025 (months)"],
    ["payback_months","Desired payback period 2026 (months)"],
    ["ideal_customer_lifetime_years","Ideal customer lifetime (years)"],
    // GM + rev share + tier MRPUs
    ["gm_2025","GM for 2025 (decimal, e.g. 0.07)"],
    ["gm_2026_anticipated","Anticipated GM for 2026 (decimal)"],
    ["rev_share_infra_2025","Revenue share from Infra 2025 (0–1)"],
    ["rev_share_managed_2025","Revenue share from Managed 2025 (0–1)"],
    ["tier1_mrpu","Tier 1 customer MRPU (monthly EUR)"],
    ["tier2_mrpu","Tier 2 customer MRPU (monthly EUR)"],
    ["tier3_mrpu","Tier 3 customer MRPU (monthly EUR)"],
    // MC controls
    ["gap_tolerance_pct","Gap tolerance for 'close' (decimal, e.g. 0.07 for ±7%)"],
    ["mc_tier_iterations","Tier MC iterations per cell"]
  ];
  const div = document.getElementById("inputs");
  keys.forEach(([k,label])=>{
    const w = document.createElement("div");
    w.style.marginBottom = "6px";
    const l = document.createElement("label");
    l.textContent = label;
    l.htmlFor = k;
    const input = document.createElement("input");
    input.type = "number";
    input.step = "any";
    input.id = k;
    input.value = (DEFAULTS_JS[k] !== undefined) ? DEFAULTS_JS[k] : "";
    w.appendChild(l);
    w.appendChild(input);
    div.appendChild(w);
  });

  // Status-quo funnel rate sliders (reach / meet / win)
  const statusHeader = document.createElement("div");
  statusHeader.style.fontWeight = "700";
  statusHeader.style.margin = "10px 0 4px";
  statusHeader.style.fontSize = "13px";
  statusHeader.textContent = "Status quo 2026 funnel rates (sliders)";
  div.appendChild(statusHeader);

  const statusCaption = document.createElement("div");
  statusCaption.className = "weights-caption";
  statusCaption.textContent = "Adjust current reach, meeting and win (hit) rates using sliders (0–100%). These feed both the KPIs and the 2026 status funnel.";
  div.appendChild(statusCaption);

  const statusKeys = [
    ["reach_rate_present","Reach rate (status quo)"],
    ["meeting_rate_present","Meeting rate (status quo)"],
    ["win_rate_present","Win / hit rate (status quo)"]
  ];
  statusKeys.forEach(([k,label])=>{
    const row = document.createElement("div");
    row.className = "weight-row";

    const lbl = document.createElement("div");
    lbl.className = "weight-label";
    lbl.textContent = label;

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0";
    slider.max = "1";
    slider.step = "0.01";
    slider.id = "slider_" + k;
    slider.value = (DEFAULTS_JS[k] !== undefined) ? DEFAULTS_JS[k] : 0;

    const val = document.createElement("div");
    val.className = "weight-value";
    val.id = "lbl_" + k;
    val.textContent = (parseFloat(slider.value)*100).toFixed(1) + "%";

    slider.addEventListener("input", () => {
      const v = parseFloat(slider.value);
      val.textContent = (v*100).toFixed(1) + "%";
      const numInput = document.getElementById(k);
      if(numInput) numInput.value = v;
    });

    row.appendChild(lbl);
    row.appendChild(slider);
    row.appendChild(val);
    div.appendChild(row);
  });

  // Uplift weights as sliders
  const weightsDiv = document.getElementById("weights");
  const wKeys = [
    ["uplift_weight_reach", "Reach uplift weight"],
    ["uplift_weight_meet",  "Meeting uplift weight"],
    ["uplift_weight_win",   "Win-rate uplift weight"]
  ];
  wKeys.forEach(([k,label])=>{
    const row = document.createElement("div");
    row.className = "weight-row";

    const lbl = document.createElement("div");
    lbl.className = "weight-label";
    lbl.textContent = label;

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0";
    slider.max = "1";
    slider.step = "0.05";
    slider.id = k;
    slider.value = (DEFAULTS_JS[k] !== undefined) ? DEFAULTS_JS[k] : 1.0;

    const val = document.createElement("div");
    val.className = "weight-value";
    val.id = "lbl_" + k;
    val.textContent = slider.value;

    slider.addEventListener("input", () => {
      val.textContent = slider.value;
    });

    row.appendChild(lbl);
    row.appendChild(slider);
    row.appendChild(val);
    weightsDiv.appendChild(row);
  });
});

/* ---------- Read inputs ---------- */
function readInputs(){
  const p = {};
  for(const k in DEFAULTS_JS){
    const el = document.getElementById(k);
    if(!el){
      p[k] = DEFAULTS_JS[k];
      continue;
    }
    p[k] = (el.value === "" ? DEFAULTS_JS[k] : Number(el.value));
  }
  return p;
}

/* ---------- Core calculation (gap, funnel & unit economics) ---------- */
function computePlan(p){
  const exit_arr = safeFloat(p.exit_arr_2025, 0);
  const target_arr = safeFloat(p.target_exit_arr_2026, 0);
  const gap_arr = Math.max(0, target_arr - exit_arr);
  const gap_mrr = gap_arr / 12.0;

  const med_mrpu = safeFloat(p.median_mrpu, 0);
  const med_n = Math.max(0, safeFloat(p.median_mrpu_customers, 0));
  const max_mrpu = safeFloat(p.max_mrpu, 0);
  const max_n = Math.max(0, safeFloat(p.max_mrpu_customers, 0));

  const total_cluster_cust = med_n + max_n;
  let avg_new_mrpu = med_mrpu;
  if(total_cluster_cust > 0){
    avg_new_mrpu = (med_mrpu * med_n + max_mrpu * max_n) / total_cluster_cust;
  }

  const required_new_customers =
    (avg_new_mrpu > 0) ? (gap_mrr / avg_new_mrpu) : Infinity;

  const reach0 = Math.min(1, Math.max(0, safeFloat(p.reach_rate_present, 0)));
  const meet0  = Math.min(1, Math.max(0, safeFloat(p.meeting_rate_present, 0)));
  const win0   = Math.min(1, Math.max(0, safeFloat(p.win_rate_present, 0)));
  const ICP_2025 = Math.max(0, safeFloat(p.ICP_2025, 0));
  const ICP_2026 = Math.max(0, safeFloat(p.ICP_2026, 0));
  const ICP_current_2026 = Math.max(0, safeFloat(p.ICP_current_2026, 0));

  const p_funnel0 = reach0 * meet0 * win0;
  const expected_wins_2025_present        = ICP_2025 * p_funnel0;
  const expected_wins_2026_present_rates  = ICP_2026 * p_funnel0;

  // Uplift weights from sliders
  const wr0 = Math.max(0, safeFloat(p.uplift_weight_reach, 1));
  const wm0 = Math.max(0, safeFloat(p.uplift_weight_meet, 1));
  const ww0 = Math.max(0, safeFloat(p.uplift_weight_win, 1));
  let sumW = wr0 + wm0 + ww0;
  let wr, wm, ww;
  if(sumW <= 0){
    wr = wm = ww = 1/3;
  } else {
    wr = wr0 / sumW;
    wm = wm0 / sumW;
    ww = ww0 / sumW;
  }

  let proposed_reach = reach0;
  let proposed_meet  = meet0;
  let proposed_win   = win0;
  let uplift_factor  = 1.0;
  let enough_already = false;

  if(expected_wins_2026_present_rates <= 0 || !isFinite(required_new_customers)){
    uplift_factor = NaN;
  } else if(expected_wins_2026_present_rates >= required_new_customers){
    uplift_factor = 1.0;
    enough_already = true;
  } else {
    const s = required_new_customers / expected_wins_2026_present_rates;
    uplift_factor = s;
    const cap = 0.95;

    proposed_reach = Math.min(cap, reach0 * Math.pow(s, wr));
    proposed_meet  = Math.min(cap, meet0  * Math.pow(s, wm));
    proposed_win   = Math.min(cap, win0   * Math.pow(s, ww));
  }

  const proposed_funnel_prob = proposed_reach * proposed_meet * proposed_win;
  const expected_wins_2026_proposed = ICP_2026 * proposed_funnel_prob;

  /* ---------- Unit economics & NDR on new customers ---------- */
  const gm_2026 = Math.max(0, safeFloat(p.gm_2026_anticipated, 0));
  const gm_2025 = Math.max(0, safeFloat(p.gm_2025, 0));
  const ndr_target = Math.max(0, safeFloat(p.ndr_target, 1.0));

  const lifetime_years  = Math.max(0, safeFloat(p.ideal_customer_lifetime_years, 0));
  const lifetime_months = lifetime_years * 12.0;

  const payback_months_2026  = Math.max(0, safeFloat(p.payback_months, 0));
  const payback_months_2025  = Math.max(0, safeFloat(p.payback_months_2025, 0));

  let new_cust_mrr_2026 = 0;
  if(isFinite(required_new_customers) && isFinite(avg_new_mrpu)){
    new_cust_mrr_2026 = required_new_customers * avg_new_mrpu;
  }

  let additional_mrr_ndr_new = 0;
  if(ndr_target > 1 && isFinite(new_cust_mrr_2026)){
    additional_mrr_ndr_new = new_cust_mrr_2026 * (ndr_target - 1);
  }

  const gross_profit_mrr_per_cust = avg_new_mrpu * gm_2026;

  let ltv_per_customer = 0;
  if(isFinite(gross_profit_mrr_per_cust) && lifetime_months > 0){
    ltv_per_customer = gross_profit_mrr_per_cust * lifetime_months;
  }

  let expected_cac = 0;
  if(isFinite(gross_profit_mrr_per_cust) && payback_months_2026 > 0){
    expected_cac = gross_profit_mrr_per_cust * payback_months_2026;
  }

  return {
    gap_arr,
    gap_mrr,
    avg_new_mrpu,
    required_new_customers,
    reach0, meet0, win0,
    expected_wins_2025_present,
    expected_wins_2026_present_rates,
    proposed_reach,
    proposed_meet,
    proposed_win,
    uplift_factor,
    enough_already,
    expected_wins_2026_proposed,
    ICP_2025,
    ICP_2026,
    ICP_current_2026,
    wr, wm, ww,
    wr0, wm0, ww0,
    gm_2025,
    gm_2026,
    ndr_target,
    lifetime_years,
    lifetime_months,
    payback_months_2025,
    payback_months_2026,
    new_cust_mrr_2026,
    additional_mrr_ndr_new,
    gross_profit_mrr_per_cust,
    ltv_per_customer,
    expected_cac
  };
}

/* ---------- Tier mix Monte Carlo ---------- */
function tierMixMonteCarlo(p, plan){
  const N_new = (isFinite(plan.required_new_customers) && plan.required_new_customers > 0)
    ? Math.round(plan.required_new_customers) : 0;
  if(N_new <= 0){
    return { recommended: null, heatmap: null, N_new: 0, tolPct: 0 };
  }

  const t1 = safeFloat(p.tier1_mrpu, 0);
  const t2 = safeFloat(p.tier2_mrpu, 0);
  const t3 = safeFloat(p.tier3_mrpu, 0);

  const gap_mrr = plan.gap_mrr;

  let tol = safeFloat(p.gap_tolerance_pct, 0.07);
  if(tol < 0) tol = 0;
  if(tol > 0.5) tol = 0.5;
  const mc_iters = Math.max(2000, Math.round(safeFloat(p.mc_tier_iterations, 5000)));

  const step = 0.05;
  const fVals = [];
  for(let f=0; f<=1.000001; f+=step) fVals.push(Math.round(f*100)/100);

  const z = [];
  const f1Vec = fVals.slice();
  const f2Vec = fVals.slice();
  let best = null;

  function randTier(f1,f2,f3){
    const r = Math.random();
    if(r < f1) return 1;
    else if(r < f1 + f2) return 2;
    return 3;
  }

  for(let j=0; j<f2Vec.length; j++){
    const row = [];
    const f2 = f2Vec[j];
    for(let i=0; i<f1Vec.length; i++){
      const f1 = f1Vec[i];
      if(f1 + f2 > 1.000001){
        row.push(NaN);
        continue;
      }
      const f3 = Math.max(0, 1 - f1 - f2);
      let successGap = 0;
      let avgMrpuSum = 0;

      for(let it=0; it<mc_iters; it++){
        let totalMRPU = 0;
        for(let k=0; k<N_new; k++){
          const tier = randTier(f1,f2,f3);
          if(tier === 1) totalMRPU += t1;
          else if(tier === 2) totalMRPU += t2;
          else totalMRPU += t3;
        }
        const new_MRR = totalMRPU;
        const avgMRPU = totalMRPU / N_new;
        avgMrpuSum += avgMRPU;

        const gap_ok = (gap_mrr > 0)
          ? (Math.abs(new_MRR - gap_mrr) <= tol * gap_mrr)
          : true;

        if(gap_ok) successGap++;
      }

      const prob_gap      = successGap / mc_iters;
      const mean_avg_mrpu = avgMrpuSum / mc_iters;

      row.push(prob_gap);

      const candidate = { f1, f2, f3, prob_gap, mean_avg_mrpu };
      if(!best ||
         candidate.prob_gap > best.prob_gap ||
         (candidate.prob_gap === best.prob_gap &&
          candidate.mean_avg_mrpu > best.mean_avg_mrpu)){
        best = candidate;
      }
    }
    z.push(row);
  }

  logDebug("Tier MC: N_new=" + N_new + ", tol=" + tol + ", iters=" + mc_iters);

  return {
    recommended: best,
    heatmap: { f1Vec, f2Vec, z },
    N_new: N_new,
    tolPct: tol
  };
}

/* ---------- KPI tiles ---------- */
function renderKPIs(plan, p){
  const kdiv = document.getElementById("kpi_area");
  kdiv.innerHTML = "";

  const items = [
    ["Exit ARR 2025", formatEuro(p.exit_arr_2025)],
    ["Target exit ARR 2026", formatEuro(p.target_exit_arr_2026)],
    ["Gap ARR (annual)", formatEuro(plan.gap_arr)],
    ["Gap closure target in MRR", formatEuro(plan.gap_mrr)],
    ["Avg new MRPU (from median/max mix)", formatEuro(plan.avg_new_mrpu)],
    ["Required new customers (2026)", isFinite(plan.required_new_customers) ? plan.required_new_customers.toFixed(1) : "—"],
    ["ICP 2025 (present)", plan.ICP_2025],
    ["ICP 2026 (plan)", plan.ICP_2026],
    ["ICP 2026 currently active (status quo)", plan.ICP_current_2026],
    ["Present reach rate", formatPct(plan.reach0)],
    ["Present meeting rate", formatPct(plan.meet0)],
    ["Present win rate", formatPct(plan.win0)],
    ["Expected wins 2025 @ present funnel", plan.expected_wins_2025_present.toFixed(1)],
    ["Expected wins 2026 @ present funnel (plan ICP)", plan.expected_wins_2026_present_rates.toFixed(1)],
    ["Proposed reach rate 2026", formatPct(plan.proposed_reach)],
    ["Proposed meeting rate 2026", formatPct(plan.proposed_meet)],
    ["Proposed win rate 2026", formatPct(plan.proposed_win)],
    ["Expected wins 2026 @ proposed funnel (plan ICP)", plan.expected_wins_2026_proposed.toFixed(1)],
    ["Overall uplift factor (vs 2026 demand)", isFinite(plan.uplift_factor) ? plan.uplift_factor.toFixed(2) : "N/A"],
    ["Normalized uplift weights (reach / meet / win)", `${plan.wr.toFixed(2)} / ${plan.wm.toFixed(2)} / ${plan.ww.toFixed(2)}`],
    ["Tier MC gap tolerance", (safeFloat(p.gap_tolerance_pct,0.07)*100).toFixed(1) + "%"],
    ["Tier MC iterations per cell", Math.round(safeFloat(p.mc_tier_iterations,5000))],
    // Unit economics
    ["Net Dollar Retention target", isFinite(plan.ndr_target) ? (plan.ndr_target*100).toFixed(1) + "%" : "—"],
    ["New-customer MRR 2026 (before NDR)", formatEuro(plan.new_cust_mrr_2026)],
    ["Additional MRR from NDR (new customers only)", formatEuro(plan.additional_mrr_ndr_new)],
    ["GM 2025 (actual)", formatPct(plan.gm_2025)],
    ["GM 2026 (anticipated)", formatPct(plan.gm_2026)],
    ["Payback 2025 (months)", isFinite(plan.payback_months_2025) ? plan.payback_months_2025.toFixed(1) : "—"],
    ["Payback 2026 target (months)", isFinite(plan.payback_months_2026) ? plan.payback_months_2026.toFixed(1) : "—"],
    ["Ideal customer lifetime (months)", isFinite(plan.lifetime_months) ? plan.lifetime_months.toFixed(1) : "—"],
    ["GM-adjusted LTV per new customer", formatEuro(plan.ltv_per_customer)],
    ["Target CAC per new customer (from 2026 payback)", formatEuro(plan.expected_cac)]
  ];

  // Define which labels are "most important" and get highlighted
  const importantLabels = new Set([
    "Gap ARR (annual)",
    "Gap closure target in MRR",
    "Required new customers (2026)",
    "Expected wins 2026 @ proposed funnel (plan ICP)",
    "GM 2026 (anticipated)",
    "Payback 2026 target (months)",
    "GM-adjusted LTV per new customer",
    "Target CAC per new customer (from 2026 payback)",
    "New-customer MRR 2026 (before NDR)",
    "Additional MRR from NDR (new customers only)"
  ]);

  items.forEach(([label,val])=>{
    const c = document.createElement("div");
    const isImportant = importantLabels.has(label);
    c.className = isImportant ? "kpi-card kpi-important" : "kpi-card";
    c.innerHTML = `<div class="muted">${label}</div><div class="big">${val}</div>`;
    kdiv.appendChild(c);
  });
}

/* ---------- Insight narrative ---------- */
function renderInsights(plan, p){
  const div = document.getElementById("insights_area");

  if(!isFinite(plan.required_new_customers)){
    div.innerHTML = `
      <div class="insight-header">Model status</div>
      <div class="insight-section">
        <span class="pill pill-critical">Check inputs</span>
        <ul class="insight-list">
          <li>Average MRPU computed from the median / max clusters is zero or invalid.</li>
          <li>Update MRPU values and rerun to get a meaningful gap-closure plan.</li>
        </ul>
      </div>
    `;
    return;
  }

  const gapBlock = `
    <div class="insight-section">
      <div class="insight-section-title">1. Gap summary</div>
      <div class="insight-row">
        <span class="pill-label">ARR gap (annual)</span>
        <span class="pill pill-critical">${formatEuro(plan.gap_arr)}</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Gap closure target in MRR</span>
        <span class="pill pill-critical">${formatEuro(plan.gap_mrr)} / month</span>
      </div>
    </div>
  `;

  const customerBlock = `
    <div class="insight-section">
      <div class="insight-section-title">2. Customer & wins math</div>
      <div class="insight-row">
        <span class="pill-label">Required new customers (2026)</span>
        <span class="pill pill-okay">${plan.required_new_customers.toFixed(1)}</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Expected wins 2026 @ present funnel (plan ICP)</span>
        <span class="pill">${plan.expected_wins_2026_present_rates.toFixed(1)} wins (ICP_2026 = ${plan.ICP_2026})</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Expected wins 2025 @ present funnel</span>
        <span class="pill">${plan.expected_wins_2025_present.toFixed(1)} wins (ICP_2025 = ${plan.ICP_2025})</span>
      </div>
    </div>
  `;

  let funnelBlock = "";

  if(plan.enough_already){
    funnelBlock = `
      <div class="insight-section">
        <div class="insight-section-title">3. Funnel verdict for 2026</div>
        <div class="insight-row">
          <span class="pill pill-okay">Already sufficient</span>
        </div>
        <ul class="insight-list">
          <li>With the <strong>present funnel</strong> and planned ICP_2026 = <strong>${plan.ICP_2026}</strong>, you already generate enough expected wins to close the gap.</li>
        </ul>
      </div>
    `;
  } else {
    funnelBlock = `
      <div class="insight-section">
        <div class="insight-section-title">3. Funnel uplift required for 2026</div>
        <div class="insight-row">
          <span class="pill-label">Overall uplift factor (vs 2026 demand)</span>
          <span class="pill pill-critical">${isFinite(plan.uplift_factor) ? plan.uplift_factor.toFixed(2) : "N/A"}×</span>
        </div>
        <div class="insight-row">
          <span class="pill-label">Slider weights (reach / meet / win)</span>
          <span class="pill">${plan.wr.toFixed(2)} / ${plan.wm.toFixed(2)} / ${plan.ww.toFixed(2)}</span>
        </div>
      </div>
    `;
  }

  const unitBlock = `
    <div class="insight-section">
      <div class="insight-section-title">4. Unit economics (NDR, LTV & CAC)</div>
      <div class="insight-row">
        <span class="pill-label">Net Dollar Retention target</span>
        <span class="pill">${(plan.ndr_target*100).toFixed(1)}%</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">New-customer MRR 2026 (before NDR)</span>
        <span class="pill pill-okay">${formatEuro(plan.new_cust_mrr_2026)} / month</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Additional MRR from NDR (new customers only)</span>
        <span class="pill pill-critical">${formatEuro(plan.additional_mrr_ndr_new)} / month</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">GM-adjusted gross profit / new customer / month</span>
        <span class="pill">${formatEuro(plan.gross_profit_mrr_per_cust)}</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">LTV per new customer</span>
        <span class="pill">${formatEuro(plan.ltv_per_customer)} (over ~${plan.lifetime_months.toFixed(0)} months)</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Target CAC per customer (from 2026 payback)</span>
        <span class="pill pill-critical">${formatEuro(plan.expected_cac)} (for ${plan.payback_months_2026.toFixed(0)}-month payback)</span>
      </div>
    </div>
  `;

  div.innerHTML = `
    <div class="insight-header">Narrative view — how much funnel uplift you need</div>
    ${gapBlock}
    ${customerBlock}
    ${funnelBlock}
    ${unitBlock}
  `;
}

/* ---------- Funnel volume chart: 2025 vs 2026 plan ---------- */
function renderFunnelChart(p, plan){
  const ICP_2025 = plan.ICP_2025;
  const ICP_2026 = plan.ICP_2026;

  const reach0 = plan.reach0;
  const meet0  = plan.meet0;
  const win0   = plan.win0;
  const reach1 = plan.proposed_reach;
  const meet1  = plan.proposed_meet;
  const win1   = plan.proposed_win;

  const stages = ["ICP", "Reach", "Meetings", "Wins"];

  const present_vals = [
    ICP_2025,
    ICP_2025 * reach0,
    ICP_2025 * reach0 * meet0,
    ICP_2025 * reach0 * meet0 * win0
  ];

  const proposed_vals = [
    ICP_2026,
    ICP_2026 * reach1,
    ICP_2026 * reach1 * meet1,
    ICP_2026 * reach1 * meet1 * win1
  ];

  const trace1 = {
    type: "funnel",
    name: "Present funnel (2025)",
    y: stages,
    x: present_vals,
    textinfo: "value+percent initial"
  };

  const trace2 = {
    type: "funnel",
    name: "Proposed funnel (2026 plan ICP)",
    y: stages,
    x: proposed_vals,
    textinfo: "value+percent initial"
  };

  const layout = {
    margin: {l: 80, r: 40, t: 20, b: 40},
    legend: {orientation: "h", y: -0.15}
  };

  Plotly.react("funnel_chart", [trace1, trace2], layout);

  // New table under the funnel volumes chart
  renderFunnelPlanTable(plan, present_vals, proposed_vals, stages);
}

/* ---------- New: Detailed table under 2025 vs 2026 funnel chart ---------- */
function renderFunnelPlanTable(plan, present_vals, proposed_vals, stages){
  const container = document.getElementById("funnel_chart_table");
  if(!container){
    return;
  }

  const rows = stages.map((stage, i) => {
    return {
      stage,
      present: present_vals[i],
      proposed: proposed_vals[i]
    };
  });

  let html = `
    <table class="funnel-table">
      <thead>
        <tr>
          <th>Stage</th>
          <th>Present volume (2025)</th>
          <th>Proposed volume (2026 plan)</th>
        </tr>
      </thead>
      <tbody>
  `;

  rows.forEach(r => {
    const presentStr  = isFinite(r.present)  ? Math.round(r.present).toLocaleString()  : "—";
    const proposedStr = isFinite(r.proposed) ? Math.round(r.proposed).toLocaleString() : "—";

    html += `
      <tr>
        <td class="stage">${r.stage}</td>
        <td>${presentStr}</td>
        <td>${proposedStr}</td>
      </tr>
    `;
  });

  html += `
      </tbody>
    </table>
  `;

  container.innerHTML = html;
}

/* ---------- 2026 status funnel: proposed vs status-quo ---------- */
function renderFunnelStatusChart(plan){
  const ICP_proposed = plan.ICP_2026;         // planned 2026 ICP
  const ICP_status   = plan.ICP_current_2026; // current 2026 ICP base

  const reach0 = plan.reach0;
  const meet0  = plan.meet0;
  const win0   = plan.win0;
  const reach1 = plan.proposed_reach;
  const meet1  = plan.proposed_meet;
  const win1   = plan.proposed_win;

  const stages = ["ICP", "Reach", "Meetings", "Wins"];

  // Proposed 2026 path (orange, plan ICP & proposed rates)
  const proposed_vals = [
    ICP_proposed,
    ICP_proposed * reach1,
    ICP_proposed * reach1 * meet1,
    ICP_proposed * reach1 * meet1 * win1
  ];

  // Status-quo path (green, current ICP & present rates from sliders)
  const status_vals = [
    ICP_status,
    ICP_status * reach0,
    ICP_status * reach0 * meet0,
    ICP_status * reach0 * meet0 * win0
  ];

  const traceProposed = {
    type: "funnel",
    name: "Proposed 2026 funnel (plan ICP)",
    y: stages,
    x: proposed_vals,
    textinfo: "value+percent initial",
    marker: { color: "#f97316" }  // orange
  };

  const traceStatus = {
    type: "funnel",
    name: "Status-quo 2026 funnel (current ICP)",
    y: stages,
    x: status_vals,
    textinfo: "value+percent initial",
    marker: { color: "#16a34a" }   // green
  };

  const layout = {
    margin: {l: 80, r: 40, t: 20, b: 40},
    legend: {orientation: "h", y: -0.15}
  };

  Plotly.react("funnel_status_chart", [traceProposed, traceStatus], layout);

  // Render the simplified detailed table under the chart
  renderFunnelStatusTable(plan, proposed_vals, status_vals, stages);
}

/* ---------- Simplified 2026 status table: only first 3 columns ---------- */
function renderFunnelStatusTable(plan, proposed_vals, status_vals, stages){
  const container = document.getElementById("funnel_status_table");
  if(!container){
    return;
  }

  const rows = stages.map((stage, i) => {
    return {
      stage,
      proposed: proposed_vals[i],
      status: status_vals[i]
    };
  });

  let html = `
    <table class="funnel-table">
      <thead>
        <tr>
          <th>Stage</th>
          <th>Proposed volume</th>
          <th>Status-quo volume</th>
        </tr>
      </thead>
      <tbody>
  `;

  rows.forEach(r => {
    const proposedStr = isFinite(r.proposed) ? Math.round(r.proposed).toLocaleString() : "—";
    const statusStr   = isFinite(r.status)   ? Math.round(r.status).toLocaleString()   : "—";

    html += `
      <tr>
        <td class="stage">${r.stage}</td>
        <td>${proposedStr}</td>
        <td>${statusStr}</td>
      </tr>
    `;
  });

  html += `
      </tbody>
    </table>
  `;

  container.innerHTML = html;
}

/* ---------- Payback vs Gross Margin chart (scatter connected + bent extrapolation) ---------- */
function renderPaybackGMChart(plan){
  const gm2025 = plan.gm_2025 * 100;
  const gm2026 = plan.gm_2026 * 100;

  const payback2025 = plan.payback_months_2025;
  const payback2026 = plan.payback_months_2026;

  // Extend GM axis nicely
  let maxGM = Math.max(gm2025, gm2026, 10);
  let xMax = Math.max(40, maxGM * 1.4);  // at least 40%, or 1.4x max

  // 1) Scatter points, connected (markers + lines)
  // Sort by GM so the line visually goes left→right
  const pts = [
    { x: gm2025, y: payback2025, label: "2025" },
    { x: gm2026, y: payback2026, label: "2026" }
  ].filter(p => isFinite(p.x) && isFinite(p.y));

  pts.sort((a,b)=>a.x - b.x);

  const xPts = pts.map(p => p.x);
  const yPts = pts.map(p => p.y);
  const labels = pts.map(p => p.label);

  const tracePoints = {
    x: xPts,
    y: yPts,
    mode: "markers+lines+text",
    name: "Observed (2025 → 2026)",
    text: labels,
    textposition: "top center",
    marker: { size: 11, symbol: "circle", color: "#2563eb" },
    line: { shape: "linear" }
  };

  // 2) Bent extrapolation curve (power-law fit through the two points)
  let lineTrace = null;
  if (pts.length === 2 && pts[0].x > 0 && pts[1].x > 0 && pts[0].y > 0 && pts[1].y > 0 && Math.abs(pts[1].x - pts[0].x) > 1e-6) {
    const g1 = pts[0].x;
    const g2 = pts[1].x;
    const p1 = pts[0].y;
    const p2 = pts[1].y;

    // Fit payback ≈ a * (GM)^b using the two points
    const b = Math.log(p2 / p1) / Math.log(g2 / g1);
    const a = p1 / Math.pow(g1, b);

    const xStart = Math.max(1, Math.min(g1, g2) * 0.5);  // start slightly left of min GM, but >0
    const xEnd   = xMax;
    const n = 80;

    const xs = [];
    const ys = [];
    for (let i = 0; i < n; i++) {
      const x = xStart + (xEnd - xStart) * (i / (n - 1));
      let y = a * Math.pow(x, b);
      if (!isFinite(y)) continue;
      // Clamp y into visible range
      y = Math.max(0, Math.min(50, y));
      xs.push(x);
      ys.push(y);
    }

    if (xs.length > 1) {
      lineTrace = {
        x: xs,
        y: ys,
        mode: "lines",
        name: "Payback frontier (bent extrapolation)",
        line: { dash: "dot" }
      };
    }
  }

  const layout = {
    margin: { l: 70, r: 20, t: 20, b: 60 },
    xaxis: {
      title: "Gross margin (%)",
      range: [0, xMax],
      zeroline: false,
      gridcolor: "#e5e7eb",
      tickformat: ",d"
    },
    yaxis: {
      title: "Payback (months)",
      range: [0, 50],
      tick0: 0,
      dtick: 5,
      gridcolor: "#e5e7eb"
    },
    legend: { orientation: "h", y: -0.2 },
    showlegend: true,
  };

  const data = lineTrace ? [tracePoints, lineTrace] : [tracePoints];

  Plotly.react("payback_gm_chart", data, layout);
}

/* ---------- Tier mix rendering ---------- */
function renderTierMixSummary(tierRes, plan, p){
  const div = document.getElementById("tier_mix_summary");
  if(!tierRes || !tierRes.recommended){
    div.innerHTML = `
      <div class="insight-header">Tier mix Monte Carlo</div>
      <div class="insight-section">
        <span class="pill pill-critical">No recommendation</span>
        <ul class="insight-list">
          <li>Required new customers is zero or invalid, so tier mix cannot be computed.</li>
          <li>Check your MRPU and gap assumptions.</li>
        </ul>
      </div>
    `;
    return;
  }

  const c = tierRes.recommended;
  const N_new = tierRes.N_new;
  const mean_new_mrr = c.mean_avg_mrpu * N_new;
  const tolPct = (tierRes.tolPct * 100).toFixed(1);
  const mcIters = Math.round(safeFloat(p.mc_tier_iterations,5000));

  div.innerHTML = `
    <div class="insight-header">Tier mix Monte Carlo — recommended split for new customers</div>
    <div class="insight-section">
      <div class="insight-section-title">1. Recommended % split (of required new customers)</div>
      <div class="insight-row">
        <span class="pill-label">Tier 1 (high MRPU)</span>
        <span class="pill pill-okay">${(c.f1*100).toFixed(0)}%</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Tier 2 (mid MRPU)</span>
        <span class="pill">${(c.f2*100).toFixed(0)}%</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Tier 3 (tail)</span>
        <span class="pill">${(c.f3*100).toFixed(0)}%</span>
      </div>
    </div>
    <div class="insight-section">
      <div class="insight-section-title">2. Monte Carlo outcome (gap only)</div>
      <div class="insight-row">
        <span class="pill-label">P(close MRR gap ±${tolPct}%)</span>
        <span class="pill">${(c.prob_gap*100).toFixed(1)}%</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Mean avg MRPU (simulated)</span>
        <span class="pill">${Math.round(c.mean_avg_mrpu).toLocaleString()} / month</span>
      </div>
        <div class="insight-row">
        <span class="pill-label">Mean new MRR from these customers</span>
        <span class="pill">${formatEuro(mean_new_mrr)}</span>
      </div>
      <div class="insight-row">
        <span class="pill-label">Iterations per grid cell</span>
        <span class="pill">${mcIters}</span>
      </div>
    </div>
  `;
}

function renderTierMixHeatmap(tierRes){
  const container = document.getElementById("tier_mix_heatmap");
  if(!tierRes || !tierRes.heatmap){
    container.innerHTML = "";
    return;
  }
  const f1 = tierRes.heatmap.f1Vec;
  const f2 = tierRes.heatmap.f2Vec;
  const z = tierRes.heatmap.z;

  const trace = {
    z: z,
    x: f1,
    y: f2,
    type: "heatmap",
    colorscale: "Viridis",
    colorbar: { title: "P(close gap)" }
  };
  const layout = {
    xaxis: { title: "Tier 1 fraction" },
    yaxis: { title: "Tier 2 fraction" },
    margin: { t: 30, l: 60, r: 20, b: 50 }
  };
  Plotly.react("tier_mix_heatmap", [trace], layout);
}

/* ---------- Update orchestration ---------- */
function updateAll(){
  try {
    const p = readInputs();
    const plan = computePlan(p);
    logDebug(
      "Recomputed plan. Gap MRR=" +
      plan.gap_mrr.toFixed(2) +
      ", required_new=" +
      (isFinite(plan.required_new_customers)?plan.required_new_customers.toFixed(2):"NaN")
    );
    renderKPIs(plan, p);
    renderInsights(plan, p);
    renderFunnelChart(p, plan);
    renderFunnelStatusChart(plan);
    renderPaybackGMChart(plan);

    const tierRes = tierMixMonteCarlo(p, plan);
    renderTierMixSummary(tierRes, plan, p);
    renderTierMixHeatmap(tierRes);

  } catch(e){
    logDebug("updateAll error: " + e.message + "\\n" + (e.stack || ""));
  }
}

/* ---------- Wiring ---------- */
window.addEventListener("load", function(){
  // Set numeric defaults
  for(const k in DEFAULTS_JS){
    const el = document.getElementById(k);
    if(el) el.value = DEFAULTS_JS[k];
  }

  // Sync status-quo sliders to defaults
  ["reach_rate_present","meeting_rate_present","win_rate_present"].forEach(k=>{
    const slider = document.getElementById("slider_" + k);
    const lbl = document.getElementById("lbl_" + k);
    if(slider && lbl){
      slider.value = DEFAULTS_JS[k];
      lbl.textContent = (DEFAULTS_JS[k]*100).toFixed(1) + "%";
    }
  });

  document.getElementById("btnUpdate").addEventListener("click", function(){
    this.disabled = true;
    this.textContent = "Updating...";
    setTimeout(()=>{
      updateAll();
      this.disabled = false;
      this.textContent = "Update";
    }, 40);
  });

  document.getElementById("btnReset").addEventListener("click", function(){
    for(const k in DEFAULTS_JS){
      const el = document.getElementById(k);
      if(el) el.value = DEFAULTS_JS[k];
    }
    ["uplift_weight_reach","uplift_weight_meet","uplift_weight_win"].forEach(k=>{
      const slider = document.getElementById(k);
      const lbl = document.getElementById("lbl_"+k);
      if(slider && lbl){
        slider.value = DEFAULTS_JS[k];
        lbl.textContent = slider.value;
      }
    });
    ["reach_rate_present","meeting_rate_present","win_rate_present"].forEach(k=>{
      const slider = document.getElementById("slider_" + k);
      const lbl = document.getElementById("lbl_" + k);
      if(slider && lbl){
        slider.value = DEFAULTS_JS[k];
        lbl.textContent = (DEFAULTS_JS[k]*100).toFixed(1) + "%";
      }
    });
    updateAll();
  });

  // initial run
  setTimeout(updateAll, 80);
});
</script>
</body>
</html>
"""

outfile = "dos_gap_closure_planner.html"
html = html.replace("REPLACE_DEFAULTS_HERE", defaults_json)

with open(outfile, "w", encoding="utf-8") as f:
    f.write(html)

print("Wrote:", os.path.abspath(outfile))
print("Open dos_gap_closure_planner.html in your browser.")
