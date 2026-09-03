# -*- coding: utf-8 -*-
TMA_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>AiGem Dashboard</title>
  <!-- Telegram WebApp SDK — defer so it doesn't block rendering -->
  <script>
    // Minimal Telegram WebApp shim in case SDK is slow
    window.Telegram = window.Telegram || { WebApp: { ready: function(){}, expand: function(){}, HapticFeedback: { impactOccurred: function(){} } } };
  </script>
  <script src="https://telegram.org/js/telegram-web-app.js" defer></script>
  <!-- Lucide Icons — loaded async, not blocking -->
  <script src="https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js" async></script>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      background-color: #090d16;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
      min-height: 100vh;
      padding-bottom: 80px;
    }
    /* Tailwind var overrides for TG theme */
    body[data-tg-theme] {
      background-color: var(--tg-theme-bg-color, #090d16);
      color: var(--tg-theme-text-color, #f8fafc);
    }
    .glass {
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .glass-card {
      background: rgba(15, 23, 42, 0.90);
      border: 1px solid rgba(255, 255, 255, 0.07);
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
      border-radius: 1rem;
    }
    .glass-card:active { transform: scale(0.985); }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    .tab-btn { transition: all 0.2s ease; }
    .tab-btn.active { background: #06b6d4; color: #fff; box-shadow: 0 4px 12px rgba(6,182,212,0.3); }
    .tab-btn:not(.active) { background: transparent; color: #94a3b8; }
    .tab-btn:not(.active):hover { color: #e2e8f0; }

    /* NAV — compact enough for 6 tabs */
    .nav-tab-bar {
      display: flex;
      gap: 4px;
      overflow-x: auto;
      padding: 4px;
      background: rgba(5,7,12,0.7);
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.05);
      -ms-overflow-style: none;
      scrollbar-width: none;
    }
    .nav-tab-bar::-webkit-scrollbar { display: none; }
    .nav-tab-btn {
      flex: 0 0 auto;
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 6px 10px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
      color: #94a3b8;
      background: transparent;
    }
    .nav-tab-btn svg { width: 13px; height: 13px; flex-shrink: 0; }
    .nav-tab-btn.active {
      background: #06b6d4;
      color: #fff;
      box-shadow: 0 2px 8px rgba(6,182,212,0.35);
    }

    input[type=range] {
      -webkit-appearance: none;
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: #1e293b;
      outline: none;
    }
    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none;
      height: 18px; width: 18px;
      border-radius: 50%;
      background: #06b6d4;
      cursor: pointer;
      box-shadow: 0 0 6px rgba(6,182,212,0.6);
    }

    /* Loading overlay */
    #loading-screen {
      position: fixed; inset: 0;
      background: #090d16;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      z-index: 9999;
      transition: opacity 0.4s ease;
    }
    #loading-screen.hidden { opacity: 0; pointer-events: none; }
    .spinner {
      width: 40px; height: 40px;
      border: 3px solid rgba(6,182,212,0.2);
      border-top-color: #06b6d4;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes spin-pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.8); }
    }

    /* Tab sections — hidden by default, shown via JS */
    .tab-content { display: none; flex-direction: column; gap: 12px; }

    /* Modal overlay */
    .modal-overlay {
      position: fixed; inset: 0; z-index: 50;
      background: rgba(0,0,0,0.75);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .modal-overlay.open { display: flex; }
    .modal-box {
      background: rgba(15,23,42,0.97);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 20px;
      padding: 20px;
      width: 100%; max-width: 360px;
      display: flex; flex-direction: column; gap: 12px;
    }
    .modal-input {
      width: 100%; padding: 10px 14px;
      border-radius: 12px;
      background: rgba(15,23,42,1);
      border: 1px solid rgba(255,255,255,0.1);
      font-size: 12px; color: #f1f5f9;
      outline: none;
    }
    .modal-input:focus { border-color: #06b6d4; }
    .modal-btn-primary {
      width: 100%; padding: 11px;
      border-radius: 12px;
      font-size: 13px; font-weight: 700;
      border: none; cursor: pointer;
      color: #fff;
    }
    .modal-btn-primary.cyan { background: #06b6d4; box-shadow: 0 4px 16px rgba(6,182,212,0.3); }
    .modal-btn-primary.emerald { background: #10b981; box-shadow: 0 4px 16px rgba(16,185,129,0.3); }
    .modal-btn-primary.indigo { background: #6366f1; box-shadow: 0 4px 16px rgba(99,102,241,0.3); }

    /* Quick card grid helper */
    .quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .quick-card {
      background: rgba(15,23,42,0.9);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 14px;
      padding: 14px;
      display: flex; flex-direction: column;
      justify-content: space-between; gap: 10px;
      cursor: pointer;
      transition: transform 0.15s;
    }
    .quick-card:active { transform: scale(0.97); }
    .status-dot { width: 12px; height: 12px; border-radius: 50%; background: #334155; transition: background 0.2s; }
    .status-dot.on { background: #34d399; box-shadow: 0 0 6px #34d399; }
  </style>
</head>
<body>

  <!-- LOADING SCREEN -->
  <div id="loading-screen">
    <div style="text-align:center">
      <div class="spinner" style="margin:0 auto 16px"></div>
      <div style="font-size:13px;font-weight:600;color:#06b6d4;">AiGem Dashboard</div>
      <div style="font-size:11px;color:#64748b;margin-top:4px;">Загружаем данные...</div>
    </div>
  </div>

  <!-- TOP HEADER -->
  <header style="position:sticky;top:0;z-index:40;width:100%;max-width:512px;margin:0 auto;padding:10px 16px 8px;display:flex;align-items:center;justify-content:space-between;" class="glass" id="main-header">
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#06b6d4,#3b82f6);display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(6,182,212,0.3);">
        <i data-lucide="cpu" style="width:18px;height:18px;color:#fff;"></i>
      </div>
      <div>
        <div style="font-size:13px;font-weight:700;display:flex;align-items:center;gap:6px;">
          AiGem Super-Bot
          <span style="width:8px;height:8px;border-radius:50%;background:#34d399;display:inline-block;animation:spin-pulse 2s ease-in-out infinite;"></span>
        </div>
        <div style="font-size:11px;color:#94a3b8;" id="header-time">24/7 Cloud • MSK</div>
      </div>
    </div>
    <button onclick="fetchDashboardData(true)" style="padding:8px;border-radius:10px;background:rgba(30,41,59,0.8);border:1px solid rgba(255,255,255,0.1);cursor:pointer;" title="Обновить">
      <i data-lucide="refresh-cw" style="width:16px;height:16px;color:#06b6d4;" id="refresh-icon"></i>
    </button>
  </header>

  <!-- NAVIGATION TABS — 6 tabs with native CSS -->
  <nav style="position:sticky;top:57px;z-index:30;width:100%;max-width:512px;margin:0 auto;padding:6px 12px;background:rgba(9,13,22,0.95);backdrop-filter:blur(12px);">
    <div class="nav-tab-bar" id="nav-bar">
      <button class="nav-tab-btn active" id="tab-btn-smart_home" onclick="switchTab('smart_home')">
        <i data-lucide="home"></i>
        <span>Дом</span>
      </button>
      <button class="nav-tab-btn" id="tab-btn-digest" onclick="switchTab('digest')">
        <i data-lucide="cloud-sun"></i>
        <span>Погода</span>
      </button>
      <button class="nav-tab-btn" id="tab-btn-tasks" onclick="switchTab('tasks')">
        <i data-lucide="cake"></i>
        <span>ДР & Дела</span>
      </button>
      <button class="nav-tab-btn" id="tab-btn-finance" onclick="switchTab('finance')">
        <i data-lucide="credit-card"></i>
        <span>Финансы</span>
      </button>
      <button class="nav-tab-btn" id="tab-btn-health" onclick="switchTab('health')">
        <i data-lucide="activity"></i>
        <span>Здоровье</span>
      </button>
      <button class="nav-tab-btn" id="tab-btn-hub" onclick="switchTab('hub')">
        <i data-lucide="layout-grid"></i>
        <span>Модули</span>
      </button>
    </div>
  </nav>

  <!-- MAIN CONTENT CONTAINER -->
  <main style="width:100%;max-width:512px;margin:0 auto;padding:8px 16px;display:flex;flex-direction:column;gap:12px;">

    <!-- TAB 1: SMART HOME -->
    <section id="tab-smart_home" class="tab-content" style="display:flex;flex-direction:column;gap:12px;">

      <div class="grid grid-cols-2 gap-2.5">
        <div class="glass-card p-3.5 rounded-2xl flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400">
            <i data-lucide="thermometer" class="w-5 h-5"></i>
          </div>
          <div>
            <div class="text-[11px] text-slate-400">Климат в доме</div>
            <div class="text-lg font-bold text-white tracking-tight" id="sh-temp-val">24.7°C</div>
            <div class="text-[10px] text-slate-400" id="sh-hum-val">💧 48% влажность</div>
          </div>
        </div>

        <div class="glass-card p-3.5 rounded-2xl flex items-center space-x-3" id="sh-security-card">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400" id="sh-sec-icon-box">
            <i data-lucide="shield-check" class="w-5 h-5" id="sh-sec-icon"></i>
          </div>
          <div>
            <div class="text-[11px] text-slate-400">Безопасность</div>
            <div class="text-xs font-bold text-emerald-400" id="sh-sec-title">Всё спокойно</div>
            <div class="text-[10px] text-slate-400" id="sh-sec-sub">Протечек нет • Дверь 🔒</div>
          </div>
        </div>
      </div>

      <!-- MASTER SWITCH -->
      <div class="glass-card p-3.5 rounded-2xl flex items-center justify-between border border-cyan-500/20 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
            <i data-lucide="power" class="w-5 h-5"></i>
          </div>
          <div>
            <div class="text-xs font-bold text-white">Главный выключатель</div>
            <div class="text-[11px] text-slate-400" id="sh-active-counter">Активно: 0 ламп</div>
          </div>
        </div>
        <button onclick="turnOffAllLights()" class="px-3.5 py-2 rounded-xl bg-rose-500/20 border border-rose-500/30 text-rose-300 font-semibold text-xs active:scale-95 transition-transform flex items-center gap-1.5">
          <i data-lucide="zap-off" class="w-3.5 h-3.5"></i>
          <span>Выкл всё</span>
        </button>
      </div>

      <!-- QUICK PRIORITY SWITCHES -->
      <div>
        <div class="text-xs font-bold text-slate-400 px-1 mb-2 uppercase tracking-wider flex items-center justify-between">
          <span>Быстрое управление</span>
          <span class="text-[10px] text-cyan-400">Прямое API Яндекса</span>
        </div>

        <div class="grid grid-cols-2 gap-2.5" id="sh-priority-grid">
          <div class="glass-card p-3.5 rounded-2xl flex flex-col justify-between space-y-3 cursor-pointer transition-all" onclick="toggleDeviceByName('выключатель коридор', 'toggle-corridor')">
            <div class="flex items-center justify-between">
              <div class="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center" id="icon-corridor">
                <i data-lucide="lightbulb" class="w-4 h-4"></i>
              </div>
              <div class="w-3 h-3 rounded-full bg-slate-600 transition-colors" id="dot-corridor"></div>
            </div>
            <div>
              <div class="text-xs font-bold text-white">Свет Коридор</div>
              <div class="text-[10px] text-slate-400" id="st-corridor">Выключено</div>
            </div>
          </div>

          <div class="glass-card p-3.5 rounded-2xl flex flex-col justify-between space-y-3 cursor-pointer transition-all" onclick="toggleDeviceByName('свет ванная', 'toggle-bathroom')">
            <div class="flex items-center justify-between">
              <div class="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center" id="icon-bathroom">
                <i data-lucide="sparkles" class="w-4 h-4"></i>
              </div>
              <div class="w-3 h-3 rounded-full bg-slate-600 transition-colors" id="dot-bathroom"></div>
            </div>
            <div>
              <div class="text-xs font-bold text-white">Свет Ванная</div>
              <div class="text-[10px] text-slate-400" id="st-bathroom">Выключено</div>
            </div>
          </div>

          <div class="glass-card p-3.5 rounded-2xl flex flex-col justify-between space-y-3 cursor-pointer transition-all" onclick="toggleDeviceByName('вытяжка', 'toggle-hood')">
            <div class="flex items-center justify-between">
              <div class="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center" id="icon-hood">
                <i data-lucide="fan" class="w-4 h-4"></i>
              </div>
              <div class="w-3 h-3 rounded-full bg-slate-600 transition-colors" id="dot-hood"></div>
            </div>
            <div>
              <div class="text-xs font-bold text-white">Вытяжка</div>
              <div class="text-[10px] text-slate-400" id="st-hood">Выключено</div>
            </div>
          </div>

          <div class="glass-card p-3.5 rounded-2xl flex flex-col justify-between space-y-3 cursor-pointer transition-all" onclick="toggleDeviceByName('теплый пол', 'toggle-floor')">
            <div class="flex items-center justify-between">
              <div class="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center" id="icon-floor">
                <i data-lucide="flame" class="w-4 h-4"></i>
              </div>
              <div class="w-3 h-3 rounded-full bg-slate-600 transition-colors" id="dot-floor"></div>
            </div>
            <div>
              <div class="text-xs font-bold text-white">Тёплый пол</div>
              <div class="text-[10px] text-slate-400" id="st-floor">Выключено</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ACCORDION DEVICES -->
      <div class="glass-card p-3.5 rounded-2xl">
        <div class="flex items-center justify-between cursor-pointer" onclick="toggleAccordion('sh-all-devices')">
          <div class="flex items-center space-x-2.5">
            <i data-lucide="layout-grid" class="w-4 h-4 text-cyan-400"></i>
            <span class="text-xs font-bold text-white">Все устройства дома (<span id="sh-total-dev-count">...</span>)</span>
          </div>
          <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition-transform" id="acc-icon-sh-all-devices"></i>
        </div>

        <div id="sh-all-devices" class="hidden mt-3 space-y-2 pt-2 border-t border-white/5 max-h-72 overflow-y-auto pr-1">
          <div class="text-xs text-slate-400 text-center py-2">Загрузка списка устройств...</div>
        </div>
      </div>
    </section>

    <!-- TAB 2: DIGEST & WEATHER -->
    <section id="tab-digest" class="tab-content hidden space-y-3.5">
      <div class="glass-card p-4 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950/50 border border-blue-500/20">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-1.5 text-xs text-cyan-400 font-semibold">
              <i data-lucide="map-pin" class="w-3.5 h-3.5"></i>
              <span id="w-location">Санкт-Петербург (Приморский р-н)</span>
            </div>
            <div class="text-3xl font-extrabold text-white mt-1 tracking-tight" id="w-temp">+17.0°C</div>
            <div class="text-xs text-slate-300 mt-0.5 flex items-center gap-1" id="w-condition">
              <span>☁️ Пасмурно</span>
            </div>
          </div>
          <div class="flex flex-col items-end gap-2">
            <div class="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-cyan-300 shadow-lg shadow-cyan-500/10">
              <i data-lucide="cloud-sun" class="w-7 h-7"></i>
            </div>
            <button onclick="refreshWeatherDirect()" title="Обновить погоду со спутников" class="text-[10px] px-2.5 py-1 rounded-lg bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 font-semibold flex items-center gap-1 active:scale-95 transition-transform">
              <i data-lucide="refresh-cw" class="w-3 h-3" id="w-mini-spin"></i>
              <span>Обновить</span>
            </button>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-white/5 text-center">
          <div class="p-2 rounded-xl bg-slate-950/40">
            <div class="text-[10px] text-slate-400">Ощущается</div>
            <div class="text-xs font-bold text-slate-200 mt-0.5" id="w-feels">+15.0°C</div>
          </div>
          <div class="p-2 rounded-xl bg-slate-950/40">
            <div class="text-[10px] text-slate-400">Влажность</div>
            <div class="text-xs font-bold text-slate-200 mt-0.5" id="w-humidity">73%</div>
          </div>
          <div class="p-2 rounded-xl bg-slate-950/40">
            <div class="text-[10px] text-slate-400">Ветер</div>
            <div class="text-xs font-bold text-slate-200 mt-0.5" id="w-wind">3.1 м/с</div>
          </div>
        </div>
      </div>

      <!-- HOURLY FORECAST CARDS -->
      <div class="space-y-1.5">
        <div class="text-xs font-bold text-slate-400 px-1 uppercase tracking-wider flex items-center justify-between">
          <span>Почасовой прогноз</span>
          <span class="text-[10px] text-cyan-400">wttr & Open-Meteo</span>
        </div>
        <div id="w-hourly-container" class="flex space-x-2 overflow-x-auto no-scrollbar py-1">
          <div class="text-xs text-slate-400 py-2">Загрузка прогноза по часам...</div>
        </div>
      </div>

      <!-- FULL SYNOPTIC TEXT REPORT -->
      <div class="glass-card p-4 rounded-2xl space-y-2">
        <div class="flex items-center space-x-2 text-xs font-bold text-slate-300">
          <i data-lucide="sparkles" class="w-4 h-4 text-amber-400"></i>
          <span>Сводка от Умного Синоптика</span>
        </div>
        <div class="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-white/5" id="w-full-text">
          Загрузка актуального прогноза...
        </div>
      </div>
    </section>

    <!-- TAB 3: BIRTHDAYS & TASKS -->
    <section id="tab-tasks" class="tab-content hidden space-y-3.5">
      <div class="glass-card p-3.5 rounded-2xl space-y-2.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400 flex items-center justify-center">
              <i data-lucide="cake" class="w-4 h-4"></i>
            </div>
            <div>
              <div class="text-xs font-bold text-white">Дни рождения (<span id="bday-total-badge">23</span>)</div>
              <div class="text-[10px] text-emerald-400 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Синхронизировано с GitHub</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1.5">
            <button onclick="syncBirthdaysCloud()" title="Синхронизировать с GitHub" class="p-2 rounded-xl bg-slate-800 text-cyan-400 border border-white/10 active:scale-95 transition-transform flex items-center gap-1 text-xs">
              <i data-lucide="refresh-cw" class="w-3.5 h-3.5" id="bday-sync-icon"></i>
            </button>
            <button onclick="openModal('modal-add-birthday')" class="px-3 py-1.5 rounded-xl bg-cyan-500 text-white font-semibold text-xs flex items-center gap-1 shadow-md shadow-cyan-500/20 active:scale-95 transition-transform">
              <i data-lucide="plus" class="w-3.5 h-3.5"></i>
              <span>Добавить</span>
            </button>
          </div>
        </div>

        <div class="space-y-2 pt-1 border-t border-white/5">
          <input type="text" id="bday-search-inp" oninput="renderFilteredBirthdays()" placeholder="🔍 Поиск по имени или месяцу..." class="w-full px-3 py-1.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
          <div class="flex space-x-1.5 text-[11px]">
            <button onclick="setBdayFilter('all')" id="bday-flt-all" class="bday-flt-btn px-2.5 py-1 rounded-lg font-semibold bg-cyan-500 text-white">Все (23)</button>
            <button onclick="setBdayFilter('upcoming')" id="bday-flt-upcoming" class="bday-flt-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-800 text-slate-300">Ближайшие (5)</button>
            <button onclick="setBdayFilter('family')" id="bday-flt-family" class="bday-flt-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-800 text-slate-300">Семья</button>
          </div>
        </div>
      </div>

      <div class="space-y-2 max-h-96 overflow-y-auto pr-0.5 no-scrollbar" id="birthdays-list">
        <div class="text-xs text-slate-400 text-center py-3">Загрузка дней рождения...</div>
      </div>

      <!-- ACTIVE TASKS & REMINDERS -->
      <div class="pt-2">
        <div class="flex items-center justify-between px-1 mb-2">
          <div class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i>
            <span>Задачи и напоминания</span>
          </div>
          <button onclick="openModal('modal-add-reminder')" class="text-xs text-cyan-400 font-semibold flex items-center gap-1 active:scale-95 transition-transform">
            <i data-lucide="plus" class="w-3.5 h-3.5"></i>
            <span>Новая</span>
          </button>
        </div>

        <div class="space-y-2" id="reminders-list">
          <div class="text-xs text-slate-400 text-center py-3">Задач пока нет</div>
        </div>
      </div>
    </section>

    <!-- TAB 4: FINANCE -->
    <section id="tab-finance" class="tab-content hidden space-y-3.5">
      <div class="flex space-x-1.5 p-1 bg-slate-950/60 rounded-xl border border-white/5 text-xs">
        <button onclick="switchFinanceSubTab('loan')" id="f-subtab-btn-loan" class="flex-1 py-1.5 rounded-lg font-bold transition-all bg-cyan-500 text-white">
          Кредитный симулятор
        </button>
        <button onclick="switchFinanceSubTab('subs')" id="f-subtab-btn-subs" class="flex-1 py-1.5 rounded-lg font-bold transition-all text-slate-400">
          Подписки & Правила
        </button>
      </div>

      <!-- LOAN CALCULATOR: 1% TO 35%, 360 MONTHS MAX -->
      <div id="f-panel-loan" class="space-y-3.5">
        <div class="glass-card p-4 rounded-2xl space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2 text-xs font-bold text-cyan-400">
              <i data-lucide="percent" class="w-4 h-4"></i>
              <span>Кредитный симулятор & Выгода досрочки</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">Аннуитет</span>
          </div>

          <!-- INPUT: AMOUNT -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-400">Сумма кредита / ипотеки:</span>
              <span class="font-bold text-white text-sm" id="calc-lbl-amount">3 000 000 ₽</span>
            </div>
            <input type="range" min="100000" max="30000000" step="100000" value="3000000" id="calc-inp-amount" oninput="runLoanCalc()" class="w-full accent-cyan-400">
          </div>

          <!-- INPUT: RATE (FROM 1.0%) -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-400">Процентная ставка (от 1%):</span>
              <span class="font-bold text-white text-sm" id="calc-lbl-rate">12.0 %</span>
            </div>
            <input type="range" min="1.0" max="35.0" step="0.1" value="12.0" id="calc-inp-rate" oninput="runLoanCalc()" class="w-full accent-cyan-400">
            <div class="flex justify-between text-[10px] text-slate-500 mt-0.5">
              <span>1% (Льготная)</span>
              <span>6% (Семейная)</span>
              <span>18% (Потреб)</span>
              <span>35%</span>
            </div>
          </div>

          <!-- INPUT: MONTHS (UP TO 360 MONTHS) -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-400">Срок кредита (до 360 мес):</span>
              <span class="font-bold text-white text-sm" id="calc-lbl-months">60 мес. (5 лет)</span>
            </div>
            <input type="range" min="6" max="360" step="6" value="60" id="calc-inp-months" oninput="runLoanCalc()" class="w-full accent-cyan-400">
            <div class="flex justify-between text-[10px] text-slate-500 mt-0.5">
              <span>6 мес.</span>
              <span>10 лет (120м)</span>
              <span>20 лет (240м)</span>
              <span>30 лет (360м)</span>
            </div>
          </div>

          <!-- INPUT: EARLY MONTHLY -->
          <div class="pt-2 border-t border-white/5">
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-400">Досрочно каждый месяц:</span>
              <span class="font-bold text-emerald-400 text-sm" id="calc-lbl-early">10 000 ₽</span>
            </div>
            <input type="range" min="0" max="200000" step="2000" value="10000" id="calc-inp-early" oninput="runLoanCalc()" class="w-full accent-emerald-400">
          </div>

          <!-- RESULTS CARD -->
          <div class="p-3.5 rounded-xl bg-slate-950/70 border border-cyan-500/20 space-y-2.5">
            <div class="flex justify-between items-center text-xs">
              <span class="text-slate-400">Ежемесячный платеж:</span>
              <span class="text-base font-bold text-white" id="calc-res-payment">66 733 ₽</span>
            </div>
            <div class="flex justify-between items-center text-xs">
              <span class="text-slate-400">Переплата без досрочки:</span>
              <span class="font-semibold text-slate-300" id="calc-res-interest">1 004 000 ₽</span>
            </div>
            <div class="flex justify-between items-center text-xs pt-2 border-t border-white/5 text-emerald-400">
              <span class="flex items-center gap-1">🔥 <b>Экономия на процентах:</b></span>
              <span class="font-bold text-sm" id="calc-res-savings">184 200 ₽</span>
            </div>
            <div class="flex justify-between items-center text-xs text-cyan-300">
              <span class="flex items-center gap-1">⏱ <b>Новый срок выплаты:</b></span>
              <span class="font-bold" id="calc-res-new-term">48 мес. (-12 мес.)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- SUBSCRIPTIONS & RULES -->
      <div id="f-panel-subs" class="space-y-3.5 hidden">
        <div class="glass-card p-4 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-indigo-500/20">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-xs text-slate-400">Регулярные платежи в месяц</div>
              <div class="text-2xl font-black text-white mt-0.5" id="sub-total-sum">40 311 ₽</div>
              <div class="text-[10px] text-slate-400 mt-0.5" id="sub-count-text">4 активные подписки</div>
            </div>
            <button onclick="openModal('modal-add-sub')" class="px-3 py-1.5 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-semibold text-xs flex items-center gap-1 active:scale-95 transition-transform">
              <i data-lucide="plus" class="w-3.5 h-3.5"></i>
              <span>Добавить</span>
            </button>
          </div>
        </div>

        <div class="space-y-2" id="subscriptions-list">
          <div class="text-xs text-slate-400 text-center py-2">Загрузка подписок...</div>
        </div>

        <div class="pt-2">
          <div class="flex items-center justify-between px-1 mb-2">
            <div class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <i data-lucide="puzzle" class="w-4 h-4 text-amber-400"></i>
              <span>Персональные правила & счетчики</span>
            </div>
          </div>
          <div class="space-y-2" id="rules-list">
            <div class="text-xs text-slate-400 text-center py-2">Загрузка правил...</div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 5: HEALTH (КБЖУ И СОН) -->
    <section id="tab-health" class="tab-content hidden space-y-3.5">
      <div class="flex space-x-1.5 p-1 bg-slate-950/60 rounded-xl border border-white/5 text-xs">
        <button onclick="switchHealthSubTab('food')" id="h-subtab-btn-food" class="flex-1 py-1.5 rounded-lg font-bold transition-all bg-cyan-500 text-white">
          🥗 КБЖУ Рацион
        </button>
        <button onclick="switchHealthSubTab('sleep')" id="h-subtab-btn-sleep" class="flex-1 py-1.5 rounded-lg font-bold transition-all text-slate-400">
          😴 Калькулятор Сна
        </button>
      </div>

      <div id="h-panel-food" class="space-y-3.5">
        <div class="glass-card p-4 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/30 border border-emerald-500/20">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-xs text-slate-400">Калории за сегодня</div>
              <div class="text-2xl font-black text-white mt-0.5">
                <span id="food-total-kcal">0</span> <span class="text-xs font-normal text-slate-400">/ <span id="food-goal-kcal">2200</span> ккал</span>
              </div>
            </div>
            <button onclick="openModal('modal-add-food')" class="px-3 py-1.5 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 font-semibold text-xs flex items-center gap-1 active:scale-95 transition-transform">
              <i data-lucide="plus" class="w-3.5 h-3.5"></i>
              <span>Записать</span>
            </button>
          </div>

          <div class="w-full bg-slate-800 h-2.5 rounded-full mt-3 overflow-hidden">
            <div class="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full rounded-full transition-all duration-500" id="food-progress-bar" style="width: 0%"></div>
          </div>

          <div class="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-white/5 text-center">
            <div class="p-2 rounded-xl bg-slate-950/40">
              <div class="text-[10px] text-rose-400 font-semibold">🥩 Белки</div>
              <div class="text-xs font-bold text-slate-100 mt-0.5"><span id="food-p">0</span> г</div>
            </div>
            <div class="p-2 rounded-xl bg-slate-950/40">
              <div class="text-[10px] text-amber-400 font-semibold">🥑 Жиры</div>
              <div class="text-xs font-bold text-slate-100 mt-0.5"><span id="food-f">0</span> г</div>
            </div>
            <div class="p-2 rounded-xl bg-slate-950/40">
              <div class="text-[10px] text-cyan-400 font-semibold">🍞 Углеводы</div>
              <div class="text-xs font-bold text-slate-100 mt-0.5"><span id="food-c">0</span> г</div>
            </div>
          </div>
        </div>

        <div>
          <div class="text-xs font-bold text-slate-400 px-1 mb-2 uppercase tracking-wider">Приемы пищи за сегодня</div>
          <div class="space-y-2" id="food-meals-list">
            <div class="text-xs text-slate-400 text-center py-3">Пока нет записей о еде за сегодня</div>
          </div>
        </div>
      </div>

      <!-- SLEEP CALCULATOR -->
      <div id="h-panel-sleep" class="space-y-3.5 hidden">
        <div class="glass-card p-4 rounded-2xl space-y-4">
          <div class="flex items-center space-x-2 text-xs font-bold text-indigo-400">
            <i data-lucide="moon" class="w-4 h-4"></i>
            <span>Калькулятор фаз сна (циклы по 90 минут)</span>
          </div>

          <div class="grid grid-cols-2 gap-2 text-xs">
            <button onclick="setSleepCalcMode('now')" id="slp-mode-now" class="p-2.5 rounded-xl border border-cyan-500/30 bg-cyan-500/20 text-cyan-300 font-bold text-left">
              🌙 Лечь сейчас
              <div class="text-[10px] text-slate-400 font-normal">Когда проснуться свежим</div>
            </button>
            <button onclick="setSleepCalcMode('wake')" id="slp-mode-wake" class="p-2.5 rounded-xl border border-white/5 bg-slate-900 text-slate-300 font-bold text-left">
              ⏰ Нужно встать в...
              <div class="text-[10px] text-slate-400 font-normal">Во сколько лечь спать</div>
            </button>
          </div>

          <div id="slp-wake-picker" class="hidden space-y-1 pt-1">
            <div class="text-xs text-slate-400">Время желаемого подъема:</div>
            <input type="time" id="slp-wake-time" value="07:00" onchange="runSleepCalc()" class="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-sm font-bold text-white focus:outline-none focus:border-indigo-400">
          </div>

          <div class="space-y-2" id="slp-results-list"></div>
        </div>

        <div class="glass-card p-4 rounded-2xl space-y-3">
          <div class="flex items-center space-x-2 text-xs font-bold text-amber-400">
            <i data-lucide="zap" class="w-4 h-4"></i>
            <span>Быстрый дневной сон (Power Nap)</span>
          </div>
          <div class="grid grid-cols-3 gap-2 text-center" id="power-naps-grid">
            <div class="p-2.5 rounded-xl bg-slate-950/50 border border-white/5">
              <div class="text-sm font-bold text-white">20 мин</div>
              <div class="text-[10px] text-emerald-400 font-semibold mt-0.5">Power Nap</div>
              <div class="text-[9px] text-slate-400 mt-1">Без вялости</div>
            </div>
            <div class="p-2.5 rounded-xl bg-slate-950/50 border border-white/5">
              <div class="text-sm font-bold text-white">26 мин</div>
              <div class="text-[10px] text-cyan-400 font-semibold mt-0.5">NASA Nap</div>
              <div class="text-[9px] text-slate-400 mt-1">+34% фокус</div>
            </div>
            <div class="p-2.5 rounded-xl bg-slate-950/50 border border-white/5">
              <div class="text-sm font-bold text-white">90 мин</div>
              <div class="text-[10px] text-purple-400 font-semibold mt-0.5">1 цикл</div>
              <div class="text-[9px] text-slate-400 mt-1">Полный перезапуск</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 6: HUB -->
    <section id="tab-hub" class="tab-content hidden space-y-3.5">
      <div class="glass-card p-4 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/40 border border-cyan-500/20">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-xs text-cyan-400 font-bold uppercase tracking-wider">Каталог возможностей</div>
            <div class="text-lg font-black text-white mt-0.5">Все 38 модулей супер-бота</div>
            <div class="text-[11px] text-slate-400 mt-0.5">Мгновенный запуск в Telegram или дашборде</div>
          </div>
          <div class="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
            <i data-lucide="sparkles" class="w-5 h-5"></i>
          </div>
        </div>
      </div>

      <!-- FOOD -->
      <div class="space-y-2">
        <div class="text-xs font-bold text-slate-400 px-1 uppercase tracking-wider flex items-center gap-1.5">
          <i data-lucide="utensils-crossed" class="w-3.5 h-3.5 text-amber-400"></i>
          <span>Гастрономия & Гранд-Шеф</span>
        </div>
        <div class="grid grid-cols-1 gap-2">
          <!-- GASTRO LOCATOR & RESTAURANTS -->
          <div class="glass-card p-3.5 rounded-2xl flex flex-col justify-between gap-2.5 border border-amber-500/30 bg-gradient-to-r from-amber-950/20 via-slate-900 to-slate-900">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-lg border border-amber-500/30">
                  🍽
                </div>
                <div>
                  <div class="text-xs font-black text-white flex items-center gap-1.5">
                    <span>Гастро-Локатор & Рестораны (GPS)</span>
                    <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">⭐️ 4.8+</span>
                  </div>
                  <div class="text-[10px] text-slate-400 mt-0.5">Стейки, спикизи, пицца, винные пары и живой диалог с сомелье</div>
                </div>
              </div>
              <button onclick="openInBot('/restaurants')" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 font-black text-xs shadow-lg shadow-amber-500/20 active:scale-95 transition-transform whitespace-nowrap">
                Открыть
              </button>
            </div>
            <div class="flex items-center gap-1 pt-2 border-t border-white/5 overflow-x-auto no-scrollbar">
              <button onclick="openInBot('🥩 Стейки')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🥩 Стейки</button>
              <button onclick="openInBot('🍸 Спикизи')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🍸 Спикизи</button>
              <button onclick="openInBot('🍕 Пицца')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🍕 Пицца</button>
              <button onclick="openInBot('🍜 Азиатские')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🍜 Азия</button>
              <button onclick="openInBot('рядом со мной')" class="px-2 py-0.5 rounded-md bg-cyan-500/20 text-[9px] text-cyan-300 border border-cyan-500/30 font-bold whitespace-nowrap">📍 Рядом GPS</button>
            </div>
          </div>

          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold">🍗</div>
              <div>
                <div class="text-xs font-bold text-white">Food Pairing Сомелье</div>
                <div class="text-[10px] text-slate-400">Идеальный напиток под любое блюдо или фото витрины</div>
              </div>
            </div>
            <button onclick="openInBot('/sommelier')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold">📸</div>
              <div>
                <div class="text-xs font-bold text-white">AI-Скан полок витрины</div>
                <div class="text-[10px] text-slate-400">Скан 20+ бутылок/банок по фото с рейтингом Untappd</div>
              </div>
            </div>
            <button onclick="openInBot('фото витрины')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold">👨‍🍳</div>
              <div>
                <div class="text-xs font-bold text-white">Dark Kitchen Шеф</div>
                <div class="text-[10px] text-slate-400">Ресторанный ужин из остатков холодильника</div>
              </div>
            </div>
            <button onclick="openInBot('/chef')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
        </div>
      </div>

      <!-- LEISURE -->
      <div class="space-y-2">
        <div class="text-xs font-bold text-slate-400 px-1 uppercase tracking-wider flex items-center gap-1.5">
          <i data-lucide="compass" class="w-3.5 h-3.5 text-pink-400"></i>
          <span>Досуг, Культура & СПб</span>
        </div>
        <div class="grid grid-cols-1 gap-2">
          <!-- COUNTRY RELAX & FAMILY VACATION -->
          <div class="glass-card p-3.5 rounded-2xl flex flex-col justify-between gap-2.5 border border-emerald-500/30 bg-gradient-to-r from-emerald-950/20 via-slate-900 to-slate-900">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-lg border border-emerald-500/30">
                  🏕
                </div>
                <div>
                  <div class="text-xs font-black text-white flex items-center gap-1.5">
                    <span>Загородный семейный отдых & Спа</span>
                    <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Семья & Дети</span>
                  </div>
                  <div class="text-[10px] text-slate-400 mt-0.5">80 баз ЛО и Карелии, теплые бассейны, бани, Q&A диалог с консьержем</div>
                </div>
              </div>
              <button onclick="openInBot('/countryside')" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-black text-xs shadow-lg shadow-emerald-500/20 active:scale-95 transition-transform whitespace-nowrap">
                Открыть
              </button>
            </div>
            <div class="flex items-center gap-1 pt-2 border-t border-white/5 overflow-x-auto no-scrollbar">
              <button onclick="openInBot('Семейные курорты')" class="px-2 py-0.5 rounded-md bg-emerald-500/20 text-[9px] text-emerald-300 border border-emerald-500/30 font-bold whitespace-nowrap">👨‍👩‍👧 С детьми</button>
              <button onclick="openInBot('Бассейны')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🏊‍♂️ Бассейны</button>
              <button onclick="openInBot('Русская баня')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🪵 Бани</button>
              <button onclick="openInBot('Глэмпинг')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🏕 Глэмпинг</button>
              <button onclick="openInBot('Рыбалка')" class="px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-[9px] text-slate-300 border border-white/10 whitespace-nowrap">🎣 Озеро</button>
            </div>
          </div>

          <!-- KIDS WEEKENDS 1-3 YEARS -->
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-pink-500/10 text-pink-400 flex items-center justify-center font-bold">👶</div>
              <div>
                <div class="text-xs font-bold text-white">Выходные с малышом (1–3 года)</div>
                <div class="text-[10px] text-slate-400">22 проверенные локации: тоддлер-зоны, бэби-театры, фермы альпак</div>
              </div>
            </div>
            <button onclick="openInBot('/weekends')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>

          <!-- SPEAKEASY BARS -->
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold">🍸</div>
              <div>
                <div class="text-xs font-bold text-white">Секретные Спикизи-Бары СПб</div>
                <div class="text-[10px] text-slate-400">Тайные двери, авторские коктейли и пароли на входе</div>
              </div>
            </div>
            <button onclick="openInBot('/speakeasy')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>

          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-pink-500/10 text-pink-400 flex items-center justify-center font-bold">🎬</div>
              <div>
                <div class="text-xs font-bold text-white">Киносомелье с памятью</div>
                <div class="text-[10px] text-slate-400">Умный подбор ТОП-5 фильмов под ваш вкус и историю</div>
              </div>
            </div>
            <button onclick="openInBot('/cinema')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold">📸</div>
              <div>
                <div class="text-xs font-bold text-white">Фото-Споты СПб и ЛО</div>
                <div class="text-[10px] text-slate-400">Кинематографичные ракурсы, золотой час и координаты</div>
              </div>
            </div>
            <button onclick="openInBot('/photospots')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold">🎧</div>
              <div>
                <div class="text-xs font-bold text-white">Музыка & Книжный сомелье</div>
                <div class="text-[10px] text-slate-400">Плейлисты Яндекс Музыки и 15-мин выжимки книг</div>
              </div>
            </div>
            <button onclick="openInBot('/music')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
        </div>

        <!-- FEATURED FAMILY RESORTS SHOWCASE -->
        <div class="pt-3">
          <div class="flex items-center justify-between px-1 mb-2">
            <div class="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
              <span>👨‍👩‍👧 Топ семейных курортов (с детьми)</span>
            </div>
            <span class="text-[10px] text-slate-500">Яндекс.Карты & Бот</span>
          </div>
          <div class="space-y-2.5" id="country-featured-list">
            <!-- Initial static cards, updated dynamically via API -->
            <div class="glass-card p-3.5 rounded-2xl bg-slate-900/90 border border-emerald-500/20 flex flex-col justify-between space-y-2.5">
              <div>
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <div class="text-xs font-bold text-white">Загородный курорт «Охта Парк»</div>
                    <div class="text-[10px] text-emerald-400 font-semibold mt-0.5">Круглогодичный семейный курорт • 4 открытых бассейна</div>
                  </div>
                  <span class="px-2 py-0.5 rounded-md text-[9px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 whitespace-nowrap">от 9 500 ₽</span>
                </div>
                <div class="text-[10px] text-slate-300 mt-2 flex items-start gap-1">
                  <span>📍</span>
                  <span>Всеволожский р-н, дер. Сярьги (15 км от СПб, ~20 мин по ЗСД)</span>
                </div>
                <div class="text-[10px] text-slate-400 mt-1 flex items-start gap-1">
                  <span>👶</span>
                  <span>Детский клуб «Индиго», альпаки, динопарк, теплый открытый бэби-бассейн</span>
                </div>
              </div>
              <div class="pt-2 border-t border-white/5 flex items-center justify-between gap-2">
                <a href="https://yandex.ru/maps/?text=Охта+Парк+Сярьги" target="_blank" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-semibold flex items-center gap-1 border border-white/5">
                  <i data-lucide="map-pin" class="w-3 h-3 text-cyan-400"></i>
                  <span>Карта</span>
                </a>
                <button onclick="openInBot('Расскажи подробнее про Охта Парк')" class="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold flex items-center gap-1 active:scale-95 transition-transform">
                  <i data-lucide="message-square" class="w-3 h-3"></i>
                  <span>Спросить в боте</span>
                </button>
              </div>
            </div>

            <div class="glass-card p-3.5 rounded-2xl bg-slate-900/90 border border-emerald-500/20 flex flex-col justify-between space-y-2.5">
              <div>
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <div class="text-xs font-bold text-white">Загородный клуб «Царство-Королевство»</div>
                    <div class="text-[10px] text-emerald-400 font-semibold mt-0.5">Коттеджный клуб в соснах • Клуб «Крольчатник»</div>
                  </div>
                  <span class="px-2 py-0.5 rounded-md text-[9px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 whitespace-nowrap">от 18 000 ₽</span>
                </div>
                <div class="text-[10px] text-slate-300 mt-2 flex items-start gap-1">
                  <span>📍</span>
                  <span>пос. Рощино (50 мин от СПб по ЗСД)</span>
                </div>
                <div class="text-[10px] text-slate-400 mt-1 flex items-start gap-1">
                  <span>👶</span>
                  <span>Детский клуб с аниматорами, живые кролики, веревочный городок</span>
                </div>
              </div>
              <div class="pt-2 border-t border-white/5 flex items-center justify-between gap-2">
                <a href="https://yandex.ru/maps/?text=Царство-Королевство+Рощино" target="_blank" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-semibold flex items-center gap-1 border border-white/5">
                  <i data-lucide="map-pin" class="w-3 h-3 text-cyan-400"></i>
                  <span>Карта</span>
                </a>
                <button onclick="openInBot('Расскажи подробнее про Царство-Королевство')" class="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold flex items-center gap-1 active:scale-95 transition-transform">
                  <i data-lucide="message-square" class="w-3 h-3"></i>
                  <span>Спросить в боте</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CAREER & AUTO -->
      <div class="space-y-2">
        <div class="text-xs font-bold text-slate-400 px-1 uppercase tracking-wider flex items-center gap-1.5">
          <i data-lucide="briefcase" class="w-3.5 h-3.5 text-cyan-400"></i>
          <span>Карьера, Авто & AI Студия</span>
        </div>
        <div class="grid grid-cols-1 gap-2">
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold">🎙</div>
              <div>
                <div class="text-xs font-bold text-white">IT QA Manager Собеседование</div>
                <div class="text-[10px] text-slate-400">7 треков, STAR-ответы, голосовые ответы и Scorecard</div>
              </div>
            </div>
            <button onclick="openInBot('/interview')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold">🛡</div>
              <div>
                <div class="text-xs font-bold text-white">Анти-Развод в Автосервисе</div>
                <div class="text-[10px] text-slate-400">Проверка смет по фото & Авто-Юрист (ДТП, штрафы)</div>
              </div>
            </div>
            <button onclick="openInBot('/autoscam')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold">🔬</div>
              <div>
                <div class="text-xs font-bold text-white">Deep Research & Промпт-Студия</div>
                <div class="text-[10px] text-slate-400">Глубокие исследования, генерация промптов, детектор ИИ</div>
              </div>
            </div>
            <button onclick="openInBot('/research')" class="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">Открыть</button>
          </div>
        </div>
      </div>
    </section>

  </main>

  <!-- MODALS -->
  <div id="modal-add-birthday" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden items-center justify-center p-4">
    <div class="glass-card w-full max-w-sm p-5 rounded-2xl space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-bold text-white">🎂 Добавить День Рождения</h3>
        <button onclick="closeModal('modal-add-birthday')" class="text-slate-400 hover:text-white"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <input type="text" id="m-bday-name" placeholder="Имя (напр. Иван Иванов)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <input type="text" id="m-bday-date" placeholder="Дата (напр. 15.03.1995 или 15 марта)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <input type="text" id="m-bday-note" placeholder="Заметка / Категория (Семья, Друзья)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <button onclick="submitAddBirthday()" class="w-full py-2.5 rounded-xl bg-cyan-500 text-white font-bold text-xs active:scale-98 transition-transform shadow-lg shadow-cyan-500/25">Сохранить и отправить в GitHub</button>
    </div>
  </div>

  <div id="modal-add-reminder" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden items-center justify-center p-4">
    <div class="glass-card w-full max-w-sm p-5 rounded-2xl space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-bold text-white">⏰ Новая задача / напоминание</h3>
        <button onclick="closeModal('modal-add-reminder')" class="text-slate-400 hover:text-white"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <input type="text" id="m-rem-text" placeholder="Текст задачи (напр. Купить фильтры)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <input type="text" id="m-rem-time" placeholder="Время (напр. завтра в 15:00)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <button onclick="submitAddReminder()" class="w-full py-2.5 rounded-xl bg-emerald-500 text-white font-bold text-xs active:scale-98 transition-transform shadow-lg shadow-emerald-500/25">Создать задачу</button>
    </div>
  </div>

  <div id="modal-add-food" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden items-center justify-center p-4">
    <div class="glass-card w-full max-w-sm p-5 rounded-2xl space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-bold text-white">🥗 Записать прием пищи</h3>
        <button onclick="closeModal('modal-add-food')" class="text-slate-400 hover:text-white"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <input type="text" id="m-food-name" placeholder="Название блюда (напр. Омлет с сыром)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400">
      <div class="grid grid-cols-2 gap-2">
        <input type="number" id="m-food-kcal" placeholder="Калории (ккал)" class="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400">
        <input type="number" id="m-food-weight" placeholder="Вес в граммах" class="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400">
      </div>
      <div class="grid grid-cols-3 gap-2">
        <input type="number" step="0.1" id="m-food-p" placeholder="Белки (г)" class="px-2.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none">
        <input type="number" step="0.1" id="m-food-f" placeholder="Жиры (г)" class="px-2.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none">
        <input type="number" step="0.1" id="m-food-c" placeholder="Углев. (г)" class="px-2.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none">
      </div>
      <button onclick="submitAddFood()" class="w-full py-2.5 rounded-xl bg-emerald-500 text-white font-bold text-xs active:scale-98 transition-transform shadow-lg shadow-emerald-500/25">Записать в рацион</button>
    </div>
  </div>

  <div id="modal-add-sub" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden items-center justify-center p-4">
    <div class="glass-card w-full max-w-sm p-5 rounded-2xl space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-bold text-white">💳 Добавить подписку</h3>
        <button onclick="closeModal('modal-add-sub')" class="text-slate-400 hover:text-white"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <input type="text" id="m-sub-name" placeholder="Название (напр. Яндекс Плюс)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <div class="grid grid-cols-2 gap-2">
        <input type="number" id="m-sub-amount" placeholder="Сумма (₽)" class="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
        <input type="number" min="1" max="31" id="m-sub-day" placeholder="День списания (1-31)" class="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      </div>
      <input type="text" id="m-sub-cat" placeholder="Категория (Сервисы, Квартира, Связь)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <button onclick="submitAddSub()" class="w-full py-2.5 rounded-xl bg-indigo-500 text-white font-bold text-xs active:scale-98 transition-transform shadow-lg shadow-indigo-500/25">Добавить регулярный платеж</button>
    </div>
  </div>

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
          if (type === 'medium') tg.HapticFeedback.impactOccurred('medium');
          else if (type === 'heavy') tg.HapticFeedback.impactOccurred('heavy');
          else tg.HapticFeedback.impactOccurred('light');
        }
      } catch(e) {}
    }

    function openInBot(command) {
      haptic('medium');
      if (window.Telegram?.WebApp) {
        const twa = window.Telegram.WebApp;
        try {
          if (twa.sendData) {
            twa.sendData(command);
            twa.close();
            return;
          }
        } catch(e) {}
        try {
          if (twa.openTelegramLink) {
            twa.openTelegramLink('https://t.me/MyAiGem_bot');
            twa.close();
            return;
          }
        } catch(e) {}
      }
      window.location.href = 'https://t.me/MyAiGem_bot';
    }

    function switchTab(tabId) {
      haptic('light');
      // Hide all sections
      document.querySelectorAll('.tab-content').forEach(el => {
        el.style.display = 'none';
      });
      // Deactivate all nav buttons
      document.querySelectorAll('.nav-tab-btn').forEach(el => {
        el.classList.remove('active');
      });

      const targetTab = document.getElementById('tab-' + tabId);
      const targetBtn = document.getElementById('tab-btn-' + tabId);
      if (targetTab) targetTab.style.display = 'flex';
      if (targetBtn) targetBtn.classList.add('active');

      // Re-init lucide icons only if library loaded
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }


    function switchFinanceSubTab(sub) {
      haptic('light');
      const pLoan = document.getElementById('f-panel-loan');
      const pSubs = document.getElementById('f-panel-subs');
      const bLoan = document.getElementById('f-subtab-btn-loan');
      const bSubs = document.getElementById('f-subtab-btn-subs');

      if (sub === 'loan') {
        pLoan.classList.remove('hidden');
        pSubs.classList.add('hidden');
        bLoan.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all bg-cyan-500 text-white';
        bSubs.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all text-slate-400';
      } else {
        pLoan.classList.add('hidden');
        pSubs.classList.remove('hidden');
        bLoan.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all text-slate-400';
        bSubs.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all bg-indigo-500 text-white';
      }
      lucide.createIcons();
    }

    function switchHealthSubTab(sub) {
      haptic('light');
      const pFood = document.getElementById('h-panel-food');
      const pSleep = document.getElementById('h-panel-sleep');
      const bFood = document.getElementById('h-subtab-btn-food');
      const bSleep = document.getElementById('h-subtab-btn-sleep');

      if (sub === 'food') {
        pFood.classList.remove('hidden');
        pSleep.classList.add('hidden');
        bFood.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all bg-cyan-500 text-white';
        bSleep.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all text-slate-400';
      } else {
        pFood.classList.add('hidden');
        pSleep.classList.remove('hidden');
        bFood.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all text-slate-400';
        bSleep.className = 'flex-1 py-1.5 rounded-lg font-bold transition-all bg-indigo-500 text-white';
        runSleepCalc();
      }
      lucide.createIcons();
    }

    function toggleAccordion(id) {
      haptic('light');
      const el = document.getElementById(id);
      const icon = document.getElementById('acc-icon-' + id);
      if (el) {
        const isHidden = el.classList.toggle('hidden');
        if (icon) icon.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
      }
    }

    function openModal(id) {
      haptic('medium');
      const m = document.getElementById(id);
      if (m) {
        m.classList.remove('hidden');
        m.classList.add('flex');
      }
      lucide.createIcons();
    }
    function closeModal(id) {
      haptic('light');
      const m = document.getElementById(id);
      if (m) {
        m.classList.add('hidden');
        m.classList.remove('flex');
      }
    }

    function renderCleanTelegramHtml(raw) {
      if (!raw) return 'Сводка погоды формируется...';
      return raw.trim().replace(/\n/g, '<br>');
    }

    let currentData = null;
    let bdayFilter = 'all';

    async function fetchDashboardData(isManual = false) {
      const refIcon = document.getElementById('refresh-icon');
      if (refIcon) { refIcon.style.animation = 'spin 0.8s linear infinite'; }

      try {
        const url = isManual ? '/api/dashboard/data?refresh=true' : '/api/dashboard/data';
        // AbortController: cancel request after 12 seconds
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);

        const resp = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        currentData = await resp.json();
        renderDashboard(currentData);
        if (isManual) haptic('medium');
      } catch (err) {
        if (err.name === 'AbortError') {
          console.warn('Dashboard fetch timed out — showing cached/empty state');
        } else {
          console.error('Fetch error:', err);
        }
      } finally {
        if (refIcon) { refIcon.style.animation = ''; }
      }
    }

    async function refreshWeatherDirect() {
      haptic('medium');
      const miniSpin = document.getElementById('w-mini-spin');
      if (miniSpin) miniSpin.classList.add('animate-spin');

      try {
        const resp = await fetch('/api/weather/refresh', { method: 'POST' });
        const res = await resp.json();
        if (res.success && res.weather) {
          if (currentData) currentData.weather = res.weather;
          renderWeatherSection(res.weather);
        }
      } catch(e) {
        console.error(e);
      } finally {
        if (miniSpin) miniSpin.classList.remove('animate-spin');
      }
    }

    async function syncBirthdaysCloud() {
      haptic('heavy');
      const icon = document.getElementById('bday-sync-icon');
      if (icon) icon.classList.add('animate-spin');

      try {
        const resp = await fetch('/api/birthdays/sync', { method: 'POST' });
        const res = await resp.json();
        if (res.success) {
          await fetchDashboardData();
          alert(`✅ Синхронизировано с GitHub! Всего в базе: ${res.count} чел.`);
        }
      } catch(e) {
        console.error(e);
      } finally {
        if (icon) icon.classList.remove('animate-spin');
      }
    }

    function renderWeatherSection(w) {
      if (!w) return;
      if (w.temp) document.getElementById('w-temp').innerText = w.temp;
      if (w.condition) document.getElementById('w-condition').innerHTML = `<span>${w.condition}</span>`;
      if (w.feels) document.getElementById('w-feels').innerText = w.feels;
      if (w.humidity) document.getElementById('w-humidity').innerText = w.humidity;
      if (w.wind) document.getElementById('w-wind').innerText = w.wind;
      if (w.location_display) document.getElementById('w-location').innerText = w.location_display;

      const hourlyContainer = document.getElementById('w-hourly-container');
      if (w.hourly && w.hourly.length > 0) {
        let hHtml = '';
        w.hourly.forEach(h => {
          const rainBadge = h.rain_chance >= 35 ? `<span class="text-[9px] text-cyan-300 font-bold">🌧 ${h.rain_chance}%</span>` : `<span class="text-[9px] text-slate-500">ясно</span>`;
          hHtml += `
            <div class="flex-none w-16 p-2 rounded-xl bg-slate-950/60 border border-white/5 text-center flex flex-col items-center justify-between space-y-1">
              <span class="text-[10px] text-slate-400 font-medium">${h.time}</span>
              <span class="text-base">${h.icon || '🌤'}</span>
              <span class="text-xs font-bold text-white">${h.temp}</span>
              ${rainBadge}
            </div>
          `;
        });
        hourlyContainer.innerHTML = hHtml;
      } else {
        hourlyContainer.innerHTML = '<div class="text-xs text-slate-400 py-1">Почасовой прогноз загружается...</div>';
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
        document.getElementById('sh-sec-title').className = 'text-xs font-bold text-rose-400';
        document.getElementById('sh-sec-sub').innerText = sh.security_alerts[0];
      } else {
        document.getElementById('sh-sec-title').innerText = 'Всё спокойно';
        document.getElementById('sh-sec-title').className = 'text-xs font-bold text-emerald-400';
        document.getElementById('sh-sec-sub').innerText = 'Протечек нет • Двери 🔒';
      }

      const activeCount = sh.active_count || 0;
      document.getElementById('sh-active-counter').innerText = 'Активно: ' + activeCount + ' приборов';

      const devListEl = document.getElementById('sh-all-devices');
      const devCountEl = document.getElementById('sh-total-dev-count');
      if (sh.devices) {
        devCountEl.innerText = sh.devices.length;
        let dHtml = '';
        sh.devices.forEach(d => {
          const isPower = d.has_on_off;
          const isOn = d.is_on;
          const statusText = isOn ? 'ВКЛ' : 'ВЫКЛ';
          const statusColor = isOn ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' : 'bg-slate-800 text-slate-400 border-white/5';
          
          dHtml += `
            <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-white/5">
              <div>
                <div class="text-xs font-semibold text-white">${d.name}</div>
                <div class="text-[10px] text-slate-400">${d.room || 'Дом'}</div>
              </div>
              ${isPower ? `
                <button onclick="toggleDeviceById('${d.id}', ${!isOn})" class="px-3 py-1 rounded-lg text-xs font-bold border transition-all ${statusColor}">
                  ${statusText}
                </button>
              ` : `
                <span class="text-[10px] text-slate-500">датчик</span>
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
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <button onclick="doneReminder('${r.id}')" title="Завершить" class="w-7 h-7 rounded-lg border border-slate-700 hover:border-emerald-400 flex items-center justify-center text-emerald-400">
                  <i data-lucide="check" class="w-4 h-4"></i>
                </button>
                <div>
                  <div class="text-xs font-semibold text-white">${r.text}</div>
                  <div class="text-[10px] text-cyan-400">${r.target_display}</div>
                </div>
              </div>
              <button onclick="deleteReminder('${r.id}')" class="text-slate-500 hover:text-rose-400 p-1">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
            </div>
          `;
        });
        rListEl.innerHTML = rHtml;
      } else {
        rListEl.innerHTML = '<div class="text-xs text-slate-400 text-center py-3">Все задачи выполнены! ✨</div>';
      }

      const food = data.food || {};
      const totalKcal = food.total_calories || 0;
      const goalKcal = food.goal_calories || 2200;
      document.getElementById('food-total-kcal').innerText = totalKcal;
      document.getElementById('food-goal-kcal').innerText = goalKcal;
      document.getElementById('food-p').innerText = food.total_protein || 0;
      document.getElementById('food-f').innerText = food.total_fat || 0;
      document.getElementById('food-c').innerText = food.total_carbs || 0;

      const pct = Math.min(100, Math.round((totalKcal / goalKcal) * 100));
      document.getElementById('food-progress-bar').style.width = pct + '%';

      const mealsListEl = document.getElementById('food-meals-list');
      if (food.meals && food.meals.length > 0) {
        let mHtml = '';
        food.meals.forEach(m => {
          mHtml += `
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-white">${m.dish_name}</div>
                <div class="text-[10px] text-slate-400">${m.time} • Б:${m.protein}г Ж:${m.fat}г У:${m.carbs}г</div>
              </div>
              <div class="flex items-center space-x-2">
                <span class="text-xs font-bold text-emerald-400">${m.calories} ккал</span>
                <button onclick="deleteFoodMeal('${m.id}')" class="text-slate-500 hover:text-rose-400 p-1">
                  <i data-lucide="trash" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            </div>
          `;
        });
        mealsListEl.innerHTML = mHtml;
      } else {
        mealsListEl.innerHTML = '<div class="text-xs text-slate-400 text-center py-3">Записей о еде пока нет</div>';
      }

      renderSubscriptionsAndRules(data.subscriptions, data.custom_rules);
      renderCountryFeatured(data.country_featured);
      lucide.createIcons();
    }

    function renderCountryFeatured(featuredList) {
      const container = document.getElementById('country-featured-list');
      if (!container) return;
      if (!featuredList || featuredList.length === 0) return;

      let html = '';
      featuredList.forEach(r => {
        const mapsUrl = `https://yandex.ru/maps/?text=${encodeURIComponent(r.geo_query || r.name)}`;
        const shortPrice = (r.price || 'По запросу').split('/')[0].trim();
        html += `
          <div class="glass-card p-3.5 rounded-2xl bg-slate-900/90 border border-emerald-500/20 flex flex-col justify-between space-y-2.5">
            <div>
              <div class="flex items-start justify-between gap-2">
                <div>
                  <div class="text-xs font-bold text-white">${r.name}</div>
                  <div class="text-[10px] text-emerald-400 font-semibold mt-0.5">${r.category}</div>
                </div>
                <span class="px-2 py-0.5 rounded-md text-[9px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 whitespace-nowrap">${shortPrice}</span>
              </div>
              <div class="text-[10px] text-slate-300 mt-2 flex items-start gap-1">
                <span>📍</span>
                <span>${r.location}</span>
              </div>
              <div class="text-[10px] text-slate-400 mt-1 flex items-start gap-1">
                <span>👶</span>
                <span>${r.kid_friendly}</span>
              </div>
            </div>
            <div class="pt-2 border-t border-white/5 flex items-center justify-between gap-2">
              <a href="${mapsUrl}" target="_blank" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-semibold flex items-center gap-1 border border-white/5">
                <i data-lucide="map-pin" class="w-3 h-3 text-cyan-400"></i>
                <span>Карта</span>
              </a>
              <button onclick="openInBot('Расскажи подробнее про ${r.name}')" class="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold flex items-center gap-1 active:scale-95 transition-transform">
                <i data-lucide="message-square" class="w-3 h-3"></i>
                <span>Спросить в боте</span>
              </button>
            </div>
          </div>
        `;
      });
      container.innerHTML = html;
      lucide.createIcons();
    }

    function setBdayFilter(filter) {
      bdayFilter = filter;
      document.querySelectorAll('.bday-flt-btn').forEach(b => {
        b.className = 'bday-flt-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-800 text-slate-300';
      });
      const activeBtn = document.getElementById('bday-flt-' + filter);
      if (activeBtn) activeBtn.className = 'bday-flt-btn px-2.5 py-1 rounded-lg font-semibold bg-cyan-500 text-white';
      renderFilteredBirthdays();
    }

    function renderFilteredBirthdays() {
      if (!currentData || !currentData.birthdays) return;
      const query = (document.getElementById('bday-search-inp')?.value || '').toLowerCase().trim();
      const bListEl = document.getElementById('birthdays-list');

      let list = [...currentData.birthdays];

      if (query) {
        list = list.filter(b => b.name.toLowerCase().includes(query) || (b.date_display && b.date_display.toLowerCase().includes(query)) || (b.note && b.note.toLowerCase().includes(query)));
      }

      if (bdayFilter === 'upcoming') {
        list = list.slice(0, 5);
      } else if (bdayFilter === 'family') {
        list = list.filter(b => (b.note && b.note.toLowerCase().includes('семь')) || ['мама', 'папа', 'брат', 'любимая жена'].includes(b.name.toLowerCase()));
      }

      if (list.length > 0) {
        let bHtml = '';
        list.forEach(b => {
          const daysText = b.days_left === 0 ? '🎉 СЕГОДНЯ!' : (b.days_left === 1 ? 'Завтра!' : `через ${b.days_left} дн.`);
          const badgeColor = b.days_left <= 3 ? 'bg-pink-500/20 text-pink-300 border-pink-500/30' : 'bg-slate-800 text-slate-300 border-white/5';
          const noteTag = b.note ? `<span class="px-1.5 py-0.5 rounded text-[9px] bg-slate-800 text-slate-400 border border-white/5">${b.note}</span>` : '';

          bHtml += `
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-xl bg-pink-500/10 text-pink-400 flex items-center justify-center font-bold text-xs border border-pink-500/20">
                  ${b.day}
                </div>
                <div>
                  <div class="text-xs font-bold text-white flex items-center gap-1.5">
                    <span>${b.name}</span>
                    ${noteTag}
                  </div>
                  <div class="text-[10px] text-slate-400">${b.date_display} ${b.age_display ? '• ' + b.age_display : ''}</div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span class="px-2 py-1 rounded-lg text-[10px] font-bold border ${badgeColor}">${daysText}</span>
                <button onclick="deleteBirthday('${b.id}', '${b.name}')" title="Удалить" class="text-slate-500 hover:text-rose-400 p-1">
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            </div>
          `;
        });
        bListEl.innerHTML = bHtml;
      } else {
        bListEl.innerHTML = '<div class="text-xs text-slate-400 text-center py-4">Дней рождения по запросу не найдено</div>';
      }
      lucide.createIcons();
    }

    function renderSubscriptionsAndRules(subsData, rulesData) {
      const sList = document.getElementById('subscriptions-list');
      if (subsData) {
        const total = subsData.total_monthly || 40311;
        document.getElementById('sub-total-sum').innerText = total.toLocaleString('ru-RU') + ' ₽';
        const items = subsData.items || [];
        document.getElementById('sub-count-text').innerText = `${items.length} активные подписки`;

        if (items.length > 0) {
          let sHtml = '';
          items.forEach(s => {
            const nextDay = s.payment_day || 1;
            sHtml += `
              <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-xs border border-indigo-500/20">
                    💳
                  </div>
                  <div>
                    <div class="text-xs font-bold text-white">${s.name}</div>
                    <div class="text-[10px] text-slate-400">${s.category || 'Сервисы'} • Списание ${nextDay}-го числа</div>
                  </div>
                </div>
                <div class="flex items-center space-x-2.5">
                  <span class="text-xs font-bold text-indigo-300">${s.amount.toLocaleString('ru-RU')} ₽</span>
                  <button onclick="deleteSub('${s.id}')" title="Удалить" class="text-slate-500 hover:text-rose-400 p-1">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                  </button>
                </div>
              </div>
            `;
          });
          sList.innerHTML = sHtml;
        } else {
          sList.innerHTML = '<div class="text-xs text-slate-400 text-center py-2">Подписок пока нет</div>';
        }
      }

      const rList = document.getElementById('rules-list');
      if (rulesData && rulesData.length > 0) {
        let rHtml = '';
        rulesData.forEach(r => {
          const isActive = r.is_active;
          const statusBg = isActive ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-slate-800 text-slate-500 border-white/5';
          rHtml += `
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div>
                <div class="text-xs font-bold text-white">${r.title}</div>
                <div class="text-[10px] text-slate-400">${r.action_text || 'Напоминание'}</div>
              </div>
              <button onclick="toggleRule('${r.id}')" class="px-2.5 py-1 rounded-lg text-xs font-bold border transition-all ${statusBg}">
                ${isActive ? 'АКТИВНО 🟢' : 'ВЫКЛ ⚪'}
              </button>
            </div>
          `;
        });
        rList.innerHTML = rHtml;
      } else {
        rList.innerHTML = `
          <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
            <div>
              <div class="text-xs font-bold text-white">Счетчики воды</div>
              <div class="text-[10px] text-slate-400">Сдача показаний счетчиков (20-24 число)</div>
            </div>
            <span class="px-2.5 py-1 rounded-lg text-xs font-bold border bg-emerald-500/20 text-emerald-300 border-emerald-500/30">АКТИВНО 🟢</span>
          </div>
        `;
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
      if (confirm(`Удалить день рождения для "${name}"?`)) {
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
      const weight_g = parseInt(document.getElementById('m-food-weight').value || 0);
      if (!dish_name || !calories) return alert('Введите название и калории!');
      haptic('medium');
      await fetch('/api/food/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dish_name, calories, protein, fat, carbs, weight_g })
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

    // LOAN CALCULATOR (1% MIN, 360 MONTHS MAX)
    function formatYearsRu(months) {
      const y = months / 12;
      if (months % 12 === 0) {
        const last100 = y % 100;
        const last10 = y % 10;
        let word = 'лет';
        if (last100 < 11 || last100 > 14) {
          if (last10 === 1) word = 'год';
          else if (last10 >= 2 && last10 <= 4) word = 'года';
        }
        return `${y} ${word}`;
      }
      return `${y.toFixed(1)} г.`;
    }

    function runLoanCalc() {
      const amount = parseFloat(document.getElementById('calc-inp-amount').value);
      const rate = parseFloat(document.getElementById('calc-inp-rate').value);
      const months = parseInt(document.getElementById('calc-inp-months').value);
      const early = parseFloat(document.getElementById('calc-inp-early').value);

      document.getElementById('calc-lbl-amount').innerText = amount.toLocaleString('ru-RU') + ' ₽';
      document.getElementById('calc-lbl-rate').innerText = rate.toFixed(1) + ' %';
      document.getElementById('calc-lbl-months').innerText = `${months} мес. (${formatYearsRu(months)})`;
      document.getElementById('calc-lbl-early').innerText = early.toLocaleString('ru-RU') + ' ₽';

      let monthlyPayment = 0;
      let totalInterest = 0;

      if (rate <= 0) {
        monthlyPayment = amount / months;
        totalInterest = 0;
      } else {
        const monthlyRate = rate / 12 / 100;
        const factor = (monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
        monthlyPayment = amount * factor;
        const totalPayout = monthlyPayment * months;
        totalInterest = totalPayout - amount;
      }

      document.getElementById('calc-res-payment').innerText = Math.round(monthlyPayment).toLocaleString('ru-RU') + ' ₽';
      document.getElementById('calc-res-interest').innerText = Math.round(totalInterest).toLocaleString('ru-RU') + ' ₽';

      if (early > 0 && rate > 0) {
        const monthlyRate = rate / 12 / 100;
        let balance = amount;
        let earlyInterest = 0;
        let earlyMonths = 0;
        const totalMonthly = monthlyPayment + early;

        while (balance > 0.01 && earlyMonths < 1200) {
          earlyMonths++;
          const interestMonth = balance * monthlyRate;
          earlyInterest += interestMonth;
          const principal = totalMonthly - interestMonth;
          balance -= principal;
        }

        const savedInterest = Math.max(0, totalInterest - earlyInterest);
        const termDiff = Math.max(0, months - earlyMonths);

        document.getElementById('calc-res-savings').innerText = Math.round(savedInterest).toLocaleString('ru-RU') + ' ₽';
        document.getElementById('calc-res-new-term').innerText = `${earlyMonths} мес. (-${termDiff} мес.)`;
      } else {
        document.getElementById('calc-res-savings').innerText = '0 ₽';
        document.getElementById('calc-res-new-term').innerText = `${months} мес.`;
      }
    }

    // SLEEP CALCULATOR
    let sleepMode = 'now';

    function setSleepCalcMode(mode) {
      sleepMode = mode;
      const bNow = document.getElementById('slp-mode-now');
      const bWake = document.getElementById('slp-mode-wake');
      const pWake = document.getElementById('slp-wake-picker');

      if (mode === 'now') {
        bNow.className = 'p-2.5 rounded-xl border border-cyan-500/30 bg-cyan-500/20 text-cyan-300 font-bold text-left';
        bWake.className = 'p-2.5 rounded-xl border border-white/5 bg-slate-900 text-slate-300 font-bold text-left';
        pWake.classList.add('hidden');
      } else {
        bNow.className = 'p-2.5 rounded-xl border border-white/5 bg-slate-900 text-slate-300 font-bold text-left';
        bWake.className = 'p-2.5 rounded-xl border border-indigo-500/30 bg-indigo-500/20 text-indigo-300 font-bold text-left';
        pWake.classList.remove('hidden');
      }
      runSleepCalc();
    }

    function runSleepCalc() {
      const listEl = document.getElementById('slp-results-list');
      const FALL_MIN = 14;
      const CYCLE_MIN = 90;

      if (sleepMode === 'now') {
        const now = new Date();
        const asleepTime = new Date(now.getTime() + FALL_MIN * 60000);

        const cycles = [
          { count: 6, hrs: '9.0 ч', badge: '⭐ Идеально', sub: 'Полное восстановление и свежесть' },
          { count: 5, hrs: '7.5 ч', badge: '🌟 Норма', sub: 'Оптимально для продуктивного дня' },
          { count: 4, hrs: '6.0 ч', badge: '✨ Бодрость', sub: 'Легкий подъем без разбитости' },
          { count: 3, hrs: '4.5 ч', badge: '⚡ Минимум', sub: 'Экстренный режим' }
        ];

        let html = '<div class="text-[11px] text-slate-400 mb-1">Рекомендуемое время будильника:</div>';
        cycles.forEach(c => {
          const wake = new Date(asleepTime.getTime() + c.count * CYCLE_MIN * 60000);
          const hh = String(wake.getHours()).padStart(2, '0');
          const mm = String(wake.getMinutes()).padStart(2, '0');
          html += `
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div>
                <div class="text-sm font-black text-white flex items-center gap-1.5">
                  <span>${hh}:${mm}</span>
                  <span class="text-[10px] text-cyan-400 font-normal">(${c.hrs})</span>
                </div>
                <div class="text-[10px] text-slate-400">${c.sub}</div>
              </div>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">${c.badge}</span>
            </div>
          `;
        });
        listEl.innerHTML = html;
      } else {
        const timeVal = document.getElementById('slp-wake-time')?.value || '07:00';
        const [wH, wM] = timeVal.split(':').map(Number);
        const targetWake = new Date();
        targetWake.setHours(wH, wM, 0, 0);

        const cycles = [
          { count: 6, hrs: '9.0 ч', badge: '⭐ Идеально' },
          { count: 5, hrs: '7.5 ч', badge: '🌟 Золотой стандарт' },
          { count: 4, hrs: '6.0 ч', badge: '✨ Достаточно' },
          { count: 3, hrs: '4.5 ч', badge: '⚡ Минимум' }
        ];

        let html = `<div class="text-[11px] text-slate-400 mb-1">Чтобы встать в ${timeVal}, ложитесь спать в:</div>`;
        cycles.forEach(c => {
          const totalMin = c.count * CYCLE_MIN + FALL_MIN;
          const bed = new Date(targetWake.getTime() - totalMin * 60000);
          const hh = String(bed.getHours()).padStart(2, '0');
          const mm = String(bed.getMinutes()).padStart(2, '0');
          html += `
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div>
                <div class="text-sm font-black text-white flex items-center gap-1.5">
                  <span>${hh}:${mm}</span>
                  <span class="text-[10px] text-indigo-400 font-normal">(${c.hrs} сна)</span>
                </div>
                <div class="text-[10px] text-slate-400">${c.count} полных циклов сна</div>
              </div>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">${c.badge}</span>
            </div>
          `;
        });
        listEl.innerHTML = html;
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      // 1. Init section visibility — show only first tab IMMEDIATELY
      document.querySelectorAll('.tab-content').forEach((el, i) => {
        el.style.display = (i === 0) ? 'flex' : 'none';
        el.style.flexDirection = 'column';
        el.style.gap = '12px';
      });

      // 2. HIDE LOADING SCREEN after 2 seconds MAX — never block the UI
      function hideLoadingScreen() {
        const ls = document.getElementById('loading-screen');
        if (ls) {
          ls.style.transition = 'opacity 0.35s ease';
          ls.style.opacity = '0';
          setTimeout(() => { if (ls.parentNode) ls.parentNode.removeChild(ls); }, 380);
        }
      }
      // Guaranteed removal after 2 seconds
      const loadingTimeout = setTimeout(hideLoadingScreen, 2000);

      // 3. Activate Telegram WebApp
      if (typeof Telegram !== 'undefined' && Telegram.WebApp) {
        try { Telegram.WebApp.ready(); Telegram.WebApp.expand(); } catch(e) {}
      }

      // 4. Init Lucide icons (with retry)
      function initIcons() {
        if (typeof lucide !== 'undefined') {
          lucide.createIcons();
        } else {
          setTimeout(initIcons, 300);
        }
      }
      initIcons();

      // 5. Run client-side calculators immediately
      try { runLoanCalc(); } catch(e) {}
      try { runSleepCalc(); } catch(e) {}

      // 6. Fetch data in background — UI already visible
      fetchDashboardData().then(() => {
        clearTimeout(loadingTimeout);
        hideLoadingScreen();
      }).catch(() => {
        clearTimeout(loadingTimeout);
        hideLoadingScreen();
      });

      // 7. Auto-refresh every 30 seconds
      setInterval(() => fetchDashboardData(false), 30000);
    });

  </script>
</body>
</html>
"""
