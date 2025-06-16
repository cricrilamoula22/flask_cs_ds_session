#\my_app\app\selection\forms.py :

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired, Length, Regexp, Optional

# ... (FilterForm reste inchangée) ...
class FilterForm(FlaskForm):
    departement = SelectField('Département', choices=[])
    commune = SelectField('Commune', choices=[])
    section = SelectField('Section', choices=[])

class AddParcelForm(FlaskForm):
    departement = SelectField(
        'Département',
        choices=[],
        validators=[DataRequired("Veuillez sélectionner un département.")]
    )
    commune = SelectField(
        'Commune',
        choices=[('', 'Sélectionner une commune')],
        validators=[DataRequired("Veuillez sélectionner une commune.")]
    )
    prefixe = StringField(
        'Préfixe INSEE (commune déléguée)',
        default='000',
        validators=[
            DataRequired(),
            Length(min=3, max=3, message="Le préfixe doit contenir exactement 3 caractères."),
            Regexp(r'^\d{3}$', message="Le préfixe doit être composé de 3 chiffres.")
        ]
    )
    section = StringField(
        'Section cadastrale',
        validators=[
            DataRequired(),
            Length(min=1, max=2, message="La section doit contenir 1 ou 2 caractères."),
            Regexp(r'^[a-zA-Z0-9]{1,2}$', message="La section ne doit contenir que des lettres (A-Z) ou des chiffres (0-9).")
        ]
    )
    numero = StringField(
        'Numéro de parcelle',
        validators=[
            DataRequired(),
            Length(min=1, max=8, message="Le numéro doit contenir entre 1 et 8 chiffres."),
            Regexp(r'^\d{1,8}$', message="Le numéro ne doit contenir que des chiffres.")
        ]
    )
    # NOUVEAU : Champ pour la subdivision fiscale
    subdivision = StringField(
        'Subdivision fiscale (optionnel)',
        validators=[
            Optional(), # Ce champ n'est pas obligatoire
            Length(max=2, message="La subdivision ne doit pas dépasser 2 lettres."),
            Regexp(r'^[a-zA-Z]*$', message="La subdivision ne doit contenir que des lettres.")
        ]
    )
    superficie = StringField(
        'Superficie de la parcelle',
        validators=[
            DataRequired(),
            Regexp(r'^\d{1,8}$', message="La superficie est à renseigner en mètres carrés.")
        ]
    )