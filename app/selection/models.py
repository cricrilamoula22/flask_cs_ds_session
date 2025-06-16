#\my_app\app\selection\models.py :


from app import db
from sqlalchemy import Table, Column, Integer, Float, Text, Date, Boolean, String, ForeignKey
from sqlalchemy import create_engine, Column, Integer, BigInteger, Text, Date, Boolean, String, MetaData, Table
from sqlalchemy import PrimaryKeyConstraint, Index, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import and_

class SelectionParcelle(db.Model):
    __tablename__ = 'selection_parcelle'

    session_id = db.Column(db.String(128), primary_key=True)
    idsuf = db.Column(db.String(20), db.ForeignKey('t_cadastre.idsuf'), primary_key=True)
    surface_demandee = db.Column(db.BigInteger, nullable=False)

    # Relationship to t_cadastre
    cadastre = db.relationship('TCadastre', back_populates='selections')

class TCadastre(db.Model):
    __tablename__ = 't_cadastre'

    idt_cadastre = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idsuf = db.Column(db.String(18), unique=True, nullable=False)
    idpar = db.Column(db.String(18))
    idprocpte = db.Column(db.String(17))
    idcom = db.Column(db.String(6), db.ForeignKey('t_commune.com'))
    ccosec = db.Column(db.String(3))
    dnupla = db.Column(db.String(5))
    ccosub = db.Column(db.String(3))
    dcntsf = db.Column(db.BigInteger)
    idprocpte_org = db.Column(db.Text)

    # Relationships
    commune = db.relationship('TCommune', back_populates='cadastres')
    selections = db.relationship('SelectionParcelle', back_populates='cadastre')

class TCommune(db.Model):
    __tablename__ = 't_commune'

    idt_commune = db.Column(db.Integer, primary_key=True, autoincrement=True)
    com = db.Column(db.String(6), unique=True)
    dep = db.Column(db.String(3))
    can = db.Column(db.String(5))
    libelle = db.Column(db.String(255))

    # Relationship to t_cadastre
    cadastres = db.relationship('TCadastre', back_populates='commune')
