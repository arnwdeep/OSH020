/* =========================================================
   OSH020 — Interactive Simulation Engine
   ========================================================= */

// ── WORKLOAD GENERATORS ─────────────────────────────────
const Gen = {
  sequential: (n = 60, start = 0) => Array.from({ length: n }, (_, i) => start + i),
  loop: (n = 60, size = 5, start = 0) => Array.from({ length: n }, (_, i) => start + (i % size)),
  locality(n = 80, wsSize = 4, total = 20, prob = 0.85) {
    const hot  = Array.from({ length: wsSize }, (_, i) => i);
    const cold = Array.from({ length: total - wsSize }, (_, i) => i + wsSize);
    return Array.from({ length: n }, () =>
      Math.random() < prob || !cold.length
        ? hot[Math.floor(Math.random() * hot.length)]
        : cold[Math.floor(Math.random() * cold.length)]
    );
  },
  random: (n = 60, unique = 15) => Array.from({ length: n }, () => Math.floor(Math.random() * unique)),
  belady: () => [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5],
  mixed(phaseLen = 25, frames = 4) {
    return [
      ...this.locality(phaseLen, frames, frames * 3, 0.9),
      ...this.sequential(phaseLen, 100),
      ...this.loop(phaseLen, frames + 1, 0),
      ...this.random(phaseLen, frames * 4),
      ...this.locality(phaseLen, frames, frames * 3, 0.92),
    ];
  }
};

// ── PAGE REPLACEMENT POLICIES ────────────────────────────
class FIFO {
  constructor() { this.name = "FIFO"; this.q = []; }
  reset() { this.q = []; }
  access(p, hit) { if (!hit && !this.q.includes(p)) this.q.push(p); }
  evict(res) {
    while (this.q.length) { const v = this.q.shift(); if (res.has(v)) return v; }
    return [...res][0];
  }
}

class LRU {
  constructor() { this.name = "LRU"; this.order = []; }
  reset() { this.order = []; }
  access(p) { this.order = this.order.filter(x => x !== p); this.order.push(p); }
  evict(res) {
    for (const p of this.order) { if (res.has(p)) { this.order = this.order.filter(x => x !== p); return p; } }
    return [...res][0];
  }
}

class Clock {
  constructor() { this.name = "Clock"; this.buf = []; this.bits = new Map(); this.hand = 0; }
  reset() { this.buf = []; this.bits.clear(); this.hand = 0; }
  access(p, hit) { this.bits.set(p, 1); if (!hit && !this.buf.includes(p)) this.buf.push(p); }
  evict(res) {
    this.buf = this.buf.filter(p => res.has(p));
    if (!this.buf.length) return [...res][0];
    if (this.hand >= this.buf.length) this.hand = 0;
    for (let i = 0; i < this.buf.length * 2 + 1; i++) {
      const c = this.buf[this.hand];
      if (this.bits.get(c)) { this.bits.set(c, 0); this.hand = (this.hand + 1) % this.buf.length; }
      else {
        this.buf.splice(this.hand, 1); this.bits.delete(c);
        this.hand = this.buf.length ? this.hand % this.buf.length : 0;
        return c;
      }
    }
    const v = this.buf.shift(); this.hand = 0; return v;
  }
}

class LFU {
  constructor() { this.name = "LFU"; this.freq = new Map(); this.t = new Map(); this.c = 0; }
  reset() { this.freq.clear(); this.t.clear(); this.c = 0; }
  access(p) {
    this.c++; this.freq.set(p, (this.freq.get(p) || 0) + 1);
    if (!this.t.has(p)) this.t.set(p, this.c);
  }
  evict(res) {
    let mf = Infinity, mt = Infinity, v = null;
    for (const p of res) {
      const f = this.freq.get(p) || 0, t = this.t.get(p) || 0;
      if (f < mf || (f === mf && t < mt)) { mf = f; mt = t; v = p; }
    }
    if (v !== null) { this.freq.delete(v); this.t.delete(v); return v; }
    return [...res][0];
  }
}

