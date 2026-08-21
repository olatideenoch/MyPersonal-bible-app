/* ============================================================
   MyPersonal Bible - Shared JS (Study pages & tools)
   Theme, offline service worker, toasts, sync helpers,
   verse share cards and quick reference navigation.
   ============================================================ */

(function () {
    'use strict';

    /* ---------- Theme ---------- */
    function initTheme() {
        const savedTheme = localStorage.getItem('bibleAppTheme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const current = document.documentElement.getAttribute('data-theme');
                const next = current === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', next);
                localStorage.setItem('bibleAppTheme', next);
                updateThemeIcons(next);
            });
        });
        updateThemeIcons(document.documentElement.getAttribute('data-theme') || 'light');
    }

    function updateThemeIcons(theme) {
        document.querySelectorAll('[data-theme-icon]').forEach(function (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        });
    }

    /* ---------- Service worker (offline reading) ---------- */
    function registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function () {
                navigator.serviceWorker.register('/sw.js').catch(function (err) {
                    console.warn('Service worker registration failed:', err);
                });
            });
        }
    }

    /* ---------- Toast ---------- */
    function showToast(message, type) {
        type = type || 'info';
        const icon = type === 'success' ? 'check-circle' : (type === 'warning' ? 'exclamation-circle' : 'info-circle');
        const toast = document.createElement('div');
        toast.className = 'sync-toast';
        toast.innerHTML = '<i class="fas fa-' + icon + ' me-2"></i>' + message;
        document.body.appendChild(toast);
        setTimeout(function () { toast.remove(); }, 3200);
    }

    /* ---------- User / sync helpers ---------- */
    async function fetchUser() {
        try {
            const res = await fetch('/api/user');
            if (res.ok) return await res.json();
        } catch (e) { /* offline */ }
        return { authenticated: false };
    }

    async function fetchSyncData() {
        try {
            const res = await fetch('/api/sync');
            if (res.ok) return await res.json();
        } catch (e) { /* offline or unauthenticated */ }
        return null;
    }

    function localData() {
        const progress = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('reading_progress_')) {
                try { progress[key] = JSON.parse(localStorage.getItem(key)); } catch (e) {}
            }
        }
        return {
            bookmarks: JSON.parse(localStorage.getItem('bibleBookmarks') || '[]'),
            highlights: JSON.parse(localStorage.getItem('bibleHighlights') || '{}'),
            highlightColors: JSON.parse(localStorage.getItem('bibleHighlightColors') || '{}'),
            highlightLabels: JSON.parse(localStorage.getItem('bibleHighlightLabels') || '{}'),
            memoryState: JSON.parse(localStorage.getItem('bibleMemoryState') || '{}'),
            notes: JSON.parse(localStorage.getItem('bibleNotes') || '[]'),
            prayers: JSON.parse(localStorage.getItem('biblePrayers') || '[]'),
            plans: JSON.parse(localStorage.getItem('biblePlans') || '{}'),
            customPlans: JSON.parse(localStorage.getItem('bibleCustomPlans') || '{}'),
            quizStats: JSON.parse(localStorage.getItem('bibleQuizStats') || 'null'),
            readingLog: JSON.parse(localStorage.getItem('bibleReadingLog') || '[]'),
            dailyActivity: JSON.parse(localStorage.getItem('bibleDailyActivity') || '{}'),
            preferred_version: localStorage.getItem('biblePreferredVersion'),
            progress: progress,
            font_size: localStorage.getItem('bibleFontSize'),
            theme: localStorage.getItem('bibleAppTheme')
        };
    }

    async function syncNow() {
        const user = await fetchUser();
        if (!user.authenticated) {
            showToast('Please sign in to sync your data', 'warning');
            return false;
        }
        showToast('Syncing your data...');
        try {
            const postBody = Object.assign(localData(), readingBuildDailyPayload());
            const response = await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(postBody)
            });
            if (response.ok) {
                readingMarkPosted();
                const serverData = await fetchSyncData();
                if (serverData) {
                    if (serverData.bookmarks) localStorage.setItem('bibleBookmarks', JSON.stringify(serverData.bookmarks));
                    if (serverData.highlights) localStorage.setItem('bibleHighlights', JSON.stringify(serverData.highlights));
                    if (serverData.highlightColors) localStorage.setItem('bibleHighlightColors', JSON.stringify(serverData.highlightColors));
                    if (serverData.highlightLabels) localStorage.setItem('bibleHighlightLabels', JSON.stringify(serverData.highlightLabels));
                    if (serverData.memoryState) localStorage.setItem('bibleMemoryState', JSON.stringify(serverData.memoryState));
                    if (serverData.customPlans) localStorage.setItem('bibleCustomPlans', JSON.stringify(serverData.customPlans));
                    if (serverData.notes) localStorage.setItem('bibleNotes', JSON.stringify(serverData.notes));
                    if (serverData.prayers) localStorage.setItem('biblePrayers', JSON.stringify(serverData.prayers));
                    if (serverData.plans) localStorage.setItem('biblePlans', JSON.stringify(serverData.plans));
                    if (serverData.quizStats) localStorage.setItem('bibleQuizStats', JSON.stringify(serverData.quizStats));
                    if (serverData.readingLog) localStorage.setItem('bibleReadingLog', JSON.stringify(serverData.readingLog));
                    if (serverData.dailyActivity) {
                        readingApplyServerDaily(serverData.dailyActivity);
                    }
                    if (serverData.preferred_version) localStorage.setItem('biblePreferredVersion', serverData.preferred_version);
                    if (serverData.progress) {
                        Object.keys(serverData.progress).forEach(function (k) {
                            try { localStorage.setItem(k, JSON.stringify(serverData.progress[k])); } catch (e) {}
                        });
                    }
                    if (serverData.font_size) localStorage.setItem('bibleFontSize', serverData.font_size);
                    if (serverData.theme) localStorage.setItem('bibleAppTheme', serverData.theme);
                }
                showToast('Sync completed successfully!', 'success');
                return true;
            } else {
                showToast('Sync failed. Please try again.', 'warning');
            }
        } catch (error) {
            console.error('Sync error:', error);
            showToast('Sync failed. Please try again.', 'warning');
        }
        return false;
    }

    /* ---------- Verse share card (canvas -> PNG, multiple designs) ---------- */
    const VERSE_CARD_TEMPLATES = [
        {
            id: 'classic',
            name: 'Classic Gold',
            paint: function (ctx, w, h) {
                const bg = ctx.createLinearGradient(0, 0, w, h);
                if (document.documentElement.getAttribute('data-theme') === 'dark') {
                    bg.addColorStop(0, '#1a0f00');
                    bg.addColorStop(1, '#3d2205');
                } else {
                    bg.addColorStop(0, '#3d2205');
                    bg.addColorStop(1, '#7a4b10');
                }
                ctx.fillStyle = bg;
                ctx.fillRect(0, 0, w, h);
                ctx.globalAlpha = 0.15;
                ctx.fillStyle = '#e8b86a';
                ctx.beginPath(); ctx.arc(w - w * 0.065, h * 0.074, w * 0.14, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.arc(w * 0.055, h - h * 0.074, w * 0.1, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 1;
            },
            label: '#e8b86a', labelFont: '600 42px Georgia, serif',
            divider: 'rgba(232,184,106,0.6)',
            verse: '#faf6ee', verseFont: 'italic 50px Georgia, serif',
            ref: '#e8b86a', refFont: '600 56px Georgia, serif',
            footer: 'rgba(250,246,238,0.8)', footerFont: '32px Georgia, serif'
        },
        {
            id: 'midnight',
            name: 'Midnight',
            paint: function (ctx, w, h) {
                const bg = ctx.createLinearGradient(0, 0, 0, h);
                bg.addColorStop(0, '#0f1b33');
                bg.addColorStop(1, '#1e3a5f');
                ctx.fillStyle = bg;
                ctx.fillRect(0, 0, w, h);
                // star field
                const stars = [[0.12, 0.2], [0.3, 0.12], [0.55, 0.18], [0.75, 0.09], [0.88, 0.24],
                               [0.2, 0.75], [0.45, 0.8], [0.7, 0.72], [0.9, 0.8], [0.08, 0.5], [0.35, 0.45], [0.85, 0.55]];
                stars.forEach(function (s, i) {
                    ctx.globalAlpha = 0.25 + (i % 3) * 0.2;
                    ctx.fillStyle = '#f0d9a8';
                    ctx.beginPath(); ctx.arc(s[0] * w, s[1] * h, w * 0.006, 0, Math.PI * 2); ctx.fill();
                });
                // moon
                ctx.globalAlpha = 0.2;
                ctx.fillStyle = '#e8b86a';
                ctx.beginPath(); ctx.arc(w * 0.85, h * 0.14, w * 0.13, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 1;
            },
            label: '#e8b86a', labelFont: '600 42px Georgia, serif',
            divider: 'rgba(232,184,106,0.55)',
            verse: '#eef2f7', verseFont: 'italic 50px Georgia, serif',
            ref: '#f0c987', refFont: '600 56px Georgia, serif',
            footer: 'rgba(238,242,247,0.7)', footerFont: '32px Georgia, serif'
        },
        {
            id: 'sunrise',
            name: 'Sunrise',
            paint: function (ctx, w, h) {
                const bg = ctx.createLinearGradient(0, 0, 0, h);
                bg.addColorStop(0, '#f9e3bd');
                bg.addColorStop(0.55, '#f2c07f');
                bg.addColorStop(1, '#e8975a');
                ctx.fillStyle = bg;
                ctx.fillRect(0, 0, w, h);
                // sun
                ctx.globalAlpha = 0.35;
                ctx.fillStyle = '#fff3dd';
                ctx.beginPath(); ctx.arc(w * 0.5, h * 0.42, w * 0.16, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 0.18;
                ctx.fillStyle = '#ffffff';
                ctx.beginPath(); ctx.arc(w * 0.5, h * 0.42, w * 0.24, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 0.12;
                ctx.beginPath(); ctx.arc(w * 0.5, h * 0.42, w * 0.32, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 1;
            },
            label: '#6b3f12', labelFont: '600 42px Georgia, serif',
            divider: 'rgba(107,63,18,0.55)',
            verse: '#3d2205', verseFont: 'italic 50px Georgia, serif',
            ref: '#7a4b10', refFont: '600 56px Georgia, serif',
            footer: 'rgba(61,34,5,0.75)', footerFont: '32px Georgia, serif'
        },
        {
            id: 'forest',
            name: 'Forest',
            paint: function (ctx, w, h) {
                const bg = ctx.createLinearGradient(0, 0, w, h);
                bg.addColorStop(0, '#12301f');
                bg.addColorStop(1, '#1f5c38');
                ctx.fillStyle = bg;
                ctx.fillRect(0, 0, w, h);
                ctx.globalAlpha = 0.12;
                ctx.fillStyle = '#9be8c0';
                ctx.beginPath(); ctx.arc(w - w * 0.06, h * 0.08, w * 0.15, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.arc(w * 0.06, h - h * 0.06, w * 0.12, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 0.1;
                ctx.beginPath(); ctx.arc(w * 0.85, h * 0.88, w * 0.1, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 1;
            },
            label: '#9be8c0', labelFont: '600 42px Georgia, serif',
            divider: 'rgba(155,232,192,0.55)',
            verse: '#f2f7f0', verseFont: 'italic 50px Georgia, serif',
            ref: '#a8e6c0', refFont: '600 56px Georgia, serif',
            footer: 'rgba(242,247,240,0.7)', footerFont: '32px Georgia, serif'
        },
        {
            id: 'ocean',
            name: 'Ocean',
            paint: function (ctx, w, h) {
                const bg = ctx.createLinearGradient(0, 0, 0, h);
                bg.addColorStop(0, '#0b3954');
                bg.addColorStop(1, '#1d6a96');
                ctx.fillStyle = bg;
                ctx.fillRect(0, 0, w, h);
                // waves
                ctx.globalAlpha = 0.16;
                ctx.strokeStyle = '#bfe9ff';
                ctx.lineWidth = Math.max(2, w * 0.006);
                [[0.62, 0.18], [0.5, 0.22], [0.55, 0.16], [0.48, 0.2]].forEach(function (wave) {
                    ctx.beginPath();
                    ctx.moveTo(0, h * wave[0]);
                    ctx.quadraticCurveTo(w * 0.25, h * (wave[0] - wave[1]), w * 0.5, h * wave[0]);
                    ctx.quadraticCurveTo(w * 0.75, h * (wave[0] + wave[1]), w, h * wave[0]);
                    ctx.stroke();
                });
                ctx.globalAlpha = 0.14;
                ctx.fillStyle = '#bfe9ff';
                ctx.beginPath(); ctx.arc(w * 0.82, h * 0.12, w * 0.12, 0, Math.PI * 2); ctx.fill();
                ctx.globalAlpha = 1;
            },
            label: '#bfe9ff', labelFont: '600 42px Georgia, serif',
            divider: 'rgba(191,233,255,0.55)',
            verse: '#f0faff', verseFont: 'italic 50px Georgia, serif',
            ref: '#9fd8f7', refFont: '600 56px Georgia, serif',
            footer: 'rgba(240,250,255,0.7)', footerFont: '32px Georgia, serif'
        },
        {
            id: 'cream',
            name: 'Minimal Cream',
            paint: function (ctx, w, h) {
                ctx.fillStyle = '#faf6ee';
                ctx.fillRect(0, 0, w, h);
                // thin gold frame
                ctx.strokeStyle = '#c9923a';
                ctx.lineWidth = w * 0.006;
                ctx.strokeRect(w * 0.03, h * 0.03, w * 0.94, h * 0.94);
                // corner accents
                ctx.fillStyle = '#c9923a';
                ctx.beginPath(); ctx.arc(w * 0.5, h * 0.2, w * 0.008, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.arc(w * 0.5, h * 0.78, w * 0.008, 0, Math.PI * 2); ctx.fill();
            },
            label: '#9a6a1e', labelFont: '700 42px Georgia, serif',
            divider: 'rgba(154,106,30,0.6)',
            verse: '#3d2205', verseFont: 'italic 50px Georgia, serif',
            ref: '#9a6a1e', refFont: '600 56px Georgia, serif',
            footer: 'rgba(61,34,5,0.7)', footerFont: '32px Georgia, serif'
        }
    ];

    function getCardTemplate(id) {
        for (let i = 0; i < VERSE_CARD_TEMPLATES.length; i++) {
            if (VERSE_CARD_TEMPLATES[i].id === id) return VERSE_CARD_TEMPLATES[i];
        }
        return VERSE_CARD_TEMPLATES[0];
    }

    function generateVerseCard(reference, text, options) {
        options = options || {};
        const tpl = getCardTemplate(options.template || 'classic');
        const width = 1080;
        const height = 1080; // square card (1:1 - ideal for social feeds)
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');

        tpl.paint(ctx, width, height);

        // Top label
        ctx.fillStyle = tpl.label;
        ctx.font = tpl.labelFont;
        ctx.textAlign = 'center';
        ctx.fillText('MyPersonal Bible', width / 2, 110);

        // Divider
        ctx.strokeStyle = tpl.divider;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(width / 2 - 60, 150);
        ctx.lineTo(width / 2 + 60, 150);
        ctx.stroke();

        // Verse text (wrapped, vertically centered)
        ctx.fillStyle = tpl.verse;
        ctx.font = tpl.verseFont;
        const words = text.split(' ');
        const maxWidth = width - 160;
        const maxLines = 7;
        let lines = [];
        let line = '';
        for (let i = 0; i < words.length; i++) {
            const test = line + (line ? ' ' : '') + words[i];
            if (ctx.measureText(test).width > maxWidth && line) {
                lines.push(line);
                line = words[i];
            } else {
                line = test;
            }
        }
        if (line) lines.push(line);

        let truncated = false;
        if (lines.length > maxLines) {
            lines = lines.slice(0, maxLines);
            truncated = true;
        }
        if (truncated) {
            lines[maxLines - 1] = lines[maxLines - 1].replace(/[.,;:!?\s]+$/, '') + ' …';
        }

        const lineHeight = 80;
        const blockHeight = lines.length * lineHeight;
        const bandTop = 220;
        const bandBottom = 800;
        let y = bandTop + Math.max(0, (bandBottom - bandTop - blockHeight) / 2) + 60;
        lines.forEach(function (l) {
            ctx.fillText(l, width / 2, y);
            y += lineHeight;
        });

        // Reference
        ctx.fillStyle = tpl.ref;
        ctx.font = tpl.refFont;
        ctx.fillText('— ' + reference + ' —', width / 2, 900);

        // Footer
        ctx.fillStyle = tpl.footer;
        ctx.font = tpl.footerFont;
        ctx.fillText('mypersonal-bible-app.onrender.com', width / 2, 990);

        return canvas;
    }

    function renderTemplateThumb(templateId, size) {
        size = size || 84;
        const tpl = getCardTemplate(templateId);
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        tpl.paint(canvas.getContext('2d'), size, size);
        return canvas;
    }

    function ensureShareStyles() {
        if (document.getElementById('mpb-share-styles')) return;
        const style = document.createElement('style');
        style.id = 'mpb-share-styles';
        style.textContent =
            '.share-template-btn{display:inline-flex;flex-direction:column;align-items:center;gap:5px;' +
            'background:none;border:2px solid transparent;border-radius:12px;padding:5px;cursor:pointer;' +
            'color:var(--text-muted);font-size:0.68rem;line-height:1.2;min-width:74px;transition:border-color .15s ease,color .15s ease;}' +
            '.share-template-btn canvas{border-radius:8px;width:64px;height:64px;display:block;}' +
            '.share-template-btn:hover{border-color:var(--border-color);}' +
            '.share-template-btn.active{border-color:var(--accent-text);color:var(--accent-text);font-weight:600;}';
        document.head.appendChild(style);
    }

    function shareVerse(reference, text, verseTextEl) {
        ensureShareStyles();
        let currentTemplate = localStorage.getItem('bibleCardTemplate') || 'classic';
        let currentUrl = null;

        function regenerate() {
            const canvas = generateVerseCard(reference, text, { template: currentTemplate });
            return new Promise(function (resolve) {
                canvas.toBlob(function (blob) {
                    if (currentUrl) URL.revokeObjectURL(currentUrl);
                    currentUrl = URL.createObjectURL(blob);
                    resolve(currentUrl);
                }, 'image/png');
            });
        }

        const encRef = encodeURIComponent(reference);
        const encText = encodeURIComponent(reference + ' - "' + text + '"');
        const pageUrl = encodeURIComponent(window.location.origin);

        const pickerHtml = VERSE_CARD_TEMPLATES.map(function (tpl) {
            return '<button type="button" class="share-template-btn' + (tpl.id === currentTemplate ? ' active' : '') +
                '" data-template="' + tpl.id + '" title="' + tpl.name + '">' +
                '<canvas width="84" height="84" data-thumb="' + tpl.id + '"></canvas>' +
                '<span>' + tpl.name + '</span></button>';
        }).join('');

        const shareHtml =
            '<div class="text-center mb-3">' +
            '  <img id="shareCardPreview" src="" alt="Verse card" style="width:100%;max-width:340px;aspect-ratio:1/1;object-fit:cover;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,0.25);">' +
            '</div>' +
            '<div class="d-flex flex-wrap justify-content-center gap-1 mb-3" id="shareTemplateRow">' + pickerHtml + '</div>' +
            '<div class="d-flex flex-wrap justify-content-center gap-2 mb-3">' +
            '  <a class="btn btn-success btn-sm" href="https://wa.me/?text=' + encText + '" target="_blank" rel="noopener"><i class="fab fa-whatsapp me-1"></i> WhatsApp</a>' +
            '  <a class="btn btn-primary btn-sm" href="https://twitter.com/intent/tweet?text=' + encText + '&url=' + pageUrl + '" target="_blank" rel="noopener"><i class="fab fa-x-twitter me-1"></i> X</a>' +
            '  <a class="btn btn-sm" style="background:#1877f2;color:#fff;" href="https://www.facebook.com/sharer/sharer.php?u=' + pageUrl + '&quote=' + encText + '" target="_blank" rel="noopener"><i class="fab fa-facebook-f me-1"></i> Facebook</a>' +
            '  <a class="btn btn-sm" style="background:#0088cc;color:#fff;" href="https://t.me/share/url?url=' + pageUrl + '&text=' + encText + '" target="_blank" rel="noopener"><i class="fab fa-telegram-plane me-1"></i> Telegram</a>' +
            '</div>' +
            '<div class="d-flex justify-content-center gap-2">' +
            '  <button class="btn btn-outline-secondary btn-sm" id="shareDownloadBtn"><i class="fas fa-download me-1"></i> Download Image</button>' +
            '  <button class="btn btn-outline-secondary btn-sm" id="shareCopyBtn"><i class="fas fa-copy me-1"></i> Copy Text</button>' +
            '</div>';

        const modal = document.createElement('div');
        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:3000;display:flex;align-items:center;justify-content:center;padding:16px;overflow-y:auto;';
        modal.innerHTML =
            '<div style="background:var(--card-bg);border-radius:16px;max-width:560px;width:100%;padding:20px;position:relative;margin:auto;">' +
            '  <button id="shareCloseBtn" style="position:absolute;top:12px;right:12px;background:none;border:none;font-size:1.4rem;color:var(--text-muted);cursor:pointer;">&times;</button>' +
            '  <h5 class="text-center mb-3" style="color:var(--text-primary);">Share This Verse</h5>' +
            '  <p class="text-center text-muted small mb-2" style="font-size:0.78rem;">Pick a card style</p>' +
            shareHtml +
            '</div>';
        document.body.appendChild(modal);

        // draw the template thumbnails
        modal.querySelectorAll('canvas[data-thumb]').forEach(function (c) {
            const thumb = renderTemplateThumb(c.dataset.thumb);
            c.getContext('2d').drawImage(thumb, 0, 0);
        });

        // initial preview
        regenerate().then(function (url) {
            const img = modal.querySelector('#shareCardPreview');
            if (img) img.src = url;
        });

        // template switching
        modal.querySelectorAll('.share-template-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                if (btn.dataset.template === currentTemplate) return;
                currentTemplate = btn.dataset.template;
                try { localStorage.setItem('bibleCardTemplate', currentTemplate); } catch (e) { /* ignore */ }
                modal.querySelectorAll('.share-template-btn').forEach(function (b) {
                    b.classList.toggle('active', b.dataset.template === currentTemplate);
                });
                regenerate().then(function (url) {
                    const img = modal.querySelector('#shareCardPreview');
                    if (img) img.src = url;
                });
            });
        });

        modal.addEventListener('click', function (e) { if (e.target === modal) modal.remove(); });
        modal.querySelector('#shareCloseBtn').addEventListener('click', function () { modal.remove(); });
        modal.querySelector('#shareDownloadBtn').addEventListener('click', function () {
            const a = document.createElement('a');
            a.href = currentUrl;
            a.download = reference.replace(/[^a-z0-9]+/gi, '-') + '.png';
            a.click();
        });
        modal.querySelector('#shareCopyBtn').addEventListener('click', function () {
            const copyText = reference + ' - "' + text + '"';
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(copyText).then(function () { showToast('Verse copied!', 'success'); });
            } else {
                const ta = document.createElement('textarea');
                ta.value = copyText;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                ta.remove();
                showToast('Verse copied!', 'success');
            }
        });
    }

    /* ---------- Quick reference jump ---------- */
    // Parses "John 3:16", "psalm 23", "1 cor 13:4" etc -> /books/{slug}?chapter=N&verse=M
    const BOOK_ALIASES = {
        '1sam': '1-samuel', '2sam': '2-samuel', '1samuel': '1-samuel', '2samuel': '2-samuel',
        '1kgs': '1-kings', '2kgs': '2-kings', '1ki': '1-kings', '2ki': '2-kings',
        '1king': '1-kings', '2king': '2-kings', '1kings': '1-kings', '2kings': '2-kings',
        '1chr': '1-chronicles', '2chr': '2-chronicles', '1chron': '1-chronicles', '2chron': '2-chronicles',
        '1chronicles': '1-chronicles', '2chronicles': '2-chronicles',
        '1cor': '1-corinthians', '2cor': '2-corinthians', '1corinthians': '1-corinthians', '2corinthians': '2-corinthians',
        '1thes': '1-thessalonians', '2thes': '2-thessalonians', '1thess': '1-thessalonians', '2thess': '2-thessalonians',
        '1tim': '1-timothy', '2tim': '2-timothy', '1timothy': '1-timothy', '2timothy': '2-timothy',
        '1pet': '1-peter', '2pet': '2-peter', '1peter': '1-peter', '2peter': '2-peter',
        '1jn': '1-john', '2jn': '2-john', '3jn': '3-john', '1john': '1-john', '2john': '2-john', '3john': '3-john',
        'ps': 'psalms', 'psalm': 'psalms', 'psa': 'psalms', 'sos': 'song-of-solomon', 'song': 'song-of-solomon',
        'ss': 'song-of-solomon', 'ecc': 'ecclesiastes', 'eccles': 'ecclesiastes', 'gen': 'genesis', 'exo': 'exodus',
        'ex': 'exodus', 'lev': 'leviticus', 'num': 'numbers', 'deut': 'deuteronomy', 'dt': 'deuteronomy',
        'jos': 'joshua', 'josh': 'joshua', 'jdg': 'judges', 'judg': 'judges', 'rev': 'revelation', 'revelations': 'revelation',
        'mt': 'matthew', 'matt': 'matthew', 'mk': 'mark', 'mrk': 'mark', 'lk': 'luke', 'luk': 'luke',
        'jn': 'john', 'jhn': 'john', 'joh': 'john', 'act': 'acts', 'rom': 'romans', 'phil': 'philippians',
        'php': 'philippians', 'col': 'colossians', 'gal': 'galatians', 'eph': 'ephesians', 'heb': 'hebrews',
        'jas': 'james', 'jam': 'james', 'jud': 'jude', 'phm': 'philemon', 'philem': 'philemon', 'tit': 'titus',
        'prov': 'proverbs', 'pro': 'proverbs', 'isa': 'isaiah', 'jer': 'jeremiah', 'ezek': 'ezekiel', 'eze': 'ezekiel',
        'dan': 'daniel', 'hos': 'hosea', 'joel': 'joel', 'amos': 'amos', 'obad': 'obadiah', 'oba': 'obadiah',
        'jon': 'jonah', 'mic': 'micah', 'nah': 'nahum', 'hab': 'habakkuk', 'zeph': 'zephaniah', 'zep': 'zephaniah',
        'hag': 'haggai', 'zech': 'zechariah', 'zec': 'zechariah', 'mal': 'malachi', 'neh': 'nehemiah', 'est': 'esther',
        'ezr': 'ezra', 'rut': 'ruth', 'lam': 'lamentations', 'lament': 'lamentations'
    };

    function parseReference(input) {
        const cleaned = String(input || '').trim().toLowerCase().replace(/\s+/g, ' ');
        if (!cleaned) return null;
        // Match: <book tokens> <chapter>[:<verse>]
        const m = cleaned.match(/^([1-3]?\s?[a-z]+(?:\s+of\s+[a-z]+)?)\s+(\d{1,3})(?:\s*[:.]\s*(\d{1,3}))?$/);
        if (!m) return null;
        let bookToken = m[1].trim().replace(/\s+of\s+$/, '');
        // Normalize "1 samuel" -> "1samuel"
        bookToken = bookToken.replace(/\s+/g, '');
        const chapter = parseInt(m[2], 10);
        const verse = m[3] ? parseInt(m[3], 10) : null;

        // Build candidate slugs
        const candidates = [];
        candidates.push(bookToken);
        if (BOOK_ALIASES[bookToken]) candidates.push(BOOK_ALIASES[bookToken]);
        if (/^[123]/.test(bookToken) && bookToken.length > 1) {
            candidates.push(bookToken.slice(1)); // e.g. "1samuel" -> "samuel"
            candidates.push(bookToken[0] + '-' + bookToken.slice(1)); // "1-samuel"
            candidates.push(bookToken.slice(0, 1) + ' ' + bookToken.slice(1)); // handled by hyphen version below
        }
        candidates.push(bookToken.replace(/^([123])([a-z])/, '$1-$2')); // "1samuel" -> "1-samuel"
        candidates.push(bookToken.replace(/^([123])([a-z])/, '$1 $2')); // "1samuel" -> "1 samuel"

        const knownSlugs = MPB_BOOK_SLUGS || [];
        let slug = null;
        for (let i = 0; i < candidates.length; i++) {
            const c = candidates[i].replace(/[\s']/g, '-');
            if (knownSlugs.indexOf(c) !== -1) { slug = c; break; }
        }
        if (!slug) {
            // Last resort: contains-match on the first word
            const firstWord = bookToken.replace(/^[123]\s*/, '');
            for (let i = 0; i < knownSlugs.length; i++) {
                if (knownSlugs[i].indexOf(firstWord) === 0) { slug = knownSlugs[i]; break; }
            }
        }
        if (!slug) return null;
        return { slug: slug, chapter: chapter, verse: verse };
    }

    function jumpToReference(input) {
        const ref = parseReference(input);
        if (!ref) {
            showToast('Could not understand that reference. Try e.g. "John 3:16"', 'warning');
            return false;
        }
        let url = '/books/' + ref.slug + '?chapter=' + ref.chapter;
        if (ref.verse) url += '&verse=' + ref.verse;
        window.location.href = url;
        return true;
    }

    /* ---------- Automatic data restore (free-tier resilience) ----------
       On free hosting the server's copy of user data is wiped on every
       redeploy. The browser copy survives. So whenever a signed-in user
       opens the app, we silently re-upload their data (throttled to once
       every 10 minutes) — the server copy rebuilds itself with zero
       action needed from the user. */
    async function autoRestoreSync() {
        try {
            const last = parseInt(localStorage.getItem('bibleLastAutoSync') || '0', 10);
            if (Date.now() - last < 10 * 60 * 1000) return;
            const user = await fetchUser();
            if (!user.authenticated) return;
            const postBody = Object.assign(localData(), readingBuildDailyPayload());
            const res = await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(postBody)
            });
            if (res.ok) {
                localStorage.setItem('bibleLastAutoSync', String(Date.now()));
                readingMarkPosted();
                const serverData = await fetchSyncData();
                if (serverData && serverData.dailyActivity) {
                    readingApplyServerDaily(serverData.dailyActivity);
                }
            }
        } catch (e) { /* offline - try again next visit */ }
    }

    // Lightweight push of today's reading time (used on tab hide/unload so
    // the server always has the freshest minutes without a full sync). When
    // the response arrives, refresh the cached server total so this device's
    // display stays in step with other devices.
    async function pushDailyActivity() {
        try {
            const body = readingBuildDailyPayload();
            const res = await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
                keepalive: true
            });
            if (res.ok) {
                readingMarkPosted();
                try {
                    const serverData = await fetchSyncData();
                    if (serverData && serverData.dailyActivity) {
                        readingApplyServerDaily(serverData.dailyActivity);
                    }
                } catch (e2) { /* response may not arrive during unload */ }
            }
        } catch (e) { /* offline or closing tab */ }
    }

    /* ---------- Daily verse reminders (Web Push) ---------- */
    const PUSH_STATE_KEY = 'biblePushReminders';

    function pushSupported() {
        return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
    }

    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
        return outputArray;
    }

    async function pushGetConfig() {
        try {
            const res = await fetch('/api/push/config');
            if (res.ok) return await res.json();
        } catch (e) { /* offline */ }
        return { available: false, public_key: '' };
    }

    async function pushStatus() {
        if (!pushSupported()) return 'unsupported';
        const cfg = await pushGetConfig();
        if (!cfg.available) return 'unconfigured';
        if (Notification.permission === 'denied') return 'denied';
        if (localStorage.getItem(PUSH_STATE_KEY) !== 'on') return 'off';
        try {
            const reg = await navigator.serviceWorker.getRegistration();
            if (!reg) return 'off';
            const sub = await reg.pushManager.getSubscription();
            return sub ? 'on' : 'off';
        } catch (e) { return 'off'; }
    }

    function updatePushUI(status) {
        document.querySelectorAll('[data-push-reminders]').forEach(function (btn) {
            const icon = btn.querySelector('[data-push-icon]');
            const label = btn.querySelector('[data-push-label]');
            const enabled = status === 'on';
            if (icon) icon.className = 'fas ' + (enabled ? 'fa-bell' : 'fa-bell-slash');
            btn.title = enabled ? 'Daily verse reminders: ON (tap to turn off)' : 'Daily verse reminders: OFF (tap to turn on)';
            if (enabled) btn.classList.add('push-on');
            else btn.classList.remove('push-on');
            if (label) label.textContent = enabled ? 'Reminder On' : 'Verse Reminder';
        });
    }

    async function refreshPushUI() {
        const status = await pushStatus();
        updatePushUI(status);
        return status;
    }

    async function pushToggle() {
        const status = await pushStatus();
        if (status === 'unsupported') {
            showToast('This browser does not support notifications', 'warning');
            return;
        }
        if (status === 'unconfigured') {
            showToast('Daily reminders are not configured yet on this server (see README)', 'warning');
            return;
        }
        if (status === 'denied') {
            showToast('Notifications are blocked in your browser settings', 'warning');
            return;
        }
        if (status === 'on') {
            // Disable
            try {
                const reg = await navigator.serviceWorker.getRegistration();
                const sub = reg ? await reg.pushManager.getSubscription() : null;
                if (sub) {
                    await fetch('/api/push/subscribe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ subscription: sub.toJSON(), enabled: false })
                    });
                    await sub.unsubscribe();
                }
                localStorage.setItem(PUSH_STATE_KEY, 'off');
                updatePushUI('off');
                showToast('Daily verse reminders turned off');
            } catch (e) {
                showToast('Could not turn off reminders', 'warning');
            }
            return;
        }
        // Enable
        if (Notification.permission === 'default') {
            const perm = await Notification.requestPermission();
            if (perm !== 'granted') {
                showToast('Permission not granted — reminders stay off', 'warning');
                updatePushUI('off');
                return;
            }
        }
        try {
            const cfg = await pushGetConfig();
            if (!cfg.available) {
                showToast('Daily reminders are not configured yet on this server (see README)', 'warning');
                return;
            }
            const reg = await navigator.serviceWorker.ready;
            let sub = await reg.pushManager.getSubscription();
            if (!sub) {
                sub = await reg.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(cfg.public_key)
                });
            }
            const res = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subscription: sub.toJSON(), enabled: true })
            });
            if (res.ok) {
                localStorage.setItem(PUSH_STATE_KEY, 'on');
                updatePushUI('on');
                showToast('Daily verse reminders are ON! 🎉 You\'ll get a verse each morning.', 'success');
            } else {
                showToast('Could not enable reminders', 'warning');
            }
        } catch (e) {
            console.error('Push enable error:', e);
            showToast('Could not enable reminders on this browser', 'warning');
        }
    }

    
    /* ---------- Scroll reveal (subtle fade-up) ---------- */
    function initScrollReveal() {
        const els = document.querySelectorAll('.reveal');
        if (!els.length) return;
        if (!('IntersectionObserver' in window)) {
            els.forEach(function (el) { el.classList.add('reveal-visible'); });
            return;
        }
        const io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('reveal-visible');
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
        els.forEach(function (el) { io.observe(el); });
    }


    /* ---------- Welcome / Features modal (shared across pages) ---------- */
    function initWelcomeModal() {
        const modalEl = document.getElementById('welcomeModal');
        if (!modalEl || typeof bootstrap === 'undefined') return;

        const wm = new bootstrap.Modal(modalEl, { backdrop: true, keyboard: true, focus: true });
        const dsc = document.getElementById('dontShowAgain');
        const WELCOME_VERSION = '2.8.0';

        // Show the modal once per app version (resets the "don't show" flag on updates)
        const lsv = localStorage.getItem('bibleAppVersion');
        if (lsv !== WELCOME_VERSION) {
            localStorage.removeItem('bibleAppWelcomeSeen');
            localStorage.removeItem('bibleAppDontShowWelcome');
            localStorage.setItem('bibleAppVersion', WELCOME_VERSION);
        }

        function showWelcome() {
            wm.show();
        }
        window.MPB.openWelcome = showWelcome;

        // Every trigger: the ? icons and the "Help & Features" dropdown item
        document.querySelectorAll('[data-welcome-open]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                // close the dropdown menu if the trigger lives inside one
                const menu = btn.closest('.dropdown-menu');
                if (menu && menu.classList.contains('show')) {
                    const toggle = menu.parentElement.querySelector('[data-bs-toggle="dropdown"]');
                    if (toggle && bootstrap.Dropdown) {
                        const inst = bootstrap.Dropdown.getInstance(toggle) || new bootstrap.Dropdown(toggle);
                        inst.hide();
                    }
                }
                showWelcome();
            });
        });

        if (dsc) {
            dsc.addEventListener('change', function () {
                if (this.checked) localStorage.setItem('bibleAppDontShowWelcome', 'true');
                else localStorage.removeItem('bibleAppDontShowWelcome');
            });
        }
        modalEl.addEventListener('hidden.bs.modal', function () {
            if (dsc && dsc.checked) localStorage.setItem('bibleAppDontShowWelcome', 'true');
        });

        // Auto-show on the home page only, and only when not dismissed
        if (document.body.getAttribute('data-welcome-autoshow') === '1' &&
            localStorage.getItem('bibleAppDontShowWelcome') !== 'true') {
            setTimeout(function () { showWelcome(); }, 250);
        }
    }

    /* ---------- Preferred Bible version ---------- */
    function getPreferredVersion(fallback) {
        const pref = localStorage.getItem('biblePreferredVersion');
        return pref || (fallback || 'en-kjv');
    }

    /* ---------- Shared reading-time tracker (books reader + profile) ----------
       Stores per-day {chapters, minutes} in localStorage under 'bibleDailyActivity'.
       The day key is the local date, so the counters reset automatically at
       midnight. Time accrues while the tab is open and visible; it pauses when
       the user leaves and continues on the next visit the same day. */
    var READING_DAILY_KEY = 'bibleDailyActivity';
    var READING_SYNC_KEY = 'bibleDailySync';
    var READING_DEVICE_KEY = 'bibleDeviceId';
    var readingTrackerStarted = false;
    var readingLastFlush = Date.now();
    var readingTickCallbacks = [];

    // Local calendar date key (NOT UTC). toISOString shifts the day by the
    // timezone offset, which mislabeled today's minutes as yesterday's near
    // midnight. Local keys keep every device's day boundary aligned.
    function readingLocalDateKey(d) {
        return d.getFullYear() + '-' +
            String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }

    function readingTodayKey() { return readingLocalDateKey(new Date()); }

    function readingDeviceId() {
        try {
            var id = localStorage.getItem(READING_DEVICE_KEY);
            if (!id) {
                id = 'dev-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
                localStorage.setItem(READING_DEVICE_KEY, id);
            }
            return id;
        } catch (e) { return 'dev-unknown'; }
    }

    // {date, posted, serverTotal}: `posted` is the device's own tracked
    // minutes most recently sent to the server; `serverTotal` is the
    // effective cross-device total the server last reported for this day.
    // Displayed minutes = serverTotal - posted + localOwn, so every device
    // shows the same day total plus whatever THIS device tracked since.
    function readingSyncState() {
        try {
            var s = JSON.parse(localStorage.getItem(READING_SYNC_KEY) || 'null');
            if (s && s.date === readingTodayKey()) return s;
        } catch (e) { /* ignore */ }
        return { date: readingTodayKey(), posted: 0, serverTotal: 0 };
    }

    function readingSaveSyncState(st) {
        try { localStorage.setItem(READING_SYNC_KEY, JSON.stringify(st)); } catch (e) { /* ignore */ }
    }

    function readingDailyLoad() {
        try { return JSON.parse(localStorage.getItem(READING_DAILY_KEY) || '{}'); } catch (e) { return {}; }
    }

    function readingDailySave(d) {
        try {
            var cutoff = readingLocalDateKey(new Date(Date.now() - 60 * 24 * 3600 * 1000));
            Object.keys(d).forEach(function (k) { if (k < cutoff) delete d[k]; });
            localStorage.setItem(READING_DAILY_KEY, JSON.stringify(d));
        } catch (e) { /* storage full or blocked */ }
    }

    function readingTodayEntry(d) {
        var k = readingTodayKey();
        if (!d[k]) d[k] = { chapters: 0, minutes: 0 };
        return { key: k, entry: d[k] };
    }

    function readingGetToday() {
        var d = readingDailyLoad();
        var k = readingTodayKey();
        var e = d[k] || { chapters: 0, minutes: 0 };
        var own = e.minutes || 0;
        var st = readingSyncState();
        var display = Math.max(0, (st.serverTotal || 0) - (st.posted || 0) + own);
        return { date: k, chapters: e.chapters || 0, minutes: Math.round(display * 10) / 10, ownMinutes: own };
    }

    function readingFlushTime() {
        try {
            var elapsed = (Date.now() - readingLastFlush) / 60000;
            readingLastFlush = Date.now();
            if (elapsed < 0.03) return;
            var d = readingDailyLoad();
            var today = readingTodayEntry(d);
            today.entry.minutes = Math.round(((today.entry.minutes || 0) + elapsed) * 10) / 10;
            readingDailySave(d);
            readingNotify(readingGetToday());
        } catch (e) { /* ignore */ }
    }

    function readingNotify(today) {
        readingTickCallbacks.forEach(function (cb) {
            try { cb(today); } catch (e) { /* listener error */ }
        });
    }

    function startReadingTracker(opts) {
        if (readingTrackerStarted) return;
        readingTrackerStarted = true;
        opts = opts || {};
        readingLastFlush = Date.now();
        setInterval(function () { if (!document.hidden) readingFlushTime(); }, opts.intervalMs || 30000);
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) readingFlushTime();
            else readingLastFlush = Date.now();
        });
        window.addEventListener('beforeunload', readingFlushTime);
    }

    function trackChapterRead(slug, chapter) {
        if (!slug || !chapter) return;
        try {
            var now = new Date();
            var lastKey = localStorage.getItem('bibleLastChapterKey');
            var lastTime = parseInt(localStorage.getItem('bibleLastChapterTime') || '0', 10);
            var thisKey = slug + '_' + chapter;
            var isSame = (lastKey === thisKey) && (now.getTime() - lastTime) < 5 * 60 * 1000;
            if (isSame) return;
            var d = readingDailyLoad();
            var today = readingTodayEntry(d);
            today.entry.chapters = (today.entry.chapters || 0) + 1;
            readingDailySave(d);
            localStorage.setItem('bibleLastChapterKey', thisKey);
            localStorage.setItem('bibleLastChapterTime', String(now.getTime()));
            readingNotify(readingGetToday());
        } catch (e) { /* ignore */ }
    }

    function onReadingActivity(cb) {
        if (typeof cb === 'function') readingTickCallbacks.push(cb);
    }

    // This device's own tracked minutes for today, contributed under its
    // stable device id: {date: {deviceId: ownMinutes}}. The server keeps the
    // latest value per device (re-sends are harmless) and SUMS across
    // devices, so time read on the computer and the phone adds up instead
    // of one overwriting the other.
    function readingBuildDailyPayload() {
        var today = readingGetToday();
        var own = today.ownMinutes;
        var contrib = {};
        if (own > 0) {
            var devMap = {};
            devMap[readingDeviceId()] = Math.round(own * 10) / 10;
            contrib[today.date] = devMap;
        }
        var todayOnly = {};
        todayOnly[today.date] = { chapters: today.chapters, minutes: own };
        return { dailyActivity: todayOnly, dailyActivityContrib: contrib };
    }

    // Record that the server accepted this device's contribution, and cache
    // the server's effective total so the display matches across devices.
    function readingMarkPosted() {
        var st = readingSyncState();
        st.posted = readingGetToday().ownMinutes;
        readingSaveSyncState(st);
    }

    function readingApplyServerDaily(serverDaily) {
        try {
            if (!serverDaily) return;
            var todayKey = readingTodayKey();
            var serverToday = serverDaily[todayKey] || { chapters: 0, minutes: 0 };
            var d = readingDailyLoad();
            var localToday = d[todayKey] || { chapters: 0, minutes: 0 };
            d[todayKey] = {
                chapters: Math.max(localToday.chapters || 0, serverToday.chapters || 0),
                minutes: localToday.minutes || 0
            };
            readingDailySave(d);
            var st = readingSyncState();
            st.serverTotal = serverToday.minutes || 0;
            readingSaveSyncState(st);
            readingNotify(readingGetToday());
        } catch (e) { /* ignore */ }
    }

    /* ---------- Expose API ---------- */


    window.MPB = {
        showToast: showToast,
        fetchUser: fetchUser,
        fetchSyncData: fetchSyncData,
        syncNow: syncNow,
        generateVerseCard: generateVerseCard,
        verseCardTemplates: VERSE_CARD_TEMPLATES.map(function (t) { return { id: t.id, name: t.name }; }),
        shareVerse: shareVerse,
        parseReference: parseReference,
        jumpToReference: jumpToReference,
        getPreferredVersion: getPreferredVersion,
        pushToggle: pushToggle,
        pushStatus: pushStatus,
        startReadingTracker: startReadingTracker,
        trackChapterRead: trackChapterRead,
        getTodayActivity: readingGetToday,
        onReadingActivity: onReadingActivity,
        pushDailyActivity: pushDailyActivity,
        getLocalDateKey: readingTodayKey,
        getDailySyncPayload: readingBuildDailyPayload,
        applyServerDailyActivity: readingApplyServerDaily,
        markDailyPosted: readingMarkPosted
    };

    /* ---------- Boot ---------- */
    initTheme();
    registerServiceWorker();
    initScrollReveal();
    initWelcomeModal();
    document.querySelectorAll('[data-push-reminders]').forEach(function (btn) {
        btn.addEventListener('click', function (e) { e.preventDefault(); pushToggle(); });
    });
    refreshPushUI();
    autoRestoreSync();
    if (window.MPB_BOOK_SLUGS === undefined) {
        // Default list of book slugs (used by parseReference)
        window.MPB_BOOK_SLUGS = [
            'genesis','exodus','leviticus','numbers','deuteronomy','joshua','judges','ruth','1-samuel','2-samuel',
            '1-kings','2-kings','1-chronicles','2-chronicles','ezra','nehemiah','esther','job','psalms','proverbs',
            'ecclesiastes','song-of-solomon','isaiah','jeremiah','lamentations','ezekiel','daniel','hosea','joel','amos',
            'obadiah','jonah','micah','nahum','habakkuk','zephaniah','haggai','zechariah','malachi','matthew','mark',
            'luke','john','acts','romans','1-corinthians','2-corinthians','galatians','ephesians','philippians',
            'colossians','1-thessalonians','2-thessalonians','1-timothy','2-timothy','titus','philemon','hebrews',
            'james','1-peter','2-peter','1-john','2-john','3-john','jude','revelation'
        ];
    }
})();
