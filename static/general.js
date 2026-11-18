const generalDate = new Intl.DateTimeFormat("sv-SE", {
  timeZone: "America/Santiago", year: "numeric", month: "2-digit", day: "2-digit",
});

function generalWeek(recent, now = new Date()) {
  const last = Date.parse(generalDate.format(now) + "T00:00:00Z");
  const days = new Map();
  for (let i = 6; i >= 0; i--) {
    const day = new Date(last - i * 86400000).toISOString().slice(0, 10);
    days.set(day, { day, attempts: 0, correct: 0 });
  }
  for (const row of recent) {
    const bucket = days.get(generalDate.format(row.created_ts * 1000));
    if (bucket) {
      bucket.attempts++;
      bucket.correct += row.correct;
    }
  }
  return [...days.values()];
}

function generalRow(label, value) {
  const row = document.createElement("li");
  const metric = document.createElement("strong");
  metric.textContent = value;
  row.append(label, metric);
  return row;
}

async function fetchGeneralOverview() {
  const response = await apiFetch("/api/general");
  if (!response.ok) throw new Error("Error al cargar el progreso.");
  const skills = await response.json();
  const { goal, recent } = skills._summary;
  document.getElementById("general-goal").textContent =
    `Meta de práctica: ${goal} aciertos acumulados al primer intento en cada habilidad.`;
  const rows = Object.entries(skills).filter(([key]) => key !== "_summary").map(([, skill]) =>
    generalRow(skill.title, skill.correct >= goal ? "Completada" : `${skill.correct} / ${goal}`));
  document.getElementById("general-progress").replaceChildren(...rows);
  const weekday = new Intl.DateTimeFormat("es-CL", { timeZone: "UTC", weekday: "short", day: "numeric", month: "short" });
  document.getElementById("general-week").replaceChildren(...generalWeek(recent).map(day =>
    generalRow(weekday.format(new Date(day.day + "T00:00:00Z")), day.attempts
      ? `${day.correct} de ${day.attempts} correctos` : "Sin intentos")));
  return skills;
}

async function loadGeneral(focusSkill) {
  const status = document.getElementById("general-status");
  try {
    const skills = await fetchGeneralOverview();
    const goal = skills._summary.goal;
    document.querySelectorAll("details[data-skill]").forEach(details => {
      const key = details.dataset.skill;
      if (focusSkill && key !== focusSkill) return;
      const skill = skills[key];
      const form = document.createElement("form");
      form.innerHTML = `
        <h3></h3><p class="example"></p><p class="accuracy"></p>
        <label><span></span> <input type="number" step="1" required></label>
        <button class="btn-primary" type="submit">Comprobar</button>
        <p role="status"></p>`;
      form.querySelector("h3").textContent = skill.title;
      form.querySelector(".example").textContent = skill.example;
      const accuracy = form.querySelector(".accuracy");
      const showCount = (correct, total) => {
        const progress = correct >= goal ? "Meta completada. Puedes pasar a otra habilidad o practicar más." :
          `Faltan ${goal - correct} aciertos para completar esta práctica.`;
        accuracy.textContent = `Primeros intentos: ${correct} de ${total} correctos. ${progress}`;
      };
      showCount(skill.correct, skill.number - 1);
      form.querySelector("label span").textContent = skill.prompt;
      const input = form.querySelector("input");
      const button = form.querySelector("button");
      const feedback = form.querySelector("[role=status]");
      form.onsubmit = async event => {
        event.preventDefault();
        if (input.disabled) {
          await loadGeneral(key);
          return;
        }
        button.disabled = true;
        try {
          const response = await apiFetch("/api/general", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skill: key, number: skill.number, answer: input.valueAsNumber }),
          });
          const result = await response.json();
          if (!response.ok) throw new Error(result.error);
          input.value = result.answer;
          input.disabled = true;
          showCount(skill.correct + Number(result.correct), skill.number);
          feedback.textContent = (result.correct ? "Correcto. " : `Respuesta correcta: ${result.expected}. `) + result.explanation;
          button.textContent = skill.correct + Number(result.correct) >= goal ? "Seguir practicando (opcional)" : "Siguiente ejercicio";
          try {
            await fetchGeneralOverview();
            status.textContent = "";
          } catch (err) {
            if (err.message !== "Unauthorized") status.textContent = "Respuesta guardada. Recarga para actualizar la actividad.";
          }
        } catch (err) {
          feedback.textContent = err.message || "Error al guardar. Vuelve a comprobar la respuesta.";
        } finally {
          button.disabled = false;
        }
      };
      // Al avanzar, conserva las respuestas en preparación de las otras habilidades.
      details.querySelector("form")?.remove();
      details.append(form);
      if (key === focusSkill) input.focus();
    });
    status.textContent = "";
    hideAuthGate();
  } catch (err) {
    if (err.message === "Unauthorized") return;
    const message = "No se pudo cargar la práctica. Recarga la página para reintentar.";
    status.textContent = message;
    if (!document.getElementById("auth-gate").classList.contains("hidden")) showAuthGate(message);
  }
}
