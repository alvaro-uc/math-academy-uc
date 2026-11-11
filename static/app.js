/* Math Academy UC — Frontend Application Logic */

let APP_STATE = null;
let SELECTED_NODE_ID = null;

let LESSON_SESSION = null;
let QUIZ_SESSION = null;
let STUDY_PENDING = false;

const DIRECT_TASKS = ["review", "prerequisite_check", "quiz_review"];
const TASK_LABELS = {
  lesson: "Lección", review: "Repaso", quiz_review: "Repaso del quiz",
  recovery: "Recuperación guiada", prerequisite_check: "Comprobación de prerrequisito",
  anticipation: "Anticipación", practice: "Práctica",
};

// Active Diagnostic Session State
let DIAG_SESSION = null;
let DIAG_SELECTION = null;
let DIAG_PENDING = false;

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
  const escaped = str.replace(/[&<>]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[character]);
  const protectedStr = escaped.replace(
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
  const diagnosticButton = document.getElementById("btn-open-diagnostic");
  const diagnosticLabels = {
    idle: "Diagnóstico del piloto",
    in_progress: "Retomar diagnóstico",
    completed: "Resultado del diagnóstico",
  };
  diagnosticButton.textContent = diagnosticLabels[APP_STATE.diagnostic] || diagnosticLabels.idle;
  const modeLabels = {mid_sem1: "Demo · Mitad del semestre 1", sem2_ready: "Demo · Inicio del semestre 2"};
  const demoLabel = document.getElementById("demo-profile-label");
  demoLabel.textContent = modeLabels[APP_STATE.preset_mode] || "";
  demoLabel.classList.toggle("hidden", !demoLabel.textContent);

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
  renderStudyCards();
  renderWeeklyActivity();
  const queueEl = document.getElementById("task-queue-list");
  const recs = APP_STATE.recommendations || [];

  if (recs.length === 0) {
    queueEl.innerHTML = `<div class="stat-card">¡Excelente! Has completado todas las tareas sugeridas por ahora.</div>`;
  } else {
    queueEl.innerHTML = recs
      .map((r) => {
        const badgeClass =
          ["review", "recovery", "prerequisite_check", "quiz_review"].includes(r.task_type)
            ? "badge-review"
            : r.task_type === "anticipation"
            ? "badge-anticipation"
            : "badge-lesson";
        return `
          <article class="task-card type-${r.task_type}">
            <div class="task-left">
              <div class="task-meta-top">
                <span class="badge ${badgeClass}">${r.tag_label}</span>
                <span class="badge badge-course">${r.course_name} · Sem ${r.semester}</span>
                <span style="font-size:0.75rem;color:var(--text-light)">⏱ ~${r.estimated_mins} min</span>
              </div>
              <div class="task-title">${r.title}</div>
              <div class="task-fire-info">${r.reason}</div>
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
  const reviewIds = new Set(APP_STATE.study.quiz_reviews);
  topics.filter((t) => t.status === "review_due").forEach((t) => reviewIds.add(t.id));

  document.getElementById("kpi-mastered").textContent = `${masteredCnt}/${topics.length}`;
  document.getElementById("kpi-available").textContent = String(frontierCnt);
  document.getElementById("kpi-reviews").textContent = String(reviewIds.size);

  // Courses progress sidebar
  const cList = document.getElementById("sidebar-courses-progress");
  cList.innerHTML = (APP_STATE.courses || [])
    .map(
      (c) => `
      <div class="course-mini-item">
        <div class="course-mini-header">
          <span>S${c.semester} · ${c.name}</span>
          <span>${c.progress_pct}% de maestría media</span>
        </div>
        <div class="course-mini-bar">
          <div class="course-mini-fill" style="width:${c.progress_pct}%; background:${c.color}"></div>
        </div>
        <small>${c.mastered_topics} de ${c.total_topics} temas dominados</small>
      </div>
    `
    )
    .join("");

  renderMath(document.getElementById("view-dashboard"));
}

function renderStudyCards() {
  const { lessons, last_lesson: last, quiz } = APP_STATE.study;
  const topics = Object.fromEntries(APP_STATE.topics.map((topic) => [topic.id, topic]));
  const cards = lessons.map((lesson) => {
    const topic = topics[lesson.topic_id];
    return `
      <article class="task-card study-card">
        <div class="task-left">
          <span class="study-meta">${TASK_LABELS[lesson.task_type]} en curso · ${topic.course_code}</span>
          <h3 class="task-title">${formatInlineMarkdown(topic.title)}</h3>
          <progress aria-label="Respuestas confirmadas" value="${lesson.answered}" max="${lesson.total}"></progress>
          <span class="study-meta">${lesson.answered} de ${lesson.total} respuestas confirmadas</span>
          ${renderPrerequisites(topic, topics)}
        </div>
        <button class="btn-primary" onclick="resumeLesson('${lesson.slot}', '${lesson.id}')">Retomar</button>
      </article>`;
  });
  const quizReady = quiz.eligible >= 2 || quiz.status !== "idle";
  const quizLabel = {
    idle: "Iniciar quiz", in_progress: "Retomar quiz", completed: "Ver resultado",
  }[quiz.status];
  const quizDescription = {
    idle: quizReady ? "Resuelve variantes nuevas de los temas que ya viste." : "Responde ejercicios de al menos dos temas del piloto para habilitarlo.",
    in_progress: `${quiz.answered} de ${quiz.total} respuestas confirmadas`,
    completed: `${quiz.total} preguntas completadas`,
  }[quiz.status];
  document.getElementById("study-cards").innerHTML = `
    ${cards.join("")}
    <article class="task-card study-card quiz-card">
      <div class="task-left">
        <span class="study-meta">MAT1107 y puente a Cálculo I</span>
        <h3 class="task-title">Quiz acumulativo</h3>
        <p class="study-meta">${quizDescription}</p>
      </div>
      <button class="btn-outline" onclick="openQuiz()" ${quizReady ? "" : "disabled"}>${quizLabel}</button>
    </article>
    ${last ? `<button class="btn-ghost study-last" onclick="resumeLesson('${last.slot}', '${last.id}')">
      Ver resultado de la última práctica
    </button>` : ""}
  `;
}

function renderWeeklyActivity() {
  const days = APP_STATE.activity_7d;
  const peak = Math.max(1, ...days.map((day) => day.xp));
  const xp = days.reduce((total, day) => total + day.xp, 0);
  const sessions = days.reduce((total, day) => total + day.sessions, 0);
  const labels = new Intl.DateTimeFormat("es-CL", { weekday: "short", day: "numeric", timeZone: "UTC" });
  document.getElementById("activity-7d").innerHTML = `
    <p class="study-meta">${xp} XP · ${sessions} ${sessions === 1 ? "sesión" : "sesiones"}</p>
    <ul class="activity-week">
      ${days.map((day) => {
        const label = labels.format(new Date(day.date));
        return `<li title="${day.xp} XP · ${day.sessions} ${day.sessions === 1 ? "sesión" : "sesiones"}">
          <span class="activity-xp">${day.xp}</span>
          <div class="activity-track" aria-hidden="true"><div style="height:${100 * day.xp / peak}%"></div></div>
          <time datetime="${day.date}">${label}</time>
        </li>`;
      }).join("")}
    </ul>`;
}

function renderPrerequisites(topic, byId) {
  if (!topic.prereqs.length) return '<p class="study-meta">Sin prerrequisitos</p>';
  return `<div class="study-meta">
    <strong>Prerrequisitos</strong>
    <ul class="prereq-list">${topic.prereqs.map((id) => `
      <li>${formatInlineMarkdown(byId[id].title)} · ${topic.met_prereqs.includes(id) ? "Cumplido" : "Pendiente"}</li>
    `).join("")}</ul>
  </div>`;
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
                ? "↻ Repaso pendiente"
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
  inspector.innerHTML = `
    <div style="margin-bottom:0.65rem">
      <span class="badge badge-course">${t.course_name} · Semestre ${t.semester}</span>
    </div>
    <h3 style="font-size:1.02rem;margin-bottom:0.5rem">${t.title}</h3>
    <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.85rem">
      Maestría: <strong>${Math.round(t.mastery * 100)}%</strong> · Estabilidad: <strong>${t.stability_days} días</strong> · Recompensa: <strong>+${t.xp} XP</strong>
    </div>

    <div style="font-size:0.8rem;margin-bottom:0.75rem">
      ${renderPrerequisites(t, byId)}
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

async function requestStudy(payload, showModal = false) {
  if (STUDY_PENDING) return;
  STUDY_PENDING = true;
  const modal = document.getElementById("lesson-modal");
  const footer = document.getElementById("lesson-footer");
  const buttons = [...footer.querySelectorAll("button:enabled")];
  buttons.forEach((button) => { button.disabled = true; });
  document.getElementById("study-status").textContent = "";
  document.getElementById("lesson-status").textContent = "";
  const token = getAuthToken();
  try {
    const res = await apiFetch("/api/study", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, client_backup: getLocalBackup() }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "No se pudo guardar el paso.");
    if (getAuthToken() !== token) return;
    APP_STATE = data.state;
    renderAll();
    if (payload.kind === "quiz") {
      QUIZ_SESSION = { ...data.session, selectedOption: null };
      LESSON_SESSION = null;
    } else {
      const { topic, task_type, answers, step, result, slot, id } = data.session;
      LESSON_SESSION = {
        topic, id, slot, answers,
        directRetrieval: DIRECT_TASKS.includes(task_type),
        stepIndex: step,
        selectedOption: step > 0 && step <= answers.length ? answers[step - 1] : null,
        answeredCurrent: step > 0 && step <= answers.length,
        correctCount: answers.filter((answer, index) => answer === topic.questions[index].correct_index).length,
        completionResponse: result,
      };
      QUIZ_SESSION = null;
    }
    if (showModal) {
      modal.classList.remove("hidden");
      modal.setAttribute("aria-hidden", "false");
    }
    if (!modal.classList.contains("hidden")) {
      if (QUIZ_SESSION) renderQuiz();
      else renderLessonStep();
      document.getElementById("lesson-title").focus();
    }
  } catch (error) {
    if (error.message === "Unauthorized") return;
    const target = modal.classList.contains("hidden") ? "study-status" : "lesson-status";
    document.getElementById(target).textContent = error.message || "No se pudo conectar. Intenta de nuevo.";
  } finally {
    STUDY_PENDING = false;
    buttons.forEach((button) => { button.disabled = false; });
  }
}

function startLesson(topicId, taskType = "lesson") {
  return requestStudy({ kind: "lesson", action: "open", topic_id: topicId, task_type: taskType }, true);
}

function resumeLesson(slot, sessionId) {
  return requestStudy({ kind: "lesson", action: "resume", slot, session_id: sessionId }, true);
}

function openQuiz(restartFrom) {
  return requestStudy({ kind: "quiz", action: "open", restart_from: restartFrom }, true);
}

function closeLessonModal() {
  const modal = document.getElementById("lesson-modal");
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
}

function renderStudyOptions(question, choice, confirmed = false) {
  return `<div class="options-grid" id="question-options">${question.options.map((option, index) => {
    let state = choice === index ? "selected" : "";
    if (confirmed && index === question.correct_index) state = "correct";
    else if (confirmed && index === choice) state = "wrong";
    return `<button class="option-btn ${state}" onclick="selectQuestionOption(${index})"
      aria-pressed="${choice === index}" ${confirmed ? "disabled" : ""}>
      <span class="option-key">${"ABCD"[index] || index + 1}</span>
      <span>${formatInlineMarkdown(option)}</span>
    </button>`;
  }).join("")}</div>`;
}

function renderQuiz() {
  const session = QUIZ_SESSION;
  const body = document.getElementById("lesson-body");
  const footer = document.getElementById("lesson-footer");
  document.getElementById("lesson-course-tag").textContent = "MAT1107 y puente a Cálculo I";
  document.getElementById("lesson-title").textContent = "Quiz acumulativo";
  document.getElementById("lesson-stepper").textContent = `${session.answered} / ${session.total} respondidas`;
  if (session.status === "completed") {
    const correct = session.results.filter((item) => item.correct).length;
    body.innerHTML = `
      <p><strong>${correct} de ${session.total} correctas</strong> · +${session.xp_earned} XP</p>
      <p class="study-meta">${correct === session.total ? "Acertaste en todos los temas del quiz." : "La cola incluye un repaso por cada tema en el que fallaste."}</p>
      ${session.results.map((item) => `
        <div class="feedback-banner quiz-feedback ${item.correct ? "ok" : "err"}">
          <strong>${item.correct ? "✓" : "✗"} ${formatInlineMarkdown(item.title)}</strong>
          <p>${formatInlineMarkdown(item.prompt)}</p>
          <p>Tu respuesta · ${formatInlineMarkdown(item.chosen)}</p>
          <p>Respuesta correcta · ${formatInlineMarkdown(item.correct_answer)}</p>
          <p>${formatInlineMarkdown(item.explanation)}</p>
        </div>`
      ).join("")}`;
    footer.innerHTML = `
      <button class="btn-outline" onclick="openQuiz('${session.id}')">Nuevo quiz</button>
      <button class="btn-primary" onclick="closeLessonModal()">Volver al panel</button>`;
  } else {
    body.innerHTML = `
      <p class="study-meta">Pregunta ${session.answered + 1} de ${session.total}</p>
      <div class="question-prompt">${formatInlineMarkdown(session.question.prompt)}</div>
      ${renderStudyOptions(session.question, session.selectedOption)}`;
    footer.innerHTML = `
      <span class="study-meta">Soluciones disponibles al terminar</span>
      <button class="btn-primary" id="btn-Verify-Answer" onclick="verifyCurrentQuestion()" disabled>
        ${session.answered + 1 === session.total ? "Finalizar quiz" : "Confirmar y continuar"}
      </button>`;
  }
  body.scrollTop = 0;
  renderMath(body);
}

function renderLessonStep() {
  const { topic, stepIndex, directRetrieval } = LESSON_SESSION;
  const totalQuestions = topic.questions.length;

  document.getElementById("lesson-course-tag").textContent = `${topic.course_name} · Semestre ${topic.semester}`;
  document.getElementById("lesson-title").textContent = topic.title;

  // Los repasos y las comprobaciones comienzan con el primer problema.
  const totalSteps = 1 + totalQuestions;
  const stepperEl = document.getElementById("lesson-stepper");
  let pillsHtml = "";
  for (let i = directRetrieval ? 1 : 0; i < totalSteps; i++) {
    const cls = i < stepIndex ? "done" : i === stepIndex ? "active" : "";
    pillsHtml += `<span class="step-pill ${cls}"></span>`;
  }
  stepperEl.innerHTML = pillsHtml;

  const bodyEl = document.getElementById("lesson-body");
  const footerEl = document.getElementById("lesson-footer");
  bodyEl.scrollTop = 0;

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
    const { selectedOption, answeredCurrent } = LESSON_SESSION;
    const correct = selectedOption === q.correct_index;

    bodyEl.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.55rem">
        <span class="badge ${q.is_parametric ? "badge-anticipation" : "badge-lesson"}">
          Problema ${qIdx + 1} de ${totalQuestions} · ${
      q.is_parametric ? "Generador Paramétrico Dinámico" : "Problema Tipo Interrogación UC"
    }
        </span>
        ${directRetrieval ? "" : '<button class="btn-ghost" onclick="toggleHint()">💡 Ver Pista</button>'}
      </div>

      <div class="question-prompt">${formatInlineMarkdown(q.prompt)}</div>

      ${renderStudyOptions(q, selectedOption, answeredCurrent)}

      ${directRetrieval ? "" : `<div id="question-hint" class="hint-box" style="display:none">
        <strong>Pista:</strong> ${formatInlineMarkdown(q.hint)}
      </div>`}

      ${answeredCurrent ? `
        <div class="feedback-banner ${correct ? "ok" : "err"}">
          <strong>${correct ? "✓ ¡Correcto!" : "✗ Respuesta incorrecta."}</strong>
          <p>${formatInlineMarkdown(q.explanation)}</p>
        </div>` : ""}
    `;

    footerEl.innerHTML = `
      <span style="font-size:0.8rem;color:var(--text-muted)">Atajo: teclas 1–4 para elegir, Enter para verificar</span>
      <div style="display:flex;gap:0.5rem">
        <button class="btn-primary" id="btn-Verify-Answer" onclick="verifyCurrentQuestion()" ${selectedOption === null ? "disabled" : ""}>
          ${answeredCurrent ? (stepIndex === totalQuestions ? "Finalizar y registrar XP" : "Siguiente problema") : "Verificar respuesta"}
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
  const session = QUIZ_SESSION || LESSON_SESSION;
  if (STUDY_PENDING || !session || session.answeredCurrent) return;
  const question = QUIZ_SESSION ? session.question : session.topic.questions[session.stepIndex - 1];
  if (!question || idx >= question.options.length) return;
  session.selectedOption = idx;
  document.querySelectorAll("#question-options .option-btn").forEach((btn, i) => {
    btn.classList.toggle("selected", i === idx);
    btn.setAttribute("aria-pressed", String(i === idx));
  });
  document.getElementById("btn-Verify-Answer").disabled = false;
}

function verifyCurrentQuestion() {
  const session = QUIZ_SESSION || LESSON_SESSION;
  if (!session || session.selectedOption === null) return;
  if (QUIZ_SESSION) {
    return requestStudy({
      kind: "quiz", action: "advance", session_id: session.id,
      answered: session.answered, choice: session.selectedOption,
    });
  }
  if (session.answeredCurrent) return nextLessonStep();
  return nextLessonStep({ choice: session.selectedOption });
}

function nextLessonStep(answer = {}) {
  const session = LESSON_SESSION;
  return requestStudy({
    kind: "lesson", action: "advance", slot: session.slot, session_id: session.id,
    step: session.stepIndex, answered: session.answers.length, ...answer,
  });
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
        <strong style="color:#15803d">Crédito de repaso FIRe</strong>
        <p style="font-size:0.83rem;color:#166534;margin-top:0.2rem">
          Tus aciertos aportaron evidencia para aplazar estos repasos.
        </p>
        <ul style="padding-left:1.2rem;margin-top:0.4rem;font-size:0.83rem;color:#14532d">
          ${res.implicit_boosted
            .map(
              (b) => {
                const operations = [...new Set((b.evidence || []).flatMap((item) => item.operations))];
                const change = b.postponed_days === undefined
                  ? `estabilidad registrada de ${b.new_stability_days} días`
                  : `repaso aplazado ${b.postponed_days.toLocaleString("es-CL")} días`;
                return `<li><strong>${formatInlineMarkdown(b.title)}</strong> · ${change}
                  ${operations.length ? `<br>${operations.map(formatInlineMarkdown).join(" ")}` : ""}</li>`;
              }
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

      <div class="lesson-result-grid">
        <div class="kpi-box">
          <div class="kpi-val" style="color:var(--emerald)">+${res ? res.xp_earned : 0} XP</div>
          <div class="kpi-label">XP Ganado</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-val">${res ? Math.round(res.new_mastery * 100) : 0}%</div>
          <div class="kpi-label">Maestría del Tópico</div>
        </div>
        ${res && res.review_scheduled ? `
          <div class="kpi-box">
            <div class="kpi-val">${res.new_stability_days} d</div>
            <div class="kpi-label">${res.recovery_scheduled ? "Próxima recuperación" : "Próximo repaso"}</div>
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
  const modal = document.getElementById("diagnostic-modal");
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
  if (DIAG_PENDING) return;
  DIAG_SESSION = null;
  DIAG_SELECTION = null;
  renderDiagnosticStep();
  await requestDiagnostic();
}

function closeDiagnosticModal() {
  const modal = document.getElementById("diagnostic-modal");
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
}

async function requestDiagnostic(payload) {
  if (DIAG_PENDING) return;
  DIAG_PENDING = true;
  renderDiagnosticStep();
  let error = "";
  try {
    const options = payload && {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, client_backup: getLocalBackup() }),
    };
    const res = await apiFetch("/api/diagnostic", options);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    DIAG_SESSION = payload ? data.diagnostic : data;
    DIAG_SELECTION = null;
    if (data.state) {
      APP_STATE = data.state;
      renderAll();
    }
  } catch (_) {
    error = "No se pudo actualizar el diagnóstico. Vuelve a intentarlo.";
  } finally {
    DIAG_PENDING = false;
    renderDiagnosticStep(error);
  }
}

function renderDiagnosticStep(error = "") {
  const bodyEl = document.getElementById("diagnostic-body");
  const footerEl = document.getElementById("diagnostic-footer");
  const disabled = DIAG_PENDING ? "disabled" : "";
  const errorMessage = error ? `<p role="alert">${error}</p>` : "";
  if (!DIAG_SESSION) {
    bodyEl.innerHTML = errorMessage || '<p role="status">Cargando diagnóstico…</p>';
    footerEl.innerHTML = error ? '<button class="btn-primary" onclick="requestDiagnostic()">Reintentar</button>' : "";
    return;
  }
  const { status, answered, max_questions: limit, item } = DIAG_SESSION;
  if (status === "idle") {
    bodyEl.innerHTML = `
      <p>El diagnóstico se adapta a tus respuestas y dura hasta ${limit} preguntas.</p>
      <p>Puedes cerrar y retomar después. Las respuestas se guardan al confirmar.</p>
      ${errorMessage}
    `;
    footerEl.innerHTML = `<button class="btn-primary" ${disabled} onclick="startDiagnostic()">Empezar</button>`;
    return;
  }
  if (status === "completed") {
    renderDiagnosticResult(bodyEl, footerEl, errorMessage, disabled);
    return;
  }

  const q = item.question;
  const keys = ["A", "B", "C", "D"];
  const reasons = {
    initial: "Pregunta inicial",
    successor: "Comprobación del tema siguiente",
    prerequisite: "Comprobación de un prerrequisito",
    confirm_inference: "Confirmación de una inferencia",
    resolve_conflict: "Segunda pregunta para aclarar evidencia contradictoria",
  };
  bodyEl.innerHTML = `
    <p><span class="badge badge-lesson">Pregunta ${answered + 1} · Máximo ${limit}</span></p>
    <h4>${item.topic_title}</h4>
    <p>${reasons[item.reason]}</p>
    <div class="question-prompt">${formatInlineMarkdown(q.prompt)}</div>
    <div class="options-grid" id="diag-options">
      ${q.options
        .map(
          (opt, i) => `
        <button class="option-btn ${i === DIAG_SELECTION ? "selected" : ""}"
                aria-pressed="${i === DIAG_SELECTION}" ${disabled} onclick="selectDiagOption(${i})">
          <span class="option-key">${keys[i]}</span>
          <span>${formatInlineMarkdown(opt)}</span>
        </button>
      `
        )
        .join("")}
    </div>
    ${errorMessage}
  `;

  footerEl.innerHTML = `
    <button class="btn-ghost" ${disabled} onclick="submitDiagQuestion(null)">Omitir pregunta</button>
    <button id="btn-confirm-diagnostic" class="btn-primary" ${DIAG_PENDING || DIAG_SELECTION === null ? "disabled" : ""}
            onclick="submitDiagQuestion(DIAG_SELECTION)">Confirmar y continuar</button>
  `;
  renderMath(bodyEl);
}

function selectDiagOption(i) {
  if (DIAG_PENDING) return;
  DIAG_SELECTION = i;
  document.querySelectorAll("#diag-options .option-btn").forEach((btn, idx) => {
    btn.classList.toggle("selected", idx === i);
    btn.setAttribute("aria-pressed", String(idx === i));
  });
  document.getElementById("btn-confirm-diagnostic").disabled = false;
}

function startDiagnostic() {
  return requestDiagnostic({ start: true, restart_from: DIAG_SESSION.session_id });
}

function submitDiagQuestion(choice) {
  return requestDiagnostic({
    session_id: DIAG_SESSION.session_id,
    answered: DIAG_SESSION.answered,
    choice,
  });
}

function diagnosticEvidenceLabel(item) {
  if (item.kind === "direct") {
    const attempts = item.correct + item.incorrect;
    const result = item.correct === attempts ? "Acierto"
      : item.correct === 0 ? "Por practicar" : "Evidencia mixta";
    return `Evidencia directa · ${result} · ${item.correct}/${attempts} aciertos`;
  }
  if (item.kind === "inferred") {
    if (item.positive_from.length && item.negative_from.length) return "Inferencia contradictoria";
    return item.positive_from.length ? "Inferencia favorable pendiente de confirmar" : "Posible laguna inferida";
  }
  return "Sin evaluar";
}

function renderDiagnosticResult(bodyEl, footerEl, errorMessage, disabled) {
  const rows = DIAG_SESSION.evidence;
  const correct = rows.reduce((sum, item) => sum + item.correct, 0);
  const scored = rows.reduce((sum, item) => sum + item.correct + item.incorrect, 0);
  bodyEl.innerHTML = `
    <h4>Resultado del piloto</h4>
    <p>${scored ? `${correct} de ${scored} respuestas correctas` : "Sin respuestas puntuadas"} · ${DIAG_SESSION.answered - scored} omitidas</p>
    <ul class="diagnostic-evidence">
      ${rows.map(item => `<li><strong>${item.topic_title}</strong><br>${diagnosticEvidenceLabel(item)}</li>`).join("")}
    </ul>
    ${errorMessage}
  `;
  footerEl.innerHTML = `
    <button class="btn-ghost" ${disabled} onclick="startDiagnostic()">Nuevo diagnóstico</button>
    <button class="btn-primary" onclick="closeDiagnosticModal()">Volver al panel</button>
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
    if (!document.getElementById("diagnostic-modal").classList.contains("hidden")) {
      if (e.key === "Escape") closeDiagnosticModal();
      return;
    }
    const lessonOpen = !document.getElementById("lesson-modal").classList.contains("hidden");
    if (!lessonOpen) return;
    if (e.key === "Escape") {
      closeLessonModal();
    } else if (["1", "2", "3", "4"].includes(e.key)) {
      const idx = parseInt(e.key, 10) - 1;
      selectQuestionOption(idx);
    } else if (e.key === "Enter" && !e.target.closest("button")) {
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