class ARC {
  constructor(c = 4) { this.name = "ARC"; this.c = c; this.p = 0; this.t1 = []; this.t2 = []; this.b1 = []; this.b2 = []; }
  reset() { this.p = 0; this.t1 = []; this.t2 = []; this.b1 = []; this.b2 = []; }
  access(page) {
    const rm = (arr, p) => arr.splice(arr.indexOf(p), 1);
    if (this.t1.includes(page)) { rm(this.t1, page); this.t2.push(page); }
    else if (this.t2.includes(page)) { rm(this.t2, page); this.t2.push(page); }
    else if (this.b1.includes(page)) {
      this.p = Math.min(this.c, this.p + Math.max(1, this.b2.length / (this.b1.length || 1)));
      rm(this.b1, page); this.t2.push(page);
    } else if (this.b2.includes(page)) {
      this.p = Math.max(0, this.p - Math.max(1, this.b1.length / (this.b2.length || 1)));
      rm(this.b2, page); this.t2.push(page);
    } else { this.t1.push(page); }
  }
  evict(res) {
    const pick = (arr) => { for (let i = 0; i < arr.length; i++) if (res.has(arr[i])) { const v = arr.splice(i, 1)[0]; return v; } return null; };
    if (this.t1.length > 0 && (this.t1.length > this.p || (this.b2.length > 0 && this.t1.length === Math.floor(this.p)))) {
      const v = pick(this.t1); if (v !== null) { this.b1.push(v); return v; }
    }
    const v = pick(this.t2); if (v !== null) { this.b2.push(v); return v; }
    return [...res][0];
  }
}

class Optimal {
  constructor(stream = []) { this.name = "Optimal (MIN)"; this.stream = stream; this.idx = 0; }
  reset() { this.idx = 0; }
  access() { this.idx++; }
  evict(res) {
    let far = -1, v = null; const rem = this.stream.slice(this.idx);
    for (const p of res) {
      const d = rem.indexOf(p); const dist = d === -1 ? Infinity : d;
      if (dist > far) { far = dist; v = p; }
    }
    return v ?? [...res][0];
  }
}

// ── WORKLOAD ANALYZER ────────────────────────────────────
function analyze(window, frameCount) {
  const n = window.length;
  if (n < 4) return { pattern: "Collecting…", rec: "LRU", reason: "Insufficient window data." };

  const unique = new Set(window);
  const uRatio = unique.size / n;

  // Sequential scan check
  let mono = true;
  for (let i = 0; i < n - 1; i++) if (window[i + 1] <= window[i]) { mono = false; break; }
  if ((mono && uRatio >= 0.85) || uRatio >= 0.90)
    return { pattern: "Sequential Scan", rec: "FIFO", reason: "Pages accessed once in order — FIFO avoids recency overhead." };

  // Loop detection
  const maxP = Math.min(frameCount * 2 + 2, Math.floor(n / 2) + 1);
  let bestPeriod = 0, bestRate = 0;
  for (let p = 2; p < maxP; p++) {
    let m = 0;
    for (let i = p; i < n; i++) if (window[i] === window[i - p]) m++;
    const r = m / (n - p);
    if (r > 0.75 && r > bestRate) { bestRate = r; bestPeriod = p; }
  }
  if (bestPeriod > 0) {
    return bestPeriod > frameCount
      ? { pattern: `Cyclic Loop (size ${bestPeriod} > frames)`, rec: "FIFO", reason: `Loop exceeds RAM — FIFO avoids catastrophic LRU thrashing.` }
      : { pattern: `Loop within RAM (size ${bestPeriod})`, rec: "LRU", reason: "Working set fits in frames — LRU preserves the cycle." };
  }

  // Locality check
  const freq = {};
  for (const p of window) freq[p] = (freq[p] || 0) + 1;
  const topSum = Object.values(freq).sort((a, b) => b - a).slice(0, frameCount).reduce((a, b) => a + b, 0);
  if (topSum / n >= 0.65)
    return { pattern: "High Temporal Locality", rec: "LRU", reason: "Hot working set — LRU protects frequently reused pages." };

  if (uRatio > 0.7)
    return { pattern: "Random Access", rec: "Clock", reason: "Uncorrelated references — Clock achieves LRU-quality with lower overhead." };

  return { pattern: "Mixed", rec: "ARC", reason: "General mixed behavior — ARC self-tunes recency vs frequency balance." };
}

