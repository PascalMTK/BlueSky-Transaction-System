document.addEventListener('DOMContentLoaded', function () {
    var csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    document.querySelectorAll('.inline-edit-select').forEach(function (select) {
        var previousValue = select.value;

        select.addEventListener('change', function () {
            var deliveryId = select.dataset.deliveryId;
            var field = select.dataset.field;
            var value = select.value;
            var endpoint = select.dataset.endpoint || ('/admin/logistics/deliveries/' + deliveryId + '/update/');

            select.disabled = true;
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'field=' + encodeURIComponent(field) + '&value=' + encodeURIComponent(value),
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                select.disabled = false;
                if (data.ok) {
                    previousValue = value;
                } else {
                    select.value = previousValue;
                    alert(data.error || 'Erreur lors de la mise à jour.');
                }
            })
            .catch(function () {
                select.disabled = false;
                select.value = previousValue;
                alert('Erreur réseau lors de la mise à jour.');
            });
        });
    });
});
