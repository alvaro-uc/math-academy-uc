/* Math Academy UC — Frontend Application Logic */

let APP_STATE = null;
let SELECTED_NODE_ID = null;

// Active Lesson Session State
let LESSON_SESSION = {
  topic: null,
  taskType: "lesson",
  stepIndex: 0, // 0 = Theory & Worked Example, 1..N = Questions, N+1 = Summary
  selectedOption: null,
  answeredCurrent: false,
  correctCount: 0,
  results: [],
};

// Active Diagnostic Session State
let DIAG_SESSION = {
  items: [],
  idx: 0,
  selectedOption: null,
  resultsByTopic: {},
};

function renderMath(el) {
  if (!el || typeof renderMathInElement !== "function") return;
  renderMathInElement(el, {
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "$", right: "$", display: false },
      { left: "\\(", right: "\\)", display: false },
      { left: "\\[", right: "\\]", display: true },
    ],
    throwOnError: false,
  });
}

function formatInlineMarkdown(str) {
  if (!str) return "";
  // Proteger bloques matemáticos ($$...$$, $...$, \[...\], \(...\)) para no alterar símbolos dentro de LaTeX
  const mathBlocks = [];
  const placeholder = (i) => `\u0000MATH_${i}\u0000`;
  const protectedStr = str.replace(
    /(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g,
    (match) => {
      mathBlocks.push(match);
      return placeholder(mathBlocks.length - 1);
    }
  );

  const formatted = protectedStr
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");

  return formatted.replace(/\u0000MATH_(\d+)\u0000/g, (_, idx) => mathBlocks[Number(idx)]);
}

function formatTextWithParagraphs(raw) {
  if (!raw) return "";
  return raw
    .split("\n\n")
    .map(
      (p) =>
        `<p style="margin-bottom:0.55rem">${formatInlineMarkdown(p).replace(/\n/g, "<br/>")}</p>`
    )
    .join("");
}

const SESSION_TOKEN_KEY = "matuc_auth_token";
const LOCAL_BACKUP_KEY = "matuc_progress_backup_v1";

function getAuthToken() {
  try {
    return sessionStorage.getItem(SESSION_TOKEN_KEY) || "";
  } catch (_) {
    return "";
  }
}

function setAuthToken(token) {
  try {
    if (token) {
      sessionStorage.setItem(SESSION_TOKEN_KEY, token);
    } else {
      sessionStorage.removeItem(SESSION_TOKEN_KEY);
    }
  } catch (_) {}
}

function getLocalBackup() {
  try {
    const raw = localStorage.getItem(LOCAL_BACKUP_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && parsed.profile && parsed.topic_state) {
      return parsed;
    }
    return null;
  } catch (_) {
    return null;
  }
}

function saveLocalBackup(snapshot) {
  if (!snapshot || typeof snapshot !== "object" || !snapshot.profile) return;
  try {
    localStorage.setItem(LOCAL_BACKUP_KEY, JSON.stringify(snapshot));
  } catch (_) {}
}

function showAuthGate(errorMsg = "") {
  const gate = document.getElementById("auth-gate");
  if (gate) gate.classList.remove("hidden");
  const errEl = document.getElementById("auth-error-msg");
  if (errEl) {
    if (errorMsg) {
      errEl.textContent = errorMsg;
      errEl.classList.remove("hidden");
    } else {
      errEl.textContent = "";
      errEl.classList.add("hidden");
    }
  }
  const input = document.getElementById("auth-password-input");
  if (input) {
    input.value = "";
    setTimeout(() => input.focus(), 50);
  }
}

function hideAuthGate() {
  const gate = document.getElementById("auth-gate");
  if (gate) gate.classList.add("hidden");
  const errEl = document.getElementById("auth-error-msg");
  if (errEl) errEl.classList.add("hidden");
}

async function apiFetch(url, options = {}) {
  const token = getAuthToken();
  const headers = Object.assign({}, options.headers || {});
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(url, Object.assign({}, options, { headers }));
  if (res.status === 401) {
    setAuthToken("");
    APP_STATE = null;
    showAuthGate();
    throw new Error("Unauthorized");
  }
  return res;
}

async function fetchState() {
  const token = getAuthToken();
  if (!token) {
    showAuthGate();
    return;
  }
  try {
    const clientBackup = getLocalBackup();
    const res = clientBackup
      ? await apiFetch("/api/state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ client_backup: clientBackup }),
        })
      : await apiFetch("/api/state");
    APP_STATE = await res.json();
    hideAuthGate();
    renderAll();
  } catch (_) {
    // 401 is handled inside apiFetch
  }
}

