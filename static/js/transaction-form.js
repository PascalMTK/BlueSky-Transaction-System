/* Shared logic for the transaction amount/fee/total block — used by
   agent/transactions/create.html and agent/transactions/edit.html.
   Le Montant remis au client est toujours calculé automatiquement
   (Montant donné par le client − Frais de l'agence) — jamais saisi à la
   main. Each page sets window.FEE_TOTAL_ERROR_MSG before loading this
   script (translated string). */

function calcTotal() {
    const amt      = parseFloat(document.getElementById('amountInput').value) || 0;
    const fee      = parseFloat(document.getElementById('feeInput').value) || 0;
    const cur      = (document.getElementById('currencyInput').value || '').toUpperCase();
    const total    = Math.round((amt - fee) * 100) / 100;
    const panel    = document.getElementById('totalPanel');
    const errorBox = document.getElementById('totalError');

    const invalid = amt > 0 && (fee < 0 || fee > amt);
    panel.classList.toggle('tx-total-invalid', invalid);
    if (invalid) {
        errorBox.style.display = 'block';
        errorBox.textContent = window.FEE_TOTAL_ERROR_MSG || '';
    } else {
        errorBox.style.display = 'none';
    }

    document.getElementById('totalDisplay').textContent  = amt > 0 ? total.toLocaleString('fr-FR') : '—';
    document.getElementById('totalCurLabel').textContent = cur;
    document.getElementById('feeCurIcon').textContent    = cur || '$';

    if (amt > 0) {
        document.getElementById('calcBar').style.display = 'flex';
        document.getElementById('calcAmt').textContent    = amt.toLocaleString('fr-FR');
        document.getElementById('calcFee').textContent    = fee.toLocaleString('fr-FR');
        document.getElementById('calcTotal2').textContent = total.toLocaleString('fr-FR');
        ['calcCur1', 'calcCur2', 'calcCur3'].forEach(function (id) { document.getElementById(id).textContent = cur; });
    } else {
        document.getElementById('calcBar').style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('txForm');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        const amt = parseFloat(document.getElementById('amountInput').value) || 0;
        const fee = parseFloat(document.getElementById('feeInput').value) || 0;
        if (amt > 0 && (fee < 0 || fee > amt)) {
            e.preventDefault();
            calcTotal();
            document.getElementById('feeInput').focus();
        }
    });
});
