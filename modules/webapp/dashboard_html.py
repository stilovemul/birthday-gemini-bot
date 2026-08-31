TMA_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>AiGem Dashboard</title>
  <!-- Telegram WebApp SDK -->
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#ecfeff', 500: '#06b6d4', 600: '#0891b2', 700: '#0e7490' },
            slate: { 850: '#111827', 900: '#0b0f19', 950: '#05070c' }
          }
        }
      }
    }
  </script>
  <style>
    body {
      background-color: var(--tg-theme-bg-color, #090d16);
      color: var(--tg-theme-text-color, #f8fafc);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }
    .glass {
      background: rgba(17, 24, 39, 0.75);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .glass-card {
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.06);
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }
    .glass-card:active {
      transform: scale(0.985);
    }
    .glow-cyan {
      box-shadow: 0 0 15px -3px rgba(6, 182, 212, 0.4);
    }
    .glow-green {
      box-shadow: 0 0 15px -3px rgba(16, 185, 129, 0.4);
    }
    .glow-purple {
      box-shadow: 0 0 15px -3px rgba(168, 85, 247, 0.4);
    }
    .toggle-checkbox:checked {
      right: 0;
      border-color: #06b6d4;
    }
    .toggle-checkbox:checked + .toggle-label {
      background-color: #06b6d4;
    }
    /* Hide scrollbar for tabs */
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  </style>
</head>
<body class="min-h-screen pb-24 text-slate-100 flex flex-col items-center">

  <!-- TOP HEADER -->
  <header class="w-full max-w-lg px-4 pt-3 pb-2 sticky top-0 z-40 glass border-b border-white/5 flex items-center justify-between">
    <div class="flex items-center space-x-2.5">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
        <i data-lucide="cpu" class="w-5 h-5 text-white"></i>
      </div>
      <div>
        <h1 class="text-sm font-bold tracking-wide flex items-center gap-1.5">
          <span>AiGem Super-Bot</span>
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        </h1>
        <p class="text-[11px] text-slate-400" id="header-time">24/7 Cloud • MSK</p>
      </div>
    </div>

    <!-- REFRESH BUTTON -->
    <button onclick="fetchDashboardData(true)" class="p-2 rounded-xl bg-slate-800/80 border border-white/10 active:rotate-180 transition-transform duration-300">
      <i data-lucide="refresh-cw" class="w-4 h-4 text-cyan-400" id="refresh-icon"></i>
    </button>
  </header>

  <!-- NAVIGATION TABS -->
  <nav class="w-full max-w-lg px-4 py-2 sticky top-14 z-30 bg-slate-900/90 backdrop-blur-md">
    <div class="flex space-x-1.5 overflow-x-auto no-scrollbar p-1 bg-slate-950/60 rounded-2xl border border-white/5">
      <button onclick="switchTab('smart_home')" id="tab-btn-smart_home" class="tab-btn flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all bg-cyan-500 text-white shadow-lg shadow-cyan-500/25 whitespace-nowrap">
        <i data-lucide="home" class="w-3.5 h-3.5"></i>
        <span>Дом</span>
      </button>
      <button onclick="switchTab('digest')" id="tab-btn-digest" class="tab-btn flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all text-slate-400 hover:text-slate-200 whitespace-nowrap">
        <i data-lucide="cloud-sun" class="w-3.5 h-3.5"></i>
        <span>Погода</span>
      </button>
      <button onclick="switchTab('tasks')" id="tab-btn-tasks" class="tab-btn flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all text-slate-400 hover:text-slate-200 whitespace-nowrap">
        <i data-lucide="calendar-heart" class="w-3.5 h-3.5"></i>
        <span>ДР & Дела</span>
      </button>
      <button onclick="switchTab('food')" id="tab-btn-food" class="tab-btn flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all text-slate-400 hover:text-slate-200 whitespace-nowrap">
        <i data-lucide="utensils" class="w-3.5 h-3.5"></i>
        <span>КБЖУ</span>
      </button>
      <button onclick="switchTab('calc')" id="tab-btn-calc" class="tab-btn flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all text-slate-400 hover:text-slate-200 whitespace-nowrap">
        <i data-lucide="calculator" class="w-3.5 h-3.5"></i>
        <span>Кредит</span>
      </button>
    </div>
  </nav>

  <!-- MAIN CONTENT CONTAINER -->
  <main class="w-full max-w-lg px-4 mt-2 space-y-4">

    <!-- ============================================== -->
    <!-- TAB 1: SMART HOME (ЯНДЕКС УМНЫЙ ДОМ) -->
    <!-- ============================================== -->
    <section id="tab-smart_home" class="tab-content space-y-3.5">
      
      <!-- TOP STATUS & CLIMATE SUMMARY -->
      <div class="grid grid-cols-2 gap-2.5">
        <!-- Climate Tile -->
        <div class="glass-card p-3.5 rounded-2xl flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400">
            <i data-lucide="thermometer" class="w-5 h-5"></i>
          </div>
          <div>
            <div class="text-[11px] text-slate-400">Климат спальня</div>
            <div class="text-lg font-bold text-white tracking-tight" id="sh-temp-val">24.7°C</div>
            <div class="text-[10px] text-slate-400" id="sh-hum-val">💧 48% влажность</div>
          </div>
        </div>

        <!-- Security Tile -->
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

      <!-- MASTER SWITCH: ALL LIGHTS OFF -->
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
          <!-- Corridor Switch -->
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

          <!-- Bathroom Light -->
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

          <!-- Exhaust Fan -->
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

          <!-- Floor Heating -->
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

      <!-- FULL SMART HOME DEVICES ACCORDION -->
      <div class="glass-card p-3.5 rounded-2xl">
        <div class="flex items-center justify-between cursor-pointer" onclick="toggleAccordion('sh-all-devices')">
          <div class="flex items-center space-x-2.5">
            <i data-lucide="layout-grid" class="w-4 h-4 text-cyan-400"></i>
            <span class="text-xs font-bold text-white">Все устройства дома (<span id="sh-total-dev-count">...</span>)</span>
          </div>
          <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition-transform" id="acc-icon-sh-all-devices"></i>
        </div>

        <div id="sh-all-devices" class="hidden mt-3 space-y-2 pt-2 border-t border-white/5 max-h-72 overflow-y-auto pr-1">
          <!-- Dynamic Device Rows inserted here -->
          <div class="text-xs text-slate-400 text-center py-2">Загрузка списка устройств...</div>
        </div>
      </div>
    </section>


    <!-- ============================================== -->
    <!-- TAB 2: DIGEST & WEATHER (ПОГОДА И ДАЙДЖЕСТ) -->
    <!-- ============================================== -->
    <section id="tab-digest" class="tab-content hidden space-y-3.5">
      
      <!-- WEATHER HERO CARD -->
      <div class="glass-card p-4 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950/50 border border-blue-500/20">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-1.5 text-xs text-cyan-400 font-semibold">
              <i data-lucide="map-pin" class="w-3.5 h-3.5"></i>
              <span id="w-location">СПб, Приморский р-н</span>
            </div>
            <div class="text-3xl font-extrabold text-white mt-1 tracking-tight" id="w-temp">+21.5°C</div>
            <div class="text-xs text-slate-300 mt-0.5" id="w-condition">🌤 Переменная облачность</div>
          </div>
          <div class="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-cyan-300">
            <i data-lucide="sun-medium" class="w-8 h-8"></i>
          </div>
        </div>

        <!-- Weather Details Grid -->
        <div class="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-white/5 text-center">
          <div class="p-2 rounded-xl bg-slate-950/40">
            <div class="text-[10px] text-slate-400">Ощущается</div>
            <div class="text-xs font-bold text-slate-200 mt-0.5" id="w-feels">+20°C</div>
          </div>
          <div class="p-2 rounded-xl bg-slate-950/40">
            <div class="text-[10px] text-slate-400">Влажность</div>
            <div class="text-xs font-bold text-slate-200 mt-0.5" id="w-humidity">64%</div>
          </div>
          <div class="p-2 rounded-xl bg-slate-950/40">
            <div class="text-[10px] text-slate-400">Ветер</div>
            <div class="text-xs font-bold text-slate-200 mt-0.5" id="w-wind">4.2 м/с</div>
          </div>
        </div>
      </div>

      <!-- FULL SYNOPTIC TEXT REPORT -->
      <div class="glass-card p-4 rounded-2xl space-y-2">
        <div class="flex items-center space-x-2 text-xs font-bold text-slate-300">
          <i data-lucide="sparkles" class="w-4 h-4 text-amber-400"></i>
          <span>Сводка от Умного Синоптика</span>
        </div>
        <div class="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/40 p-3 rounded-xl border border-white/5" id="w-full-text">
          Загрузка актуального прогноза...
        </div>
      </div>
    </section>


    <!-- ============================================== -->
    <!-- TAB 3: BIRTHDAYS & TASKS (ДНИ РОЖДЕНИЯ & ДЕЛА) -->
    <!-- ============================================== -->
    <section id="tab-tasks" class="tab-content hidden space-y-3.5">
      
      <!-- UPCOMING BIRTHDAYS HEADER -->
      <div class="flex items-center justify-between px-1">
        <div class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <i data-lucide="cake" class="w-4 h-4 text-pink-400"></i>
          <span>Дни рождения</span>
        </div>
        <button onclick="openModal('modal-add-birthday')" class="text-xs text-cyan-400 font-semibold flex items-center gap-1 active:scale-95 transition-transform">
          <i data-lucide="plus" class="w-3.5 h-3.5"></i>
          <span>Добавить</span>
        </button>
      </div>

      <!-- BIRTHDAY CARDS LIST -->
      <div class="space-y-2" id="birthdays-list">
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


    <!-- ============================================== -->
    <!-- TAB 4: FOOD & NUTRITION (КБЖУ & ПИТАНИЕ) -->
    <!-- ============================================== -->
    <section id="tab-food" class="tab-content hidden space-y-3.5">
      
      <!-- CALORIES SUMMARY CARD -->
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

        <!-- PROGRESS BAR -->
        <div class="w-full bg-slate-800 h-2.5 rounded-full mt-3 overflow-hidden">
          <div class="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full rounded-full transition-all duration-500" id="food-progress-bar" style="width: 0%"></div>
        </div>

        <!-- MACROS (P / F / C) GRID -->
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

      <!-- TODAY'S MEALS LIST -->
      <div>
        <div class="text-xs font-bold text-slate-400 px-1 mb-2 uppercase tracking-wider">Приемы пищи за сегодня</div>
        <div class="space-y-2" id="food-meals-list">
          <div class="text-xs text-slate-400 text-center py-3">Пока нет записей о еде за сегодня</div>
        </div>
      </div>
    </section>


    <!-- ============================================== -->
    <!-- TAB 5: LOAN CALCULATOR (КРЕДИТЫ & ДОСРОЧКА) -->
    <!-- ============================================== -->
    <section id="tab-calc" class="tab-content hidden space-y-3.5">
      
      <div class="glass-card p-4 rounded-2xl space-y-4">
        <div class="flex items-center space-x-2 text-xs font-bold text-cyan-400">
          <i data-lucide="percent" class="w-4 h-4"></i>
          <span>Кредитный симулятор & Выгода досрочки</span>
        </div>

        <!-- INPUT: AMOUNT -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-slate-400">Сумма кредита:</span>
            <span class="font-bold text-white" id="calc-lbl-amount">1 000 000 ₽</span>
          </div>
          <input type="range" min="100000" max="15000000" step="50000" value="1000000" id="calc-inp-amount" oninput="runLoanCalc()" class="w-full accent-cyan-400">
        </div>

        <!-- INPUT: RATE -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-slate-400">Процентная ставка:</span>
            <span class="font-bold text-white" id="calc-lbl-rate">18.5 %</span>
          </div>
          <input type="range" min="5.0" max="35.0" step="0.5" value="18.5" id="calc-inp-rate" oninput="runLoanCalc()" class="w-full accent-cyan-400">
        </div>

        <!-- INPUT: MONTHS -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-slate-400">Срок кредита:</span>
            <span class="font-bold text-white" id="calc-lbl-months">60 мес. (5 лет)</span>
          </div>
          <input type="range" min="6" max="240" step="6" value="60" id="calc-inp-months" oninput="runLoanCalc()" class="w-full accent-cyan-400">
        </div>

        <!-- INPUT: EARLY MONTHLY -->
        <div class="pt-2 border-t border-white/5">
          <div class="flex justify-between text-xs mb-1">
            <span class="text-slate-400">Досрочно в месяц:</span>
            <span class="font-bold text-emerald-400" id="calc-lbl-early">10 000 ₽</span>
          </div>
          <input type="range" min="0" max="100000" step="2000" value="10000" id="calc-inp-early" oninput="runLoanCalc()" class="w-full accent-emerald-400">
        </div>

        <!-- RESULTS CARD -->
        <div class="p-3.5 rounded-xl bg-slate-950/60 border border-cyan-500/20 space-y-2">
          <div class="flex justify-between items-center text-xs">
            <span class="text-slate-400">Ежемесячный платеж:</span>
            <span class="text-sm font-bold text-white" id="calc-res-payment">25 660 ₽</span>
          </div>
          <div class="flex justify-between items-center text-xs">
            <span class="text-slate-400">Переплата без досрочки:</span>
            <span class="font-semibold text-slate-300" id="calc-res-interest">539 600 ₽</span>
          </div>
          <div class="flex justify-between items-center text-xs pt-2 border-t border-white/5 text-emerald-400">
            <span>🔥 Экономия на процентах:</span>
            <span class="font-bold text-sm" id="calc-res-savings">184 200 ₽</span>
          </div>
          <div class="flex justify-between items-center text-xs text-cyan-300">
            <span>⏱ Новый срок выплаты:</span>
            <span class="font-bold" id="calc-res-new-term">38 мес. (-22 мес.)</span>
          </div>
        </div>
      </div>
    </section>

  </main>


  <!-- ============================================== -->
  <!-- MODALS (ADD BIRTHDAY, ADD TASK, ADD FOOD) -->
  <!-- ============================================== -->

  <!-- MODAL: ADD BIRTHDAY -->
  <div id="modal-add-birthday" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden items-center justify-center p-4">
    <div class="glass-card w-full max-w-sm p-5 rounded-2xl space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-bold text-white">🎂 Добавить День Рождения</h3>
        <button onclick="closeModal('modal-add-birthday')" class="text-slate-400 hover:text-white"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <input type="text" id="m-bday-name" placeholder="Имя (напр. Иван Иванов)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <input type="text" id="m-bday-date" placeholder="Дата (напр. 15.03.1995 или 15 марта)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <input type="text" id="m-bday-note" placeholder="Заметка (опционально)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <button onclick="submitAddBirthday()" class="w-full py-2.5 rounded-xl bg-cyan-500 text-white font-bold text-xs active:scale-98 transition-transform shadow-lg shadow-cyan-500/25">Сохранить</button>
    </div>
  </div>

  <!-- MODAL: ADD REMINDER -->
  <div id="modal-add-reminder" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden items-center justify-center p-4">
    <div class="glass-card w-full max-w-sm p-5 rounded-2xl space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-bold text-white">⏰ Новая задача / напоминание</h3>
        <button onclick="closeModal('modal-add-reminder')" class="text-slate-400 hover:text-white"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <input type="text" id="m-rem-text" placeholder="Текст задачи (напр. Купить фильтры)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <input type="text" id="m-rem-time" placeholder="Время (напр. завтра в 15:00)" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400">
      <button onclick="submitAddReminder()" class="w-full py-2.5 rounded-xl bg-emerald-500 text-white font-bold text-xs active:scale-98 transition-transform shadow-lg shadow-emerald-500/25">Создать</button>
    </div>
  </div>

  <!-- MODAL: ADD FOOD -->
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


  <!-- ============================================== -->
  <!-- JAVASCRIPT LOGIC & TELEGRAM INTEGRATION -->
  <!-- ============================================== -->
  <script>
    // Initialize Telegram WebApp
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

    // TAB SWITCHING
    function switchTab(tabId) {
      haptic('light');
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('bg-cyan-500', 'text-white', 'shadow-lg', 'shadow-cyan-500/25');
        el.classList.add('text-slate-400');
      });

      const targetTab = document.getElementById('tab-' + tabId);
      const targetBtn = document.getElementById('tab-btn-' + tabId);
      if (targetTab) targetTab.classList.remove('hidden');
      if (targetBtn) {
        targetBtn.classList.remove('text-slate-400');
        targetBtn.classList.add('bg-cyan-500', 'text-white', 'shadow-lg', 'shadow-cyan-500/25');
      }
    }

    // ACCORDION
    function toggleAccordion(id) {
      haptic('light');
      const el = document.getElementById(id);
      const icon = document.getElementById('acc-icon-' + id);
      if (el) {
        const isHidden = el.classList.toggle('hidden');
        if (icon) icon.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
      }
    }

    // MODAL OPEN / CLOSE
    function openModal(id) {
      haptic('medium');
      const m = document.getElementById(id);
      if (m) {
        m.classList.remove('hidden');
        m.classList.add('flex');
      }
    }
    function closeModal(id) {
      haptic('light');
      const m = document.getElementById(id);
      if (m) {
        m.classList.add('hidden');
        m.classList.remove('flex');
      }
    }

    // STATE & FETCH DATA
    let currentData = null;

    async function fetchDashboardData(isManual = false) {
      const refIcon = document.getElementById('refresh-icon');
      if (refIcon) refIcon.classList.add('animate-spin');

      try {
        const resp = await fetch('/api/dashboard/data');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        currentData = await resp.json();
        renderDashboard(currentData);
        if (isManual) haptic('medium');
      } catch (err) {
        console.error('Fetch error:', err);
      } finally {
        if (refIcon) refIcon.classList.remove('animate-spin');
      }
    }

    function renderDashboard(data) {
      if (!data) return;

      // 1. Time
      if (data.server_time_msk) {
        document.getElementById('header-time').innerText = data.server_time_msk + ' MSK';
      }

      // 2. Smart Home
      const sh = data.smart_home || {};
      if (sh.climate && sh.climate.length > 0) {
        const c0 = sh.climate[0];
        document.getElementById('sh-temp-val').innerText = c0.temperature + '°C';
        if (c0.humidity) document.getElementById('sh-hum-val').innerText = '💧 ' + c0.humidity + '% влажность';
      }

      // Security
      if (sh.security_alerts && sh.security_alerts.length > 0) {
        document.getElementById('sh-sec-title').innerText = 'Внимание: тревога!';
        document.getElementById('sh-sec-title').className = 'text-xs font-bold text-rose-400';
        document.getElementById('sh-sec-sub').innerText = sh.security_alerts[0];
      } else {
        document.getElementById('sh-sec-title').innerText = 'Всё спокойно';
        document.getElementById('sh-sec-title').className = 'text-xs font-bold text-emerald-400';
        document.getElementById('sh-sec-sub').innerText = 'Протечек нет • Двери 🔒';
      }

      // Active devices counter
      const activeCount = sh.active_count || 0;
      document.getElementById('sh-active-counter').innerText = 'Активно: ' + activeCount + ' приборов';

      // Devices accordion
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

      // 3. Weather
      const w = data.weather || {};
      if (w.text) {
        document.getElementById('w-full-text').innerText = w.text;
      }

      // 4. Birthdays
      const bListEl = document.getElementById('birthdays-list');
      if (data.birthdays && data.birthdays.length > 0) {
        let bHtml = '';
        data.birthdays.slice(0, 5).forEach(b => {
          const daysText = b.days_left === 0 ? '🎉 СЕГОДНЯ!' : (b.days_left === 1 ? 'Завтра!' : `через ${b.days_left} дн.`);
          const badgeColor = b.days_left <= 3 ? 'bg-pink-500/20 text-pink-300 border-pink-500/30' : 'bg-slate-800 text-slate-300 border-white/5';
          
          bHtml += `
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-xl bg-pink-500/10 text-pink-400 flex items-center justify-center font-bold text-xs">
                  ${b.day}
                </div>
                <div>
                  <div class="text-xs font-bold text-white">${b.name}</div>
                  <div class="text-[10px] text-slate-400">${b.date_display} ${b.age_display ? '• ' + b.age_display : ''}</div>
                </div>
              </div>
              <div class="text-right">
                <span class="px-2.5 py-1 rounded-lg text-[10px] font-bold border ${badgeColor}">${daysText}</span>
              </div>
            </div>
          `;
        });
        bListEl.innerHTML = bHtml;
      } else {
        bListEl.innerHTML = '<div class="text-xs text-slate-400 text-center py-3">Дней рождения не найдено</div>';
      }

      // 5. Reminders
      const rListEl = document.getElementById('reminders-list');
      if (data.reminders && data.reminders.length > 0) {
        let rHtml = '';
        data.reminders.forEach(r => {
          rHtml += `
            <div class="glass-card p-3 rounded-2xl flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <button onclick="doneReminder('${r.id}')" class="w-7 h-7 rounded-lg border border-slate-700 hover:border-emerald-400 flex items-center justify-center text-emerald-400">
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

      // 6. Food
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

      // Re-initialize Lucide Icons
      lucide.createIcons();
    }

    // ACTIONS: SMART HOME
    async function toggleDeviceById(deviceId, state) {
      haptic('medium');
      try {
        const resp = await fetch('/api/smart_home/toggle', {
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
        const resp = await fetch('/api/smart_home/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name, state: true }) // Backend handles toggle
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

    // ACTIONS: TASKS & BIRTHDAYS & FOOD
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

    // LOAN CALCULATOR CLIENT-SIDE REACTIVE
    function runLoanCalc() {
      const amount = parseFloat(document.getElementById('calc-inp-amount').value);
      const rate = parseFloat(document.getElementById('calc-inp-rate').value);
      const months = parseInt(document.getElementById('calc-inp-months').value);
      const early = parseFloat(document.getElementById('calc-inp-early').value);

      document.getElementById('calc-lbl-amount').innerText = amount.toLocaleString('ru-RU') + ' ₽';
      document.getElementById('calc-lbl-rate').innerText = rate.toFixed(1) + ' %';
      document.getElementById('calc-lbl-months').innerText = `${months} мес. (${(months/12).toFixed(1)} г.)`;
      document.getElementById('calc-lbl-early').innerText = early.toLocaleString('ru-RU') + ' ₽';

      const monthlyRate = rate / 12 / 100;
      const annuityKoeff = (monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
      const monthlyPayment = amount * annuityKoeff;
      const totalPayout = monthlyPayment * months;
      const totalInterest = totalPayout - amount;

      document.getElementById('calc-res-payment').innerText = Math.round(monthlyPayment).toLocaleString('ru-RU') + ' ₽';
      document.getElementById('calc-res-interest').innerText = Math.round(totalInterest).toLocaleString('ru-RU') + ' ₽';

      // Calculate early savings
      if (early > 0) {
        let balance = amount;
        let earlyInterest = 0;
        let earlyMonths = 0;
        const totalMonthly = monthlyPayment + early;

        while (balance > 0 && earlyMonths < 600) {
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

    // INITIAL LOAD
    document.addEventListener('DOMContentLoaded', () => {
      lucide.createIcons();
      fetchDashboardData();
      runLoanCalc();
      // Auto-refresh every 30 seconds
      setInterval(fetchDashboardData, 30000);
    });
  </script>
</body>
</html>
"""