function renderAll() {
  if (!APP_STATE) return;
  if (APP_STATE.backup_snapshot) {
    saveLocalBackup(APP_STATE.backup_snapshot);
  }
  renderTopBar();
  renderDashboard();
  renderDAG();
  renderCoursesCatalog();
}

function renderTopBar() {
  const p = APP_STATE.profile;
  const pct = Math.min(100, Math.round((p.today_xp / Math.max(1, p.daily_goal_xp)) * 100));
  document.getElementById("xp-today-label").textContent = `${p.today_xp} / ${p.daily_goal_xp} XP hoy`;
  document.getElementById("xp-bar-fill").style.width = `${pct}%`;
  document.getElementById("total-xp-badge").textContent = `${p.total_xp} XP Total`;

  const semSelect = document.getElementById("select-semester");
  if (semSelect) semSelect.value = String(p.current_semester);

  const storageBadge = document.getElementById("storage-backend-badge");
  if (storageBadge) {
    const backend = APP_STATE.storage_backend || "sqlite-local";
    if (backend === "postgres-cloud") {
      storageBadge.textContent = "☁️ Sincronizado en Cloud (PostgreSQL)";
    } else if (backend === "turso-cloud") {
      storageBadge.textContent = "☁️ Sincronizado en Cloud (Turso SQLite)";
    } else {
      storageBadge.textContent = "💾 Almacenamiento SQLite Local";
    }
  }
}

function renderDashboard() {
  const queueEl = document.getElementById("task-queue-list");
  const recs = APP_STATE.recommendations || [];

  if (recs.length === 0) {
    queueEl.innerHTML = `<div class="stat-card">¡Excelente! Has completado todas las tareas sugeridas por ahora.</div>`;
  } else {
    queueEl.innerHTML = recs
      .map((r) => {
        const badgeClass =
          r.task_type === "review"
            ? "badge-review"
            : r.task_type === "anticipation"
            ? "badge-anticipation"
            : "badge-lesson";
        const implicitHtml =
          r.implicit_rep_topics && r.implicit_rep_topics.length > 0
            ? `<div class="task-fire-info">
                <span>⚡ Crédito implícito FIRe a:</span>
                ${r.implicit_rep_topics
                  .slice(0, 3)
                  .map(
                    (it) =>
                      `<span class="fire-chip">${it.title} (${Math.round(it.weight * 100)}%)</span>`
                  )
                  .join("")}
               </div>`
            : `<div class="task-fire-info"><span>🌱 Tópico fundacional · Desbloquea ${r.unlocks_count} tema(s) posterior(es)</span></div>`;

        return `
          <article class="task-card type-${r.task_type}">
            <div class="task-left">
              <div class="task-meta-top">
                <span class="badge ${badgeClass}">${r.tag_label}</span>
                <span class="badge badge-course">${r.course_name} · Sem ${r.semester}</span>
                <span style="font-size:0.75rem;color:var(--text-light)">⏱ ~${r.estimated_mins} min</span>
              </div>
              <div class="task-title">${r.title}</div>
              ${implicitHtml}
            </div>
            <div class="task-right">
              <span class="xp-reward">+${r.xp} XP</span>
              <button class="btn-primary" onclick="startLesson('${r.topic_id}', '${r.task_type}')">
                Entrenar ahora →
              </button>
            </div>
          </article>
        `;
      })
      .join("");
  }

  // KPIs
  const topics = APP_STATE.topics || [];
  const masteredCnt = topics.filter((t) => t.status === "mastered" || t.status === "review_due").length;
  const frontierCnt = topics.filter((t) => t.status === "available" || t.status === "in_progress").length;
  const reviewCnt = topics.filter((t) => t.status === "review_due").length;

  document.getElementById("kpi-mastered").textContent = `${masteredCnt}/${topics.length}`;
  document.getElementById("kpi-available").textContent = String(frontierCnt);
  document.getElementById("kpi-reviews").textContent = String(reviewCnt);

  // Courses progress sidebar
  const cList = document.getElementById("sidebar-courses-progress");
  cList.innerHTML = (APP_STATE.courses || [])
    .map(
      (c) => `
      <div class="course-mini-item">
        <div class="course-mini-header">
          <span>S${c.semester} · ${c.name}</span>
          <span>${c.progress_pct}%</span>
        </div>
        <div class="course-mini-bar">
          <div class="course-mini-fill" style="width:${c.progress_pct}%; background:${c.color}"></div>
        </div>
      </div>
    `
    )
    .join("");

  renderMath(document.getElementById("view-dashboard"));
}

