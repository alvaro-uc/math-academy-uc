async function loadGeneral(focusSkill) {
  const status = document.getElementById("general-status");
  try {
    const res = await apiFetch("/api/general");
    if (!res.ok) throw new Error();
    const skills = await res.json();
    document.querySelectorAll("details[data-skill]").forEach(details => {
      const key = details.dataset.skill;
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
        accuracy.textContent = total ? `Primeros intentos: ${correct} de ${total} correctos.` : "Primera práctica";
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
          button.textContent = "Siguiente ejercicio";
        } catch (err) {
          feedback.textContent = err.message || "Error al guardar. Vuelve a comprobar la respuesta.";
        } finally {
          button.disabled = false;
        }
      };
      // Al avanzar, conserva las respuestas en preparación de las otras habilidades.
      if (!focusSkill || key === focusSkill) {
        details.querySelector("form")?.remove();
        details.append(form);
        if (key === focusSkill) input.focus();
      }
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