// ── STATIC SIMULATION ────────────────────────────────────
function simulate(policy, stream, numFrames) {
  policy.reset();
  const res = new Set(); const slots = Array(numFrames).fill(null);
  let hits = 0;

  for (const page of stream) {
    if (res.has(page)) {
      hits++;
      if (policy.access) policy.access(page, true);
    } else {
      if (res.size < numFrames) {
        const idx = slots.indexOf(null); slots[idx] = page; res.add(page);
      } else {
        const victim = policy.evict(res);
        res.delete(victim);
        const idx = slots.indexOf(victim); slots[idx] = page; res.add(page);
      }
      if (policy.access) policy.access(page, false);
    }
  }
  const total = stream.length;
  return { hits, faults: total - hits, total, hitRate: total ? (hits / total * 100).toFixed(1) : "0.0" };
}

// ── MAIN APP ─────────────────────────────────────────────
class App {
  constructor() {
    this.numFrames  = 4;
    this.wk         = "mixed";
    this.stream     = [];
    this.stepIdx    = 0;
    this.isPlaying  = false;
    this.timer      = null;
    this.speed      = 300;

    // Adaptive state
    this.policies = { FIFO: new FIFO(), LRU: new LRU(), Clock: new Clock(), LFU: new LFU(), ARC: new ARC(4) };
    this.activePolName = "LRU";
    this.activePol     = this.policies.LRU;
    this.res           = new Set();
    this.slots         = Array(this.numFrames).fill(null);
    this.win           = [];
    this.winSize       = 25;
    this.cooldown      = 5;
    this.stepsNoSwitch = 5;
    this.adaptHits     = 0;
    this.adaptFaults   = 0;
    this.switchLog     = [];
    this.fullHistory   = [];   // {page, isHit, evicted, policy, frames[]}
    this.benchData     = [];

    this.$  = id => document.getElementById(id);
    this.init();
  }

  init() {
    // Tab bar
    document.getElementById("tabBar").addEventListener("click", e => {
      const btn = e.target.closest(".tab-btn"); if (!btn) return;
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      this.wk = btn.dataset.workload;
      this.loadWorkload();
    });

    this.$("btnPlay").addEventListener("click",  () => this.togglePlay());
    this.$("btnStep").addEventListener("click",  () => this.step());
    this.$("btnReset").addEventListener("click", () => this.reset());

    this.$("sliderFrames").addEventListener("input", e => {
      this.numFrames = +e.target.value;
      this.$("lblFrames").textContent = this.numFrames;
      this.policies.ARC = new ARC(this.numFrames);
      this.reset();
    });

    this.$("sliderSpeed").addEventListener("input", e => {
      const v = +e.target.value;
      const spd  = [700, 450, 250, 100, 30];
      const lbls = ["Slowest","Slow","Medium","Fast","Fastest"];
      this.speed = spd[v - 1];
      this.$("lblSpeed").textContent = lbls[v - 1];
      if (this.isPlaying) { clearInterval(this.timer); this.timer = setInterval(() => this.step(), this.speed); }
    });

    this.$("inspectorSlider").addEventListener("input", e => {
      const i = +e.target.value;
      this.$("inspectorStepLabel").textContent = i;
      this.renderInspector(i);
    });

    this.loadWorkload();
  }

