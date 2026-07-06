/* Shared circular pan/zoom photo cropper — used by profile, register and
   admin agent-photo uploads so the user picks exactly which part of a photo
   stays visible, instead of a silent center-crop. No external JS library. */
(function () {
    var OUTPUT_SIZE = 480;
    var state = null;

    function buildModal() {
        if (document.getElementById('pcropOverlay')) return;
        var el = document.createElement('div');
        el.id = 'pcropOverlay';
        el.className = 'pcrop-overlay';
        el.innerHTML =
            '<div class="pcrop-box">' +
                '<div class="pcrop-title">Ajuster la photo</div>' +
                '<div class="pcrop-viewport" id="pcropViewport">' +
                    '<img id="pcropImg" draggable="false" alt="">' +
                '</div>' +
                '<div class="pcrop-zoom-row">' +
                    '<span class="pcrop-zoom-ico">−</span>' +
                    '<input type="range" id="pcropZoom" min="1" max="3" step="0.01" value="1">' +
                    '<span class="pcrop-zoom-ico">+</span>' +
                '</div>' +
                '<div class="pcrop-hint">Glissez pour repositionner &middot; curseur pour zoomer</div>' +
                '<div class="pcrop-actions">' +
                    '<button type="button" class="btn btn-secondary" id="pcropCancel">✕ Annuler</button>' +
                    '<button type="button" class="btn btn-primary" id="pcropConfirm">✓ Valider</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(el);
    }

    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

    function applyTransform() {
        var img = document.getElementById('pcropImg');
        img.style.width  = (state.nw * state.scale) + 'px';
        img.style.height = (state.nh * state.scale) + 'px';
        img.style.left   = state.offX + 'px';
        img.style.top    = state.offY + 'px';
    }

    function clampOffsets() {
        var dispW = state.nw * state.scale, dispH = state.nh * state.scale;
        state.offX = clamp(state.offX, state.vp - dispW, 0);
        state.offY = clamp(state.offY, state.vp - dispH, 0);
    }

    function pointerXY(e) {
        var t = e.touches && e.touches[0] ? e.touches[0] : e;
        return { x: t.clientX, y: t.clientY };
    }

    function onPointerDown(e) {
        if (!state) return;
        state.dragging = true;
        var p = pointerXY(e);
        state.startX = p.x - state.offX;
        state.startY = p.y - state.offY;
    }
    function onPointerMove(e) {
        if (!state || !state.dragging) return;
        e.preventDefault();
        var p = pointerXY(e);
        state.offX = p.x - state.startX;
        state.offY = p.y - state.startY;
        clampOffsets();
        applyTransform();
    }
    function onPointerUp() { if (state) state.dragging = false; }

    function onZoom(e) {
        if (!state) return;
        var factor = parseFloat(e.target.value);
        var oldScale = state.scale;
        var newScale = state.baseScale * factor;
        var cx = state.vp / 2, cy = state.vp / 2;
        var relX = (cx - state.offX) / oldScale;
        var relY = (cy - state.offY) / oldScale;
        state.scale = newScale;
        state.offX = cx - relX * newScale;
        state.offY = cy - relY * newScale;
        clampOffsets();
        applyTransform();
    }

    function cleanup() {
        var zoom = document.getElementById('pcropZoom');
        var vp   = document.getElementById('pcropViewport');
        document.getElementById('pcropOverlay').classList.remove('open');
        zoom.removeEventListener('input', onZoom);
        vp.removeEventListener('pointerdown', onPointerDown);
        vp.removeEventListener('touchstart', onPointerDown);
        window.removeEventListener('pointermove', onPointerMove);
        window.removeEventListener('touchmove', onPointerMove);
        window.removeEventListener('pointerup', onPointerUp);
        window.removeEventListener('touchend', onPointerUp);
        if (state && state.objectUrl) URL.revokeObjectURL(state.objectUrl);
        state = null;
    }

    function openWithFile(file, onConfirm, onCancel) {
        if (file.type === 'image/gif') {
            if (onCancel) onCancel();
            return;
        }
        buildModal();
        var overlay  = document.getElementById('pcropOverlay');
        var img      = document.getElementById('pcropImg');
        var viewport = document.getElementById('pcropViewport');
        var zoom     = document.getElementById('pcropZoom');
        var objectUrl = URL.createObjectURL(file);

        img.onload = function () {
            // Make the viewport visible *before* measuring it — clientWidth
            // reads 0 while the overlay is still display:none, which zeroed
            // out the scale and left only the dark placeholder background.
            overlay.classList.add('open');
            var vp = viewport.clientWidth;
            var baseScale = vp / Math.min(img.naturalWidth, img.naturalHeight);
            state = {
                nw: img.naturalWidth, nh: img.naturalHeight,
                vp: vp, baseScale: baseScale, scale: baseScale,
                offX: (vp - img.naturalWidth * baseScale) / 2,
                offY: (vp - img.naturalHeight * baseScale) / 2,
                dragging: false, objectUrl: objectUrl
            };
            zoom.value = 1;
            applyTransform();
        };
        img.src = objectUrl;

        zoom.addEventListener('input', onZoom);
        viewport.addEventListener('pointerdown', onPointerDown);
        viewport.addEventListener('touchstart', onPointerDown, { passive: true });
        window.addEventListener('pointermove', onPointerMove);
        window.addEventListener('touchmove', onPointerMove, { passive: false });
        window.addEventListener('pointerup', onPointerUp);
        window.addEventListener('touchend', onPointerUp);

        document.getElementById('pcropCancel').onclick = function () {
            cleanup();
            if (onCancel) onCancel();
        };
        document.getElementById('pcropConfirm').onclick = function () {
            var canvas = document.createElement('canvas');
            canvas.width = OUTPUT_SIZE; canvas.height = OUTPUT_SIZE;
            var ctx = canvas.getContext('2d');
            var sx = (0 - state.offX) / state.scale;
            var sy = (0 - state.offY) / state.scale;
            var sSize = state.vp / state.scale;
            ctx.drawImage(img, sx, sy, sSize, sSize, 0, 0, OUTPUT_SIZE, OUTPUT_SIZE);
            var mime = file.type === 'image/png' ? 'image/png'
                     : file.type === 'image/webp' ? 'image/webp'
                     : 'image/jpeg';
            var ext = mime === 'image/png' ? '.png' : mime === 'image/webp' ? '.webp' : '.jpg';
            canvas.toBlob(function (blob) {
                var namePart = file.name.replace(/\.[^.]+$/, '');
                var croppedFile = new File([blob], namePart + ext, { type: mime });
                cleanup();
                onConfirm(croppedFile);
            }, mime, 0.9);
        };
    }

    window.BlueskyCrop = {
        /**
         * Opens the crop modal for `source` — either a File (e.g. from a file
         * input) or an image URL string (e.g. the user's already-uploaded
         * avatar, fetched and converted to a File so the same crop pipeline
         * applies). Calls onConfirm(croppedFile) once the user validates, or
         * onCancel() if they cancel. Animated GIFs are passed straight to
         * onCancel (signals "skip cropping") since rasterizing would flatten
         * the animation to a single frame.
         */
        open: function (source, onConfirm, onCancel) {
            if (!source) return;
            if (typeof source === 'string') {
                fetch(source, { credentials: 'same-origin' })
                    .then(function (r) { return r.blob(); })
                    .then(function (blob) {
                        var name = source.split('/').pop().split('?')[0] || 'photo.jpg';
                        openWithFile(new File([blob], name, { type: blob.type }), onConfirm, onCancel);
                    })
                    .catch(function () { if (onCancel) onCancel(); });
                return;
            }
            openWithFile(source, onConfirm, onCancel);
        }
    };
})();
