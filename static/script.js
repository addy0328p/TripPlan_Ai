/* ═══════════════════════════════════════════════════════════
   TripMate AI  —  script.js  v2
   Covers:
   • Floating particles
   • Nav scroll + active link spy
   • Scroll-reveal (IntersectionObserver)
   • Animated count-up
   • Rotating placeholder
   • Textarea auto-resize
   • Loading steps animation (7 steps)
   • sendMessage / showResult / showError
   • HITL: approveItinerary / requestChanges / showApproval
   • Guardrail blocked state
   • Agent Activity Panel toggle
   • copyResult
   • downloadPDF  (fixed – white background, header shown)
═══════════════════════════════════════════════════════════ */

"use strict";

/* ─────────────────────────────────────────
   STATE
───────────────────────────────────────── */
let currentThreadId      = localStorage.getItem("travel_thread_id") || null;
let latestAnswerMarkdown = "";
let latestResponseData   = null;   // full API response for agent panel
let loadingTimer         = null;

/* ─────────────────────────────────────────
   PARTICLES
───────────────────────────────────────── */
function spawnParticles() {
    const container = document.getElementById("particles");
    if (!container) return;

    const count = window.innerWidth < 600 ? 12 : 22;

    for (let i = 0; i < count; i++) {
        const p = document.createElement("div");
        p.className = "particle";

        const size = Math.random() * 4 + 2;
        const left = Math.random() * 100;
        const delay = Math.random() * 12;
        const dur   = Math.random() * 14 + 10;

        p.style.cssText = `
            width:${size}px; height:${size}px;
            left:${left}%;
            bottom:-${size}px;
            animation-duration:${dur}s;
            animation-delay:${delay}s;
            opacity:${Math.random() * .4 + .1};
        `;
        container.appendChild(p);
    }
}

/* ─────────────────────────────────────────
   NAV — scroll class + active link spy
───────────────────────────────────────── */
function initNav() {
    const nav   = document.getElementById("nav");
    const links = document.querySelectorAll("[data-nav]");

    // scroll class
    const onScroll = () => {
        nav.classList.toggle("scrolled", window.scrollY > 40);
    };
    window.addEventListener("scroll", onScroll, { passive: true });

    // active link
    const sections = Array.from(links)
        .map(a => document.querySelector(a.getAttribute("href")))
        .filter(Boolean);

    const spy = new IntersectionObserver(
        entries => {
            entries.forEach(e => {
                if (!e.isIntersecting) return;
                links.forEach(a => {
                    a.classList.toggle(
                        "active",
                        a.getAttribute("href") === "#" + e.target.id
                    );
                });
            });
        },
        { rootMargin: "-40% 0px -55% 0px" }
    );

    sections.forEach(s => spy.observe(s));
}

/* ─────────────────────────────────────────
   SCROLL-REVEAL
───────────────────────────────────────── */
function initReveal() {
    const els = document.querySelectorAll("[data-reveal]");

    const observer = new IntersectionObserver(
        entries => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    e.target.classList.add("visible");
                    observer.unobserve(e.target);
                }
            });
        },
        { threshold: 0.12 }
    );

    els.forEach(el => observer.observe(el));
}

/* ─────────────────────────────────────────
   COUNT-UP ANIMATION
───────────────────────────────────────── */
function animateCount(el) {
    const target  = parseInt(el.dataset.target, 10);
    const dur     = 1600;
    const step    = 16;
    const total   = Math.ceil(dur / step);
    let   current = 0;

    const timer = setInterval(() => {
        current++;
        const val = Math.round(target * easeOut(current / total));
        el.textContent = val;
        if (current >= total) {
            el.textContent = target;
            clearInterval(timer);
        }
    }, step);
}

function easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
}

function initCounts() {
    const counts = document.querySelectorAll(".count[data-target]");
    if (!counts.length) return;

    const observer = new IntersectionObserver(
        entries => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    animateCount(e.target);
                    observer.unobserve(e.target);
                }
            });
        },
        { threshold: 0.5 }
    );
    counts.forEach(c => observer.observe(c));
}