  loadWorkload() {
    if      (this.wk === "mixed")       this.stream = Gen.mixed(25, this.numFrames);
    else if (this.wk === "scan")        this.stream = Gen.sequential(60);
    else if (this.wk === "loop")        this.stream = Gen.loop(60, this.numFrames + 1);
    else if (this.wk === "locality")    this.stream = Gen.locality(80, this.numFrames, this.numFrames * 3);
    else if (this.wk === "random")      this.stream = Gen.random(60, this.numFrames * 4);
    else if (this.wk === "belady-trace")this.stream = Gen.belady();
    this.reset();
  }

  reset() {
    this.pause();
    this.stepIdx = 0; this.adaptHits = 0; this.adaptFaults = 0;
    this.switchLog = []; this.fullHistory = []; this.win = [];
    this.res.clear();
    this.slots = Array(this.numFrames).fill(null);
    this.stepsNoSwitch = this.cooldown;
    this.activePolName = "LRU"; this.activePol = this.policies.LRU;
    for (const p of Object.values(this.policies)) p.reset();

    this.renderFrameSlots();
    this.updateScorecard();
    this.updateHeroStats();
    this.$("statusStep").textContent = `0 / ${this.stream.length}`;
    this.$("statusPage").textContent = "—";
    this.$("statusBadge").textContent = "—";
    this.$("statusBadge").className = "badge-miss";
    this.$("statusPolicy").textContent = "LRU";
    this.$("statusPattern").textContent = "—";
    this.$("inspectorSlider").max = Math.max(0, this.stream.length - 1);
    this.$("inspectorSlider").value = 0;
    this.$("inspectorStepLabel").textContent = "0";
    this.renderInspector(0);
    this.$("auditLog").innerHTML = `
      <div class="audit-entry">
        <span class="audit-step">—</span>
        <div><div class="audit-change">Ready</div>
        <div class="audit-reason">Press Run or Step to observe dynamic policy adaptation.</div></div>
      </div>`;

    this.computeBenchmarks();
  }

  togglePlay() {
    if (this.isPlaying) this.pause();
    else {
      if (this.stepIdx >= this.stream.length) this.reset();
      this.isPlaying = true;
      this.$("btnPlay").textContent = "⏸ Pause";
      this.timer = setInterval(() => {
        if (this.stepIdx >= this.stream.length) this.pause();
        else this.step();
      }, this.speed);
    }
  }

  pause() {
    this.isPlaying = false;
    this.$("btnPlay").textContent = "▶ Run";
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
  }

  step() {
    if (this.stepIdx >= this.stream.length) { this.pause(); return; }

    const page = this.stream[this.stepIdx];
    this.win.push(page); if (this.win.length > this.winSize) this.win.shift();
    this.stepsNoSwitch++;

    const { pattern, rec, reason } = analyze(this.win, this.numFrames);

    // Policy switching
    if (rec !== this.activePolName && this.stepsNoSwitch >= this.cooldown && this.win.length >= 6) {
      const from = this.activePolName;
      this.activePolName = rec;
      this.activePol = this.policies[rec] || this.policies.LRU;
      this.stepsNoSwitch = 0;
      const sw = { step: this.stepIdx, from, to: rec, pattern, reason };
      this.switchLog.push(sw);
      this.prependAuditEntry(sw);
    }

    // Memory access
    const isHit = this.res.has(page);
    let evicted = null;

    if (isHit) {
      this.adaptHits++;
      if (this.activePol.access) this.activePol.access(page, true);
    } else {
      this.adaptFaults++;
      if (this.res.size < this.numFrames) {
        const idx = this.slots.indexOf(null); this.slots[idx] = page; this.res.add(page);
      } else {
        evicted = this.activePol.evict(this.res);
        this.res.delete(evicted);
        const idx = this.slots.indexOf(evicted); this.slots[idx] = page; this.res.add(page);
      }
      if (this.activePol.access) this.activePol.access(page, false);
    }

    this.fullHistory.push({ page, isHit, evicted, policy: this.activePolName, frames: [...this.slots] });

    this.stepIdx++;
    this.renderFrameSlots(page, isHit);
    this.updateScorecard();
    this.updateHeroStats();
    this.updateLiveStatus(page, isHit, pattern);
    this.updateBenchAdaptiveRow();
  }

