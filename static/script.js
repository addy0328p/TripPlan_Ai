/* ═══════════════════════════════════════════════════════════
   TripMate AI  —  script.js
   Covers:
   • Floating particles
   • Nav scroll + active link spy
   • Scroll-reveal (IntersectionObserver)
   • Animated count-up
   • Rotating placeholder
   • Textarea auto-resize
   • Loading steps animation
   • sendMessage / showResult / showError
   • copyResult
   • downloadPDF  (fixed – white background, header shown)
═══════════════════════════════════════════════════════════ */

"use strict";

/* ─────────────────────────────────────────
   STATE
───────────────────────────────────────── */
let currentThreadId      = localStorage.getItem("travel_thread_id") || null;
let latestAnswerMarkdown = "";
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
   LOADING STEPS
───────────────────────────────────────── */
const STEP_IDS    = ["ls1", "ls2", "ls3", "ls4"];
const STEP_DELAYS = [0, 2200, 4800, 8000]; // ms after loading starts

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
   SHOW RESULT
───────────────────────────────────────── */
function showResult(answer, threadId) {
    latestAnswerMarkdown = answer;

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
            body:    JSON.stringify({ message, thread_id: currentThreadId }),
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || "Something went wrong. Please try again.");
        }

        currentThreadId = data.thread_id;
        localStorage.setItem("travel_thread_id", currentThreadId);

        showResult(data.answer, data.thread_id);

    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
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