function renderDAG() {
  const nodesContainer = document.getElementById("dag-nodes");
  const topics = APP_STATE.topics || [];

  const cols = [1, 2, 3, 4].map((sem) => {
    const semTopics = topics.filter((t) => t.semester === sem);
    const label = sem === 1 ? "Semestre 1 (Base UC)" : sem === 2 ? "Semestre 2" : `Semestre ${sem} (Anticipación)`;
    return `
      <div class="dag-col" data-sem="${sem}">
        <div class="dag-col-header">${label}</div>
        ${semTopics
          .map((t) => {
            const isSel = SELECTED_NODE_ID === t.id ? "selected" : "";
            const statusLabel =
              t.status === "mastered"
                ? `✓ ${Math.round(t.mastery * 100)}%`
                : t.status === "review_due"
                ? "↻ Repaso FIRe"
                : t.status === "available" || t.status === "in_progress"
                ? "● Frontera"
                : "🔒 Bloqueado";
            return `
              <div class="dag-node status-${t.status} ${isSel}" id="dag-node-${t.id}" onclick="selectDagNode('${t.id}')">
                <div class="dag-node-top">
                  <span>${t.course_id}</span>
                  <span>${statusLabel}</span>
                </div>
                <div class="dag-node-title">${t.title}</div>
              </div>
            `;
          })
          .join("")}
      </div>
    `;
  });

  nodesContainer.innerHTML = cols.join("");
  if (!SELECTED_NODE_ID && topics.length > 0) {
    SELECTED_NODE_ID = topics[0].id;
  }
  if (SELECTED_NODE_ID) {
    renderNodeInspector(SELECTED_NODE_ID);
  }
  requestAnimationFrame(drawDagEdges);
}

function drawDagEdges() {
  const svg = document.getElementById("dag-svg");
  const container = document.getElementById("dag-container");
  if (!svg || !container || !APP_STATE) return;

  const rect = container.getBoundingClientRect();
  svg.setAttribute("width", container.scrollWidth);
  svg.setAttribute("height", container.scrollHeight);

  let linesHtml = "";
  const topics = APP_STATE.topics || [];

  topics.forEach((t) => {
    const targetEl = document.getElementById(`dag-node-${t.id}`);
    if (!targetEl) return;
    const tBox = targetEl.getBoundingClientRect();
    const x2 = tBox.left - rect.left + container.scrollLeft;
    const y2 = tBox.top - rect.top + container.scrollTop + tBox.height / 2;

    (t.prereqs || []).forEach((preId) => {
      const srcEl = document.getElementById(`dag-node-${preId}`);
      if (!srcEl) return;
      const sBox = srcEl.getBoundingClientRect();
      const x1 = sBox.left - rect.left + container.scrollLeft + sBox.width;
      const y1 = sBox.top - rect.top + container.scrollTop + sBox.height / 2;

      const isHighlighted = SELECTED_NODE_ID === t.id || SELECTED_NODE_ID === preId;
      const stroke = isHighlighted ? "#4f46e5" : "#cbd5e1";
      const width = isHighlighted ? "2.4" : "1.5";
      const cx1 = x1 + (x2 - x1) * 0.45;
      const cx2 = x1 + (x2 - x1) * 0.55;
      linesHtml += `<path d="M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}" fill="none" stroke="${stroke}" stroke-width="${width}" />`;
    });
  });

  svg.innerHTML = linesHtml;
}

function selectDagNode(topicId) {
  SELECTED_NODE_ID = topicId;
  document.querySelectorAll(".dag-node").forEach((el) => {
    el.classList.toggle("selected", el.id === `dag-node-${topicId}`);
  });
  renderNodeInspector(topicId);
  drawDagEdges();
}

