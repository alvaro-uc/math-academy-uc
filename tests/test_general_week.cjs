const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

test("cuenta siete fechas de Santiago durante el cambio de hora y conserva días vacíos", () => {
  const script = readFileSync(path.join(__dirname, "../static/general.js"), "utf8");
  const rows = [
    ["2026-09-04T03:59:59Z", 1], // 3 de septiembre en Santiago, fuera del período
    ["2026-09-04T04:00:00Z", 1],
    ["2026-09-10T02:59:59Z", 0],
    ["2026-09-10T03:00:00Z", 1],
  ].map(([time, correct]) => ({ created_ts: Date.parse(time) / 1000, correct }));
  const days = vm.runInNewContext(script + "\ngeneralWeek(rows, new Date('2026-09-11T02:00:00Z'))", { rows });
  assert.equal(days.length, 7);
  assert.equal(days[0].day, "2026-09-04");
  assert.equal(days[0].attempts, 1);
  assert.equal(days[1].attempts, 0);
  assert.equal(days[5].attempts, 1);
  assert.equal(days[5].correct, 0);
  assert.equal(days[6].correct, 1);
});
