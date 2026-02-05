/**
 * METACODE 使用範例與測試
 * 展示如何使用元代碼進行跨域研究
 */

import MetaCode from './metacode_core.js';
import fs from 'fs';
import path from 'path';

// ===== 顏色輸出 =====
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(msg, color = 'reset') {
  console.log(`${colors[color]}${msg}${colors.reset}`);
}

// ===== 場景 1：數學 Hausdorff 維度研究 =====
async function scenario1_Math(meta) {
  log('\n╔══════════════════════════════════════╗', 'cyan');
  log('║  場景 1：Hausdorff 維度跨域映射      ║', 'cyan');
  log('╚══════════════════════════════════════╝', 'cyan');

  // 創建 Hausdorff 維度粒子
  const hausdorff = meta.createParticle({
    domain: 'math',
    mag: 1.0,
    zoom: 0.85,      // 高精度觀察
    surprisal: 0.15, // 低驚奇度（已知理論）
    conf: 0.95,      // 高信度
    N: 100,          // 理論層級堆疊
    eta: 0.92,       // 高效率（純數學）
    tags: ['math', 'hausdorff', 'dimension', 'fractal']
  });

  log(`\n✓ 創建 Hausdorff 粒子: ${hausdorff.id.substring(0, 40)}...`, 'green');
  log(`  Zoom: ${hausdorff.cap.axes.zoom}`, 'yellow');
  log(`  Present capacity: ${hausdorff.amplify.present.toFixed(2)}`, 'yellow');

  // 演化
  meta.evolveParticle(hausdorff.id, { N: 150, eta: 0.93 });
  log(`\n✓ 演化後 capacity: ${hausdorff.amplify.present.toFixed(2)}`, 'green');

  return hausdorff;
}

// ===== 場景 2：儲存系統 NAND 映射 =====
async function scenario2_Storage(meta) {
  log('\n╔══════════════════════════════════════╗', 'cyan');
  log('║  場景 2：NAND Flash 儲存粒子         ║', 'cyan');
  log('╚══════════════════════════════════════╝', 'cyan');

  // SLC (Single-Level Cell)
  const slc = meta.createParticle({
    domain: 'storage',
    mag: 1.0,
    zoom: 0.6,       // 中等尺度
    surprisal: 0.2,  // 已知技術
    conf: 0.98,      // 極高可靠性
    N: 50,           // 單層堆疊
    eta: 0.95,       // 高效率
    tags: ['storage', 'nand', 'slc', '1bit']
  });

  // MLC (Multi-Level Cell)
  const mlc = meta.createParticle({
    domain: 'storage',
    mag: 1.0,
    zoom: 0.62,
    surprisal: 0.25,
    conf: 0.92,      // 稍低可靠性
    N: 100,          // 2 bit = 雙層
    eta: 0.85,       // 效率降低
    tags: ['storage', 'nand', 'mlc', '2bit']
  });

  // TLC (Triple-Level Cell)
  const tlc = meta.createParticle({
    domain: 'storage',
    mag: 1.0,
    zoom: 0.64,
    surprisal: 0.3,
    conf: 0.88,      // 更低可靠性
    N: 150,          // 3 bit = 三層
    eta: 0.75,       // 效率再降
    tags: ['storage', 'nand', 'tlc', '3bit']
  });

  log(`\n✓ 創建 3 種 NAND 粒子:`, 'green');
  log(`  SLC: N=${slc.amplify.N}, η=${slc.amplify.eta}, Present=${slc.amplify.present.toFixed(2)}`, 'yellow');
  log(`  MLC: N=${mlc.amplify.N}, η=${mlc.amplify.eta}, Present=${mlc.amplify.present.toFixed(2)}`, 'yellow');
  log(`  TLC: N=${tlc.amplify.N}, η=${tlc.amplify.eta}, Present=${tlc.amplify.present.toFixed(2)}`, 'yellow');

  // 建立演化關聯
  meta.createLink(slc.id, mlc.id, 'evolves-to');
  meta.createLink(mlc.id, tlc.id, 'evolves-to');

  log(`\n✓ 建立演化鏈: SLC → MLC → TLC`, 'green');

  return { slc, mlc, tlc };
}

