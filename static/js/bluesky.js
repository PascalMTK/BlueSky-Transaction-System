/* ============================================================
   BLUESKY TRANSACTIONS — Main JavaScript
   Dark mode | Animations | Counters | UI interactions
   ============================================================ */

'use strict';

/* ============================================================
   1. DARK MODE
   ============================================================ */
const ThemeManager = {
    STORAGE_KEY: 'bluesky-theme',

    init() {
        const saved = localStorage.getItem(this.STORAGE_KEY) || 'light';
        this.apply(saved);
    },

    apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(this.STORAGE_KEY, theme);

        const btn = document.getElementById('themeToggle');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
            btn.title = theme === 'dark' ? 'Mode clair' : 'Mode sombre';
        }

        // Switch logo images based on theme (data-logo-light / data-logo-dark attributes)
        document.querySelectorAll('[data-logo-light]').forEach(function(img) {
            img.src = theme === 'dark' ? img.dataset.logoDark : img.dataset.logoLight;
        });

        // Update chart colors if charts exist
        if (window.blueskyCharts) {
            window.blueskyCharts.forEach(chart => {
                chart.options.plugins.legend.labels.color = theme === 'dark' ? '#94A3B8' : '#374151';
                chart.options.scales && Object.values(chart.options.scales).forEach(scale => {
                    scale.ticks = { ...scale.ticks, color: theme === 'dark' ? '#94A3B8' : '#374151' };
                    if (scale.grid) scale.grid.color = theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
                });
                chart.update('none');
            });
        }
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        this.apply(next);

        // Bounce animation on toggle
        const btn = document.getElementById('themeToggle');
        if (btn) {
            btn.style.transform = 'scale(1.3) rotate(20deg)';
            setTimeout(() => btn.style.transform = '', 300);
        }
    }
};

/* ============================================================
   2. ANIMATED COUNTER
   ============================================================ */
const CounterManager = {
    observed: new Set(),

    init() {
        const counters = document.querySelectorAll('[data-counter]');
        if (!counters.length) return;

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !this.observed.has(entry.target)) {
                        this.observed.add(entry.target);
                        this.animateCounter(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.3 });
            counters.forEach(c => observer.observe(c));
        } else {
            counters.forEach(c => this.animateCounter(c));
        }
    },

    animateCounter(el) {
        const target   = parseFloat(el.dataset.counter.replace(/[^0-9.]/g, ''));
        const suffix   = el.dataset.suffix || '';
        const prefix   = el.dataset.prefix || '';
        const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 0;

        // Start from the server-rendered value (avoids 0-flash when values are pre-rendered)
        const rawText  = el.textContent.trim().replace(/[^0-9.]/g, '');
        const startFrom = Math.min(parseFloat(rawText) || 0, target);

        // Already showing the correct value — no animation needed
        if (startFrom === target) return;

        const duration = 1400;
        const range    = target - startFrom;
        const start    = performance.now();
        const easeOutExpo = t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t);

        const update = (now) => {
            const elapsed = Math.min((now - start) / duration, 1);
            const value   = startFrom + range * easeOutExpo(elapsed);
            el.textContent = prefix + this.formatNumber(value, decimals) + suffix;
            if (elapsed < 1) requestAnimationFrame(update);
        };

        requestAnimationFrame(update);
    },

    formatNumber(n, decimals) {
        if (decimals > 0) return n.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        return Math.floor(n).toLocaleString('fr-FR');
    }
};

/* ============================================================
   3. TABLE ROW ANIMATIONS
   ============================================================ */

/* ============================================================
   4. SIDEBAR
   ============================================================ */
function toggleSidebar() {
    const sidebar  = document.getElementById('sidebar');
    const overlay  = document.getElementById('sidebarOverlay');
    const isOpen   = sidebar.classList.contains('open');
    sidebar.classList.toggle('open', !isOpen);
    overlay.classList.toggle('visible', !isOpen);
}
function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('visible');
}

/* ============================================================
   5. DROPDOWN
   ============================================================ */
function toggleDropdown(el) {
    const menu = el.nextElementSibling || document.getElementById('userDropdown');
    document.querySelectorAll('.dropdown-menu.show').forEach(m => { if (m !== menu) m.classList.remove('show'); });
    menu?.classList.toggle('show');
    event?.stopPropagation();
}
document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
});

/* ============================================================
   6. AUTO-HIDE ALERTS
   ============================================================ */