  renderFrameSlots(highlightPage = null, isHit = false) {
    const grid = this.$("frameSlotsGrid");
    const cols = this.numFrames <= 4 ? 2 : 3;
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    grid.innerHTML = this.slots.map((p, i) => {
      let cls = "frame-cell";
      if (p !== null) cls += " occupied";
      if (p === highlightPage && highlightPage !== null) cls += isHit ? " is-hit" : " is-fault";
      return `<div class="${cls}"><div class="frame-cell-idx">F${i}</div><div class="frame-cell-val">${p !== null ? p : "—"}</div></div>`;
    }).join("");
  }

  updateScorecard() {
    const total = this.adaptHits + this.adaptFaults;
    const rate  = total ? (this.adaptHits / total * 100).toFixed(1) : "0.0";
    this.$("kpiHitRate").textContent = `${rate}%`;
    this.$("kpiHits").textContent    = this.adaptHits;
    this.$("kpiHitsOf").textContent  = `of ${total} accesses`;
    this.$("kpiFaults").textContent  = this.adaptFaults;
    this.$("kpiSwitches").textContent = this.switchLog.length;
  }

  updateHeroStats() {
    const total = this.adaptHits + this.adaptFaults;
    const rate  = total ? (this.adaptHits / total * 100).toFixed(1) : "0.0";
    this.$("heroTotalAccesses").textContent = this.stream.length;
    this.$("heroHitRate").textContent = `${rate}%`;
    this.$("heroSwitches").textContent = this.switchLog.length;
  }

  updateLiveStatus(page, isHit, pattern) {
    this.$("statusStep").textContent  = `${this.stepIdx} / ${this.stream.length}`;
    this.$("statusPage").textContent  = `Page ${page}`;
    const badge = this.$("statusBadge");
    badge.textContent = isHit ? "HIT" : "FAULT";
    badge.className   = isHit ? "badge-hit" : "badge-miss";
    this.$("statusPolicy").textContent  = this.activePolName;
    this.$("statusPattern").textContent = pattern;
  }

  prependAuditEntry(sw) {
    const log = this.$("auditLog");
    if (log.querySelector(".audit-placeholder, .audit-entry:only-child")) log.innerHTML = "";
    const el = document.createElement("div");
    el.className = "audit-entry";
    el.innerHTML = `
      <span class="audit-step">Step ${sw.step}</span>
      <div>
        <div class="audit-change">${sw.from} → ${sw.to}</div>
        <div class="audit-reason">${sw.pattern} — ${sw.reason}</div>
      </div>`;
    log.prepend(el);
  }

  renderInspector(i) {
    const ev = this.fullHistory[i];
    if (!ev) {
      this.$("inspPage").textContent    = "—";
      this.$("inspResult").textContent  = "—";
      this.$("inspPolicy").textContent  = "—";
      this.$("inspEvicted").textContent = "—";
      this.$("inspectorFrames").innerHTML = "";
      return;
    }
    this.$("inspPage").textContent    = `Page ${ev.page}`;
    this.$("inspResult").textContent  = ev.isHit ? "✅ HIT" : "❌ FAULT";
    this.$("inspPolicy").textContent  = ev.policy;
    this.$("inspEvicted").textContent = ev.evicted !== null ? `Page ${ev.evicted}` : "None";

    this.$("inspectorFrames").innerHTML = ev.frames.map((p, idx) => {
      let cls = "inspector-frame";
      if (p !== null) cls += " occupied";
      if (p === ev.page) cls += ev.isHit ? " is-hit" : " is-fault";
      return `<div class="${cls}"><div class="inspector-frame-idx">Frame ${idx}</div><div class="inspector-frame-val">${p !== null ? p : "—"}</div></div>`;
    }).join("");
  }

