# -*- coding: utf-8 -*-
TMA_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru" data-theme="ios">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>AiGem Dashboard</title>
  <script>
    window.Telegram = window.Telegram || { WebApp: { ready: function(){}, expand: function(){}, HapticFeedback: { impactOccurred: function(){} } } };
  </script>
  <script src="https://telegram.org/js/telegram-web-app.js" defer></script>
  <script src="https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js" defer></script>
  <style>
    /* ══════════════════════════════════════════════════════════════
       THEME SYSTEM TOKENS (CSS VARIABLES)
       ══════════════════════════════════════════════════════════════ */
    :root, [data-theme="ios"] {
      --bg-main: #000000;
      --bg-ambient: radial-gradient(circle at 50% -10%, rgba(10, 132, 255, 0.12) 0%, transparent 60%), #000000;
      --card-bg: rgba(28, 28, 30, 0.78);
      --card-border: rgba(255, 255, 255, 0.10);
      --card-radius: 20px;
      --card-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
      --accent: #0A84FF;
      --accent-glow: rgba(10, 132, 255, 0.35);
      --accent-secondary: #64D2FF;
      --accent-green: #30D158;
      --accent-orange: #FF9F0A;
      --nav-bg: #1C1C1E;
      --nav-active-bg: #2C2C2E;
      --nav-active-text: #FFFFFF;
      --text-primary: #FFFFFF;
      --text-secondary: #8E8E93;
      --text-muted: #636366;
      --switch-on: #30D158;
      --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif;
    }

    [data-theme="visionos"] {
      --bg-main: #060914;
      --bg-ambient: radial-gradient(circle at 20% 15%, rgba(100, 210, 255, 0.18) 0%, transparent 45%),
                    radial-gradient(circle at 80% 85%, rgba(191, 90, 242, 0.15) 0%, transparent 50%),
                    #060914;
      --card-bg: rgba(255, 255, 255, 0.08);
      --card-border: rgba(255, 255, 255, 0.18);
      --card-radius: 26px;
      --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45), inset 0 1px 1px 0 rgba(255, 255, 255, 0.25);
      --accent: #64D2FF;
      --accent-glow: rgba(100, 210, 255, 0.4);
      --accent-secondary: #BF5AF2;
      --accent-green: #34D399;
      --accent-orange: #FBBF24;
      --nav-bg: rgba(255, 255, 255, 0.08);
      --nav-active-bg: rgba(255, 255, 255, 0.22);
      --nav-active-text: #FFFFFF;
      --text-primary: #FFFFFF;
      --text-secondary: #A1A1AA;
      --text-muted: #71717A;
      --switch-on: #64D2FF;
      --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif;
    }

    [data-theme="cyber"] {
      --bg-main: #090D16;
      --bg-ambient: linear-gradient(180deg, #0c1220 0%, #080c14 100%);
      --card-bg: rgba(15, 23, 42, 0.92);
      --card-border: rgba(6, 182, 212, 0.28);
      --card-radius: 14px;
      --card-shadow: 0 0 18px rgba(6, 182, 212, 0.15), inset 0 0 1px rgba(6, 182, 212, 0.4);
      --accent: #06B6D4;
      --accent-glow: rgba(6, 182, 212, 0.5);
      --accent-secondary: #A855F7;
      --accent-green: #10B981;
      --accent-orange: #F59E0B;
      --nav-bg: #0F172A;
      --nav-active-bg: linear-gradient(135deg, rgba(6, 182, 212, 0.35), rgba(168, 85, 247, 0.3));
      --nav-active-text: #38BDF8;
      --text-primary: #F8FAFC;
      --text-secondary: #94A3B8;
      --text-muted: #64748B;
      --switch-on: #06B6D4;
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "JetBrains Mono", monospace;
    }

    [data-theme="bento"] {
      --bg-main: #0C0C0E;
      --bg-ambient: radial-gradient(circle at 50% 0%, rgba(245, 158, 11, 0.08) 0%, transparent 50%), #0C0C0E;
      --card-bg: #141417;
      --card-border: rgba(245, 158, 11, 0.18);
      --card-radius: 18px;
      --card-shadow: 0 6px 24px rgba(0, 0, 0, 0.6);
      --accent: #F59E0B;
      --accent-glow: rgba(245, 158, 11, 0.35);
      --accent-secondary: #EAB308;
      --accent-green: #22C55E;
      --accent-orange: #F97316;
      --nav-bg: #1A1A1E;
      --nav-active-bg: #F59E0B;
      --nav-active-text: #000000;
      --text-primary: #FAFAFA;
      --text-secondary: #A1A1AA;
      --text-muted: #71717A;
      --switch-on: #F59E0B;
      --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", sans-serif;
    }

    /* ══════════════════════════════════════════════════════════════
       GLOBAL LAYOUT
       ══════════════════════════════════════════════════════════════ */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { min-height: 100vh; background-color: var(--bg-main); color: var(--text-primary); font-family: var(--font-family); }
    body {
      background: var(--bg-ambient);
      background-attachment: fixed;
      -webkit-font-smoothing: antialiased;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
      display: flex;
      justify-content: center;
      padding-bottom: env(safe-area-inset-bottom, 24px);
    }

    .app-viewport {
      width: 100%;
      max-width: 620px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      position: relative;
      border-left: 1px solid rgba(255, 255, 255, 0.04);
      border-right: 1px solid rgba(255, 255, 255, 0.04);
      box-shadow: 0 0 60px rgba(0, 0, 0, 0.7);
    }

    /* Loading Screen */
    #loading-screen {
      position: fixed; inset: 0; z-index: 9999;
      background: #000000;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      transition: opacity 0.35s ease;
    }
    .loading-spinner {
      width: 44px; height: 44px;
      border: 3px solid rgba(10, 132, 255, 0.15);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Header */
    .app-header {
      position: sticky; top: 0; z-index: 50;
      padding: calc(env(safe-area-inset-top, 0px) + 12px) 16px 10px;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border-bottom: 1px solid var(--card-border);
      display: flex; align-items: center; justify-content: space-between; gap: 10px;
    }
    .header-left { display: flex; align-items: center; gap: 10px; }
    .header-avatar {
      width: 38px; height: 38px; border-radius: 12px;
      background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
      display: flex; align-items: center; justify-content: center;
      color: #FFF; box-shadow: 0 4px 14px var(--accent-glow);
    }
    .header-title-text { font-size: 15px; font-weight: 700; letter-spacing: -0.2px; display: flex; align-items: center; gap: 6px; }
    .header-live-pill {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 1px 7px; border-radius: 100px;
      background: rgba(48, 209, 88, 0.15); border: 1px solid rgba(48, 209, 88, 0.3);
      color: var(--accent-green); font-size: 10px; font-weight: 700;
    }
    .header-live-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--accent-green); box-shadow: 0 0 5px var(--accent-green); }
    .header-time-label { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }

    .header-actions { display: flex; align-items: center; gap: 8px; }
    
    /* Theme Toggle Button */
    .theme-toggle-btn {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 6px 10px; border-radius: 12px;
      background: rgba(255, 255, 255, 0.08); border: 1px solid var(--card-border);
      color: var(--text-primary); font-size: 11px; font-weight: 600;
      cursor: pointer; transition: all 0.15s;
    }
    .theme-toggle-btn:active { transform: scale(0.95); background: rgba(255, 255, 255, 0.15); }
    .theme-toggle-btn svg { width: 13px; height: 13px; }

    .header-icon-btn {
      width: 34px; height: 34px; border-radius: 10px;
      background: rgba(255, 255, 255, 0.08); border: 1px solid var(--card-border);
      display: flex; align-items: center; justify-content: center;
      color: var(--accent); cursor: pointer; transition: all 0.15s;
    }
    .header-icon-btn:active { transform: scale(0.92); }
    .header-icon-btn svg { width: 16px; height: 16px; }

    /* Segmented Navigation */
    .nav-segmented-wrap {
      position: sticky; top: 62px; z-index: 45;
      padding: 6px 14px;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
    }
    .nav-segmented-bar {
      display: flex; gap: 3px; padding: 3px;
      background: var(--nav-bg); border-radius: 14px;
      border: 1px solid var(--card-border);
      overflow-x: auto; scrollbar-width: none;
    }
    .nav-segmented-bar::-webkit-scrollbar { display: none; }
    
    .nav-seg-btn {
      flex: 1 0 auto;
      display: flex; align-items: center; justify-content: center; gap: 5px;
      padding: 7px 11px; border-radius: 11px;
      border: none; background: transparent;
      color: var(--text-secondary); font-size: 12px; font-weight: 600;
      cursor: pointer; white-space: nowrap; transition: all 0.2s;
    }
    .nav-seg-btn svg { width: 14px; height: 14px; }
    .nav-seg-btn.active {
      background: var(--nav-active-bg);
      color: var(--nav-active-text);
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    /* Content Area */
    .app-main { padding: 12px 14px 40px; display: flex; flex-direction: column; gap: 14px; }

    /* Card System */
    .app-card {
      background: var(--card-bg);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 16px;
      box-shadow: var(--card-shadow);
      transition: transform 0.15s, border-color 0.2s;
    }
    .app-card:active { transform: scale(0.985); }

    /* Widget Grid (Home) */
    .widget-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .widget-box {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 14px;
      display: flex; flex-direction: column; justify-content: space-between; gap: 10px;
      min-height: 110px; cursor: pointer; transition: all 0.2s;
    }
    .widget-box:active { transform: scale(0.97); }
    .widget-box.active-light {
      border-color: var(--accent);
      box-shadow: 0 4px 18px var(--accent-glow);
    }
    .widget-icon-pill {
      width: 36px; height: 36px; border-radius: 11px;
      background: rgba(255, 255, 255, 0.08);
      display: flex; align-items: center; justify-content: center;
      color: var(--text-secondary);
    }
    .widget-box.active-light .widget-icon-pill {
      background: var(--accent); color: #000;
      box-shadow: 0 0 12px var(--accent-glow);
    }

    /* iOS Switch */
    .ui-switch {
      position: relative; width: 44px; height: 26px;
      background: #39393D; border-radius: 100px; transition: background 0.25s;
    }
    .ui-switch.on { background: var(--switch-on); }
    .ui-switch-knob {
      position: absolute; top: 2px; left: 2px;
      width: 22px; height: 22px; border-radius: 50%;
      background: #FFF; box-shadow: 0 2px 5px rgba(0,0,0,0.35);
      transition: transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .ui-switch.on .ui-switch-knob { transform: translateX(18px); }

    /* Grouped Rows */
    .group-header {
      font-size: 12px; font-weight: 700; color: var(--text-secondary);
      text-transform: uppercase; letter-spacing: 0.5px;
      padding: 0 4px 6px; display: flex; align-items: center; justify-content: space-between;
    }
    .group-container {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      overflow: hidden;
    }
    .group-row {
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 14px; position: relative;
    }
    .group-row:not(:last-child)::after {
      content: ''; position: absolute; bottom: 0; left: 52px; right: 0;
      height: 1px; background: rgba(255, 255, 255, 0.06);
    }
    .group-row-left { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
    
    .badge-icon-square {
      width: 32px; height: 32px; border-radius: 9px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; color: #FFF; font-size: 14px;
    }
    .badge-cyan { background: linear-gradient(135deg, #64D2FF, #0A84FF); }
    .badge-green { background: linear-gradient(135deg, #30D158, #28CD41); }
    .badge-amber { background: linear-gradient(135deg, #FF9F0A, #FFB340); }
    .badge-pink { background: linear-gradient(135deg, #FF375F, #FF2D55); }
    .badge-purple { background: linear-gradient(135deg, #BF5AF2, #AF52DE); }

    /* Resort & Curated Cards */
    .resort-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--card-radius);
      padding: 16px; display: flex; flex-direction: column; gap: 10px;
    }
    .resort-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
    .resort-name { font-size: 14px; font-weight: 700; color: #FFF; }
    .resort-cat { font-size: 11px; font-weight: 600; color: var(--accent-green); margin-top: 2px; }
    .resort-price-pill {
      padding: 3px 9px; border-radius: 100px;
      background: rgba(48, 209, 88, 0.12); border: 1px solid rgba(48, 209, 88, 0.25);
      color: var(--accent-green); font-size: 11px; font-weight: 700; white-space: nowrap;
    }
    .resort-meta-line { font-size: 11px; color: #D1D1D6; display: flex; align-items: flex-start; gap: 5px; line-height: 1.4; }
    .resort-actions-row { display: grid; grid-template-columns: 1fr 1.6fr; gap: 8px; margin-top: 4px; }
    
    .btn-card-secondary {
      display: flex; align-items: center; justify-content: center; gap: 5px;
      padding: 9px 12px; border-radius: 12px;
      background: rgba(255, 255, 255, 0.08); border: 1px solid var(--card-border);
      color: var(--accent); font-size: 11px; font-weight: 600; text-decoration: none;
      cursor: pointer; transition: all 0.15s;
    }
    .btn-card-secondary:active { transform: scale(0.97); background: rgba(255, 255, 255, 0.15); }
    .btn-card-primary {
      display: flex; align-items: center; justify-content: center; gap: 5px;
      padding: 9px 12px; border-radius: 12px;
      background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
      border: none; color: #FFF; font-size: 11px; font-weight: 700;
      cursor: pointer; box-shadow: 0 4px 12px var(--accent-glow); transition: all 0.15s;
    }
    .btn-card-primary:active { transform: scale(0.97); }

    /* Module pills grid */
    .module-capsules { display: flex; flex-wrap: wrap; gap: 6px; }
    .capsule-btn {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 7px 12px; border-radius: 100px;
      background: var(--nav-bg); border: 1px solid var(--card-border);
      color: var(--text-primary); font-size: 11px; font-weight: 600;
      cursor: pointer; transition: all 0.15s;
    }
    .capsule-btn:active { transform: scale(0.95); background: rgba(255, 255, 255, 0.15); }

    /* Modals */
    .modal-overlay {
      position: fixed; inset: 0; z-index: 100;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
      display: none; align-items: center; justify-content: center; padding: 16px;
    }
    .modal-overlay.open { display: flex; }
    .modal-box {
      background: #18181B; border: 1px solid var(--card-border);
      border-radius: 22px; padding: 20px; width: 100%; max-width: 380px;
      display: flex; flex-direction: column; gap: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.7);
    }
    .modal-header-row { display: flex; align-items: center; justify-content: space-between; }
    .modal-title-text { font-size: 15px; font-weight: 700; color: #FFF; }
    .modal-close-icon {
      background: rgba(255, 255, 255, 0.08); border: none;
      width: 28px; height: 28px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      color: var(--text-secondary); cursor: pointer;
    }
    .modal-input-field {
      width: 100%; padding: 10px 12px; border-radius: 12px;
      background: rgba(0, 0, 0, 0.4); border: 1px solid var(--card-border);
      font-size: 12px; color: #FFF; outline: none;
    }
    .modal-input-field:focus { border-color: var(--accent); }
    .modal-submit-btn {
      width: 100%; padding: 11px; border-radius: 12px;
      background: var(--accent); border: none; color: #FFF;
      font-size: 13px; font-weight: 700; cursor: pointer;
      box-shadow: 0 4px 14px var(--accent-glow);
    }

    /* Theme Selector Modal Items */
    .theme-pick-item {
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 14px; border-radius: 14px;
      background: rgba(255, 255, 255, 0.04); border: 1px solid var(--card-border);
      cursor: pointer; transition: all 0.15s;
    }
    .theme-pick-item:active { transform: scale(0.98); }
    .theme-pick-item.selected {
      border-color: var(--accent);
      background: rgba(255, 255, 255, 0.08);
    }
    .theme-pick-title { font-size: 13px; font-weight: 700; color: #FFF; }
    .theme-pick-sub { font-size: 10px; color: var(--text-secondary); margin-top: 2px; }
    .theme-check-mark { font-size: 16px; color: var(--accent); font-weight: 800; }
  </style>
</head>
<body>

  <!-- LOADING SCREEN -->
  <div id="loading-screen">
    <div style="text-align:center">
      <div class="loading-spinner" style="margin:0 auto 16px"></div>
      <div style="font-size:14px;font-weight:700;color:var(--accent);">AiGem Dashboard</div>
      <div style="font-size:11px;color:#8E8E93;margin-top:4px;">Загружаем данные...</div>
    </div>
  </div>
  <script>
    setTimeout(function() {
      var ls = document.getElementById('loading-screen');
      if (ls) {
        ls.style.transition = 'opacity 0.35s ease';
        ls.style.opacity = '0';
        setTimeout(function() { if (ls && ls.parentNode) ls.parentNode.removeChild(ls); }, 380);
      }
    }, 1500);
  </script>

  <!-- TOAST NOTIFICATION -->
  <div id="ui-toast" style="position:fixed;top:18px;left:50%;transform:translateX(-50%);z-index:99999;background:rgba(28,28,30,0.92);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.18);padding:9px 18px;border-radius:100px;font-size:12px;font-weight:600;color:#FFF;box-shadow:0 8px 30px rgba(0,0,0,0.6);display:none;align-items:center;gap:8px;pointer-events:none;transition:opacity 0.25s ease;">
    <span id="ui-toast-text"></span>
  </div>

  <div class="app-viewport">
    <!-- HEADER -->
    <header class="app-header">
      <div class="header-left">
        <div class="header-avatar">
          <i data-lucide="sparkles" style="width:20px;height:20px;"></i>
        </div>
        <div>
          <div class="header-title-text">
            <span>AiGem Super-Bot</span>
            <span class="header-live-pill"><span class="header-live-dot"></span>Live</span>
          </div>
          <div class="header-time-label" id="header-time">24/7 Cloud • MSK</div>
        </div>
      </div>

      <div class="header-actions">
        <!-- Theme Toggle Button -->
        <button class="theme-toggle-btn" onclick="openModal('modal-theme-select')" id="btn-current-theme" title="Сменить тему оформления">
          <span id="cur-theme-emoji">🍏</span>
          <span id="cur-theme-name">iOS 18</span>
          <i data-lucide="chevron-down"></i>
        </button>

        <!-- Refresh Button -->
        <button class="header-icon-btn" onclick="fetchDashboardData(true)" title="Обновить">
          <i data-lucide="rotate-cw" id="refresh-icon"></i>
        </button>
      </div>
    </header>

    <!-- SEGMENTED NAVIGATION -->
    <div class="nav-segmented-wrap">
      <div class="nav-segmented-bar">
        <button class="nav-seg-btn active" id="tab-btn-smart_home" onclick="switchTab('smart_home')">
          <i data-lucide="home"></i>
          <span>Дом</span>
        </button>
        <button class="nav-seg-btn" id="tab-btn-digest" onclick="switchTab('digest')">
          <i data-lucide="cloud-sun"></i>
          <span>Погода</span>
        </button>
        <button class="nav-seg-btn" id="tab-btn-tasks" onclick="switchTab('tasks')">
          <i data-lucide="cake"></i>
          <span>ДР & Дела</span>
        </button>
        <button class="nav-seg-btn" id="tab-btn-finance" onclick="switchTab('finance')">
          <i data-lucide="credit-card"></i>
          <span>Финансы</span>
        </button>
        <button class="nav-seg-btn" id="tab-btn-health" onclick="switchTab('health')">
          <i data-lucide="activity"></i>
          <span>Здоровье</span>
        </button>
        <button class="nav-seg-btn" id="tab-btn-hub" onclick="switchTab('hub')">
          <i data-lucide="grid"></i>
          <span>Каталог</span>
        </button>
      </div>
    </div>

    <!-- MAIN VIEW CONTAINER -->
    <main class="app-main">

      <!-- TAB 1: SMART HOME -->
      <section id="tab-smart_home" class="tab-content" style="display:flex;flex-direction:column;gap:12px;">
        <div class="widget-grid">
          <!-- Climate Widget -->
          <div class="widget-box">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div class="widget-icon-pill" style="color:var(--accent-orange);">
                <i data-lucide="thermometer" style="width:20px;height:20px;"></i>
              </div>
              <span style="font-size:11px;font-weight:700;color:var(--accent-orange);">Климат</span>
            </div>
            <div>
              <div style="font-size:24px;font-weight:800;color:#FFF;" id="sh-temp-val">24.5°C</div>
              <div style="font-size:11px;color:var(--text-secondary);" id="sh-hum-val">💧 48% влажность</div>
            </div>
          </div>

          <!-- Security Widget -->
          <div class="widget-box" id="sh-security-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div class="widget-icon-pill" style="color:var(--accent-green);" id="sh-sec-icon-box">
                <i data-lucide="shield-check" style="width:20px;height:20px;" id="sh-sec-icon"></i>
              </div>
              <span style="font-size:11px;font-weight:700;color:var(--accent-green);">Сейф & Дом</span>
            </div>
            <div>
              <div style="font-size:13px;font-weight:700;color:var(--accent-green);" id="sh-sec-title">Всё спокойно</div>
              <div style="font-size:11px;color:var(--text-secondary);" id="sh-sec-sub">Протечек нет • Дверь 🔒</div>
            </div>
          </div>
        </div>

        <!-- Master Switch -->
        <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;">
          <div style="display:flex;align-items:center;gap:12px;">
            <div class="widget-icon-pill" style="background:rgba(10,132,255,0.15);color:var(--accent);">
              <i data-lucide="power" style="width:20px;height:20px;"></i>
            </div>
            <div>
              <div style="font-size:13px;font-weight:700;color:#FFF;">Главный выключатель</div>
              <div style="font-size:11px;color:var(--text-secondary);" id="sh-active-counter">Активно: 0 ламп</div>
            </div>
          </div>
          <button onclick="turnOffAllLights()" style="padding:7px 12px;border-radius:12px;background:rgba(255,55,95,0.15);border:1px solid rgba(255,55,95,0.3);color:#FF375F;font-size:11px;font-weight:700;cursor:pointer;">
            Выкл всё
          </button>
        </div>

        <!-- Quick Toggles -->
        <div>
          <div class="group-header">
            <span>Быстрое управление</span>
            <span style="color:var(--accent);font-size:10px;">Яндекс SmartHome</span>
          </div>

          <div class="widget-grid" id="sh-priority-grid">
            <div class="widget-box" onclick="toggleDeviceByName('выключатель коридор', 'toggle-corridor')">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="widget-icon-pill" id="icon-corridor"><i data-lucide="lightbulb" style="width:18px;height:18px;"></i></div>
                <div class="ui-switch" id="sw-corridor"><div class="ui-switch-knob"></div></div>
              </div>
              <div>
                <div style="font-size:13px;font-weight:700;color:#FFF;">Свет Коридор</div>
                <div style="font-size:10px;color:var(--text-secondary);" id="st-corridor">Выключено</div>
              </div>
            </div>

            <div class="widget-box" onclick="toggleDeviceByName('свет ванная', 'toggle-bathroom')">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="widget-icon-pill" id="icon-bathroom"><i data-lucide="sparkles" style="width:18px;height:18px;"></i></div>
                <div class="ui-switch" id="sw-bathroom"><div class="ui-switch-knob"></div></div>
              </div>
              <div>
                <div style="font-size:13px;font-weight:700;color:#FFF;">Свет Ванная</div>
                <div style="font-size:10px;color:var(--text-secondary);" id="st-bathroom">Выключено</div>
              </div>
            </div>

            <div class="widget-box" onclick="toggleDeviceByName('вытяжка', 'toggle-hood')">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="widget-icon-pill" id="icon-hood"><i data-lucide="fan" style="width:18px;height:18px;"></i></div>
                <div class="ui-switch" id="sw-hood"><div class="ui-switch-knob"></div></div>
              </div>
              <div>
                <div style="font-size:13px;font-weight:700;color:#FFF;">Вытяжка</div>
                <div style="font-size:10px;color:var(--text-secondary);" id="st-hood">Выключено</div>
              </div>
            </div>

            <div class="widget-box" onclick="toggleDeviceByName('теплый пол', 'toggle-floor')">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="widget-icon-pill" id="icon-floor"><i data-lucide="flame" style="width:18px;height:18px;"></i></div>
                <div class="ui-switch" id="sw-floor"><div class="ui-switch-knob"></div></div>
              </div>
              <div>
                <div style="font-size:13px;font-weight:700;color:#FFF;">Тёплый пол</div>
                <div style="font-size:10px;color:var(--text-secondary);" id="st-floor">Выключено</div>
              </div>
            </div>
          </div>
        </div>

        <!-- All Devices Inset List -->
        <div>
          <div class="group-header">
            <span>Все устройства дома (<span id="sh-total-dev-count">...</span>)</span>
            <span style="cursor:pointer;color:var(--accent);" onclick="toggleAccordion('sh-all-devices')">Показать/Скрыть ▾</span>
          </div>
          <div class="group-container" id="sh-all-devices">
            <div style="padding:14px;text-align:center;font-size:11px;color:var(--text-secondary);">Загрузка списка устройств...</div>
          </div>
        </div>
      </section>

      <!-- TAB 2: DIGEST & WEATHER -->
      <section id="tab-digest" class="tab-content" style="display:none;flex-direction:column;gap:12px;">
        <div class="app-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <div style="display:flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:var(--accent);">
                <i data-lucide="map-pin" style="width:14px;height:14px;"></i>
                <span id="w-location">Санкт-Петербург (Приморский р-н)</span>
              </div>
              <div style="font-size:36px;font-weight:800;color:#FFF;margin-top:2px;" id="w-temp">+17.0°C</div>
              <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;" id="w-condition">⛅ Переменная облачность</div>
            </div>
            <div style="width:48px;height:48px;border-radius:14px;background:rgba(100,210,255,0.1);display:flex;align-items:center;justify-content:center;color:var(--accent);">
              <i data-lucide="cloud-sun" style="width:28px;height:28px;"></i>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.06);">
            <div style="font-size:11px;color:var(--text-secondary);">Ощущается: <b style="color:#FFF;" id="w-feels">+15°C</b></div>
            <div style="font-size:11px;color:var(--text-secondary);">Влажность: <b style="color:#FFF;" id="w-humidity">68%</b></div>
            <div style="font-size:11px;color:var(--text-secondary);">Ветер: <b style="color:#FFF;" id="w-wind">4 м/с</b></div>
            <div style="font-size:11px;color:var(--accent);font-weight:700;cursor:pointer;" onclick="refreshWeatherDirect()">⚡ Обновить со спутников</div>
          </div>
        </div>

        <!-- Hourly Scroll -->
        <div class="group-header"><span>Почасовой прогноз</span></div>
        <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none;" id="w-hourly-container">
          <!-- Dynamic Hourly items -->
        </div>

        <!-- Synoptic Report -->
        <div class="app-card">
          <div style="font-size:13px;font-weight:700;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
            <i data-lucide="sparkles" style="width:15px;height:15px;color:var(--accent-orange);"></i>
            <span>Сводка синоптика</span>
          </div>
          <div style="font-size:12px;color:#D1D1D6;line-height:1.5;" id="w-full-text">Сводка погоды формируется...</div>
        </div>
      </section>

      <!-- TAB 3: BIRTHDAYS & TASKS -->
      <section id="tab-tasks" class="tab-content" style="display:none;flex-direction:column;gap:12px;">
        <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-size:14px;font-weight:700;color:#FFF;">Дни рождения & События</div>
            <div style="font-size:11px;color:var(--text-secondary);">Синхронизировано с базой (<span id="bday-total-badge">23</span> чел.)</div>
          </div>
          <div style="display:flex;gap:6px;">
            <button onclick="syncBirthdaysCloud()" style="padding:6px 10px;border-radius:10px;background:rgba(255,255,255,0.08);border:1px solid var(--card-border);color:var(--text-secondary);cursor:pointer;" title="Синхронизация">
              <i data-lucide="rotate-cw" style="width:14px;height:14px;" id="bday-sync-icon"></i>
            </button>
            <button onclick="openModal('modal-add-birthday')" class="btn-card-primary" style="padding:6px 12px;font-size:11px;">
              + Добавить
            </button>
          </div>
        </div>

        <!-- Filter Bar -->
        <div style="display:flex;gap:6px;">
          <button class="bday-flt-btn active" id="bday-flt-all" onclick="setBdayFilter('all')" style="flex:1;padding:6px;border-radius:10px;border:none;background:var(--accent);color:#FFF;font-size:11px;font-weight:700;cursor:pointer;">Все</button>
          <button class="bday-flt-btn" id="bday-flt-upcoming" onclick="setBdayFilter('upcoming')" style="flex:1;padding:6px;border-radius:10px;border:none;background:var(--nav-bg);color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;">Ближайшие</button>
          <button class="bday-flt-btn" id="bday-flt-family" onclick="setBdayFilter('family')" style="flex:1;padding:6px;border-radius:10px;border:none;background:var(--nav-bg);color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;">Семья</button>
        </div>

        <!-- Birthdays List -->
        <div style="display:flex;flex-direction:column;gap:8px;" id="birthdays-list"></div>

        <!-- Reminders Section -->
        <div style="margin-top:12px;">
          <div class="group-header">
            <span>Умные напоминания</span>
            <span style="color:var(--accent);cursor:pointer;" onclick="openModal('modal-add-reminder')">+ Создать</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;" id="reminders-list"></div>
        </div>
      </section>

      <!-- TAB 4: FINANCE -->
      <section id="tab-finance" class="tab-content" style="display:none;flex-direction:column;gap:12px;">
        <!-- Sub-tabs -->
        <div style="display:flex;gap:4px;background:var(--nav-bg);padding:3px;border-radius:12px;border:1px solid var(--card-border);">
          <button id="f-subtab-btn-loan" onclick="switchFinanceSubTab('loan')" style="flex:1;padding:7px;border-radius:9px;border:none;background:var(--accent);color:#FFF;font-size:11px;font-weight:700;cursor:pointer;">Калькулятор кредита</button>
          <button id="f-subtab-btn-subs" onclick="switchFinanceSubTab('subs')" style="flex:1;padding:7px;border-radius:9px;border:none;background:transparent;color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;">Подписки & Правила</button>
        </div>

        <!-- Panel Loan -->
        <div id="f-panel-loan" style="display:flex;flex-direction:column;gap:12px;">
          <div class="app-card">
            <div style="font-size:13px;font-weight:700;margin-bottom:12px;">Параметры кредита / ипотеки</div>
            
            <div style="display:flex;flex-direction:column;gap:10px;">
              <div>
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;">
                  <span style="color:var(--text-secondary);">Сумма:</span>
                  <b id="calc-lbl-amount" style="color:#FFF;">1 000 000 ₽</b>
                </div>
                <input type="range" min="50000" max="15000000" step="50000" value="1000000" id="calc-inp-amount" oninput="runLoanCalc()">
              </div>

              <div>
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;">
                  <span style="color:var(--text-secondary);">Ставка (%):</span>
                  <b id="calc-lbl-rate" style="color:#FFF;">18.5 %</b>
                </div>
                <input type="range" min="1" max="40" step="0.5" value="18.5" id="calc-inp-rate" oninput="runLoanCalc()">
              </div>

              <div>
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;">
                  <span style="color:var(--text-secondary);">Срок:</span>
                  <b id="calc-lbl-months" style="color:#FFF;">60 мес. (5 лет)</b>
                </div>
                <input type="range" min="6" max="360" step="6" value="60" id="calc-inp-months" oninput="runLoanCalc()">
              </div>

              <div>
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;">
                  <span style="color:var(--text-secondary);">Досрочное погашение (в месяц):</span>
                  <b id="calc-lbl-early" style="color:var(--accent-green);">0 ₽</b>
                </div>
                <input type="range" min="0" max="100000" step="5000" value="0" id="calc-inp-early" oninput="runLoanCalc()">
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.08);">
              <div class="app-card" style="padding:10px;text-align:center;">
                <div style="font-size:10px;color:var(--text-secondary);">Платеж в месяц</div>
                <div style="font-size:16px;font-weight:800;color:var(--accent);margin-top:2px;" id="calc-res-payment">25 650 ₽</div>
              </div>
              <div class="app-card" style="padding:10px;text-align:center;">
                <div style="font-size:10px;color:var(--text-secondary);">Переплата</div>
                <div style="font-size:16px;font-weight:800;color:var(--accent-orange);margin-top:2px;" id="calc-res-interest">539 000 ₽</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Panel Subs -->
        <div id="f-panel-subs" style="display:none;flex-direction:column;gap:12px;">
          <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:11px;color:var(--text-secondary);">Регулярные подписки</div>
              <div style="font-size:22px;font-weight:800;color:var(--accent);" id="sub-total-sum">0 ₽</div>
              <div style="font-size:10px;color:var(--text-muted);" id="sub-count-text">0 активных подписок</div>
            </div>
            <button onclick="openModal('modal-add-sub')" class="btn-card-primary" style="padding:6px 12px;font-size:11px;">
              + Добавить
            </button>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;" id="subscriptions-list"></div>

          <!-- Rules -->
          <div style="margin-top:8px;">
            <div class="group-header"><span>Правила & Автоматизации</span></div>
            <div style="display:flex;flex-direction:column;gap:8px;" id="rules-list"></div>
          </div>
        </div>
      </section>

      <!-- TAB 5: HEALTH & FOOD -->
      <section id="tab-health" class="tab-content" style="display:none;flex-direction:column;gap:12px;">
        <div style="display:flex;gap:4px;background:var(--nav-bg);padding:3px;border-radius:12px;border:1px solid var(--card-border);">
          <button id="h-subtab-btn-food" onclick="switchHealthSubTab('food')" style="flex:1;padding:7px;border-radius:9px;border:none;background:var(--accent);color:#FFF;font-size:11px;font-weight:700;cursor:pointer;">КБЖУ Рацион</button>
          <button id="h-subtab-btn-sleep" onclick="switchHealthSubTab('sleep')" style="flex:1;padding:7px;border-radius:9px;border:none;background:transparent;color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;">Калькулятор сна</button>
        </div>

        <!-- Food Panel -->
        <div id="h-panel-food" style="display:flex;flex-direction:column;gap:12px;">
          <div class="app-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div>
                <div style="font-size:11px;color:var(--text-secondary);">Калории сегодня</div>
                <div style="font-size:24px;font-weight:800;color:var(--accent-green);"><span id="food-total-kcal">0</span> / <span id="food-goal-kcal">2200</span> ккал</div>
              </div>
              <button onclick="openModal('modal-add-food')" class="btn-card-primary" style="padding:6px 12px;font-size:11px;">+ Прием пищи</button>
            </div>
            <!-- Progress Bar -->
            <div style="width:100%;height:6px;border-radius:3px;background:rgba(255,255,255,0.08);margin-top:10px;overflow:hidden;">
              <div id="food-progress-bar" style="width:0%;height:100%;background:var(--accent-green);border-radius:3px;transition:width 0.3s;"></div>
            </div>
            <!-- Macros -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:12px;text-align:center;">
              <div class="app-card" style="padding:8px;"><span style="font-size:10px;color:var(--text-secondary);">Белки</span><div style="font-size:13px;font-weight:700;" id="food-p">0г</div></div>
              <div class="app-card" style="padding:8px;"><span style="font-size:10px;color:var(--text-secondary);">Жиры</span><div style="font-size:13px;font-weight:700;" id="food-f">0г</div></div>
              <div class="app-card" style="padding:8px;"><span style="font-size:10px;color:var(--text-secondary);">Углеводы</span><div style="font-size:13px;font-weight:700;" id="food-c">0г</div></div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;" id="food-meals-list"></div>
        </div>

        <!-- Sleep Panel -->
        <div id="h-panel-sleep" style="display:none;flex-direction:column;gap:12px;">
          <div class="app-card">
            <div style="font-size:13px;font-weight:700;margin-bottom:8px;">Фазы сна и циркадные ритмы (цикл 90 мин)</div>
            <div style="display:flex;gap:6px;margin-bottom:12px;">
              <button id="slp-mode-now" onclick="setSleepCalcMode('now')" style="flex:1;padding:8px;border-radius:10px;border:1px solid var(--accent);background:rgba(10,132,255,0.15);color:var(--accent);font-size:11px;font-weight:700;cursor:pointer;">Спать сейчас</button>
              <button id="slp-mode-wake" onclick="setSleepCalcMode('wake')" style="flex:1;padding:8px;border-radius:10px;border:1px solid var(--card-border);background:var(--nav-bg);color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;">Время подъема</button>
            </div>
            <div id="slp-wake-picker" style="display:none;margin-bottom:12px;">
              <label style="font-size:11px;color:var(--text-secondary);">Во сколько нужно проснуться?</label>
              <input type="time" id="slp-wake-time" value="07:30" class="modal-input-field" style="margin-top:4px;" onchange="runSleepCalc()">
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;" id="slp-results-list"></div>
          </div>
        </div>
      </section>

      <!-- TAB 6: CATALOG & MODULES (HUB) -->
      <section id="tab-hub" class="tab-content" style="display:none;flex-direction:column;gap:14px;">
        <div class="app-card" style="background:linear-gradient(135deg,rgba(10,132,255,0.12),rgba(100,210,255,0.05));">
          <div style="font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;">Каталог возможностей</div>
          <div style="font-size:16px;font-weight:800;color:#FFF;margin-top:2px;">Все 38 модулей супер-бота</div>
          <div style="font-size:11px;color:var(--text-secondary);margin-top:2px;">Мгновенный запуск прямо в Telegram диалоге</div>
        </div>

        <!-- Curated Country Resorts -->
        <div>
          <div class="group-header">
            <span>👨‍👩‍👧 Загородный семейный отдых & Спа</span>
            <span style="color:var(--accent-green);">ТОП баз</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:10px;" id="country-featured-list">
            <!-- Rendered by renderCountryFeatured() -->
          </div>
        </div>

        <!-- Quick 38 Modules List -->
        <div>
          <div class="group-header"><span>Все модули бота</span></div>
          <div class="module-capsules">
            <button class="capsule-btn" onclick="openInBot('🥗 КБЖУ')">🥗 КБЖУ</button>
            <button class="capsule-btn" onclick="openInBot('🔢 Кредиты')">🔢 Кредиты</button>
            <button class="capsule-btn" onclick="openInBot('🚗 Авто-Юрист')">🚗 Авто-Юрист</button>
            <button class="capsule-btn" onclick="openInBot('🔬 Ресерч')">🔬 Ресерч</button>
            <button class="capsule-btn" onclick="openInBot('🎙 Собеседование')">🎙 Собеседование</button>
            <button class="capsule-btn" onclick="openInBot('📚 Книги')">📚 Книги</button>
            <button class="capsule-btn" onclick="openInBot('🎬 Кино')">🎬 Кино</button>
            <button class="capsule-btn" onclick="openInBot('🛡 Манипуляции')">🛡 Манипуляции</button>
            <button class="capsule-btn" onclick="openInBot('🧠 Мышление')">🧠 Мышление</button>
            <button class="capsule-btn" onclick="openInBot('❓ Справка')">❓ Справка</button>
            <button class="capsule-btn" onclick="openInBot('🏠 Умный дом')">🏠 Умный дом</button>
            <button class="capsule-btn" onclick="openInBot('🌤 Погода')">🌤 Погода</button>
            <button class="capsule-btn" onclick="openInBot('😴 Сон')">😴 Сон</button>
            <button class="capsule-btn" onclick="openInBot('🎂 Дни рожд.')">🎂 Дни рожд.</button>
            <button class="capsule-btn" onclick="openInBot('⏰ Напоминания')">⏰ Напоминания</button>
            <button class="capsule-btn" onclick="openInBot('💳 Подписки')">💳 Подписки</button>
            <button class="capsule-btn" onclick="openInBot('🌅 Дайджест')">🌅 Дайджест</button>
            <button class="capsule-btn" onclick="openInBot('🍽 Рестораны')">🍽 Рестораны</button>
            <button class="capsule-btn" onclick="openInBot('🏕 Загород')">🏕 Загород</button>
            <button class="capsule-btn" onclick="openInBot('🍸 Спикизи')">🍸 Спикизи</button>
            <button class="capsule-btn" onclick="openInBot('🍷 Сомелье')">🍷 Сомелье</button>
            <button class="capsule-btn" onclick="openInBot('🎨 Фото AI')">🎨 Фото AI</button>
            <button class="capsule-btn" onclick="openInBot('🔐 Сейф')">🔐 Сейф</button>
            <button class="capsule-btn" onclick="openInBot('📝 Заметки')">📝 Заметки</button>
            <button class="capsule-btn" onclick="openInBot('📸 Фото-споты')">📸 Фото-споты</button>
            <button class="capsule-btn" onclick="openInBot('🎧 Музыка')">🎧 Музыка</button>
            <button class="capsule-btn" onclick="openInBot('🚗 Drive2')">🚗 Drive2</button>
            <button class="capsule-btn" onclick="openInBot('🔵 ВКонтакте')">🔵 ВКонтакте</button>
          </div>
        </div>
      </section>
    </main>
  </div>

  <!-- THEME SELECTOR MODAL -->
  <div id="modal-theme-select" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header-row">
        <div class="modal-title-text">🎨 Тема оформления</div>
        <button onclick="closeModal('modal-theme-select')" class="modal-close-icon"><i data-lucide="x" style="width:16px;height:16px;"></i></button>
      </div>
      <div style="font-size:11px;color:var(--text-secondary);">Выберите стиль интерфейса дашборда:</div>

      <div style="display:flex;flex-direction:column;gap:8px;">
        <!-- Option 1 -->
        <div class="theme-pick-item selected" id="theme-opt-ios" onclick="selectTheme('ios')">
          <div>
            <div class="theme-pick-title">🍏 Apple iOS 18 (Cupertino)</div>
            <div class="theme-pick-sub">Нативный стиль iPhone, матовое стекло Liquid Glass</div>
          </div>
          <div class="theme-check-mark" id="check-ios">✓</div>
        </div>

        <!-- Option 2 -->
        <div class="theme-pick-item" id="theme-opt-visionos" onclick="selectTheme('visionos')">
          <div>
            <div class="theme-pick-title">🥽 Apple VisionOS (Spatial 3D)</div>
            <div class="theme-pick-sub">Парящие стеклянные панели, глубина и космический градиент</div>
          </div>
          <div class="theme-check-mark" id="check-visionos"></div>
        </div>

        <!-- Option 3 -->
        <div class="theme-pick-item" id="theme-opt-cyber" onclick="selectTheme('cyber')">
          <div>
            <div class="theme-pick-title">⚡ Linear & Raycast (Cyber HUD)</div>
            <div class="theme-pick-sub">Технологичный минимализм, темный графит и неоновые рамки</div>
          </div>
          <div class="theme-check-mark" id="check-cyber"></div>
        </div>

        <!-- Option 4 -->
        <div class="theme-pick-item" id="theme-opt-bento" onclick="selectTheme('bento')">
          <div>
            <div class="theme-pick-title">🧭 Bento Luxury (Swiss & Gold)</div>
            <div class="theme-pick-sub">Швейцарская модульная сетка и янтарно-золотые акценты</div>
          </div>
          <div class="theme-check-mark" id="check-bento"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- MODALS FOR ADDING ITEMS -->
  <div id="modal-add-birthday" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header-row">
        <div class="modal-title-text">🎂 Новый день рождения</div>
        <button onclick="closeModal('modal-add-birthday')" class="modal-close-icon"><i data-lucide="x" style="width:16px;height:16px;"></i></button>
      </div>
      <input type="text" id="m-bday-name" placeholder="Имя человека (напр. Анна)" class="modal-input-field">
      <input type="date" id="m-bday-date" class="modal-input-field">
      <input type="text" id="m-bday-note" placeholder="Заметка / Категория (Семья, Друзья)" class="modal-input-field">
      <button onclick="submitAddBirthday()" class="modal-submit-btn">Сохранить</button>
    </div>
  </div>

  <div id="modal-add-reminder" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header-row">
        <div class="modal-title-text">⏰ Новое напоминание</div>
        <button onclick="closeModal('modal-add-reminder')" class="modal-close-icon"><i data-lucide="x" style="width:16px;height:16px;"></i></button>
      </div>
      <input type="text" id="m-rem-text" placeholder="Что нужно сделать?" class="modal-input-field">
      <input type="text" id="m-rem-time" placeholder="Время (напр. Завтра в 14:00)" class="modal-input-field">
      <button onclick="submitAddReminder()" class="modal-submit-btn">Поставить напоминание</button>
    </div>
  </div>

  <div id="modal-add-food" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header-row">
        <div class="modal-title-text">🥗 Записать прием пищи</div>
        <button onclick="closeModal('modal-add-food')" class="modal-close-icon"><i data-lucide="x" style="width:16px;height:16px;"></i></button>
      </div>
      <input type="text" id="m-food-name" placeholder="Название блюда" class="modal-input-field">
      <input type="number" id="m-food-kcal" placeholder="Калории (ккал)" class="modal-input-field">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;">
        <input type="number" id="m-food-p" placeholder="Белки" class="modal-input-field">
        <input type="number" id="m-food-f" placeholder="Жиры" class="modal-input-field">
        <input type="number" id="m-food-c" placeholder="Углеводы" class="modal-input-field">
      </div>
      <button onclick="submitAddFood()" class="modal-submit-btn">Записать в рацион</button>
    </div>
  </div>

  <div id="modal-add-sub" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header-row">
        <div class="modal-title-text">💳 Новая регулярная подписка</div>
        <button onclick="closeModal('modal-add-sub')" class="modal-close-icon"><i data-lucide="x" style="width:16px;height:16px;"></i></button>
      </div>
      <input type="text" id="m-sub-name" placeholder="Сервис (напр. Яндекс Плюс, iCloud)" class="modal-input-field">
      <input type="number" id="m-sub-amount" placeholder="Сумма в рублях" class="modal-input-field">
      <input type="number" id="m-sub-day" placeholder="День списания (1-31)" min="1" max="31" class="modal-input-field">
      <input type="text" id="m-sub-cat" placeholder="Категория" class="modal-input-field">
      <button onclick="submitAddSub()" class="modal-submit-btn">Добавить подписку</button>
    </div>
  </div>

  <!-- JAVASCRIPT LOGIC -->
  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      try { tg.enableClosingConfirmation(); } catch(e) {}
    }

    function haptic(type = 'light') {
      try {
        if (tg?.HapticFeedback) {
          if (type === 'light') tg.HapticFeedback.impactOccurred('light');
          else if (type === 'medium') tg.HapticFeedback.impactOccurred('medium');
          else if (type === 'heavy') tg.HapticFeedback.impactOccurred('heavy');
        }
      } catch(e) {}
    }

    // THEME SWITCHER ENGINE
    const THEMES = {
      'ios': { name: 'iOS 18', emoji: '🍏' },
      'visionos': { name: 'VisionOS', emoji: '🥽' },
      'cyber': { name: 'Cyber HUD', emoji: '⚡' },
      'bento': { name: 'Bento Lux', emoji: '🧭' }
    };

    function selectTheme(themeId) {
      if (!THEMES[themeId]) themeId = 'ios';
      haptic('medium');
      document.documentElement.setAttribute('data-theme', themeId);
      localStorage.setItem('aigem_theme', themeId);

      const info = THEMES[themeId];
      const curName = document.getElementById('cur-theme-name');
      const curEmoji = document.getElementById('cur-theme-emoji');
      if (curName) curName.innerText = info.name;
      if (curEmoji) curEmoji.innerText = info.emoji;

      // Update check marks
      Object.keys(THEMES).forEach(k => {
        const item = document.getElementById('theme-opt-' + k);
        const check = document.getElementById('check-' + k);
        if (item) item.classList.toggle('selected', k === themeId);
        if (check) check.innerText = (k === themeId) ? '✓' : '';
      });

      closeModal('modal-theme-select');
    }

    function initTheme() {
      const saved = localStorage.getItem('aigem_theme') || 'ios';
      selectTheme(saved);
    }

    function showToast(text, duration = 2500) {
      const t = document.getElementById('ui-toast');
      const txt = document.getElementById('ui-toast-text');
      if (t && txt) {
        txt.innerText = text;
        t.style.display = 'flex';
        t.style.opacity = '1';
        setTimeout(() => {
          t.style.opacity = '0';
          setTimeout(() => { t.style.display = 'none'; }, 250);
        }, duration);
      }
    }

    async function openInBot(command) {
      haptic('medium');
      const cmd = (command || '').trim();
      const lower = cmd.toLowerCase();

      // 1. Internal Dashboard Tab Navigation (never close dashboard!)
      if (lower.includes('кбжу') || lower.includes('/food') || lower === 'еда') {
        switchTab('health');
        switchHealthSubTab('food');
        return;
      }
      if (lower.includes('сон') || lower.includes('/sleep')) {
        switchTab('health');
        switchHealthSubTab('sleep');
        return;
      }
      if (lower.includes('кредит') || lower.includes('/credit')) {
        switchTab('finance');
        switchFinanceSubTab('loan');
        return;
      }
      if (lower.includes('подписк') || lower.includes('/subs')) {
        switchTab('finance');
        switchFinanceSubTab('subs');
        return;
      }
      if (lower.includes('дом') || lower.includes('/home')) {
        switchTab('smart_home');
        return;
      }
      if (lower.includes('погод') || lower.includes('/weather')) {
        switchTab('digest');
        return;
      }
      if (lower.includes('дни рожд') || lower.includes('рожд') || lower.includes('/list')) {
        switchTab('tasks');
        setBdayFilter('all');
        return;
      }
      if (lower.includes('напомина') || lower.includes('/remind') || lower.includes('/reminders')) {
        switchTab('tasks');
        return;
      }

      // 2. Chat Module Dispatch
      showToast('💬 Перехожу в диалог с ботом...');
      try {
        await fetch('/api/bot/dispatch_command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: cmd })
        });
      } catch (e) {
        console.warn('Dispatch API issue:', e);
      }

      // Close Telegram Mini App smoothly so user returns to active bot chat
      if (window.Telegram?.WebApp) {
        const twa = window.Telegram.WebApp;
        try {
          if (twa.sendData) twa.sendData(cmd);
        } catch(e) {}
        setTimeout(() => {
          try { twa.close(); } catch(e) {}
        }, 450);
        return;
      }
      window.location.href = 'https://t.me/MyAiGem_bot';
    }

    function safeCreateIcons() {
      try {
        if (typeof lucide !== 'undefined' && lucide && typeof lucide.createIcons === 'function') {
          lucide.createIcons();
        }
      } catch (e) {}
    }

    function switchTab(tabId) {
      haptic('light');
      document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
      document.querySelectorAll('.nav-seg-btn').forEach(el => el.classList.remove('active'));

      const targetTab = document.getElementById('tab-' + tabId);
      const targetBtn = document.getElementById('tab-btn-' + tabId);
      if (targetTab) {
        targetTab.style.display = 'flex';
        targetTab.style.flexDirection = 'column';
        targetTab.style.gap = '12px';
      }
      if (targetBtn) targetBtn.classList.add('active');
      safeCreateIcons();
    }

    function switchFinanceSubTab(sub) {
      haptic('light');
      const pLoan = document.getElementById('f-panel-loan');
      const pSubs = document.getElementById('f-panel-subs');
      const bLoan = document.getElementById('f-subtab-btn-loan');
      const bSubs = document.getElementById('f-subtab-btn-subs');

      if (sub === 'loan') {
        pLoan.style.display = 'flex';
        pSubs.style.display = 'none';
        bLoan.style.background = 'var(--accent)';
        bLoan.style.color = '#FFF';
        bSubs.style.background = 'transparent';
        bSubs.style.color = 'var(--text-secondary)';
      } else {
        pLoan.style.display = 'none';
        pSubs.style.display = 'flex';
        bLoan.style.background = 'transparent';
        bLoan.style.color = 'var(--text-secondary)';
        bSubs.style.background = 'var(--accent)';
        bSubs.style.color = '#FFF';
      }
      safeCreateIcons();
    }

    function switchHealthSubTab(sub) {
      haptic('light');
      const pFood = document.getElementById('h-panel-food');
      const pSleep = document.getElementById('h-panel-sleep');
      const bFood = document.getElementById('h-subtab-btn-food');
      const bSleep = document.getElementById('h-subtab-btn-sleep');

      if (sub === 'food') {
        pFood.style.display = 'flex';
        pSleep.style.display = 'none';
        bFood.style.background = 'var(--accent)';
        bFood.style.color = '#FFF';
        bSleep.style.background = 'transparent';
        bSleep.style.color = 'var(--text-secondary)';
      } else {
        pFood.style.display = 'none';
        pSleep.style.display = 'flex';
        bFood.style.background = 'transparent';
        bFood.style.color = 'var(--text-secondary)';
        bSleep.style.background = 'var(--accent)';
        bSleep.style.color = '#FFF';
        runSleepCalc();
      }
      safeCreateIcons();
    }

    function toggleAccordion(id) {
      haptic('light');
      const el = document.getElementById(id);
      if (el) {
        el.style.display = (el.style.display === 'none') ? 'flex' : 'none';
      }
    }

    function openModal(id) {
      haptic('medium');
      const m = document.getElementById(id);
      if (m) m.classList.add('open');
      safeCreateIcons();
    }
    function closeModal(id) {
      haptic('light');
      const m = document.getElementById(id);
      if (m) m.classList.remove('open');
    }

    function renderCleanTelegramHtml(raw) {
      if (!raw) return 'Сводка погоды формируется...';
      return raw.trim().split(String.fromCharCode(10)).join('<br>');
    }

    let currentData = null;
    let bdayFilter = 'all';

    async function fetchDashboardData(isManual = false) {
      const refIcon = document.getElementById('refresh-icon');
      if (refIcon) { refIcon.style.animation = 'spin 0.8s linear infinite'; }

      try {
        const url = isManual ? '/api/dashboard/data?refresh=true' : '/api/dashboard/data';
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);

        const resp = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        currentData = await resp.json();
        renderDashboard(currentData);
        if (isManual) haptic('medium');
      } catch (err) {
        console.warn('Dashboard fetch issue:', err);
      } finally {
        if (refIcon) { refIcon.style.animation = ''; }
      }
    }

    async function refreshWeatherDirect() {
      haptic('medium');
      try {
        const resp = await fetch('/api/weather/refresh', { method: 'POST' });
        const res = await resp.json();
        if (res.success && res.weather) {
          if (currentData) currentData.weather = res.weather;
          renderWeatherSection(res.weather);
        }
      } catch(e) { console.error(e); }
    }

    async function syncBirthdaysCloud() {
      haptic('heavy');
      const icon = document.getElementById('bday-sync-icon');
      if (icon) icon.style.animation = 'spin 0.8s linear infinite';

      try {
        const resp = await fetch('/api/birthdays/sync', { method: 'POST' });
        const res = await resp.json();
        if (res.success) {
          await fetchDashboardData();
          alert('✅ Синхронизировано с GitHub! Всего в базе: ' + res.count + ' чел.');
        }
      } catch(e) {
        console.error(e);
      } finally {
        if (icon) icon.style.animation = '';
      }
    }

    function renderWeatherSection(w) {
      if (!w) return;
      if (w.temp) document.getElementById('w-temp').innerText = w.temp;
      if (w.condition) document.getElementById('w-condition').innerHTML = '<span>' + w.condition + '</span>';
      if (w.feels) document.getElementById('w-feels').innerText = w.feels;
      if (w.humidity) document.getElementById('w-humidity').innerText = w.humidity;
      if (w.wind) document.getElementById('w-wind').innerText = w.wind;
      if (w.location_display) document.getElementById('w-location').innerText = w.location_display;

      const hourlyContainer = document.getElementById('w-hourly-container');
      if (w.hourly && w.hourly.length > 0) {
        let hHtml = '';
        w.hourly.forEach(h => {
          const rainBadge = h.rain_chance >= 35 ? '<span style="font-size:9px;color:var(--accent);font-weight:700;">🌧 ' + h.rain_chance + '%</span>' : '<span style="font-size:9px;color:var(--text-muted);">ясно</span>';
          hHtml += `
            <div style="flex:0 0 70px;padding:8px;border-radius:14px;background:var(--card-bg);border:1px solid var(--card-border);text-align:center;display:flex;flex-direction:column;align-items:center;gap:3px;">
              <span style="font-size:10px;color:var(--text-secondary);">${h.time}</span>
              <span style="font-size:16px;">${h.icon || '🌤'}</span>
              <span style="font-size:12px;font-weight:700;color:#FFF;">${h.temp}</span>
              ${rainBadge}
            </div>
          `;
        });
        hourlyContainer.innerHTML = hHtml;
      }

      const synopticEl = document.getElementById('w-full-text');
      if (synopticEl) {
        synopticEl.innerHTML = renderCleanTelegramHtml(w.report || w.text);
      }
    }

    function renderDashboard(data) {
      if (!data) return;
      if (data.server_time_msk) {
        document.getElementById('header-time').innerText = data.server_time_msk + ' MSK';
      }

      const sh = data.smart_home || {};
      if (sh.climate && sh.climate.length > 0) {
        const c0 = sh.climate[0];
        document.getElementById('sh-temp-val').innerText = c0.temperature + '°C';
        if (c0.humidity) document.getElementById('sh-hum-val').innerText = '💧 ' + c0.humidity + '% влажность';
      }

      if (sh.security_alerts && sh.security_alerts.length > 0) {
        document.getElementById('sh-sec-title').innerText = 'Внимание: тревога!';
        document.getElementById('sh-sec-title').style.color = '#FF375F';
        document.getElementById('sh-sec-sub').innerText = sh.security_alerts[0];
      } else {
        document.getElementById('sh-sec-title').innerText = 'Всё спокойно';
        document.getElementById('sh-sec-title').style.color = 'var(--accent-green)';
        document.getElementById('sh-sec-sub').innerText = 'Протечек нет • Двери 🔒';
      }

      const activeCount = sh.active_count || 0;
      document.getElementById('sh-active-counter').innerText = 'Активно: ' + activeCount + ' ламп';

      const devListEl = document.getElementById('sh-all-devices');
      const devCountEl = document.getElementById('sh-total-dev-count');
      if (sh.devices) {
        devCountEl.innerText = sh.devices.length;
        let dHtml = '';
        sh.devices.forEach(d => {
          const isPower = d.has_on_off;
          const isOn = d.is_on;
          const statusText = isOn ? 'ВКЛ' : 'ВЫКЛ';
          const bgStatus = isOn ? 'background:rgba(10,132,255,0.2);color:var(--accent);border:1px solid var(--accent);' : 'background:rgba(255,255,255,0.06);color:var(--text-secondary);border:1px solid var(--card-border);';
          
          dHtml += `
            <div class="group-row">
              <div class="group-row-left">
                <div class="badge-icon-square ${isOn ? 'badge-cyan' : ''}" style="${!isOn ? 'background:rgba(255,255,255,0.08);color:var(--text-secondary);' : ''}">
                  <i data-lucide="${isPower ? 'lightbulb' : 'cpu'}" style="width:16px;height:16px;"></i>
                </div>
                <div>
                  <div style="font-size:13px;font-weight:600;color:#FFF;">${d.name}</div>
                  <div style="font-size:10px;color:var(--text-secondary);">${d.room || 'Дом'}</div>
                </div>
              </div>
              ${isPower ? `
                <button onclick="toggleDeviceById('${d.id}', ${!isOn})" style="padding:4px 10px;border-radius:8px;font-size:11px;font-weight:700;cursor:pointer;${bgStatus}">
                  ${statusText}
                </button>
              ` : `
                <span style="font-size:10px;color:var(--text-muted);">датчик</span>
              `}
            </div>
          `;
        });
        devListEl.innerHTML = dHtml;
      }

      renderWeatherSection(data.weather);

      if (data.birthdays) {
        document.getElementById('bday-total-badge').innerText = data.birthdays.length;
        renderFilteredBirthdays();
      }

      const rListEl = document.getElementById('reminders-list');
      if (data.reminders && data.reminders.length > 0) {
        let rHtml = '';
        data.reminders.forEach(r => {
          rHtml += `
            <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;padding:12px;">
              <div style="display:flex;align-items:center;gap:10px;">
                <button onclick="doneReminder('${r.id}')" style="width:26px;height:26px;border-radius:8px;border:1px solid var(--accent-green);background:transparent;color:var(--accent-green);display:flex;align-items:center;justify-content:center;cursor:pointer;">
                  <i data-lucide="check" style="width:14px;height:14px;"></i>
                </button>
                <div>
                  <div style="font-size:13px;font-weight:600;color:#FFF;">${r.text}</div>
                  <div style="font-size:10px;color:var(--accent);">${r.target_display}</div>
                </div>
              </div>
              <button onclick="deleteReminder('${r.id}')" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:4px;">
                <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
              </button>
            </div>
          `;
        });
        rListEl.innerHTML = rHtml;
      } else {
        rListEl.innerHTML = '<div style="font-size:11px;color:var(--text-secondary);text-align:center;padding:12px;">Все задачи выполнены! ✨</div>';
      }

      const food = data.food || {};
      const totalKcal = food.total_calories || 0;
      const goalKcal = food.goal_calories || 2200;
      document.getElementById('food-total-kcal').innerText = totalKcal;
      document.getElementById('food-goal-kcal').innerText = goalKcal;
      document.getElementById('food-p').innerText = (food.total_protein || 0) + 'г';
      document.getElementById('food-f').innerText = (food.total_fat || 0) + 'г';
      document.getElementById('food-c').innerText = (food.total_carbs || 0) + 'г';

      const pct = Math.min(100, Math.round((totalKcal / goalKcal) * 100));
      document.getElementById('food-progress-bar').style.width = pct + '%';

      const mealsListEl = document.getElementById('food-meals-list');
      if (food.meals && food.meals.length > 0) {
        let mHtml = '';
        food.meals.forEach(m => {
          mHtml += `
            <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;padding:12px;">
              <div>
                <div style="font-size:13px;font-weight:700;color:#FFF;">${m.dish_name}</div>
                <div style="font-size:10px;color:var(--text-secondary);">${m.time} • Б:${m.protein}г Ж:${m.fat}г У:${m.carbs}г</div>
              </div>
              <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:12px;font-weight:700;color:var(--accent-green);">${m.calories} ккал</span>
                <button onclick="deleteFoodMeal('${m.id}')" style="background:none;border:none;color:var(--text-muted);cursor:pointer;">
                  <i data-lucide="trash" style="width:13px;height:13px;"></i>
                </button>
              </div>
            </div>
          `;
        });
        mealsListEl.innerHTML = mHtml;
      } else {
        mealsListEl.innerHTML = '<div style="font-size:11px;color:var(--text-secondary);text-align:center;padding:10px;">Записей о питании сегодня нет</div>';
      }

      renderSubscriptionsAndRules(data.subscriptions, data.custom_rules);
      renderCountryFeatured(data.country_featured);
      safeCreateIcons();
    }

    function renderCountryFeatured(featuredList) {
      const container = document.getElementById('country-featured-list');
      if (!container) return;
      if (!featuredList || featuredList.length === 0) return;

      let html = '';
      featuredList.forEach(r => {
        const mapsUrl = 'https://yandex.ru/maps/?text=' + encodeURIComponent(r.geo_query || r.name);
        const shortPrice = (r.price || 'По запросу').split('/')[0].trim();
        html += `
          <div class="resort-card">
            <div class="resort-header-row">
              <div>
                <div class="resort-name">${r.name}</div>
                <div class="resort-cat">${r.category}</div>
              </div>
              <span class="resort-price-pill">${shortPrice}</span>
            </div>
            <div class="resort-meta-line">
              <span>📍</span>
              <span>${r.location}</span>
            </div>
            <div class="resort-meta-line" style="color:var(--text-secondary);">
              <span>👶</span>
              <span>${r.kid_friendly}</span>
            </div>
            <div class="resort-actions-row">
              <a href="${mapsUrl}" target="_blank" class="btn-card-secondary">
                <i data-lucide="map-pin" style="width:13px;height:13px;"></i>
                <span>Карта</span>
              </a>
              <button onclick="openInBot('Расскажи подробнее про ${r.name}')" class="btn-card-primary">
                <i data-lucide="message-square" style="width:13px;height:13px;"></i>
                <span>Спросить в боте</span>
              </button>
            </div>
          </div>
        `;
      });
      container.innerHTML = html;
      safeCreateIcons();
    }

    function setBdayFilter(filter) {
      bdayFilter = filter;
      document.querySelectorAll('.bday-flt-btn').forEach(b => {
        b.style.background = 'var(--nav-bg)';
        b.style.color = 'var(--text-secondary)';
      });
      const activeBtn = document.getElementById('bday-flt-' + filter);
      if (activeBtn) {
        activeBtn.style.background = 'var(--accent)';
        activeBtn.style.color = '#FFF';
      }
      renderFilteredBirthdays();
    }

    function renderFilteredBirthdays() {
      if (!currentData || !currentData.birthdays) return;
      const bListEl = document.getElementById('birthdays-list');
      let list = [...currentData.birthdays];

      if (bdayFilter === 'upcoming') {
        list = list.slice(0, 5);
      } else if (bdayFilter === 'family') {
        list = list.filter(b => (b.note && b.note.toLowerCase().includes('семь')) || ['мама', 'папа', 'брат', 'любимая жена'].includes(b.name.toLowerCase()));
      }

      if (list.length > 0) {
        let bHtml = '';
        list.forEach(b => {
          const daysText = b.days_left === 0 ? '🎉 СЕГОДНЯ!' : (b.days_left === 1 ? 'Завтра!' : 'через ' + b.days_left + ' дн.');
          const badgeColor = b.days_left <= 3 ? 'background:rgba(255,55,95,0.15);color:#FF375F;border:1px solid rgba(255,55,95,0.3);' : 'background:rgba(255,255,255,0.06);color:var(--text-secondary);border:1px solid var(--card-border);';

          bHtml += `
            <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;padding:12px;">
              <div style="display:flex;align-items:center;gap:12px;">
                <div class="badge-icon-square badge-pink" style="font-weight:700;">
                  ${b.day}
                </div>
                <div>
                  <div style="font-size:13px;font-weight:700;color:#FFF;">${b.name}</div>
                  <div style="font-size:10px;color:var(--text-secondary);">${b.date_display} ${b.age_display ? '• ' + b.age_display : ''}</div>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:6px;">
                <span style="padding:3px 7px;border-radius:8px;font-size:10px;font-weight:700;${badgeColor}">${daysText}</span>
                <button onclick="deleteBirthday('${b.id}', '${b.name}')" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:4px;">
                  <i data-lucide="trash-2" style="width:13px;height:13px;"></i>
                </button>
              </div>
            </div>
          `;
        });
        bListEl.innerHTML = bHtml;
      } else {
        bListEl.innerHTML = '<div style="font-size:11px;color:var(--text-secondary);text-align:center;padding:12px;">Дней рождения по запросу не найдено</div>';
      }
      safeCreateIcons();
    }

    function renderSubscriptionsAndRules(subsData, rulesData) {
      const sList = document.getElementById('subscriptions-list');
      if (subsData) {
        const total = subsData.total_monthly || 0;
        document.getElementById('sub-total-sum').innerText = total.toLocaleString('ru-RU') + ' ₽';
        const items = subsData.items || [];
        document.getElementById('sub-count-text').innerText = items.length + ' активных подписок';

        if (items.length > 0) {
          let sHtml = '';
          items.forEach(s => {
            sHtml += `
              <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;padding:12px;">
                <div style="display:flex;align-items:center;gap:10px;">
                  <div class="badge-icon-square badge-cyan">💳</div>
                  <div>
                    <div style="font-size:13px;font-weight:700;color:#FFF;">${s.name}</div>
                    <div style="font-size:10px;color:var(--text-secondary);">${s.category || 'Сервисы'} • Списание ${s.payment_day || 1}-го числа</div>
                  </div>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                  <span style="font-size:13px;font-weight:700;color:var(--accent);">${s.amount.toLocaleString('ru-RU')} ₽</span>
                  <button onclick="deleteSub('${s.id}')" style="background:none;border:none;color:var(--text-muted);cursor:pointer;">
                    <i data-lucide="trash-2" style="width:13px;height:13px;"></i>
                  </button>
                </div>
              </div>
            `;
          });
          sList.innerHTML = sHtml;
        } else {
          sList.innerHTML = '<div style="font-size:11px;color:var(--text-secondary);text-align:center;padding:10px;">Подписок пока нет</div>';
        }
      }

      const rList = document.getElementById('rules-list');
      if (rulesData && rulesData.length > 0) {
        let rHtml = '';
        rulesData.forEach(r => {
          const isActive = r.is_active;
          const statusBg = isActive ? 'background:rgba(48,209,88,0.15);color:var(--accent-green);border:1px solid rgba(48,209,88,0.3);' : 'background:rgba(255,255,255,0.06);color:var(--text-muted);border:1px solid var(--card-border);';
          rHtml += `
            <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;padding:12px;">
              <div>
                <div style="font-size:13px;font-weight:700;color:#FFF;">${r.title}</div>
                <div style="font-size:10px;color:var(--text-secondary);">${r.action_text || 'Напоминание'}</div>
              </div>
              <button onclick="toggleRule('${r.id}')" style="padding:4px 9px;border-radius:8px;font-size:10px;font-weight:700;cursor:pointer;${statusBg}">
                ${isActive ? 'АКТИВНО 🟢' : 'ВЫКЛ ⚪'}
              </button>
            </div>
          `;
        });
        rList.innerHTML = rHtml;
      }
    }

    async function toggleDeviceById(deviceId, state) {
      haptic('medium');
      try {
        await fetch('/api/smart_home/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device_id: deviceId, state: state })
        });
        fetchDashboardData();
      } catch(e) { console.error(e); }
    }

    async function toggleDeviceByName(name, uiId) {
      haptic('medium');
      try {
        await fetch('/api/smart_home/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name, state: true })
        });
        fetchDashboardData();
      } catch(e) { console.error(e); }
    }

    async function turnOffAllLights() {
      haptic('heavy');
      if (confirm('Выключить весь свет и приборы?')) {
        try {
          await fetch('/api/smart_home/all_off', { method: 'POST' });
          fetchDashboardData();
        } catch(e) { console.error(e); }
      }
    }

    async function deleteBirthday(id, name) {
      haptic('heavy');
      if (confirm('Удалить день рождения для "' + name + '"?')) {
        await fetch('/api/birthdays/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: id })
        });
        fetchDashboardData();
      }
    }

    async function doneReminder(id) {
      haptic('light');
      await fetch('/api/reminders/done', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
      });
      fetchDashboardData();
    }

    async function deleteReminder(id) {
      haptic('light');
      await fetch('/api/reminders/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
      });
      fetchDashboardData();
    }

    async function submitAddBirthday() {
      const name = document.getElementById('m-bday-name').value;
      const date = document.getElementById('m-bday-date').value;
      const note = document.getElementById('m-bday-note').value;
      if (!name || !date) return alert('Заполните имя и дату!');
      haptic('medium');
      await fetch('/api/birthdays/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, date, note })
      });
      closeModal('modal-add-birthday');
      fetchDashboardData();
    }

    async function submitAddReminder() {
      const text = document.getElementById('m-rem-text').value;
      const time = document.getElementById('m-rem-time').value;
      if (!text) return alert('Введите текст напоминания!');
      haptic('medium');
      await fetch('/api/reminders/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, target_display: time })
      });
      closeModal('modal-add-reminder');
      fetchDashboardData();
    }

    async function submitAddFood() {
      const dish_name = document.getElementById('m-food-name').value;
      const calories = parseInt(document.getElementById('m-food-kcal').value || 0);
      const protein = parseFloat(document.getElementById('m-food-p').value || 0);
      const fat = parseFloat(document.getElementById('m-food-f').value || 0);
      const carbs = parseFloat(document.getElementById('m-food-c').value || 0);
      if (!dish_name || !calories) return alert('Введите название и калории!');
      haptic('medium');
      await fetch('/api/food/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dish_name, calories, protein, fat, carbs })
      });
      closeModal('modal-add-food');
      fetchDashboardData();
    }

    async function deleteFoodMeal(id) {
      haptic('light');
      await fetch('/api/food/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      fetchDashboardData();
    }

    async function submitAddSub() {
      const name = document.getElementById('m-sub-name').value;
      const amount = parseFloat(document.getElementById('m-sub-amount').value || 0);
      const payment_day = parseInt(document.getElementById('m-sub-day').value || 1);
      const category = document.getElementById('m-sub-cat').value || 'Сервисы';
      if (!name || amount <= 0) return alert('Заполните название и сумму!');
      haptic('medium');
      await fetch('/api/subscriptions/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, amount, payment_day, category })
      });
      closeModal('modal-add-sub');
      fetchDashboardData();
    }

    async function deleteSub(id) {
      haptic('light');
      if (confirm('Удалить регулярный платеж?')) {
        await fetch('/api/subscriptions/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sub_id: id })
        });
        fetchDashboardData();
      }
    }

    async function toggleRule(id) {
      haptic('light');
      await fetch('/api/rules/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_id: id })
      });
      fetchDashboardData();
    }

    // LOAN CALC
    function formatYearsRu(months) {
      const y = months / 12;
      if (months % 12 === 0) {
        const last10 = y % 10;
        let word = 'лет';
        if (last10 === 1 && y !== 11) word = 'год';
        else if (last10 >= 2 && last10 <= 4 && (y < 12 || y > 14)) word = 'года';
        return y + ' ' + word;
      }
      return y.toFixed(1) + ' г.';
    }

    function runLoanCalc() {
      const amount = parseFloat(document.getElementById('calc-inp-amount')?.value || 1000000);
      const rate = parseFloat(document.getElementById('calc-inp-rate')?.value || 18.5);
      const months = parseInt(document.getElementById('calc-inp-months')?.value || 60);

      document.getElementById('calc-lbl-amount').innerText = amount.toLocaleString('ru-RU') + ' ₽';
      document.getElementById('calc-lbl-rate').innerText = rate.toFixed(1) + ' %';
      document.getElementById('calc-lbl-months').innerText = months + ' мес. (' + formatYearsRu(months) + ')';

      let monthlyPayment = 0;
      let totalInterest = 0;

      if (rate <= 0) {
        monthlyPayment = amount / months;
      } else {
        const monthlyRate = rate / 12 / 100;
        const factor = (monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
        monthlyPayment = amount * factor;
        const totalPayout = monthlyPayment * months;
        totalInterest = totalPayout - amount;
      }

      document.getElementById('calc-res-payment').innerText = Math.round(monthlyPayment).toLocaleString('ru-RU') + ' ₽';
      document.getElementById('calc-res-interest').innerText = Math.round(totalInterest).toLocaleString('ru-RU') + ' ₽';
    }

    // SLEEP CALC
    let sleepMode = 'now';
    function setSleepCalcMode(mode) {
      sleepMode = mode;
      const bNow = document.getElementById('slp-mode-now');
      const bWake = document.getElementById('slp-mode-wake');
      const pWake = document.getElementById('slp-wake-picker');
      if (mode === 'now') {
        bNow.style.background = 'rgba(10,132,255,0.15)';
        bNow.style.borderColor = 'var(--accent)';
        bNow.style.color = 'var(--accent)';
        bWake.style.background = 'var(--nav-bg)';
        bWake.style.borderColor = 'var(--card-border)';
        bWake.style.color = 'var(--text-secondary)';
        pWake.style.display = 'none';
      } else {
        bNow.style.background = 'var(--nav-bg)';
        bNow.style.borderColor = 'var(--card-border)';
        bNow.style.color = 'var(--text-secondary)';
        bWake.style.background = 'rgba(10,132,255,0.15)';
        bWake.style.borderColor = 'var(--accent)';
        bWake.style.color = 'var(--accent)';
        pWake.style.display = 'block';
      }
      runSleepCalc();
    }

    function runSleepCalc() {
      const listEl = document.getElementById('slp-results-list');
      if (!listEl) return;
      const FALL_MIN = 14;
      const CYCLE_MIN = 90;

      if (sleepMode === 'now') {
        const now = new Date();
        const asleepTime = new Date(now.getTime() + FALL_MIN * 60000);
        const cycles = [
          { count: 6, hrs: '9.0 ч', badge: '⭐ Идеально' },
          { count: 5, hrs: '7.5 ч', badge: '🌟 Норма' },
          { count: 4, hrs: '6.0 ч', badge: '✨ Бодрость' },
          { count: 3, hrs: '4.5 ч', badge: '⚡ Минимум' }
        ];
        let html = '';
        cycles.forEach(c => {
          const wake = new Date(asleepTime.getTime() + c.count * CYCLE_MIN * 60000);
          const hh = String(wake.getHours()).padStart(2, '0');
          const mm = String(wake.getMinutes()).padStart(2, '0');
          html += `
            <div class="app-card" style="display:flex;align-items:center;justify-content:space-between;padding:10px;">
              <div>
                <span style="font-size:14px;font-weight:800;color:#FFF;">${hh}:${mm}</span>
                <span style="font-size:10px;color:var(--accent);margin-left:4px;">(${c.hrs})</span>
              </div>
              <span style="padding:2px 7px;border-radius:6px;font-size:10px;font-weight:700;background:rgba(100,210,255,0.15);color:var(--accent);">${c.badge}</span>
            </div>
          `;
        });
        listEl.innerHTML = html;
      }
    }

    function initApp() {
      // 1. Restore Theme
      initTheme();

      // 2. Hide loading screen
      function hideLoadingScreen() {
        const ls = document.getElementById('loading-screen');
        if (ls) {
          ls.style.transition = 'opacity 0.35s ease';
          ls.style.opacity = '0';
          setTimeout(() => { if (ls && ls.parentNode) ls.parentNode.removeChild(ls); }, 380);
        }
      }
      const loadingTimeout = setTimeout(hideLoadingScreen, 1500);

      // 3. Telegram WebApp
      if (typeof Telegram !== 'undefined' && Telegram.WebApp) {
        try { Telegram.WebApp.ready(); Telegram.WebApp.expand(); } catch(e) {}
      }

      // 4. Lucide icons
      function initIcons() {
        safeCreateIcons();
        if (typeof lucide === 'undefined') setTimeout(initIcons, 300);
      }
      initIcons();

      // 5. Calculators
      try { runLoanCalc(); } catch(e) {}
      try { runSleepCalc(); } catch(e) {}

      // 6. Fetch initial data
      fetchDashboardData().then(() => {
        clearTimeout(loadingTimeout);
        hideLoadingScreen();
      }).catch(() => {
        clearTimeout(loadingTimeout);
        hideLoadingScreen();
      });

      // 7. Auto refresh
      setInterval(() => fetchDashboardData(false), 30000);
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initApp);
    } else {
      initApp();
    }
  </script>
</body>
</html>
"""