// ===== 場景 3：CPU/GPU 計算粒子 =====
async function scenario3_Compute(meta) {
  log('\n╔══════════════════════════════════════╗', 'cyan');
  log('║  場景 3：CPU vs GPU 計算架構         ║', 'cyan');
  log('╚══════════════════════════════════════╝', 'cyan');

  // CPU 粒子
  const cpu = meta.createParticle({
    domain: 'compute',
    mag: 1.0,
    zoom: 0.7,
    surprisal: 0.1,
    conf: 0.99,
    N: 16,           // 16 核心
    eta: 0.88,       // 高效但不並行
    tags: ['compute', 'cpu', 'serial', 'x86']
  });

  // GPU 粒子
  const gpu = meta.createParticle({
    domain: 'compute',
    mag: 1.0,
    zoom: 0.72,
    surprisal: 0.15,
    conf: 0.95,
    N: 5120,         // 5120 CUDA cores
    eta: 0.65,       // 並行但有開銷
    tags: ['compute', 'gpu', 'parallel', 'cuda']
  });

  log(`\n✓ 創建計算粒子:`, 'green');
  log(`  CPU: N=${cpu.amplify.N}, η=${cpu.amplify.eta}, Present=${cpu.amplify.present.toFixed(2)}`, 'yellow');
  log(`  GPU: N=${gpu.amplify.N}, η=${gpu.amplify.eta}, Present=${gpu.amplify.present.toFixed(2)}`, 'yellow');

  // 比較
  const ratio = gpu.amplify.present / cpu.amplify.present;
  log(`\n✓ GPU/CPU 效能比: ${ratio.toFixed(2)}x`, 'magenta');

  // 建立互補關聯
  meta.createLink(cpu.id, gpu.id, 'complementary');

  return { cpu, gpu };
}

// ===== 場景 4：跨域一致性檢測 =====
async function scenario4_CrossDomain(meta, math, storage, compute) {
  log('\n╔══════════════════════════════════════╗', 'cyan');
  log('║  場景 4：跨域一致性映射              ║', 'cyan');
  log('╚══════════════════════════════════════╝', 'cyan');

  // 創建一個新粒子，看它會被分類到哪裡
  const mystery = meta.createParticle({
    domain: 'unknown',
    mag: 1.0,
    zoom: 0.7,       // 接近 compute
    surprisal: 0.25,
    conf: 0.90,
    tags: ['mystery']
  });

  log(`\n✓ 創建神秘粒子: ${mystery.id.substring(0, 40)}...`, 'green');

  // 與各域粒子進行匹配
  const matches = [
    { domain: 'math', particle: math, score: meta.calculateSimilarity(mystery, math) },
    { domain: 'storage', particle: storage.slc, score: meta.calculateSimilarity(mystery, storage.slc) },
    { domain: 'compute', particle: compute.cpu, score: meta.calculateSimilarity(mystery, compute.cpu) }
  ].sort((a, b) => b.score - a.score);

  log(`\n✓ 匹配結果:`, 'yellow');
  matches.forEach((m, i) => {
    log(`  ${i + 1}. ${m.domain}: ${(m.score * 100).toFixed(2)}%`, 'cyan');
  });

  const best = matches[0];
  log(`\n✓ 最佳匹配: ${best.domain} (${(best.score * 100).toFixed(2)}%)`, 'magenta');

  // 決策
  const decision = meta.matchParticle(mystery);
  log(`✓ 決策: ${decision.decision} - ${decision.reason}`, 'green');

  return mystery;
}

