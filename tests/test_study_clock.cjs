const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "../static/app.js"), "utf8");
const key = "matuc_question_time:lesson-1:0";

function browser(storage = new Map([["matuc_auth_token", "test"]])) {
  const screen = { now: 0, focused: true, open: true };
  const elements = new Map();
  const document = {
    visibilityState: "visible",
    hasFocus: () => screen.focused,
    addEventListener() {},
    getElementById(id) {
      if (!elements.has(id)) {
        elements.set(id, {
          classList: {
            contains: () => !screen.open,
            add: () => { screen.open = false; },
            remove: () => { screen.open = true; },
          },
          setAttribute() {}, focus() {}, querySelectorAll: () => [],
        });
      }
      return elements.get(id);
    },
  };
  const context = vm.createContext({
    document,
    performance: { now: () => screen.now },
    sessionStorage: {
      getItem: (name) => storage.get(name),
      setItem: (name, value) => storage.set(name, value),
      removeItem: (name) => storage.delete(name),
    },
  });
  const run = (source) => vm.runInContext(source, context);
  run(app);
  run(`LESSON_SESSION = {
    id: "lesson-1", slot: "topic:lesson", stepIndex: 1, answers: [], selectedOption: 0,
    topic: { questions: [{ prompt: "Ejercicio", correct_index: 0, options: ["A", "B"] }] },
  }; syncQuestionClock();`);
  return { context, document, screen, run, storage };
}

test("closing, reloading, losing focus and idling exclude paused time", () => {
  let tab = browser();
  tab.screen.now = 5_000;
  tab.run("closeLessonModal()");
  assert.equal(tab.storage.get(key), "5000");

  tab = browser(tab.storage);
  tab.screen.now = 3_000;
  tab.screen.focused = false;
  tab.run("pauseQuestionClock()");
  tab.screen.now = 30_000;
  tab.screen.focused = true;
  tab.run("syncQuestionClock()");
  tab.screen.now = 105_000;
  tab.run("markStudyActivity()");
  tab.screen.now = 107_000;
  tab.document.visibilityState = "hidden";
  tab.run("syncQuestionClock()");
  assert.equal(tab.storage.get(key), "70000");
});

test("a failed submission keeps the timer and a confirmed answer clears it", async () => {
  const tab = browser();
  const sent = [];
  Object.assign(tab.context, {
    renderAll() {},
    renderLessonStep() {},
    apiFetch: async (_url, options) => {
      sent.push(JSON.parse(options.body));
      if (sent.length === 1) return { ok: false, json: async () => ({ error: "Reintenta" }) };
      const topic = tab.run("LESSON_SESSION.topic");
      const session = { id: "lesson-1", slot: "topic:lesson", topic, task_type: "lesson", step: 1, answers: [0] };
      return { ok: true, json: async () => ({ session, state: {} }) };
    },
  });
  tab.screen.now = 4_000;
  await tab.run("verifyCurrentQuestion()");
  assert.equal(sent[0].active_ms, 4_000);
  assert.equal(tab.storage.get(key), "4000");

  tab.screen.now = 5_000;
  await tab.run("verifyCurrentQuestion()");
  assert.equal(sent[1].active_ms, 5_000);
  assert.equal(tab.storage.has(key), false);
  assert.equal(tab.run("QUESTION_CLOCK"), null);
});