/* ─────────────────────────────────────────
   ROTATING PLACEHOLDER
───────────────────────────────────────── */
const PLACEHOLDERS = [
    "Plan a 7-day Kerala backwaters trip from Mumbai with houseboat, flights & ayurveda under ₹60,000...",
    "Plan a 5-day Rajasthan trip from Delhi covering Jaipur, Jodhpur & Udaipur with palace hotels under ₹45,000...",
    "Plan a 4-day Goa beach trip from Hyderabad with flights, beach resort & water sports under ₹30,000...",
    "Plan a 6-day Himachal trip from Delhi: Shimla, Manali & Kullu under ₹35,000...",
    "Plan a complete Leh-Ladakh 8-day bike trip from Delhi with accommodation & permits...",
    "Plan a 5-day Andaman Islands trip from Chennai with flights, beach hotel & snorkelling under ₹40,000...",
    "Plan a 7-day Japan trip from Delhi with flights, ryokan stay & sightseeing under ₹1,50,000...",
    "Plan a 3-day Varanasi spiritual trip from Kolkata with ghats tour & temples...",
];

let phIdx = 0;

function initPlaceholderRotation() {
    const ta = document.getElementById("userInput");
    if (!ta) return;
    setInterval(() => {
        if (document.activeElement === ta) return;
        phIdx = (phIdx + 1) % PLACEHOLDERS.length;
        ta.placeholder = PLACEHOLDERS[phIdx];
    }, 4000);
}

/* ─────────────────────────────────────────
   TEXTAREA AUTO-RESIZE
───────────────────────────────────────── */
function initTextareaResize() {
    const ta = document.getElementById("userInput");
    if (!ta) return;
    ta.addEventListener("input", () => {
        ta.style.height = "auto";
        ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
    });
}

/* ─────────────────────────────────────────
   LOADING STEPS (7 steps)
───────────────────────────────────────── */
const STEP_IDS    = ["ls1", "ls2", "ls3", "ls4", "ls5", "ls6", "ls7"];
const STEP_DELAYS = [0, 1800, 3600, 5400, 7600, 10000, 13000]; // ms after loading starts

function startLoadingSteps() {
    // reset
    STEP_IDS.forEach((id, i) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove("active", "done");
        if (i === 0) el.classList.add("active");
    });

    // schedule transitions
    loadingTimer = STEP_IDS.map((id, i) => {
        if (i === 0) return null;
        return setTimeout(() => {
            const prev = document.getElementById(STEP_IDS[i - 1]);
            const curr = document.getElementById(id);
            if (prev) { prev.classList.remove("active"); prev.classList.add("done"); }
            if (curr)   curr.classList.add("active");
        }, STEP_DELAYS[i]);
    });
}

function stopLoadingSteps() {
    if (loadingTimer) {
        loadingTimer.forEach(t => t && clearTimeout(t));
        loadingTimer = null;
    }
    STEP_IDS.forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.classList.remove("active"); el.classList.add("done"); }
    });
}