// ===== 場景 5：粒子演化與傳播 =====
async function scenario5_Evolution(meta, hausdorff) {
  log('\n╔══════════════════════════════════════╗', 'cyan');
  log('║  場景 5：演化傳播與牽一髮動全身      ║', 'cyan');
  log('╚══════════════════════════════════════╝', 'cyan');

  // 找出所有依賴 hausdorff 的粒子
  const beforeMetrics = meta.calculateMetrics();
  
  log(`\n✓ 演化前狀態:`, 'yellow');
  log(`  Total particles: ${beforeMetrics.total_particles}`, 'cyan');
  log(`  Total links: ${beforeMetrics.total_links}`, 'cyan');
  log(`  Avg η: ${beforeMetrics.avg_eta.toFixed(3)}`, 'cyan');

  // 演化 hausdorff
  meta.evolveParticle(hausdorff.id, { N: 200, eta: 0.95 });
  log(`\n✓ Hausdorff 演化: N=200, η=0.95`, 'green');

  // 傳播變化
  const affected = meta.propagate(hausdorff.id);
  log(`✓ 影響了 ${affected.length} 個粒子`, 'green');

  const afterMetrics = meta.calculateMetrics();
  log(`\n✓ 演化後狀態:`, 'yellow');
  log(`  Avg η: ${afterMetrics.avg_eta.toFixed(3)} (變化: ${(afterMetrics.avg_eta - beforeMetrics.avg_eta).toFixed(4)})`, 'cyan');
}

// ===== 場景 6：自我驗證與指標 =====
async function scenario6_Verification(meta) {
  log('\n╔══════════════════════════════════════╗', 'cyan');
  log('║  場景 6：系統自我驗證與指標          ║', 'cyan');
  log('╚══════════════════════════════════════╝', 'cyan');

  // 驗證
  const verification = meta.verify();
  log(`\n✓ 自我驗證: ${verification.ok ? 'PASSED ✓' : 'FAILED ✗'}`, verification.ok ? 'green' : 'yellow');

  if (verification.errors.length > 0) {
    log(`  發現 ${verification.errors.length} 個問題:`, 'yellow');
    verification.errors.forEach(err => {
      log(`    - ${err.type}: ${err.message}`, 'yellow');
    });
  }

  // 指標
  const metrics = meta.calculateMetrics();
  log(`\n✓ 系統指標:`, 'magenta');
  log(`  ┌─────────────────────────────────┐`, 'cyan');
  log(`  │ Total Particles: ${String(metrics.total_particles).padEnd(14)} │`, 'cyan');
  log(`  │ Total Links:     ${String(metrics.total_links).padEnd(14)} │`, 'cyan');
  log(`  │ Total Cycles:    ${String(metrics.total_cycles).padEnd(14)} │`, 'cyan');
  log(`  │ Coverage:        ${(metrics.coverage * 100).toFixed(2).padEnd(14)}% │`, 'cyan');
  log(`  │ Spawn Rate:      ${(metrics.spawn_rate * 100).toFixed(2).padEnd(14)}% │`, 'cyan');
  log(`  │ Avg η:           ${metrics.avg_eta.toFixed(4).padEnd(14)} │`, 'cyan');
  log(`  │ Domains:         ${metrics.domains.join(', ').padEnd(14)} │`, 'cyan');
  log(`  └─────────────────────────────────┘`, 'cyan');
}

