/* Shared logic for the transaction amount/fee/total block — used by
   agent/transactions/create.html and agent/transactions/edit.html.
   Le Montant remis au client est calculé automatiquement (Montant donné
   par le client − Frais de l'agence) mais reste éditable : si l'agent le
   modifie directement, c'est le Frais qui se recalcule à l'inverse.
   Each page sets window.FEE_TOTAL_ERROR_MSG before loading this script
   (translated string). */

var totalIsSource = false;
function onFeeInput() {
    totalIsSource = false;
    document.getElementById('feeInput').dataset.userEdited = '1';
    calcTotal();
}
function onTotalInput() {
    totalIsSource = true;
    calcTotal();
}

function calcTotal() {
    const amt        = parseFloat(document.getElementById('amountInput').value) || 0;
    const feeInput   = document.getElementById('feeInput');
    const totalInput = document.getElementById('totalInput');
    const cur        = (document.getElementById('currencyInput').value || '').toUpperCase();
    const panel      = document.getElementById('totalPanel');
    const errorBox   = document.getElementById('totalError');

    let fee, total;
    if (totalIsSource) {
        total = parseFloat(totalInput.value) || 0;
        fee   = Math.round((amt - total) * 100) / 100;
        feeInput.value = fee;
    } else {
        fee   = parseFloat(feeInput.value) || 0;
        total = Math.round((amt - fee) * 100) / 100;
        totalInput.value = amt > 0 ? total : '';
    }

    const invalid = amt > 0 && (fee < 0 || total < 0);
    panel.classList.toggle('tx-total-invalid', invalid);
    if (invalid) {
        errorBox.style.display = 'block';
        errorBox.textContent = window.FEE_TOTAL_ERROR_MSG || '';
    } else {
        errorBox.style.display = 'none';
    }

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

/* La devise doit être choisie dans la liste (datalist) — on bloque la
   saisie de chiffres pour éviter qu'un montant soit tapé par erreur
   dans ce champ. */
document.addEventListener('DOMContentLoaded', function () {
    const currencyInput = document.getElementById('currencyInput');
    if (currencyInput) {
        currencyInput.addEventListener('keypress', function (e) {
            if (/[0-9]/.test(e.key)) e.preventDefault();
        });
        currencyInput.addEventListener('input', function () {
            const stripped = this.value.replace(/[0-9]/g, '');
            if (stripped !== this.value) this.value = stripped;
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('txForm');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        const amt   = parseFloat(document.getElementById('amountInput').value) || 0;
        const fee   = parseFloat(document.getElementById('feeInput').value) || 0;
        const total = parseFloat(document.getElementById('totalInput').value) || 0;
        if (amt > 0 && (fee < 0 || total < 0)) {
            e.preventDefault();
            calcTotal();
            document.getElementById('totalInput').focus();
        }
    });
});