function renderNodeInspector(topicId) {
  const inspector = document.getElementById("node-inspector");
  const t = (APP_STATE.topics || []).find((x) => x.id === topicId);
  if (!t) return;

  const byId = Object.fromEntries((APP_STATE.topics || []).map((x) => [x.id, x]));
  const prereqList =
    t.prereqs.length > 0
      ? t.prereqs
          .map((pid) => `<li>${byId[pid] ? byId[pid].title : pid}</li>`)
          .join("")
      : "<li>Sin prerrequisitos (Nodo raíz de Semestre 1)</li>";

  const implicitEntries = Object.entries(t.implicit_targets || {});
  const implicitHtml =
    implicitEntries.length > 0
      ? implicitEntries
          .map(
            ([sid, w]) =>
              `<li><strong>${byId[sid] ? byId[sid].title : sid}</strong>: recibe <code>${Math.round(
                w * 100
              )}%</code> de crédito FIRe</li>`
          )
          .join("")
      : "<li>No abarca nodos previos.</li>";

  inspector.innerHTML = `
    <div style="margin-bottom:0.65rem">
      <span class="badge badge-course">${t.course_name} · Semestre ${t.semester}</span>
    </div>
    <h3 style="font-size:1.02rem;margin-bottom:0.5rem">${t.title}</h3>
    <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.85rem">
      Maestría: <strong>${Math.round(t.mastery * 100)}%</strong> · Estabilidad: <strong>${t.stability_days} días</strong> · Recompensa: <strong>+${t.xp} XP</strong>
    </div>

    <div style="font-size:0.8rem;margin-bottom:0.75rem">
      <strong>Prerrequisitos directos:</strong>
      <ul style="padding-left:1.1rem;margin-top:0.25rem;color:var(--text-muted)">${prereqList}</ul>
    </div>

    <div style="font-size:0.8rem;margin-bottom:1rem">
      <strong>Repetición Implícita (FIRe):</strong>
      <ul style="padding-left:1.1rem;margin-top:0.25rem;color:var(--text-muted)">${implicitHtml}</ul>
    </div>

    <button class="btn-primary" style="width:100%" onclick="startLesson('${t.id}', 'lesson')">
      ${t.status === "locked" ? "Explorar en Modo Anticipación →" : "Iniciar Entrenamiento (+ " + t.xp + " XP) →"}
    </button>
  `;
}

function renderCoursesCatalog() {
  const container = document.getElementById("courses-catalog");
  const courses = APP_STATE.courses || [];
  const topics = APP_STATE.topics || [];

  container.innerHTML = courses
    .map((c) => {
      const cTopics = topics.filter((t) => t.course_id === c.id);
      return `
        <div class="course-card">
          <div class="course-card-header">
            <div>
              <span class="course-sem-tag">Semestre ${c.semester} · ${c.code}</span>
              <h3 style="font-size:1.02rem;margin-top:0.25rem">${c.name}</h3>
            </div>
            <span class="badge badge-lesson">${c.progress_pct}% Dominio</span>
          </div>
          <p style="font-size:0.82rem;color:var(--text-muted)">${c.description}</p>
          <div class="course-topics-list">
            ${cTopics
              .map(
                (t) => `
                <div class="course-topic-row">
                  <div>
                    <div style="font-weight:600">${t.title}</div>
                    <div style="font-size:0.73rem;color:var(--text-light)">Maestría: ${Math.round(
                      t.mastery * 100
                    )}% · +${t.xp} XP</div>
                  </div>
                  <button class="btn-outline" onclick="startLesson('${t.id}', 'lesson')">
                    Practicar
                  </button>
                </div>
              `
              )
              .join("")}
          </div>
        </div>
      `;
    })
    .join("");
}

/* ============================================================================
   INTERACTIVE MICRO-LESSON & PRACTICE ENGINE
   ============================================================================ */

async function startLesson(topicId, taskType = "lesson") {
  const res = await apiFetch(`/api/topic/${topicId}`);
  if (!res.ok) return;
  const topic = await res.json();

  LESSON_SESSION = {
    topic,
    taskType,
    stepIndex: 0, // 0 = Theory + Worked Example, 1..N = Questions, N+1 = Summary
    selectedOption: null,
    answeredCurrent: false,
    correctCount: 0,
    results: [],
    completionResponse: null,
  };

  document.getElementById("lesson-modal").classList.remove("hidden");
  renderLessonStep();
}

function closeLessonModal() {
  document.getElementById("lesson-modal").classList.add("hidden");
}