/* ─────────────────────────────────────────
   UI HELPERS
───────────────────────────────────────── */
function setLoading(on) {
    const btn    = document.getElementById("sendBtn");
    const text   = document.getElementById("btnText");
    const loader = document.getElementById("btnLoader");
    const card   = document.getElementById("loadingState");

    btn.disabled = on;
    text.classList.toggle("hidden", on);
    loader.classList.toggle("hidden", !on);
    card.classList.toggle("hidden", !on);

    if (on) {
        startLoadingSteps();
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else {
        stopLoadingSteps();
    }
}

function showError(msg) {
    const box = document.getElementById("errorBox");
    box.innerHTML = `<strong>⚠️ Error:</strong> ${msg}`;
    box.classList.remove("hidden");
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideError() {
    const box = document.getElementById("errorBox");
    box.classList.add("hidden");
    box.textContent = "";
}

function hideAllSections() {
    document.getElementById("resultSection").classList.add("hidden");
    document.getElementById("approvalSection").classList.add("hidden");
    document.getElementById("guardrailBlocked").classList.add("hidden");
}

function resetToPlanner() {
    hideAllSections();
    hideError();
    document.getElementById("userInput").value = "";
    document.getElementById("planner").scrollIntoView({ behavior: "smooth" });
}

/* ─────────────────────────────────────────
   SET PROMPT (quick chips)
───────────────────────────────────────── */
function setPrompt(text) {
    const ta = document.getElementById("userInput");
    ta.value = text;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
    ta.focus();
    ta.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ─────────────────────────────────────────
   AGENT ACTIVITY PANEL HELPERS
───────────────────────────────────────── */
const AGENT_DISPLAY = {
    flight_agent:    { emoji: "✈️", label: "Flight Agent" },
    hotel_agent:     { emoji: "🏨", label: "Hotel Agent" },
    weather_agent:   { emoji: "🌤️", label: "Weather Agent" },
    budget_agent:    { emoji: "💰", label: "Budget Agent" },
    itinerary_agent: { emoji: "📋", label: "Itinerary Agent" },
};

function renderAgentTags(container, selectedAgents) {
    container.innerHTML = "";
    const allAgents = Object.keys(AGENT_DISPLAY);

    allAgents.forEach(agent => {
        const info = AGENT_DISPLAY[agent];
        const isActive = selectedAgents.includes(agent);
        const tag = document.createElement("span");
        tag.className = `agent-tag ${isActive ? "agent-active" : "agent-skipped"}`;
        tag.textContent = `${info.emoji} ${info.label}`;
        container.appendChild(tag);
    });
}

function populateAgentPanel(data, prefix) {
    // Guardrail badge
    const guardrailBadge = document.getElementById(`${prefix}GuardrailBadge`);
    if (guardrailBadge) {
        if (data.guardrail_allowed) {
            guardrailBadge.textContent = "✅ Passed";
            guardrailBadge.className = "activity-badge badge-passed";
        } else {
            guardrailBadge.textContent = "❌ Blocked";
            guardrailBadge.className = "activity-badge badge-blocked";
        }
    }

    // Supervisor reasoning
    const supervisorText = document.getElementById(`${prefix}SupervisorText`) ||
                           document.getElementById(`${prefix}ReasoningText`);
    if (supervisorText) {
        supervisorText.textContent = data.supervisor_reasoning || "Dynamic routing applied";
    }

    // Agent tags
    const tagContainer = document.getElementById(`${prefix}AgentTags`);
    if (tagContainer) {
        renderAgentTags(tagContainer, data.selected_agents || []);
    }

    // LLM calls
    const llmEl = document.getElementById(`${prefix}LlmCalls`) ||
                  document.getElementById(`${prefix}CallsCount`);
    if (llmEl) {
        llmEl.textContent = data.llm_calls || 0;
    }
}

function toggleAgentPanel() {
    const body = document.getElementById("agentActivityBody");
    const toggle = document.getElementById("agentActivityToggle");
    body.classList.toggle("hidden");
    toggle.classList.toggle("open");
}

function toggleResultAgentPanel() {
    const body = document.getElementById("resultAgentBody");
    const toggle = document.getElementById("resultAgentToggle");
    body.classList.toggle("hidden");
    toggle.classList.toggle("open");
}

/* ─────────────────────────────────────────
   SHOW GUARDRAIL BLOCKED
───────────────────────────────────────── */
function showGuardrailBlocked(reason) {
    hideAllSections();
    const card = document.getElementById("guardrailBlocked");
    const reasonEl = document.getElementById("guardrailBlockedReason");
    reasonEl.textContent = reason || "This request was blocked by the travel input guardrail.";
    card.classList.remove("hidden");
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/* ─────────────────────────────────────────
   SHOW APPROVAL (HITL)
───────────────────────────────────────── */
function showApproval(data) {
    hideAllSections();
    latestResponseData = data;

    const section  = document.getElementById("approvalSection");
    const threadEl = document.getElementById("approvalThreadInfo");
    const draftBox = document.getElementById("approvalDraftBox");

    threadEl.textContent = `Thread: ${data.thread_id}`;

    // Render draft itinerary
    const draft = data.itinerary || data.answer || "";
    if (typeof marked !== "undefined") {
        marked.setOptions({ breaks: true, gfm: true });
        draftBox.innerHTML = marked.parse(draft);
    } else {
        draftBox.innerText = draft;
    }

    // Populate agent activity panel
    populateAgentPanel(data, "guardrail");
    const supervisorReasoningText = document.getElementById("supervisorReasoningText");
    if (supervisorReasoningText) {
        supervisorReasoningText.textContent = data.supervisor_reasoning || "Dynamic routing applied";
    }
    const selectedAgentTags = document.getElementById("selectedAgentTags");
    if (selectedAgentTags) {
        renderAgentTags(selectedAgentTags, data.selected_agents || []);
    }
    const llmCallsCount = document.getElementById("llmCallsCount");
    if (llmCallsCount) {
        llmCallsCount.textContent = data.llm_calls || 0;
    }

    // Clear previous feedback
    const feedbackInput = document.getElementById("feedbackInput");
    if (feedbackInput) feedbackInput.value = "";

    // Show section
    section.classList.remove("hidden");
    setTimeout(() => {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
}

/* ─────────────────────────────────────────
   SHOW RESULT (final)
───────────────────────────────────────── */
function showResult(answer, threadId, data) {
    hideAllSections();
    latestAnswerMarkdown = answer;
    latestResponseData = data || {};

    const section  = document.getElementById("resultSection");
    const card     = section.querySelector(".result-card");
    const box      = document.getElementById("resultBox");
    const threadEl = document.getElementById("threadInfo");

    // render markdown
    if (typeof marked !== "undefined") {
        marked.setOptions({ breaks: true, gfm: true });
        box.innerHTML = marked.parse(answer);
    } else {
        box.innerText = answer;
    }

    threadEl.textContent = `Thread: ${threadId}`;

    // Populate result agent activity panel
    if (data) {
        populateAgentPanel(data, "result");
        const approvalBadge = document.getElementById("resultApprovalBadge");
        if (approvalBadge) {
            if (data.approved === true) {
                approvalBadge.textContent = "✅ Approved";
                approvalBadge.className = "activity-badge badge-passed";
            } else if (data.approved === false) {
                approvalBadge.textContent = "✏️ Revised";
                approvalBadge.className = "activity-badge badge-revised";
            } else {
                approvalBadge.textContent = "—";
                approvalBadge.className = "activity-badge";
            }
        }
        const resultLlmCalls = document.getElementById("resultLlmCalls");
        if (resultLlmCalls) resultLlmCalls.textContent = data.llm_calls || 0;
    }

    // show section
    section.classList.remove("hidden");

    // remove then re-add glow so it fires even on repeat queries
    card.classList.remove("glow");
    void card.offsetWidth; // reflow
    card.classList.add("glow");

    // scroll after a brief paint delay
    setTimeout(() => {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
}

/* ─────────────────────────────────────────
   SEND MESSAGE
───────────────────────────────────────── */
async function sendMessage() {
    hideError();
    hideAllSections();

    const input   = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please describe your trip first — destination, duration, budget, starting city.");
        return;
    }

    setLoading(true);

    try {
        const res  = await fetch("/api/travel", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ message, thread_id: null }),
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || "Something went wrong. Please try again.");
        }

        currentThreadId = data.thread_id;
        localStorage.setItem("travel_thread_id", currentThreadId);

        // Check if guardrail blocked the request
        if (data.guardrail_allowed === false) {
            showGuardrailBlocked(data.guardrail_reason || data.answer);
            return;
        }

        // Check if HITL approval is needed
        if (data.requires_approval) {
            showApproval(data);
            return;
        }

        // Otherwise show final result directly
        showResult(data.answer, data.thread_id, data);

    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

/* ─────────────────────────────────────────
   HITL: APPROVE ITINERARY
───────────────────────────────────────── */
async function approveItinerary() {
    if (!currentThreadId) {
        showError("No active thread. Please generate a plan first.");
        return;
    }

    const approveBtn = document.getElementById("approveBtn");
    const reviseBtn  = document.getElementById("reviseBtn");
    const btnText    = document.getElementById("approveBtnText");
    const btnLoader  = document.getElementById("approveBtnLoader");

    approveBtn.disabled = true;
    reviseBtn.disabled  = true;
    btnText.classList.add("hidden");
    btnLoader.classList.remove("hidden");

    try {
        const res = await fetch("/api/travel/approve", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                thread_id: currentThreadId,
                approved:  true,
                feedback:  "",
            }),
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || "Approval failed. Please try again.");
        }

        showResult(data.answer, data.thread_id, data);

    } catch (err) {
        showError(err.message);
    } finally {
        approveBtn.disabled = false;
        reviseBtn.disabled  = false;
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
    }
}

/* ─────────────────────────────────────────
   HITL: REQUEST CHANGES
───────────────────────────────────────── */
async function requestChanges() {
    if (!currentThreadId) {
        showError("No active thread. Please generate a plan first.");
        return;
    }

    const feedback   = (document.getElementById("feedbackInput").value || "").trim();
    const approveBtn = document.getElementById("approveBtn");
    const reviseBtn  = document.getElementById("reviseBtn");
    const btnText    = document.getElementById("reviseBtnText");
    const btnLoader  = document.getElementById("reviseBtnLoader");

    approveBtn.disabled = true;
    reviseBtn.disabled  = true;
    btnText.classList.add("hidden");
    btnLoader.classList.remove("hidden");

    try {
        const res = await fetch("/api/travel/approve", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                thread_id: currentThreadId,
                approved:  false,
                feedback:  feedback || "Please improve and revise the itinerary.",
            }),
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || "Revision failed. Please try again.");
        }

        showResult(data.answer, data.thread_id, data);

    } catch (err) {
        showError(err.message);
    } finally {
        approveBtn.disabled = false;
        reviseBtn.disabled  = false;
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
    }
}