  computeBenchmarks() {
    const s = this.stream;
    const f = this.numFrames;
    const opt = new Optimal(s);
    this.benchData = [
      { name: "Optimal (MIN)", type: "theory",   ...simulate(opt, s, f) },
      { name: "Adaptive Engine", type: "adapt",  hits: this.adaptHits, faults: this.adaptFaults, total: this.adaptHits + this.adaptFaults, hitRate: "—" },
      { name: "ARC",   type: "static", ...simulate(new ARC(f), s, f) },
      { name: "LFU",   type: "static", ...simulate(new LFU(), s, f) },
      { name: "LRU",   type: "static", ...simulate(new LRU(), s, f) },
      { name: "Clock", type: "static", ...simulate(new Clock(), s, f) },
      { name: "FIFO",  type: "static", ...simulate(new FIFO(), s, f) },
    ];
    this.renderLeaderboard();
    this.renderTimeline();
    this.renderBeladyCard();
  }

  updateBenchAdaptiveRow() {
    const total = this.adaptHits + this.adaptFaults;
    const rate  = total ? (this.adaptHits / total * 100).toFixed(1) : "0.0";
    const r = this.benchData.find(x => x.name === "Adaptive Engine");
    if (r) { r.hits = this.adaptHits; r.faults = this.adaptFaults; r.total = total; r.hitRate = rate; }
    this.renderLeaderboard();
    this.renderTimeline();
  }

  renderLeaderboard() {
    const sorted = [...this.benchData].sort((a, b) => parseFloat(b.hitRate) - parseFloat(a.hitRate));
    const typeLabel = { adapt: "Adaptive", static: "Static", theory: "Theoretical" };
    const typeBadge = { adapt: "type-adaptive", static: "type-static", theory: "type-theory" };
    const barClass  = { adapt: "p-adaptive", theory: "p-theory", static: "" };

    this.$("leaderboardBody").innerHTML = sorted.map(r => `
      <tr class="${r.type === "adapt" ? "row-adaptive" : ""}">
        <td><strong>${r.name}</strong></td>
        <td><span class="type-badge ${typeBadge[r.type]}">${typeLabel[r.type]}</span></td>
        <td>${r.hits}</td>
        <td>${r.faults}</td>
        <td><strong>${r.hitRate}%</strong></td>
        <td>
          <div class="progress-bar">
            <div class="progress-fill ${barClass[r.type]}" style="width:${parseFloat(r.hitRate) || 0}%"></div>
          </div>
        </td>
      </tr>
    `).join("");
  }

  renderTimeline() {
    const sorted = [...this.benchData].sort((a, b) => parseFloat(b.hitRate) - parseFloat(a.hitRate));
    this.$("timelineGrid").innerHTML = sorted.map(r => {
      const pct = parseFloat(r.hitRate) || 0;
      const color = r.type === "adapt" ? "linear-gradient(90deg, #3d5eff, #9aaeff)"
                  : r.type === "theory" ? "#a855f7" : "rgba(255,255,255,0.35)";
      return `
        <div class="timeline-policy-row">
          <span class="timeline-pol-name">${r.name}</span>
          <div class="timeline-bar-outer">
            <div class="timeline-bar-inner" style="width:${pct}%; background:${color};"></div>
          </div>
          <span class="timeline-pct">${r.hitRate}%</span>
        </div>`;
    }).join("");
  }

  renderBeladyCard() {
    const s  = Gen.belady();
    const r4 = simulate(new ARC(4), s, 4);
    const faults4 = simulate(new Optimal(s), s, 4); // Use Adaptive flavor
    const adap = simulate(new LRU(), s, 4); // LRU is stack-safe
    const beladyAdap = this.$("beladyAdapVal");
    if (beladyAdap) beladyAdap.textContent = `${adap.faults} Faults — ${adap.hitRate}% Hits`;
  }
}

document.addEventListener("DOMContentLoaded", () => { window.app = new App(); });
