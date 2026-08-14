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
                navigator.serviceWorker.register('/static/sw.js').catch(function (err) {
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
        return {
            bookmarks: JSON.parse(localStorage.getItem('bibleBookmarks') || '[]'),
            highlights: JSON.parse(localStorage.getItem('bibleHighlights') || '{}'),
            highlightColors: JSON.parse(localStorage.getItem('bibleHighlightColors') || '{}'),
            notes: JSON.parse(localStorage.getItem('bibleNotes') || '[]'),
            prayers: JSON.parse(localStorage.getItem('biblePrayers') || '[]'),
            plans: JSON.parse(localStorage.getItem('biblePlans') || '{}'),
            quizStats: JSON.parse(localStorage.getItem('bibleQuizStats') || 'null'),
            readingLog: JSON.parse(localStorage.getItem('bibleReadingLog') || '[]'),
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
            const response = await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(localData())
            });
            if (response.ok) {
                const serverData = await fetchSyncData();
                if (serverData) {
                    if (serverData.bookmarks) localStorage.setItem('bibleBookmarks', JSON.stringify(serverData.bookmarks));
                    if (serverData.highlights) localStorage.setItem('bibleHighlights', JSON.stringify(serverData.highlights));
                    if (serverData.highlightColors) localStorage.setItem('bibleHighlightColors', JSON.stringify(serverData.highlightColors));
                    if (serverData.notes) localStorage.setItem('bibleNotes', JSON.stringify(serverData.notes));
                    if (serverData.prayers) localStorage.setItem('biblePrayers', JSON.stringify(serverData.prayers));
                    if (serverData.plans) localStorage.setItem('biblePlans', JSON.stringify(serverData.plans));
                    if (serverData.quizStats) localStorage.setItem('bibleQuizStats', JSON.stringify(serverData.quizStats));
                    if (serverData.readingLog) localStorage.setItem('bibleReadingLog', JSON.stringify(serverData.readingLog));
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

    /* ---------- Verse share card (canvas -> PNG) ---------- */
    function generateVerseCard(reference, text, options) {
        options = options || {};
        const width = 1080;
        const height = 1350;
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');

        // Background
        const bg = ctx.createLinearGradient(0, 0, width, height);
        const dark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (dark) {
            bg.addColorStop(0, '#1a0f00');
            bg.addColorStop(1, '#3d2205');
        } else {
            bg.addColorStop(0, '#3d2205');
            bg.addColorStop(1, '#7a4b10');
        }
        ctx.fillStyle = bg;
        ctx.fillRect(0, 0, width, height);

        // Decorative circles
        ctx.globalAlpha = 0.15;
        ctx.fillStyle = '#e8b86a';
        ctx.beginPath(); ctx.arc(width - 80, 90, 160, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(70, height - 100, 130, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 1;

        // Top label
        ctx.fillStyle = '#e8b86a';
        ctx.font = '600 44px Georgia, serif';
        ctx.textAlign = 'center';
        ctx.fillText('MyPersonal Bible', width / 2, 130);

        // Divider
        ctx.strokeStyle = 'rgba(232,184,106,0.6)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(width / 2 - 60, 170);
        ctx.lineTo(width / 2 + 60, 170);
        ctx.stroke();

        // Verse text (wrapped)
        ctx.fillStyle = '#faf6ee';
        ctx.font = 'italic 52px Georgia, serif';
        ctx.textAlign = 'center';
        const words = text.split(' ');
        const maxWidth = width - 160;
        const lines = [];
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

        let y = 420;
        const lineHeight = 84;
        lines.slice(0, 9).forEach(function (l) {
            ctx.fillText(l, width / 2, y);
            y += lineHeight;
        });

        // Reference
        ctx.fillStyle = '#e8b86a';
        ctx.font = '600 58px Georgia, serif';
        ctx.fillText('— ' + reference + ' —', width / 2, height - 180);

        // Footer
        ctx.fillStyle = 'rgba(250,246,238,0.8)';
        ctx.font = '36px Georgia, serif';
        ctx.fillText('mypersonal-bible-app.onrender.com', width / 2, height - 90);

        return canvas;
    }

    function shareVerse(reference, text, verseTextEl) {
        const canvas = generateVerseCard(reference, text);
        canvas.toBlob(function (blob) {
            const url = URL.createObjectURL(blob);
            const encRef = encodeURIComponent(reference);
            const encText = encodeURIComponent(reference + ' - "' + text + '"');
            const pageUrl = encodeURIComponent(window.location.origin);

            const shareHtml =
                '<div class="text-center mb-3">' +
                '  <img src="' + url + '" alt="Verse card" style="max-width:100%;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,0.25);">' +
                '</div>' +
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
            modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:3000;display:flex;align-items:center;justify-content:center;padding:16px;';
            modal.innerHTML =
                '<div style="background:var(--card-bg);border-radius:16px;max-width:520px;width:100%;padding:20px;position:relative;">' +
                '  <button id="shareCloseBtn" style="position:absolute;top:12px;right:12px;background:none;border:none;font-size:1.4rem;color:var(--text-muted);cursor:pointer;">&times;</button>' +
                '  <h5 class="text-center mb-3" style="color:var(--text-primary);">Share This Verse</h5>' +
                shareHtml +
                '</div>';
            document.body.appendChild(modal);
            modal.addEventListener('click', function (e) { if (e.target === modal) modal.remove(); });
            modal.querySelector('#shareCloseBtn').addEventListener('click', function () { modal.remove(); });
            modal.querySelector('#shareDownloadBtn').addEventListener('click', function () {
                const a = document.createElement('a');
                a.href = url;
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
        }, 'image/png');
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

    /* ---------- Expose API ---------- */
    window.MPB = {
        showToast: showToast,
        fetchUser: fetchUser,
        fetchSyncData: fetchSyncData,
        syncNow: syncNow,
        generateVerseCard: generateVerseCard,
        shareVerse: shareVerse,
        parseReference: parseReference,
        jumpToReference: jumpToReference
    };

    /* ---------- Boot ---------- */
    initTheme();
    registerServiceWorker();
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
