// ResumeIQ front-end: tab switching, file handling and rendering results.

const $ = (sel) => document.querySelector(sel);

// ---------- Tabs ----------
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
  });
});

// ---------- File input + drag and drop ----------
const fileInput = $("#resume-file");
const drop = $("#drop");
fileInput.addEventListener("change", () => {
  $("#file-label").textContent = fileInput.files[0] ? `Selected: ${fileInput.files[0].name}` : "Drop a PDF / DOCX / TXT here or click to browse";
});
["dragenter", "dragover"].forEach((evt) => drop.addEventListener(evt, (e) => { e.preventDefault(); drop.classList.add("drag"); }));
["dragleave", "drop"].forEach((evt) => drop.addEventListener(evt, (e) => { e.preventDefault(); drop.classList.remove("drag"); }));
drop.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    fileInput.dispatchEvent(new Event("change"));
  }
});

$("#rank-files").addEventListener("change", (e) => {
  const n = e.target.files.length;
  $("#rank-label").textContent = n ? `${n} resume(s) selected` : "Select multiple resumes";
});

// ---------- Helpers ----------
function showError(el, msg) { el.textContent = msg; el.classList.remove("hidden"); }
function chips(container, items, cls) {
  container.innerHTML = "";
  if (!items.length) { container.innerHTML = '<span class="muted">None</span>'; return; }
  items.forEach((item) => {
    const span = document.createElement("span");
    span.className = `chip ${cls || ""}`;
    span.textContent = item;
    container.appendChild(span);
  });
}
function colorFor(score) {
  if (score >= 75) return "#16a34a";
  if (score >= 55) return "#4f46e5";
  if (score >= 35) return "#d97706";
  return "#dc2626";
}

// ---------- Candidate mode ----------
$("#analyze-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("#error");
  err.classList.add("hidden");
  const btn = $("#analyze-btn");
  btn.disabled = true;
  btn.textContent = "Analyzing...";
  try {
    const res = await fetch("/api/analyze", { method: "POST", body: new FormData(e.target) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    render(data);
  } catch (ex) {
    showError(err, ex.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze resume";
  }
});

function render(d) {
  $("#results").classList.remove("hidden");
  const ring = $("#ring");
  ring.style.setProperty("--p", d.score);
  ring.style.setProperty("--ring-color", colorFor(d.score));
  $("#score").textContent = Math.round(d.score);
  $("#verdict").textContent = d.verdict;
  $("#verdict").style.color = colorFor(d.score);
  $("#skill-score").textContent = `${Math.round(d.skill_score)}%`;
  $("#sim-score").textContent = `${Math.round(d.similarity_score)}%`;
  $("#word-count").textContent = d.word_count;

  chips($("#matched"), d.matched_skills, "ok");
  chips($("#missing"), d.missing_skills, "no");
  chips($("#extra"), d.extra_skills);

  const list = $("#checklist");
  list.innerHTML = "";
  const items = [
    ...d.sections_found.map((s) => [s, true]),
    ...d.sections_missing.map((s) => [s, false]),
    ...Object.entries(d.contact),
  ];
  items.forEach(([name, ok]) => {
    const li = document.createElement("li");
    li.textContent = `${ok ? "✅" : "❌"} ${name}`;
    list.appendChild(li);
  });

  const tips = $("#tips");
  tips.innerHTML = "";
  (d.suggestions.length ? d.suggestions : ["Great job, your resume covers this role well!"]).forEach((t) => {
    const li = document.createElement("li");
    li.textContent = t;
    tips.appendChild(li);
  });
  $("#results").scrollIntoView({ behavior: "smooth" });
}

// ---------- Recruiter mode ----------
$("#rank-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("#rank-error");
  err.classList.add("hidden");
  try {
    const res = await fetch("/api/rank", { method: "POST", body: new FormData(e.target) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    const body = $("#rank-body");
    body.innerHTML = "";
    data.results.forEach((r) => {
      const tr = document.createElement("tr");
      [r.rank, r.name, r.score, r.verdict, r.missing_skills.slice(0, 5).join(", ") || "-"].forEach((v) => {
        const td = document.createElement("td");
        td.textContent = v;
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    $("#rank-results").classList.remove("hidden");
    if (data.skipped.length) showError(err, `Skipped unreadable files: ${data.skipped.join(", ")}`);
  } catch (ex) {
    showError(err, ex.message);
  }
});
