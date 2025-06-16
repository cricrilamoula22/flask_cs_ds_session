$(document).ready(function () {
    const filterForm = $('#filter-form');
    const deptSelect = $('#departement');
    const communeSelect = $('#commune');
    const sectionSelect = $('#section');

    // Filtres
    deptSelect.change(function () {
        const deptCode = $(this).val();
        communeSelect.empty().append('<option value="">En cours de chargement...</option>');
        sectionSelect.empty().append('<option value="">Sélectionner une section</option>');

        $.getJSON('/get_communes_options', { departement: deptCode })
            .done(function (data) {
                communeSelect.empty().append('<option value="">Sélectionner une commune</option>');
                data.forEach(c => {
                    communeSelect.append($('<option>', { value: c.value, text: c.text }));
                });
                filterForm.submit();
            })
            .fail(() => {
                communeSelect.empty().append('<option value="">En cours de chargement</option>');
                filterForm.submit();
            });
    });

    communeSelect.change(function () {
        const communeINSEE = $(this).val();
        sectionSelect.empty().append('<option value="">En cours de chargement...</option>');

        if (communeINSEE) {
            $.getJSON('/get_sections_options', { commune_insee: communeINSEE })
                .done(function (data) {
                    sectionSelect.empty().append('<option value="">Sélectionner une section</option>');
                    data.forEach(s => {
                        sectionSelect.append($('<option>', { value: s.value, text: s.text }));
                    });
                    filterForm.submit();
                })
                .fail(() => {
                    sectionSelect.empty().append('<option value="">En cours de chargement</option>');
                    filterForm.submit();
                });
        } else {
            sectionSelect.empty().append('<option value="">Sélectionner une section</option>');
            filterForm.submit();
        }
    });

    sectionSelect.change(() => filterForm.submit());

    // Cocher/Décocher une parcelle
    $('#parcelles-list-group').on('change', '.parcelle-checkbox', function () {
        const idsuf = $(this).data('idsuf');
        const checked = $(this).is(':checked');

        $.post('/selection/parcelle/toggle', { idsuf: idsuf, checked: checked })
            .done(response => {
    if (response.status === 'ok') {
        location.reload();
    } else {
        showToast('Erreur: ' + response.message, 'danger');
    }
})
    });

// Vider la sélection
$('#clear-selection-form').on('submit', function (e) {
    e.preventDefault();

    // Sélection des éléments du modal
    const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    const modalBody = $('#confirmationModal .modal-body');
    const confirmBtn = $('#confirmActionBtn');

    // Définir le texte de la question
    modalBody.text("Voulez-vous vraiment vider toutes les parcelles sélectionnées ?");

    // L'astuce est ici : on attache l'événement 'click' UNE SEULE FOIS.
    // .one() garantit que le code ne s'exécutera qu'une fois, évitant les actions multiples.
    confirmBtn.one('click', function() {
        // C'est le code qui était après le 'confirm()'
        $.post('/selection/parcelle/clear')
            .done(() => location.reload())
            .fail(() => showToast('Erreur de communication avec le serveur.', 'danger'));
        
        // On cache le modal après avoir cliqué
        confirmationModal.hide();
    });

    // Afficher le modal
    confirmationModal.show();
});

    // Ajout manuel : chargement communes
    const addDeptSelect = $('#add_departement');
    const addCommuneSelect = $('#add_commune');

    addDeptSelect.change(function () {
        const deptCode = $(this).val();
        addCommuneSelect.empty().append('<option value="">Chargement...</option>');

        if (deptCode) {
            $.getJSON('/get_communes_options', { departement: deptCode })
                .done(data => {
                    addCommuneSelect.empty().append('<option value="">Sélectionner une commune</option>');
                    data.forEach(c => {
                        addCommuneSelect.append($('<option>', { value: c.value, text: c.text }));
                    });
                })
                .fail(() => {
                    addCommuneSelect.empty().append('<option value="">En cours de chargement</option>');
                });
        } else {
            addCommuneSelect.empty().append('<option value="">Sélectionner d\'abord un département</option>');
        }
    });

    // Recalcul des sous-totaux et du total
    function recalculerTotaux() {
        const sousTotaux = {};
        let total = 0;

        $('.surface-input').each(function () {
            const $input = $(this);
            const surface = parseInt($input.val()) || 0;
            const codeInsee = $input.data('code-insee');

            if (!sousTotaux[codeInsee]) sousTotaux[codeInsee] = 0;
            sousTotaux[codeInsee] += surface;
            total += surface;
        });

        // Mettre à jour les sous-totaux
// ---- CORRECTION ----

// Mettre à jour les sous-totaux
$('#sous-totaux-list .list-group-item').each(function () {
    const $item = $(this);
    const code = $item.data('code-insee');
    const val = sousTotaux[code] || 0;

    // LIGNE DE DEBUG À AJOUTER :
    console.log('Mise à jour sous-total pour commune ' + code + '. Valeur:', val, 'Type:', typeof val);

    $item.find('.subtotal-value').text(val);
});

// Total général
$('#total-selection').text(total);
    }

    // Lors de la saisie : recalcul + validation
    $(document).on('input', '.surface-input', function () {
        const $input = $(this);
        //const val = parseFloat($input.val());
        //const max = parseFloat($input.data('surface-cadastre'));
		const val = parseInt($input.val(), 10);
		const max = parseInt($input.data('surface-cadastre'), 10);

        //if (val > max) {
            //alert("La surface demandée ne peut pas dépasser la surface cadastrale (" + max + " m²).");
            //$input.val(max);
        //}
		if (val > max) {
			showToast("La surface demandée ne peut excéder la surface cadastrale (" + max + " m²).", 'warning');
			$input.val(max);
		}

        recalculerTotaux();
    });

    // Lors de la modification finale (blur ou Enter)
    $(document).on('change', '.surface-input', function () {
        const $input = $(this);
        //const surface = $input.val();
		const surface = parseInt($input.val(), 10) || 0;
        const idsuf = $input.data('idsuf');

        if (!idsuf || !surface) return;

        $.post('/selection/parcelle/update_surface', {
            idsuf: idsuf,
            surface_demandee: surface
        }).done(function (response) {
            if (response.status !== 'ok') {
                alert('Erreur : ' + response.message);
            }
        }).fail(function () {
            alert('Erreur de communication avec le serveur.');
        });
    });
});

/**
 * Affiche un toast Bootstrap.
 * @param {string} message Le message à afficher.
 * @param {string} type Le type de toast ('success', 'danger', 'warning', 'info'). Par défaut 'info'.
 */
function showToast(message, type = 'info') {
    const toastContainer = $('.toast-container');
    if (!toastContainer.length) return; // Ne fait rien si le conteneur n'existe pas

    // Détermine la couleur de fond en fonction du type
    let bgColor = 'bg-primary';
    if (type === 'success') bgColor = 'bg-success';
    else if (type === 'danger') bgColor = 'bg-danger';
    else if (type === 'warning') bgColor = 'bg-warning';

    const toastId = 'toast-' + Date.now();

    // Crée le HTML du toast dynamiquement
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgColor} text-white">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Fermer"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.append(toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: 5000 // Le toast disparaît après 5 secondes
    });
    
    // Supprime l'élément du DOM après sa disparition pour ne pas surcharger la page
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });

    toast.show();
}
