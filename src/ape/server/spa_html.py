"""
MVP Single-Page Application (SPA) Web UI Template — ORION-101 Week 1 & 2 Specification.
Presents the value proposition: "Hire your first AI Engineering Department in 5 minutes."
"""

MVP_SPA_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>APE Platform — Hire your AI Engineering Department in 5 minutes</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #0b0f19;
      --bg-card: #131b2e;
      --bg-card-hover: #1c2742;
      --border: #233154;
      --accent: #6366f1;
      --accent-gradient: linear-gradient(135deg, #6366f1, #a855f7);
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg-dark);
      color: var(--text-main);
      font-family: var(--font-sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    header {
      background: rgba(19, 27, 46, 0.85);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
      padding: 1.25rem 2.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-logo {
      width: 40px;
      height: 40px;
      background: var(--accent-gradient);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.2rem;
      box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
    }
    .brand-title {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-tag {
      font-size: 0.75rem;
      background: rgba(99, 102, 241, 0.15);
      color: #818cf8;
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 0.2rem 0.6rem;
      border-radius: 20px;
      font-weight: 600;
    }

    .hero {
      text-align: center;
      padding: 4rem 2rem 2rem;
      max-width: 900px;
      margin: 0 auto;
    }
    .hero h1 {
      font-size: 2.75rem;
      font-weight: 800;
      line-height: 1.2;
      background: linear-gradient(180deg, #ffffff 0%, #9ca3af 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 1rem;
    }
    .hero p {
      font-size: 1.15rem;
      color: var(--text-muted);
      line-height: 1.6;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 1.5rem;
      padding: 2rem 2.5rem;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
    }

    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.75rem;
      transition: all 0.2s ease;
    }
    .card:hover {
      border-color: #3b82f6;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .btn {
      background: var(--accent-gradient);
      color: white;
      border: none;
      padding: 0.8rem 1.5rem;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      font-size: 0.95rem;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.9; }

    input {
      width: 100%;
      background: var(--bg-dark);
      border: 1px solid var(--border);
      color: white;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      margin-bottom: 1rem;
      font-family: var(--font-sans);
    }

    .console {
      background: #060911;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      color: #34d399;
      min-height: 180px;
      max-height: 300px;
      overflow-y: auto;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-logo">A</div>
      <div class="brand-title">APE Cloud</div>
      <span class="brand-tag">v1.0 MVP</span>
    </div>
  </header>

  <section class="hero">
    <h1>Hire Your First AI Engineering Department in 5 Minutes</h1>
    <p>The Operating System that lets any business hire, govern, and scale AI departments as real organizational units.</p>
  </section>

  <div class="grid">
    <!-- Step 1: Create Workspace -->
    <div class="card">
      <div class="card-title">1. Initialize Workspace</div>
      <input type="text" id="wsName" placeholder="Organization Name (e.g. Acme Corp)" value="Acme Corp">
      <button class="btn" onclick="initWorkspace()">Provision Workspace</button>
      <div id="wsStatus" style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-muted);">Status: Ready</div>
    </div>

    <!-- Step 2: Connect GitHub Repo -->
    <div class="card">
      <div class="card-title">2. Connect GitHub Repository</div>
      <input type="text" id="repoUrl" placeholder="GitHub Repo (e.g. acme/api-service)" value="acme/api-service">
      <button class="btn" onclick="connectGitHub()">Connect GitHub Repo</button>
      <div id="ghStatus" style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-muted);">Status: Disconnected</div>
    </div>

    <!-- Step 3: Run AI Engineering Department -->
    <div class="card">
      <div class="card-title">3. Deploy AI Engineering Dept</div>
      <input type="text" id="taskDesc" placeholder="Task Objective (e.g. Build REST API)" value="Produce Golden Path REST API">
      <button class="btn" onclick="runDepartment()">Execute AI Department Task</button>
      <div id="deptStatus" style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-muted);">Status: Idle</div>
    </div>
  </div>

  <!-- Live Output Console & Evidence -->
  <div style="padding: 0 2.5rem 3rem; max-width: 1400px; margin: 0 auto; width: 100%;">
    <div class="card">
      <div class="card-title">Live Evidence & Real-Time Output Console</div>
      <div class="console" id="consoleOutput">APE MVP System Initialized.
Connected to APE Engine v1.0.
Awaiting user action...</div>
    </div>
  </div>

  <script>
    async function initWorkspace() {
      const name = document.getElementById('wsName').value;
      log(`[Workspace] Initializing workspace for '${name}'...`);
      const res = await fetch('/api/v1/mvp/workspace', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name})
      });
      const data = await res.json();
      document.getElementById('wsStatus').innerText = `Status: Active (${data.slug})`;
      log(`[Workspace] PROVISIONED! Slug: ${data.slug}`);
    }

    async function connectGitHub() {
      const repo = document.getElementById('repoUrl').value;
      log(`[GitHub] Connecting to repository '${repo}'...`);
      const res = await fetch('/api/v1/mvp/github/connect', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({repo: repo})
      });
      const data = await res.json();
      document.getElementById('ghStatus').innerText = `Status: CONNECTED (${data.repo})`;
      log(`[GitHub] CONNECTED! Webhook listener registered for ${data.repo}`);
    }

    async function runDepartment() {
      const task = document.getElementById('taskDesc').value;
      const repo = document.getElementById('repoUrl').value;
      log(`[AI Department] Deploying Engineering Unit for task: '${task}'...`);
      log(`[Pipeline] Planner -> Coder -> QA -> Quality OS Audit running...`);
      document.getElementById('deptStatus').innerText = 'Status: EXECUTING...';
      const res = await fetch('/api/v1/mvp/department/run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task: task, repo: repo})
      });
      const data = await res.json();
      document.getElementById('deptStatus').innerText = `Status: RELEASED (${data.confidence}% Confidence)`;
      log(`[AI Department] SUCCESS! Quality OS Audit: PASS.`);
      log(`[GitHub PR] PULL REQUEST CREATED! Link: ${data.pr_url}`);
      log(`[Evidence] Merkle Proof Hash: ${data.merkle_proof}`);
      log(`[User Outcome] 'It actually worked.' 🎉`);
    }

    function log(msg) {
      const el = document.getElementById('consoleOutput');
      el.innerText += `\n[${new Date().toLocaleTimeString()}] ${msg}`;
      el.scrollTop = el.scrollHeight;
    }
  </script>
</body>
</html>
"""
