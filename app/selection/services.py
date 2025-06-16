#\my_app\app\selection\services.py :

from app import db
from app.selection.models import TCadastre, TCommune, SelectionParcelle # Added SelectionParcelle
from sqlalchemy import distinct
from sqlalchemy.orm import selectinload
from sqlalchemy import asc, desc, func, and_

def update_surface_demandee(idsuf, surface_demandee, session_id):
    parcelle = SelectionParcelle.query.filter_by(idsuf=idsuf, session_id=session_id).first()
    if parcelle:
        parcelle.surface_demandee = surface_demandee
        db.session.commit()
    else:
        new_parcelle = SelectionParcelle(idsuf=idsuf, surface_demandee=surface_demandee, session_id=session_id)
        db.session.add(new_parcelle)
        db.session.commit()


def get_or_create_parcelle_from_idsuf(idsuf):
    cadastre_entry = TCadastre.query.filter_by(idsuf=idsuf).first()
    if not cadastre_entry:
        return None  # Erreur de cohérence

    # Vérifie si la parcelle existe déjà
    parcelle = Parcelle.query.filter_by(idsuf=idsuf).first()
    if parcelle:
        return parcelle

    # Sinon, créer la parcelle
    parcelle = Parcelle(
        idsuf=cadastre_entry.idsuf,
        section=cadastre_entry.ccosec,
        commune_code_insee=cadastre_entry.idcom
    )
    db.session.add(parcelle)
    db.session.commit()
    return parcelle


def get_departement_choices():
    # Liste manuelle des départements bretons : (code, label)
    bretons = [
        ('22', '22 - Côtes-d\'Armor'),
        ('29', '29 - Finistère'),
        ('35', '35 - Ille-et-Vilaine'),
        ('56', '56 - Morbihan')
    ]
    choices = [('', 'Sélectionner un département')] + bretons
    return choices


def get_communes_for_departement(dep_code):
    if not dep_code:
        return []  # Pas de département sélectionné : pas de communes
    communes = db.session.query(TCommune).filter(TCommune.dep == dep_code).order_by(TCommune.libelle).all()
    #communes = db.session.query(Commune).filter(Commune.dep_code == dep_code).order_by(Commune.nom).all()
    return [(com.com, com.libelle) for com in communes]

def get_sections_for_commune(commune_code_insee=None):
    """
    Renvoie une liste de sections distinctes pour la commune donnée.
    """
    if not commune_code_insee:
        return []
    query = db.session.query(distinct(TCadastre.ccosec)).filter(TCadastre.idcom == commune_code_insee)
    #query = db.session.query(distinct(Parcelle.section)).filter(Parcelle.commune_code_insee == commune_code_insee)
    sections = query.order_by(TCadastre.ccosec).all()
    #sections = query.order_by(Parcelle.section).all()
    return [s[0] for s in sections] # sections will be like [('A',), ('B',)]


def get_parcelles_by_filters(dep_code=None, commune_code_insee=None, section_val=None):
    query = db.session.query(TCadastre).select_from(TCadastre).join(TCommune, TCadastre.idcom == TCommune.com)\
    .order_by(func.substr(TCadastre.idsuf, 10, 7))
    """
    query = db.session.query(TCadastre).\
    join(TCommune, TCadastre.idcom == TCommune.com).\
    filter(and_(
        TCadastre.idcom.like('%22055'),
        TCadastre.ccosec.like('%AC'),
        func.substring(TCadastre.idsuf, 7, 3) == '007'
    )).\
    order_by(func.substring(TCadastre.idsuf, 10, 7).asc())
    """
    #query = TCadastre.query.join(TCadastre.commune)

    # On ne filtre que si la troisième liste (section_val) est sélectionnée
    if section_val:
        # Enlève l'apostrophe de début si elle existe
        #cleaned_section_val = section_val.lstrip("'")
        if dep_code:
            query = query.filter(TCommune.dep == dep_code)
        if commune_code_insee:
            query = query.filter(TCadastre.idcom == commune_code_insee)
        query = query.filter(TCadastre.ccosec == section_val)
    else:
        # Pas de filtrage, on retourne tout (ou éventuellement une liste vide)
        query = query.filter(False)  # Retourne aucun résultat tant que section_val n'est pas choisi
    #func.ltrim(TCadastre.ccosec, "'")
    return query.order_by(func.substr(TCadastre.idsuf, 10, 7), TCadastre.ccosec, TCadastre.idcom).all()


# New/Adapted functions for selection

def add_parcelle_to_selection(session_id, idsuf, surface_demandee=None):
    # Vérifie si la parcelle est déjà sélectionnée
    selection = SelectionParcelle.query.filter_by(session_id=session_id, idsuf=idsuf).first()
    if not selection:
        # Si surface_demandee non renseignée, la récupérer depuis la table TCadastre
        if surface_demandee is None:
            cadastre = TCadastre.query.filter_by(idsuf=idsuf).first()
            if cadastre:
                surface_demandee = cadastre.dcntsf or 0
            else:
                surface_demandee = 0  # Par défaut 0 si parcelle inconnue
        
        # Créer une nouvelle sélection
        selection = SelectionParcelle(
            session_id=session_id,
            idsuf=idsuf,
            surface_demandee=surface_demandee
        )
        db.session.add(selection)
        db.session.commit()
    return selection


def remove_parcelle_from_selection(session_id, idsuf):
    SelectionParcelle.query.filter_by(session_id=session_id, idsuf=idsuf).delete()
    db.session.commit()

def get_selected_parcelle_objects(session_id):
    return (
        db.session.query(SelectionParcelle, TCadastre, TCommune)
        .join(TCadastre, SelectionParcelle.idsuf == TCadastre.idsuf)
        .join(TCommune, TCadastre.idcom == TCommune.com)
        .filter(SelectionParcelle.session_id == session_id)
        .order_by(func.substr(SelectionParcelle.idsuf, 10, 7))
        .all()
    )

def get_parcelle_subtotals(session_id):
    rows = (
        db.session.query(
            TCadastre.ccosec,
            db.func.coalesce(db.func.sum(TCadastre.dcntsf), 0)  # Coalesce to avoid None
        )
        .join(SelectionParcelle, SelectionParcelle.idsuf == TCadastre.idsuf)
        .filter(SelectionParcelle.session_id == session_id)
        .group_by(TCadastre.ccosec)
        .order_by(func.substr(SelectionParcelle.idsuf, 10, 7))
        .all()
    )
    return {section: total for section, total in rows}