function initAlerts() {
    document.querySelectorAll('.alert').forEach(alert => {
        const close = document.createElement('button');
        close.innerHTML = '✕';
        close.style.cssText = 'background:none;border:none;cursor:pointer;font-size:14px;margin-left:auto;opacity:0.6;flex-shrink:0;padding:0;line-height:1;';
        close.onclick = () => dismissAlert(alert);
        alert.appendChild(close);

        setTimeout(() => dismissAlert(alert), 6000);
    });
}
function dismissAlert(alert) {
    alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease, max-height 0.4s ease, padding 0.4s ease, margin 0.4s ease';
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(20px)';
    alert.style.maxHeight = '0';
    alert.style.padding = '0';
    alert.style.marginBottom = '0';
    setTimeout(() => alert.remove(), 500);
}

/* ============================================================
   7. TOPBAR SCROLL EFFECT
   ============================================================ */
function initTopbarScroll() {
    const topbar = document.querySelector('.topbar');
    if (!topbar) return;
    window.addEventListener('scroll', () => {
        topbar.classList.toggle('scrolled', window.scrollY > 10);
    }, { passive: true });
}

/* ============================================================
   8. STAT CARD RIPPLE
   ============================================================ */
function initRipples() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const ripple = document.createElement('span');
            ripple.style.cssText = `position:absolute;width:10px;height:10px;background:rgba(255,255,255,0.4);border-radius:50%;transform:scale(0);left:${x-5}px;top:${y-5}px;pointer-events:none;animation:ripple 0.6s ease;`;
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 700);
        });
    });
}

/* ============================================================
   9. TABLE ROW HIGHLIGHT
   ============================================================ */
function initTableAnimations() {
    // CSS handles row entrance via fadeInLeft + nth-child delays (animation-fill-mode:backwards)
    // No JS opacity manipulation — avoids post-paint flash
}

/* ============================================================
   10. CHART DEFAULTS (dark-aware)
   ============================================================ */
function getChartDefaults() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        gridColor:  dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
        tickColor:  dark ? '#64748B' : '#94A3B8',
        labelColor: dark ? '#94A3B8' : '#374151',
        bgCard:     dark ? '#111827' : '#ffffff',
    };
}

/* Register Chart.js global defaults */
function applyChartDefaults() {
    if (typeof Chart === 'undefined') return;
    const d = getChartDefaults();
    Chart.defaults.color = d.labelColor;
    Chart.defaults.borderColor = d.gridColor;
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
    Chart.defaults.plugins.legend.labels.boxWidth = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
}

/* ============================================================
   11. SMOOTH NUMBER FORMAT
   ============================================================ */
window.formatMoney = (n) => {
    return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 0 }).format(Math.floor(n));
};

/* ============================================================
   12. CONFIRM DIALOGS (styled)
   ============================================================ */
function bskyConfirm(message) {
    return new Promise(resolve => {
        const i18n      = window.bskyI18n || {};
        const okLabel   = i18n.confirm_ok     || 'Confirmer';
        const noLabel   = i18n.confirm_cancel || 'Annuler';

        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px);animation:fadeIn 0.2s ease;';

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const bg  = isDark ? '#111827' : '#ffffff';
        const txt = isDark ? '#F1F5F9' : '#0F172A';
        const brd = isDark ? '#1F2937' : '#E2E8F0';

        overlay.innerHTML = `
            <div style="background:${bg};color:${txt};border:1px solid ${brd};border-radius:16px;padding:28px 32px;max-width:400px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.4);animation:scaleIn 0.3s ease;text-align:center;">
                <div style="font-size:36px;margin-bottom:12px;">⚠️</div>
                <div style="font-size:16px;font-weight:700;margin-bottom:8px;color:${txt}">Confirmation</div>
                <div style="font-size:14px;color:#64748B;margin-bottom:24px;">${message}</div>
                <div style="display:flex;gap:10px;justify-content:center;">
                    <button id="bskyConfirmNo" style="padding:10px 20px;border-radius:9px;border:1px solid ${brd};background:transparent;color:${txt};font-size:13px;font-weight:600;cursor:pointer;">${noLabel}</button>
                    <button id="bskyConfirmYes" style="padding:10px 22px;border-radius:9px;border:none;background:linear-gradient(135deg,#EF4444,#F87171);color:white;font-size:13px;font-weight:700;cursor:pointer;">${okLabel}</button>
                </div>
            </div>`;

        document.body.appendChild(overlay);
        document.getElementById('bskyConfirmYes').onclick = () => { overlay.remove(); resolve(true); };
        document.getElementById('bskyConfirmNo').onclick  = () => { overlay.remove(); resolve(false); };
        overlay.addEventListener('click', e => { if (e.target === overlay) { overlay.remove(); resolve(false); } });
    });
}

