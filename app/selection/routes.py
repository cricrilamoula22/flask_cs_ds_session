#\my_app\app\selection\routes.py :

from flask import Blueprint, request, session, jsonify, render_template, send_file, flash, redirect, url_for
from app import db
# MODIFIÉ : Importer le nouveau formulaire
from app.selection.forms import FilterForm, AddParcelForm
from app.selection.models import TCommune, TCadastre, SelectionParcelle
from app.selection.services import (
    get_departement_choices,
    get_communes_for_departement,
    get_sections_for_commune,
    get_parcelles_by_filters,
    add_parcelle_to_selection,
    remove_parcelle_from_selection,
    get_selected_parcelle_objects,
    get_parcelle_subtotals,
    update_surface_demandee
)
from sqlalchemy import func
from io import BytesIO
import openpyxl

selection_bp = Blueprint('selection', __name__)

@selection_bp.route('/', methods=['GET', 'POST'])
def index():
    form = FilterForm(request.form)
    # NOUVEAU : Instancier le formulaire pour le popup
    add_form = AddParcelForm()
    
    session_id = session.get('session_id')

    # MODIFIÉ : Peupler les choix de départements pour les deux formulaires
    departement_choices = get_departement_choices()
    form.departement.choices = departement_choices
    add_form.departement.choices = departement_choices

    # --- Logique existante pour les filtres ---
    selected_dep = form.departement.data
    selected_com_insee = form.commune.data
    # 1. Récupérer la valeur brute du champ "section"
    #selected_sec = form.section.data
        
    # 2. Nettoyer la valeur en retirant l'apostrophe de début
    #selected_sec = selected_sec.lstrip("'")
    selected_sec = form.section.data
    #selected_sec = func.ltrim(form.section.data, "'")
    
    commune_choices = [('', 'Sélectionner une commune')]
    if selected_dep and selected_dep != '':
        commune_choices.extend(get_communes_for_departement(selected_dep))
    form.commune.choices = commune_choices
    
    section_choices = [('', 'Sélectionner une section')]
    if selected_com_insee and selected_com_insee != '':
        sections = get_sections_for_commune(selected_com_insee)
        section_choices.extend([(s, s) for s in sections])
    form.section.choices = section_choices

    # --- NOUVEAU : Logique de pré-remplissage du formulaire du popup ---
    # On peuple la liste des départements du popup (comme avant)
    add_form.departement.choices = departement_choices

    # Si un département est déjà sélectionné dans le filtre principal...
    if selected_dep:
        # 1. On le présélectionne dans le popup
        add_form.departement.data = selected_dep
        
        # 2. On charge la liste des communes correspondante pour le popup
        add_commune_choices = [('', 'Sélectionner une commune')] + get_communes_for_departement(selected_dep)
        add_form.commune.choices = add_commune_choices
        
        # 3. Si une commune est aussi sélectionnée, on la présélectionne dans le popup
        if selected_com_insee:
            add_form.commune.data = selected_com_insee
    # --- FIN DE LA NOUVELLE LOGIQUE ---
    
    parcelles_list = get_parcelles_by_filters(
        selected_dep if selected_dep != '' else None,
        selected_com_insee,
        selected_sec
    )
    current_parcelles_on_page = [p.idcom for p in parcelles_list]

    selected_parcelles_associations = []
    subtotals = {}
    total_selection = 0
    if session_id:
        """
        selected_parcelles_associations = get_selected_parcelle_objects(session_id)
        subtotals = get_parcelle_subtotals(session_id)
        total_selection = sum(val for val in subtotals.values() if val is not None) if subtotals else 0
        # Agrégation des surfaces par code INSEE de la commune
        sous_totaux = db.session.query(
            TCommune.com,
            func.sum(TCadastre.dcntsf).label('surface_totale')
        ).join(
            TCadastre, TCadastre.idcom == TCommune.com
        ).group_by(
            TCommune.com
        ).all()
        """
        selected_parcelles_associations = get_selected_parcelle_objects(session_id)
        #selected_parcelles_ids = [spa.idsuf for spa in selected_parcelles_associations]
        selected_parcelles_ids = [spa.TCadastre.idsuf for spa in selected_parcelles_associations]

        # Agrégation des surfaces demandées par commune, uniquement pour les parcelles sélectionnées
        sous_totaux = db.session.query(
            TCommune.com,
            TCommune.libelle,
            func.sum(TCadastre.dcntsf).label('surface_totale')
        ).join(
            TCadastre, TCadastre.idcom == TCommune.com
        ).filter(
            TCadastre.idsuf.in_(selected_parcelles_ids)
        ).group_by(
            TCommune.com,
            TCommune.libelle
        ).all()

        # Construction d'un dictionnaire pour un accès rapide aux sous-totaux par code INSEE
        #subtotals = {com: surface_totale for com, surface_totale in sous_totaux}
        subtotals = {(com, libelle): surface_totale for com, libelle, surface_totale in sous_totaux}
        total_selection = sum(subtotals.values())
        
    selected_parcelles_for_checkbox = [spa.TCadastre for spa in selected_parcelles_associations]

    # MODIFIÉ : Passer le formulaire d'ajout au template
    return render_template('selection.html',
        form=form,
        add_form=add_form,
        parcelles_list=parcelles_list,
        selected_parcelles_associations=selected_parcelles_associations,
        selected_parcelles_for_checkbox=selected_parcelles_for_checkbox,
        subtotals=subtotals,
        sous_totaux=sous_totaux,
        total_selection=total_selection,
        current_parcelles_ids_on_page=current_parcelles_on_page
    )

