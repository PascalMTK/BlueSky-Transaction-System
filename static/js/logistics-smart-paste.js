document.addEventListener('DOMContentLoaded', function () {
    var parseBtn = document.getElementById('spParseBtn');
    if (!parseBtn) return;

    var csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    function applyConfidence(el, level) {
        el.classList.toggle('confidence-low', level === 'low');
    }

    parseBtn.addEventListener('click', function () {
        var text = document.getElementById('spInput').value;
        if (!text.trim()) return;

        parseBtn.disabled = true;
        fetch('/admin/logistics/smart-paste/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'text=' + encodeURIComponent(text),
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            parseBtn.disabled = false;
            if (!data.ok) {
                alert(data.error || 'Erreur lors de l\'analyse.');
                return;
            }
            var fields = data.fields || {};
            var confidence = data.confidence || {};

            var nameEl = document.getElementById('spName');
            var phoneEl = document.getElementById('spPhone');
            var emailEl = document.getElementById('spEmail');
            var addressEl = document.getElementById('spAddress');
            var notesEl = document.getElementById('spNotes');

            nameEl.value = fields.name || '';
            phoneEl.value = fields.phone || '';
            emailEl.value = fields.email || '';
            addressEl.value = fields.address || '';
            notesEl.value = fields.notes || '';

            applyConfidence(nameEl, confidence.name);
            applyConfidence(phoneEl, confidence.phone);
            applyConfidence(addressEl, confidence.address);
        })
        .catch(function () {
            parseBtn.disabled = false;
            alert('Erreur réseau lors de l\'analyse.');
        });
    });
});