function bskyDangerConfirm(opts) {
    return new Promise(resolve => {
        const i18n  = window.bskyI18n || {};
        const title      = opts.title      || 'Attention';
        const message    = opts.message    || '';
        const checkLabel = opts.checkLabel || i18n.reset_system_confirm_check || 'Je confirme';
        const okLabel    = opts.okLabel    || i18n.confirm_ok                 || 'Confirmer';
        const noLabel    = opts.noLabel    || i18n.confirm_cancel             || 'Annuler';

        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px);animation:fadeIn 0.2s ease;';

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const bg  = isDark ? '#111827' : '#ffffff';
        const txt = isDark ? '#F1F5F9' : '#0F172A';
        const brd = isDark ? '#1F2937' : '#E2E8F0';
        const uid = 'bdc_' + Math.random().toString(36).slice(2);

        overlay.innerHTML = `
            <div style="background:${bg};color:${txt};border:2px solid #EF4444;border-radius:18px;padding:32px 32px 28px;max-width:440px;width:92%;box-shadow:0 24px 80px rgba(239,68,68,0.25);animation:scaleIn 0.3s ease;text-align:center;">
                <div style="width:60px;height:60px;background:rgba(239,68,68,0.1);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:28px;border:2px solid rgba(239,68,68,0.25);">🗑️</div>
                <div style="font-size:18px;font-weight:800;margin-bottom:10px;color:#EF4444;">${title}</div>
                <div style="font-size:13.5px;color:#64748B;margin-bottom:22px;line-height:1.6;">${message}</div>
                <label style="display:flex;align-items:flex-start;gap:10px;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:12px 14px;margin-bottom:22px;cursor:pointer;text-align:left;">
                    <input type="checkbox" id="${uid}" style="width:16px;height:16px;margin-top:2px;accent-color:#EF4444;flex-shrink:0;">
                    <span style="font-size:13px;font-weight:600;color:${txt};">${checkLabel}</span>
                </label>
                <div style="display:flex;gap:10px;justify-content:center;">
                    <button id="${uid}_no"  style="padding:10px 22px;border-radius:9px;border:1px solid ${brd};background:transparent;color:${txt};font-size:13px;font-weight:600;cursor:pointer;">${noLabel}</button>
                    <button id="${uid}_yes" disabled style="padding:10px 22px;border-radius:9px;border:none;background:linear-gradient(135deg,#DC2626,#EF4444);color:white;font-size:13px;font-weight:700;cursor:not-allowed;opacity:0.35;transition:opacity 0.2s,cursor 0.2s;">${okLabel}</button>
                </div>
            </div>`;

        document.body.appendChild(overlay);

        const cb  = document.getElementById(uid);
        const yes = document.getElementById(uid + '_yes');
        const no  = document.getElementById(uid + '_no');

        cb.addEventListener('change', () => {
            yes.disabled      = !cb.checked;
            yes.style.opacity = cb.checked ? '1' : '0.35';
            yes.style.cursor  = cb.checked ? 'pointer' : 'not-allowed';
        });
        yes.onclick = () => { overlay.remove(); resolve(true); };
        no.onclick  = () => { overlay.remove(); resolve(false); };
        overlay.addEventListener('click', e => { if (e.target === overlay) { overlay.remove(); resolve(false); } });
    });
}

/* Override native confirm on action forms */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const msg = form.dataset.confirm;
            const ok = await bskyConfirm(msg);
            if (ok) form.submit();
        });
    });
});

/* ============================================================
   13. LIVE CLOCK
   ============================================================ */
function startClock() {
    const el = document.getElementById('liveClock');
    if (!el) return;
    const tick = () => {
        const now = new Date();
        el.textContent = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };
    tick();
    setInterval(tick, 1000);
}

/* ============================================================
   INIT — DOMContentLoaded
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    CounterManager.init();
    initAlerts();
    initTopbarScroll();
    initTableAnimations();
    applyChartDefaults();
    startClock();
});

/* Global expose */
window.ThemeManager  = ThemeManager;
window.bskyConfirm   = bskyConfirm;
window.blueskyCharts = [];
