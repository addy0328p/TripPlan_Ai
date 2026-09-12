let currentThreadId = localStorage.getItem("travel_thread_id") || null;
let latestAnswerMarkdown = "";

// ============================================================
// Rotating placeholder examples (Indian cities focus)
// ============================================================
const placeholders = [
    "Plan a 7 days Kerala backwaters trip from Mumbai with houseboat, flights and ayurveda under ₹60,000...",
    "Plan a 5 days Rajasthan trip from Delhi covering Jaipur, Jodhpur and Udaipur with palace hotels under ₹45,000...",
    "Plan a 4 days Goa beach trip from Hyderabad with flights, beach resort and water sports under ₹30,000...",
    "Plan a 6 days Himachal Pradesh trip from Delhi covering Shimla, Manali and Kullu under ₹35,000...",
    "Plan a 3 days Varanasi spiritual trip from Kolkata including flights, ghats tour and temples...",
    "Plan a 5 days Andaman Islands trip from Chennai with flights, beach hotel and snorkelling under ₹40,000...",
    "Plan a 7 days Japan trip from Delhi with flights, ryokan stay and sightseeing under ₹1,50,000...",
    "Plan a 4 days Ooty and Coorg trip from Bangalore with homestays, trekking and coffee estate tours...",
    "Plan a complete Leh-Ladakh 8 days bike trip from Delhi with accommodation and permits...",
    "Plan a 5 days Pondicherry and Auroville trip from Chennai with French Quarter stay under ₹20,000...",
];

let placeholderIndex = 0;
let typingInterval = null;

function rotatePlaceholder() {
    const textarea = document.getElementById("userInput");
    if (!textarea || document.activeElement === textarea) return;

    placeholderIndex = (placeholderIndex + 1) % placeholders.length;
    textarea.placeholder = placeholders[placeholderIndex];
}

// Rotate placeholder every 4 seconds
setInterval(rotatePlaceholder, 4000);


// ============================================================
// Core functions
// ============================================================

function setPrompt(text) {
    const ta = document.getElementById("userInput");
    ta.value = text;
    ta.focus();
    // Scroll textarea into view smoothly
    ta.scrollIntoView({ behavior: "smooth", block: "center" });
}

function setLoading(isLoading) {
    const sendBtn   = document.getElementById("sendBtn");
    const btnText   = document.getElementById("btnText");
    const btnLoader = document.getElementById("btnLoader");

    sendBtn.disabled = isLoading;

    if (isLoading) {
        btnText.classList.add("hidden");
        btnLoader.classList.remove("hidden");
    } else {
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
    }
}

function showError(message) {
    const errorBox = document.getElementById("errorBox");
    errorBox.innerHTML = `<strong>⚠️ Error:</strong> ${message}`;
    errorBox.classList.remove("hidden");
    errorBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideError() {
    const errorBox = document.getElementById("errorBox");
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
}

function showResult(answer, threadId) {
    latestAnswerMarkdown = answer;

    const resultSection = document.getElementById("resultSection");
    const resultBox     = document.getElementById("resultBox");
    const threadInfo    = document.getElementById("threadInfo");

    // Render markdown
    if (typeof marked !== "undefined") {
        marked.setOptions({ breaks: true, gfm: true });
        resultBox.innerHTML = marked.parse(answer);
    } else {
        resultBox.innerText = answer;
    }

    threadInfo.textContent = `Thread ID: ${threadId}`;

    // Make visible before animating
    resultSection.classList.remove("hidden");

    // Fade + slide in
    resultSection.style.opacity = "0";
    resultSection.style.transform = "translateY(20px)";
    requestAnimationFrame(() => {
        resultSection.style.transition = "opacity 0.5s ease, transform 0.5s ease";
        resultSection.style.opacity = "1";
        resultSection.style.transform = "translateY(0)";
    });

    // Smooth scroll then trigger glow once the section is in view
    setTimeout(() => {
        resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

        // Trigger glow after scroll lands (~700ms for smooth scroll)
        setTimeout(() => {
            resultSection.classList.remove("result-glow"); // reset if re-triggered
            void resultSection.offsetWidth;                // force reflow to restart animation
            resultSection.classList.add("result-glow");

            // Clean up class after animation finishes
            resultSection.addEventListener("animationend", () => {
                resultSection.classList.remove("result-glow");
            }, { once: true });
        }, 700);
    }, 100);
}

async function sendMessage() {
    hideError();

    const input   = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please describe your trip first. For example: Plan a 5 days Goa trip from Mumbai.");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch("/api/travel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message:   message,
                thread_id: currentThreadId
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Something went wrong. Please try again.");
        }

        currentThreadId = data.thread_id;
        localStorage.setItem("travel_thread_id", currentThreadId);

        showResult(data.answer, data.thread_id);

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

function copyResult() {
    const resultBox = document.getElementById("resultBox");
    const text = resultBox.innerText;

    if (!text) return;

    navigator.clipboard.writeText(text)
        .then(() => {
            const btn = document.querySelector(".copy-btn");
            const old = btn.innerHTML;
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
            btn.style.borderColor = "rgba(34,197,94,0.5)";
            btn.style.color = "#86efac";
            setTimeout(() => {
                btn.innerHTML = old;
                btn.style.borderColor = "";
                btn.style.color = "";
            }, 2000);
        })
        .catch(() => showError("Could not copy to clipboard."));
}

function downloadPDF() {
    const pdfContent = document.getElementById("pdfContent");

    if (!latestAnswerMarkdown || !pdfContent) {
        showError("No travel plan available to download.");
        return;
    }

    const btn = document.querySelector(".download-btn");
    const old = btn.innerHTML;
    btn.innerHTML = `<span class="loader"></span> Preparing...`;
    btn.disabled = true;

    // Show the hidden PDF title during export
    const pdfTitle = document.querySelector(".pdf-title");
    pdfTitle.style.display = "block";

    const options = {
        margin:   [0.5, 0.5, 0.5, 0.5],
        filename: "TripMate-AI-Travel-Plan.pdf",
        image:    { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
        jsPDF: { unit: "in", format: "a4", orientation: "portrait" },
        pagebreak: { mode: ["avoid-all", "css", "legacy"] }
    };

    html2pdf()
        .set(options)
        .from(pdfContent)
        .save()
        .then(() => {
            pdfTitle.style.display = "";
            btn.innerHTML = old;
            btn.disabled = false;
        })
        .catch(() => {
            pdfTitle.style.display = "";
            btn.innerHTML = old;
            btn.disabled = false;
            showError("Could not generate PDF.");
        });
}

// Ctrl+Enter to submit
document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter") sendMessage();
});

// Auto-resize textarea
document.addEventListener("DOMContentLoaded", () => {
    const ta = document.getElementById("userInput");
    if (!ta) return;

    ta.addEventListener("input", () => {
        ta.style.height = "auto";
        ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
    });
});