function renderLessonStep() {
  const { topic, stepIndex } = LESSON_SESSION;
  const totalQuestions = topic.questions.length;

  document.getElementById("lesson-course-tag").textContent = `${topic.course_name} · Semestre ${topic.semester}`;
  document.getElementById("lesson-title").textContent = topic.title;

  // Stepper pills: 1 for Theory + 1 per Question
  const totalSteps = 1 + totalQuestions;
  const stepperEl = document.getElementById("lesson-stepper");
  let pillsHtml = "";
  for (let i = 0; i < totalSteps; i++) {
    const cls = i < stepIndex ? "done" : i === stepIndex ? "active" : "";
    pillsHtml += `<span class="step-pill ${cls}"></span>`;
  }
  stepperEl.innerHTML = pillsHtml;

  const bodyEl = document.getElementById("lesson-body");
  const footerEl = document.getElementById("lesson-footer");

  if (stepIndex === 0) {
    // STEP 0: Micro-Teoría + Conexión Ciencia de Datos + Tip Interrogación UC + Ejemplo Resuelto
    const we = topic.worked_example;
    bodyEl.innerHTML = `
      <div class="theory-box">
        <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;color:var(--primary-hover);margin-bottom:0.35rem">
          Concepto Clave &amp; Formalismo
        </div>
        ${formatTextWithParagraphs(topic.theory)}
      </div>

      <div class="callout-grid">
        <div class="callout-box callout-ds">
          <strong>📊 Conexión con Ingeniería en Ciencia de Datos:</strong>
          <p style="margin-top:0.25rem">${formatInlineMarkdown(topic.ds_connection)}</p>
        </div>
        <div class="callout-box callout-uc">
          <strong>🎓 Estrategia de Interrogación UC (I1/I2/Examen):</strong>
          <p style="margin-top:0.25rem">${formatInlineMarkdown(topic.uc_exam_tip)}</p>
        </div>
      </div>

      <div class="worked-example-box">
        <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:0.4rem">
          Ejemplo Resuelto Paso a Paso
        </div>
        <div style="font-weight:700;margin-bottom:0.65rem">${formatInlineMarkdown(we.problem)}</div>
        ${we.steps
          .map(
            (st, idx) =>
              `<div class="worked-step"><strong>Paso ${idx + 1}:</strong> ${formatInlineMarkdown(st)}</div>`
          )
          .join("")}
        <div style="margin-top:0.65rem;padding-top:0.55rem;border-top:2px solid var(--border);font-weight:700;color:var(--emerald)">
          Respuesta final: ${formatInlineMarkdown(we.final_answer)}
        </div>
      </div>
    `;

    footerEl.innerHTML = `
      <span style="font-size:0.82rem;color:var(--text-muted)">
        A continuación: <strong>${totalQuestions} problemas</strong> (curados + generados paramétricamente)
      </span>
      <button class="btn-primary" onclick="nextLessonStep()">
        Pasar a Práctica Activa →
      </button>
    `;
    renderMath(bodyEl);
    return;
  }

  if (stepIndex >= 1 && stepIndex <= totalQuestions) {
    const qIdx = stepIndex - 1;
    const q = topic.questions[qIdx];
    const keys = ["A", "B", "C", "D"];

    bodyEl.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.55rem">
        <span class="badge ${q.is_parametric ? "badge-anticipation" : "badge-lesson"}">
          Problema ${qIdx + 1} de ${totalQuestions} · ${
      q.is_parametric ? "Generador Paramétrico Dinámico" : "Problema Tipo Interrogación UC"
    }
        </span>
        <button class="btn-ghost" onclick="toggleHint()">💡 Ver Pista</button>
      </div>

      <div class="question-prompt">${formatInlineMarkdown(q.prompt)}</div>

      <div class="options-grid" id="question-options">
        ${q.options
          .map(
            (opt, idx) => `
          <button class="option-btn" id="opt-btn-${idx}" onclick="selectQuestionOption(${idx})">
            <span class="option-key">${keys[idx] || idx + 1}</span>
            <span>${formatInlineMarkdown(opt)}</span>
          </button>
        `
          )
          .join("")}
      </div>

      <div id="question-hint" class="hint-box" style="display:none">
        <strong>Pista:</strong> ${formatInlineMarkdown(q.hint)}
      </div>

      <div id="question-feedback"></div>
    `;

    footerEl.innerHTML = `
      <span style="font-size:0.8rem;color:var(--text-muted)">Atajo: teclas 1–4 para elegir, Enter para verificar</span>
      <div style="display:flex;gap:0.5rem">
        <button class="btn-primary" id="btn-Verify-Answer" onclick="verifyCurrentQuestion()">
          Verificar Respuesta
        </button>
      </div>
    `;

    renderMath(bodyEl);
    return;
  }

  // Summary Step
  renderLessonSummary();
}

function toggleHint() {
  const el = document.getElementById("question-hint");
  if (!el) return;
  el.style.display = el.style.display === "none" ? "block" : "none";
  renderMath(el);
}

function selectQuestionOption(idx) {
  if (LESSON_SESSION.answeredCurrent) return;
  LESSON_SESSION.selectedOption = idx;
  document.querySelectorAll("#question-options .option-btn").forEach((btn, i) => {
    btn.classList.toggle("selected", i === idx);
  });
}

async function verifyCurrentQuestion() {
  if (LESSON_SESSION.answeredCurrent) {
    nextLessonStep();
    return;
  }
  if (LESSON_SESSION.selectedOption === null) return;

  const qIdx = LESSON_SESSION.stepIndex - 1;
  const q = LESSON_SESSION.topic.questions[qIdx];
  const chosen = LESSON_SESSION.selectedOption;
  const isCorrect = chosen === q.correct_index;

  LESSON_SESSION.answeredCurrent = true;
  if (isCorrect) LESSON_SESSION.correctCount += 1;

  document.querySelectorAll("#question-options .option-btn").forEach((btn, i) => {
    btn.disabled = true;
    if (i === q.correct_index) btn.classList.add("correct");
    else if (i === chosen && !isCorrect) btn.classList.add("wrong");
  });

  const fb = document.getElementById("question-feedback");
  fb.innerHTML = `
    <div class="feedback-banner ${isCorrect ? "ok" : "err"}">
      <strong>${isCorrect ? "✓ ¡Correcto!" : "✗ Respuesta incorrecta."}</strong>
      <div style="margin-top:0.3rem">${formatInlineMarkdown(q.explanation)}</div>
    </div>
  `;
  renderMath(fb);

  const btn = document.getElementById("btn-Verify-Answer");
  const isLast = LESSON_SESSION.stepIndex === LESSON_SESSION.topic.questions.length;
  btn.textContent = isLast ? "Finalizar y Registrar XP →" : "Siguiente Problema →";
}

async function nextLessonStep() {
  const totalQuestions = LESSON_SESSION.topic.questions.length;
  if (LESSON_SESSION.stepIndex === totalQuestions) {
    // Enviar resultado al motor FIRe junto con el respaldo local para entornos serverless
    const res = await apiFetch("/api/complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic_id: LESSON_SESSION.topic.id,
        correct_count: LESSON_SESSION.correctCount,
        total_count: totalQuestions,
        task_type: LESSON_SESSION.taskType,
        client_backup: getLocalBackup(),
      }),
    });
    const data = await res.json();
    LESSON_SESSION.completionResponse = data.result;
    APP_STATE = data.state;
    renderAll();
  }

  LESSON_SESSION.stepIndex += 1;
  LESSON_SESSION.selectedOption = null;
  LESSON_SESSION.answeredCurrent = false;
  renderLessonStep();
}

function renderLessonSummary() {
  const bodyEl = document.getElementById("lesson-body");
  const footerEl = document.getElementById("lesson-footer");
  const res = LESSON_SESSION.completionResponse;
  const totalQ = LESSON_SESSION.topic.questions.length;

  const implicitHtml =
    res && res.implicit_boosted && res.implicit_boosted.length > 0
      ? `
      <div style="margin-top:1rem;padding:0.9rem 1rem;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px">
        <strong style="color:#15803d">⚡ Propagación FIRe (Repetición Implícita Fraccionaria):</strong>
        <p style="font-size:0.83rem;color:#166534;margin-top:0.2rem">
          Al aprobar este intento, el motor extendió el intervalo de repaso de tus prerrequisitos:
        </p>
        <ul style="padding-left:1.2rem;margin-top:0.4rem;font-size:0.83rem;color:#14532d">
          ${res.implicit_boosted
            .map(
              (b) =>
                `<li><strong>${b.title}</strong> (peso ${Math.round(
                  b.weight * 100
                )}%) → nueva estabilidad: <strong>${b.new_stability_days} días</strong></li>`
            )
            .join("")}
        </ul>
      </div>
    `
      : "";

  bodyEl.innerHTML = `
    <div style="text-align:center;padding:1.2rem 0.5rem">
      <div style="font-size:2.4rem;margin-bottom:0.4rem">${res && res.passed ? "🎯" : "🔁"}</div>
      <h3 style="font-size:1.3rem">${
        res && res.passed ? "¡Intento aprobado!" : "Intento registrado · Bajo el 65 %"
      }</h3>
      <p style="color:var(--text-muted);margin-top:0.3rem">
        Obtuviste <strong>${LESSON_SESSION.correctCount} de ${totalQ}</strong> respuestas correctas (${Math.round(
    (LESSON_SESSION.correctCount / totalQ) * 100
  )}%).
      </p>

      <div style="display:flex;justify-content:center;gap:1rem;margin-top:1.1rem">
        <div class="kpi-box" style="min-width:130px">
          <div class="kpi-val" style="color:var(--emerald)">+${res ? res.xp_earned : 0} XP</div>
          <div class="kpi-label">XP Ganado</div>
        </div>
        <div class="kpi-box" style="min-width:130px">
          <div class="kpi-val">${res ? Math.round(res.new_mastery * 100) : 0}%</div>
          <div class="kpi-label">Maestría del Tópico</div>
        </div>
        ${res && res.review_scheduled ? `
          <div class="kpi-box" style="min-width:130px">
            <div class="kpi-val">${res.new_stability_days} d</div>
            <div class="kpi-label">Próximo Repaso FIRe</div>
          </div>
        ` : ""}
      </div>
    </div>
    ${implicitHtml}
  `;

  footerEl.innerHTML = `
    <button class="btn-outline" onclick="startLesson('${LESSON_SESSION.topic.id}', 'practice')">
      Generar Nuevos Problemas de este Tópico ↻
    </button>
    <button class="btn-primary" onclick="closeLessonModal()">
      Volver a mi Cola Adaptativa ✓
    </button>
  `;
}

/* ============================================================================
   DIAGNOSTIC PLACEMENT TEST MODAL
   ============================================================================ */

async function openDiagnosticModal() {
  const res = await apiFetch("/api/diagnostic");
  const data = await res.json();
  DIAG_SESSION = {
    items: data.items || [],
    idx: 0,
    selectedOption: null,
    resultsByTopic: {},
  };
  document.getElementById("diagnostic-modal").classList.remove("hidden");
  renderDiagnosticStep();
}

function closeDiagnosticModal() {
  document.getElementById("diagnostic-modal").classList.add("hidden");
}

function renderDiagnosticStep() {
  const bodyEl = document.getElementById("diagnostic-body");
  const footerEl = document.getElementById("diagnostic-footer");
  const { items, idx } = DIAG_SESSION;

  if (idx >= items.length) {
    finishDiagnostic();
    return;
  }

  const item = items[idx];
  const q = item.question;
  const keys = ["A", "B", "C", "D"];

  bodyEl.innerHTML = `
    <div style="margin-bottom:0.75rem;display:flex;justify-content:space-between;align-items:center">
      <span class="badge badge-lesson">Pregunta ${idx + 1} de ${items.length} · ${item.course_name}</span>
      <span style="font-size:0.78rem;color:var(--text-muted)">Evalúa: ${item.topic_title}</span>
    </div>
    <div class="question-prompt">${formatInlineMarkdown(q.prompt)}</div>
    <div class="options-grid" id="diag-options">
      ${q.options
        .map(
          (opt, i) => `
        <button class="option-btn" onclick="selectDiagOption(${i})">
          <span class="option-key">${keys[i]}</span>
          <span>${formatInlineMarkdown(opt)}</span>
        </button>
      `
        )
        .join("")}
    </div>
  `;

  footerEl.innerHTML = `
    <button class="btn-ghost" onclick="skipDiagQuestion()">Todavía no he visto este tema (Saltar)</button>
    <button class="btn-primary" onclick="submitDiagQuestion()">Confirmar y Continuar →</button>
  `;
  renderMath(bodyEl);
}

function selectDiagOption(i) {
  DIAG_SESSION.selectedOption = i;
  document.querySelectorAll("#diag-options .option-btn").forEach((btn, idx) => {
    btn.classList.toggle("selected", idx === i);
  });
}

function skipDiagQuestion() {
  const item = DIAG_SESSION.items[DIAG_SESSION.idx];
  DIAG_SESSION.resultsByTopic[item.topic_id] = false;
  DIAG_SESSION.idx += 1;
  DIAG_SESSION.selectedOption = null;
  renderDiagnosticStep();
}

function submitDiagQuestion() {
  if (DIAG_SESSION.selectedOption === null) return;
  const item = DIAG_SESSION.items[DIAG_SESSION.idx];
  const isCorrect = DIAG_SESSION.selectedOption === item.question.correct_index;
  DIAG_SESSION.resultsByTopic[item.topic_id] = isCorrect;
  DIAG_SESSION.idx += 1;
  DIAG_SESSION.selectedOption = null;
  renderDiagnosticStep();
}

async function finishDiagnostic() {
  const sem = parseInt(document.getElementById("select-semester").value || "1", 10);
  const res = await apiFetch("/api/diagnostic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      results: DIAG_SESSION.resultsByTopic,
      target_semester: sem,
      client_backup: getLocalBackup(),
    }),
  });
  const data = await res.json();
  APP_STATE = data.state;
  renderAll();

  const bodyEl = document.getElementById("diagnostic-body");
  const footerEl = document.getElementById("diagnostic-footer");
  bodyEl.innerHTML = `
    <div style="text-align:center;padding:1.5rem 0.5rem">
      <div style="font-size:2.4rem;margin-bottom:0.5rem">🧭</div>
      <h3>¡Frontera de Conocimiento Calibrada!</h3>
      <p style="color:var(--text-muted);margin-top:0.4rem">
        Has acreditado dominio en <strong>${data.result.mastered_count} nodos base</strong> y ganaste <strong>+${data.result.xp_bonus} XP</strong>.
        Tu cola diaria ahora apunta directamente a tu nueva frontera.
      </p>
    </div>
  `;
  footerEl.innerHTML = `
    <span></span>
    <button class="btn-primary" onclick="closeDiagnosticModal()">Ir a mi Cola Personalizada →</button>
  `;
}

/* ============================================================================
   EVENT LISTENERS & NAVIGATION
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
  // Auth Gate Form
  const authForm = document.getElementById("auth-form");
  if (authForm) {
    authForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = document.getElementById("auth-password-input");
      const btn = document.getElementById("auth-submit-btn");
      const password = input ? input.value : "";
      if (!password) return;
      if (btn) btn.disabled = true;
      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password }),
        });
        const data = await res.json();
        if (res.ok && data.ok && data.token) {
          setAuthToken(data.token);
          hideAuthGate();
          await fetchState();
        } else {
          showAuthGate(data.error || "Contraseña incorrecta.");
        }
      } catch (_) {
        showAuthGate("Error de conexión al verificar la contraseña.");
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  }

  // Logout / Lock Button
  const btnLogout = document.getElementById("btn-logout");
  if (btnLogout) {
    btnLogout.addEventListener("click", () => {
      setAuthToken("");
      APP_STATE = null;
      closeLessonModal();
      closeDiagnosticModal();
      showAuthGate();
    });
  }

  // Navigation Tabs
  document.querySelectorAll(".nav-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".view-panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const view = tab.getAttribute("data-view");
      document.getElementById(`view-${view}`).classList.add("active");
      if (view === "graph") {
        requestAnimationFrame(drawDagEdges);
      }
    });
  });

  // Semester focus selector
  document.getElementById("select-semester").addEventListener("change", async (e) => {
    const sem = parseInt(e.target.value, 10);
    const res = await apiFetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_semester: sem,
        client_backup: getLocalBackup(),
      }),
    });
    const data = await res.json();
    APP_STATE = data.state;
    renderAll();
  });

  // Presets buttons
  document.querySelectorAll("[data-preset]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const preset = btn.getAttribute("data-preset");
      const res = await apiFetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset_mode: preset }),
      });
      const data = await res.json();
      APP_STATE = data.state;
      renderAll();
    });
  });

  // Export & Import Backup
  const btnExport = document.getElementById("btn-export-backup");
  if (btnExport) {
    btnExport.addEventListener("click", async () => {
      const localSnap = (APP_STATE && APP_STATE.backup_snapshot) || getLocalBackup();
      let payload = localSnap;
      if (!payload) {
        const res = await apiFetch("/api/backup");
        payload = await res.json();
      }
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `math-academy-uc-avance-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });
  }

  const btnImport = document.getElementById("btn-import-backup");
  const inputImport = document.getElementById("input-import-backup");
  if (btnImport && inputImport) {
    btnImport.addEventListener("click", () => inputImport.click());
    inputImport.addEventListener("change", async (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const payload = JSON.parse(text);
        const res = await apiFetch("/api/backup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (data.state) {
          APP_STATE = data.state;
          renderAll();
        }
      } catch (err) {
        alert("No se pudo importar el archivo JSON: " + err.message);
      } finally {
        inputImport.value = "";
      }
    });
  }

  // Modals close
  document.getElementById("btn-close-lesson").addEventListener("click", closeLessonModal);
  document.getElementById("btn-open-diagnostic").addEventListener("click", openDiagnosticModal);
  document.getElementById("btn-close-diagnostic").addEventListener("click", closeDiagnosticModal);

  // Keyboard shortcuts inside Lesson Modal
  window.addEventListener("keydown", (e) => {
    const lessonOpen = !document.getElementById("lesson-modal").classList.contains("hidden");
    if (!lessonOpen) return;
    if (e.key === "Escape") {
      closeLessonModal();
    } else if (["1", "2", "3", "4"].includes(e.key)) {
      const idx = parseInt(e.key, 10) - 1;
      selectQuestionOption(idx);
    } else if (e.key === "Enter" && LESSON_SESSION.stepIndex >= 1) {
      verifyCurrentQuestion();
    }
  });

  window.addEventListener("resize", () => {
    if (document.getElementById("view-graph").classList.contains("active")) {
      drawDagEdges();
    }
  });

  fetchState();
});