// ===== 場景 7：導出與持久化 =====
async function scenario7_Export(meta) {
  log('\n╔══════════════════════════════════════╗', 'cyan');
  log('║  場景 7：導出與文件生成              ║', 'cyan');
  log('╚══════════════════════════════════════╝', 'cyan');

  // 導出
  const exported = meta.export();

  // 創建目錄
  const dataDir = './data';
  ['particles', 'links', 'cycles', 'journal'].forEach(sub => {
    const dir = path.join(dataDir, sub);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });

  // 寫入文件
  const timestamp = new Date().toISOString().split('T')[0];

  // 1. Particles
  const particlesPath = path.join(dataDir, 'particles', `MRLsmall.${timestamp}.jsonl`);
  const particlesData = exported.particles.map(p => JSON.stringify(p)).join('\n');
  fs.writeFileSync(particlesPath, particlesData);
  log(`\n✓ Particles 已寫入: ${particlesPath}`, 'green');

  // 2. Links
  const linksPath = path.join(dataDir, 'links', `MRLsmall.links.${timestamp}.jsonl`);
  const linksData = exported.links.map(l => JSON.stringify(l)).join('\n');
  fs.writeFileSync(linksPath, linksData);
  log(`✓ Links 已寫入: ${linksPath}`, 'green');

  // 3. Cycles
  const cyclesPath = path.join(dataDir, 'cycles', `MRLsmall.cycles.${timestamp}.jsonl`);
  const cyclesData = exported.cycles.map(c => JSON.stringify(c)).join('\n');
  fs.writeFileSync(cyclesPath, cyclesData);
  log(`✓ Cycles 已寫入: ${cyclesPath}`, 'green');

  // 4. Journal
  const journalPath = path.join(dataDir, 'journal', `MRLsmall.journal.${timestamp}.jsonl`);
  const journalData = exported.journal.map(j => JSON.stringify(j)).join('\n');
  fs.writeFileSync(journalPath, journalData);
  log(`✓ Journal 已寫入: ${journalPath}`, 'green');

  // 5. 完整導出
  const fullPath = path.join(dataDir, `MetaCode.export.${timestamp}.json`);
  fs.writeFileSync(fullPath, JSON.stringify(exported, null, 2));
  log(`✓ 完整導出已寫入: ${fullPath}`, 'green');

  log(`\n✓ 總計寫入 ${exported.particles.length} 個粒子`, 'magenta');
  log(`✓ 總計寫入 ${exported.links.length} 個關聯`, 'magenta');
  log(`✓ 總計寫入 ${exported.cycles.length} 個演化週期`, 'magenta');
  log(`✓ 總計寫入 ${exported.journal.length} 個事件`, 'magenta');

  return exported;
}

// ===== 主執行流程 =====
async function main() {
  log('\n╔════════════════════════════════════════════════╗', 'bright');
  log('║                                                ║', 'bright');
  log('║        🌍 METACODE 完整使用範例                ║', 'bright');
  log('║     Minimal Representable Logic System        ║', 'bright');
  log('║                                                ║', 'bright');
  log('╚════════════════════════════════════════════════╝', 'bright');

  const meta = new MetaCode();

  log(`\n✓ MetaCode 實例已創建`, 'green');
  log(`  ID: ${meta.id}`, 'cyan');
  log(`  Version: ${meta.version}`, 'cyan');

  try {
    // 場景 1-7
    const hausdorff = await scenario1_Math(meta);
    const storage = await scenario2_Storage(meta);
    const compute = await scenario3_Compute(meta);
    const mystery = await scenario4_CrossDomain(meta, hausdorff, storage, compute);
    await scenario5_Evolution(meta, hausdorff);
    await scenario6_Verification(meta);
    const exported = await scenario7_Export(meta);

    // 最終總結
    log('\n╔════════════════════════════════════════════════╗', 'bright');
    log('║              🎉 執行完成                       ║', 'bright');
    log('╚════════════════════════════════════════════════╝', 'bright');

    log(`\n✓ 成功演示了 MetaCode 的以下能力:`, 'green');
    log(`  1. 跨域粒子創建 (數學/儲存/計算)`, 'cyan');
    log(`  2. 一致性匹配與分類決策`, 'cyan');
    log(`  3. 粒子演化與放大公式`, 'cyan');
    log(`  4. 關聯建立與依賴圖`, 'cyan');
    log(`  5. 變化傳播（牽一髮動全身）`, 'cyan');
    log(`  6. 自我驗證與指標計算`, 'cyan');
    log(`  7. 完整導出與持久化`, 'cyan');

    log(`\n✓ 數據已保存至 ./data/ 目錄`, 'magenta');
    log(`✓ 可使用其他工具讀取並繼續研究\n`, 'magenta');

  } catch (error) {
    log(`\n✗ 執行錯誤: ${error.message}`, 'yellow');
    console.error(error);
  }
}

// 執行
main();