/* ─────────────────────────────────────────
   COPY
───────────────────────────────────────── */
function copyResult() {
    const box  = document.getElementById("resultBox");
    const text = box.innerText;
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById("copyBtn");
        const orig = btn.innerHTML;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
        btn.style.color        = "#86efac";
        btn.style.borderColor  = "rgba(34,197,94,.4)";
        setTimeout(() => {
            btn.innerHTML     = orig;
            btn.style.color   = "";
            btn.style.borderColor = "";
        }, 2200);
    }).catch(() => showError("Could not copy to clipboard."));
}

/* ─────────────────────────────────────────
   DOWNLOAD PDF  (fixed)
   Strategy:
   1. Clone #pdfContent so we never mutate the live DOM
   2. Force white background + show the hidden header in the clone
   3. Temporarily append clone off-screen, run html2pdf, then remove
───────────────────────────────────────── */
function downloadPDF() {
    if (!latestAnswerMarkdown) {
        showError("Generate a travel plan first, then download.");
        return;
    }

    const btn  = document.getElementById("pdfBtn");
    const orig = btn.innerHTML;
    btn.innerHTML = `<span class="spin"></span> Preparing...`;
    btn.disabled  = true;

    // ── clone the white content box ──
    const source = document.getElementById("pdfContent");
    const clone  = source.cloneNode(true);

    // force styles on clone
    clone.style.cssText = `
        background: #ffffff !important;
        color: #111827 !important;
        padding: 40px !important;
        font-family: Inter, Arial, sans-serif !important;
        font-size: 14px !important;
        line-height: 1.7 !important;
        width: 720px;
    `;

    // show the PDF header block
    const headerBlock = clone.querySelector("#pdfHeaderBlock");
    if (headerBlock) headerBlock.style.display = "block";

    // fix heading + paragraph colours for PDF (clone inherits dark-mode vars otherwise)
    clone.querySelectorAll("h1,h2,h3,h4,h5,h6").forEach(h => {
        h.style.color = "#0f172a";
    });
    clone.querySelectorAll("p,li,td,th").forEach(el => {
        el.style.color = "#1f2937";
    });
    clone.querySelectorAll("th").forEach(el => {
        el.style.background = "#eff6ff";
        el.style.color = "#1e3a8a";
    });

    // attach off-screen so html2pdf can measure it
    clone.style.position = "absolute";
    clone.style.left     = "-9999px";
    clone.style.top      = "0";
    document.body.appendChild(clone);

    const options = {
        margin:      [12, 14, 12, 14],   // mm
        filename:    "TripMate-AI-Travel-Plan.pdf",
        image:       { type: "jpeg", quality: 0.97 },
        html2canvas: {
            scale:           2,
            useCORS:         true,
            backgroundColor: "#ffffff",
            logging:         false,
        },
        jsPDF: {
            unit:        "mm",
            format:      "a4",
            orientation: "portrait",
            compress:    true,
        },
        pagebreak: { mode: ["css", "legacy"] },
    };

    html2pdf()
        .set(options)
        .from(clone)
        .save()
        .then(() => {
            document.body.removeChild(clone);
            btn.innerHTML = orig;
            btn.disabled  = false;
        })
        .catch(err => {
            document.body.removeChild(clone);
            btn.innerHTML = orig;
            btn.disabled  = false;
            showError("Could not generate PDF. Try again.");
            console.error("PDF error:", err);
        });
}

/* ─────────────────────────────────────────
   KEYBOARD SHORTCUT  Ctrl+Enter
───────────────────────────────────────── */
document.addEventListener("keydown", e => {
    if (e.ctrlKey && e.key === "Enter") sendMessage();
});

/* ─────────────────────────────────────────
   BOOT
───────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
    spawnParticles();
    initNav();
    initReveal();
    initCounts();
    initPlaceholderRotation();
    initTextareaResize();
});