# NOUVEAU : Route pour gérer l'ajout manuel depuis le popup
@selection_bp.route('/selection/parcelle/add', methods=['POST'])
def add_manual_parcelle():
    form = AddParcelForm(request.form)
    session_id = session.get('session_id')

    form.departement.choices = get_departement_choices()
    if form.departement.data:
        form.commune.choices = [('', 'Sélectionner une commune')] + get_communes_for_departement(form.departement.data)

    if form.validate_on_submit():
        commune = form.commune.data
        prefixe = form.prefixe.data
        section = form.section.data.upper().zfill(2)
        numero = form.numero.data.zfill(4)
        subdivision = form.subdivision.data.upper()
        superficie = form.superficie.data
        idsuf = f"{commune}{prefixe}{section}{numero}{subdivision}"

        if len(idsuf) > 18:
            flash(f"L'identifiant construit ({idsuf}) est trop long (max 17 caractères). Veuillez raccourcir les champs saisis.", "danger")
            return redirect(url_for('selection.index'))

        # Check if the parcel already exists in t_cadastre
        parcelle_exists = db.session.query(TCadastre).filter_by(idsuf=idsuf).first()

        if not parcelle_exists:
            # Get the maximum idt_cadastre value from the database
            max_id = db.session.query(db.func.max(TCadastre.idt_cadastre)).scalar()
            if max_id is None:
                max_id = 0

            # Increment the maximum id by 1
            new_id = max_id + 1

            # Add an apostrophe to the ccosec value
            ccosec_with_apostrophe = f"'{section}"

            # Add to t_cadastre first with the manually set primary key and modified ccosec value
            nouvelle_parcelle = TCadastre(
                idt_cadastre=new_id,  # Manually set the primary key
                idsuf=idsuf,
                idpar=numero,
                idcom=commune,
                ccosec=ccosec_with_apostrophe,  # Use the modified ccosec value
                dnupla=numero,
                ccosub=subdivision if subdivision else None,
                dcntsf=superficie if superficie else 0  # default surface
            )
            db.session.add(nouvelle_parcelle)
            db.session.commit()
            flash(f"La parcelle {idsuf} a été ajoutée au cadastre et à la sélection.", "info")
        else:
            flash(f"La parcelle {idsuf} est déjà présente en base.", "success")

        # Then add to the selection
        add_parcelle_to_selection(session_id, idsuf)

        return redirect(url_for('selection.index'))

    # Handle form errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Erreur dans le champ '{getattr(form, field).label.text}': {error}", "danger")
    return redirect(url_for('selection.index'))


