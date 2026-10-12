// smoke.js —— 离线回放冒烟测试（需要 Node）。
//
// 为什么要它：board.html 的渲染器是在浏览器里跑的，Python 侧跑不到。
// 这个脚本把 Canvas 与 DOM 全部桩掉，然后：
//   1) 逐帧调用 setFrame(0..n-1) —— 每个渲染分支都真的画一遍；
//   2) 把每个参数推到极值再调 paintConsole() —— 检查读数是否真的随参数变化；
//   3) 检查读数有没有变成 null（表达式求值坏掉时的典型症状是读数显示「—」）。
//
// 用法：
//   python scripts/generate.py all ./out
//   node scripts/smoke.js ./out
//
// 退出码 0 = 全部通过。

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const dir = process.argv[2];
if (!dir) {
  console.error('用法: node scripts/smoke.js <generate.py all 的输出目录>');
  process.exit(2);
}

function stubEl(tag) {
  return {
    tagName: (tag || 'div').toUpperCase(),
    style: {}, innerHTML: '', textContent: '', value: '', max: '', min: '', step: '',
    className: '', children: [], selected: false,
    classList: { add() {}, remove() {}, toggle() {} },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener() {}, removeEventListener() {},
    getContext() { return ctx; },
    parentElement: { clientWidth: 640 },
    offsetWidth: 0, onclick: null, onchange: null, oninput: null,
  };
}

const ctx = new Proxy({}, {
  get(t, k) {
    if (k === 'measureText') return () => ({ width: 0 });
    if (k === 'canvas') return { width: 640, height: 400 };
    if (typeof t[k] === 'undefined') return () => undefined;
    return t[k];
  },
  set(t, k, v) { t[k] = v; return true; },
});

const els = {};
const getEl = id => els[id] || (els[id] = stubEl('div'));

function runPage(file) {
  const html = fs.readFileSync(file, 'utf8');
  const blocks = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)]
    .map(m => m[1]).filter(b => b.trim());
  const head = blocks.find(b => /const\s+LESSON\s*=/.test(b));
  const engine = blocks.find(b => /CS 步骤回放引擎/.test(b));
  if (!head || !engine) return { file, ok: false, stage: 'parse', err: new Error('未找到 LESSON 或引擎脚本块') };

  const sandbox = {
    console, JSON, Math, Object, Array, String, Number, Boolean, Date, Set, Map,
    isFinite, isNaN, parseInt, parseFloat, Infinity, NaN,
    setTimeout: () => 0, clearTimeout: () => {},
    setInterval: () => 0, clearInterval: () => {},
    document: {
      readyState: 'complete', getElementById: getEl,
      createElement: t => stubEl(t), addEventListener() {}, body: stubEl('body'),
    },
    window: { devicePixelRatio: 1, addEventListener() {}, innerWidth: 1400 },
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);

  try {
    vm.runInContext(head, sandbox, { filename: 'lesson.js' });
    vm.runInContext(engine, sandbox, { filename: 'engine.js' });
  } catch (e) { return { file, ok: false, stage: 'boot', err: e }; }

  try {
    const n = vm.runInContext('steps().length', sandbox);
    for (let i = 0; i < n; i++) vm.runInContext(`setFrame(${i})`, sandbox);
    vm.runInContext('resize()', sandbox);
    vm.runInContext('paintConsole()', sandbox);
    const kind = vm.runInContext('scene().kind', sandbox);
    const params = vm.runInContext('(LESSON.console.params||[]).length', sandbox);

    const probe = vm.runInContext(`(() => {
      const c = LESSON.console || {};
      const snap = () => (c.readouts||[]).map(r => [r.id, ENV[r.id]]);
      const before = snap();
      (c.params||[]).forEach(p => { ENV[p.id] = (typeof p.value === 'number') ? p.max : p.value; });
      paintConsole();
      const after = snap();
      (c.params||[]).forEach(p => { ENV[p.id] = p.value; });
      paintConsole();
      const bad = [];
      before.forEach(([id, v]) => { if (v === null || v === undefined) bad.push('读数 ' + id + ' = null'); });
      after.forEach(([id, v]) => { if (v === null || v === undefined) bad.push('读数(max) ' + id + ' = null'); });
      return {
        bad,
        moved: JSON.stringify(before.map(x => x[1])) !== JSON.stringify(after.map(x => x[1])),
        lights: (c.lights||[]).length,
      };
    })()`, sandbox);

    if (probe.bad.length) return { file, ok: false, stage: 'console', err: new Error(probe.bad.join('; ')) };
    return { file, ok: true, frames: n, kind, params, readoutsMoved: probe.moved, lights: probe.lights };
  } catch (e) { return { file, ok: false, stage: 'frame', err: e }; }
}

const files = fs.readdirSync(dir)
  .filter(f => f.endsWith('.html') && f !== 'index.html')
  .map(f => path.join(dir, f)).sort();

let bad = 0, moved = 0, lights = 0, stale = [];
const kinds = {};
for (const f of files) {
  const r = runPage(f);
  const name = path.basename(f, '.html');
  if (!r.ok) {
    bad++;
    console.log(`✗ ${name.padEnd(18)} [${r.stage}] ${r.err && r.err.message}`);
  } else {
    if (r.readoutsMoved) moved++; else stale.push(name);
    lights += r.lights || 0;
    kinds[r.kind] = (kinds[r.kind] || 0) + 1;
  }
}
console.log(`场景覆盖: ${JSON.stringify(kinds)}`);
console.log(`读数随参数联动: ${moved}/${files.length} 页   状态灯合计: ${lights} 个`);
if (stale.length) console.log(`⚠ 读数不随参数变化（滑块可能是摆设）: ${stale.join(', ')}`);
console.log(bad ? `\nFAIL  ${bad}/${files.length}` : `\nPASS  ${files.length}/${files.length}`);
process.exit(bad ? 1 : 0);