# NOUVEAU : Endpoint JSON pour remplir dynamiquement les communes dans le popup
@selection_bp.route('/get_communes_options')
def get_communes_options():
    dep_code = request.args.get('departement')
    if not dep_code:
        return jsonify([])
    communes = get_communes_for_departement(dep_code)
    # Formatte la liste pour qu'elle soit exploitable en JSON
    communes_dict = [{'value': v, 'text': t} for v, t in communes]
    return jsonify(communes_dict)


# ... (le reste de vos routes : toggle_parcelle_selection, export_parcelles_excel, clear_selection) ...

@selection_bp.route('/selection/parcelle/toggle', methods=['POST'])
def toggle_parcelle_selection():
    idsuf = request.form.get('idsuf')
    checked = request.form.get('checked') == 'true'
    session_id = session.get('session_id')

    if not session_id or not idsuf:
        return jsonify({'status': 'error', 'message': 'Session ou IDSuf manquant'}), 400

    if checked:
        # Ajoute la parcelle à la sélection, surface_demandee par défaut à la surface cadastrale
        add_parcelle_to_selection(session_id, idsuf)
    else:
        # Retire la parcelle de la sélection
        remove_parcelle_from_selection(session_id, idsuf)

    return jsonify({'status': 'ok'})



@selection_bp.route('/selection/parcelle/export')
def export_parcelles_excel():
    session_id = session.get('session_id')
    if not session_id:
        return "Aucune session active.", 403

    # Jointure directe : SelectionParcelle → TCadastre → TCommune
    rows = (
        db.session.query(
            SelectionParcelle.idsuf,
            TCadastre.ccosec,
            TCommune.libelle,
            TCommune.com,
            TCommune.dep,
            SelectionParcelle.surface_demandee  # Ajout de la surface demandée
        )
        .join(TCadastre, SelectionParcelle.idsuf == TCadastre.idsuf)
        .join(TCommune, TCadastre.idcom == TCommune.com)
        .filter(SelectionParcelle.session_id == session_id)
        .order_by(TCommune.dep, TCommune.libelle, TCadastre.ccosec, SelectionParcelle.idsuf)
        .all()
    )

    # Création du fichier Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Parcelles Sélectionnées"

    headers = ["IDSuf", "Section", "Commune", "Code INSEE", "Département", "Surface Demandée (m²)"]
    ws.append(headers)

    for idsuf, section, libelle, insee, dep, surface_demandee in rows:
        ws.append([idsuf, section, libelle, insee, dep, surface_demandee])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="selection_parcelles.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    

@selection_bp.route('/selection/parcelle/clear', methods=['POST'])
def clear_selection():
    session_id = session.get('session_id')
    if not session_id:
        flash("Session manquante.", "danger")
        return redirect(url_for('selection.index'))

    SelectionParcelle.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    flash("Sélection vidée avec succès.", "success")
    return redirect(url_for('selection.index'))


@selection_bp.route('/selection/parcelle/update_surface', methods=['POST'])
@selection_bp.route('/selection/parcelle/update_surface', methods=['POST'])
def update_surface():
    idsuf = request.form.get('idsuf')
    surface_demandee = request.form.get('surface_demandee')

    if not idsuf or not surface_demandee:
        return jsonify(status='error', message="Données incomplètes.")

    try:
        surface_demandee = float(surface_demandee)
    except ValueError:
        return jsonify(status='error', message="Surface invalide.")

    # Récupération des données cadastrales pour vérification
    cadastre = TCadastre.query.filter_by(idsuf=idsuf).first()
    if not cadastre:
        return jsonify(status='error', message="Parcelle introuvable dans le cadastre.")

    surface_max = cadastre.dcntsf or 0
    if surface_demandee > surface_max:
        return jsonify(status='error', message=f"Surface demandée ({surface_demandee} m²) supérieure à la surface cadastrale ({surface_max} m²).")

    # Mise à jour ou création de la sélection
    selection = SelectionParcelle.query.filter_by(idsuf=idsuf).first()
    if selection:
        selection.surface_demandee = surface_demandee
    else:
        selection = SelectionParcelle(idsuf=idsuf, surface_demandee=surface_demandee)
        db.session.add(selection)

    db.session.commit()

    return jsonify(status='ok')
