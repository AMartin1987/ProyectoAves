from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, \
  TextAreaField, HiddenField, RadioField, FileField, SelectMultipleField, widgets
from wtforms.validators import Length, Email, ValidationError, InputRequired
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms.widgets import html_params

import sqlite3, os

UPLOAD_PATH = '/upload'

class SignupForm(FlaskForm):
  name = StringField('Nombre', validators=[InputRequired(), Length(max=64)])
  password = PasswordField('Contraseña', validators=[InputRequired()])
  email = StringField('Email', validators=[InputRequired(), Email()])
  submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
  email = StringField('Email',validators=[InputRequired(),Email()])
  password = PasswordField('Contraseña',validators=[InputRequired()])
  remember = BooleanField('Recordarme')
  submit = SubmitField('Iniciar sesión')

def validate_email(self, email):
  db = sqlite3.connect('proyecto.db')
  cur = db.cursor()
  cur.execute("SELECT email FROM USUARIOS where Email = (?)",[email.data])
  valemail = cur.fetchone()
  if valemail is None:
    raise ValidationError('Email no registrado.')

def select_multi_checkbox(field, ul_class='', **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = [u'<ul %s>' % html_params(id=field_id, class_=ul_class)]
    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id)
        if checked:
            options['checked'] = 'checked'
        html.append(u'<li><input %s /> ' % html_params(**options))
        html.append(u'<label for="%s">%s</label></li>' % (field_id, label))
    html.append(u'</ul>')
    return u''.join(html)    

class BirdForm(FlaskForm):
  especie = SelectField(u'¿Qué tipo de ave es?:', [InputRequired()], choices=
  [('paloma', 'Palomas (torcazas, urbanas, etc.)'), ('peqsil', 'Pequeñas aves silvestres(gorriones, horneros, etc.)'\
    ), ('medsil', 'Aves silvestres medianas (loros, búhos, chimangos, etc.)'), ('corral', \
      'Aves de granja (gallinas, patos, etc.)')])
  espEsp = StringField('Especificá la especie:', [InputRequired()], render_kw={"placeholder": "Ejemplo: 'Colibrí'"})
  edad = StringField('Edad aproximada:', [InputRequired()], render_kw={"placeholder": \
    "Ejemplos: 'Pichón' o 'un mes y medio'"})
  salud = TextAreaField('Estado de salud:', render_kw={"placeholder": "Ejemplos: 'Buena' o 'fractura en un ala'"})
  localiz = StringField('¿Dónde está el ave actualmente?:', [InputRequired()], render_kw={"placeholder":\
     "Ejemplo: 'Estomba 900, Bahía Blanca.'"})
  loc_lat = HiddenField()
  loc_long = HiddenField()
  lugar = RadioField('El ave necesita:', choices=[('transito', 'Un lugar de tránsito hasta su liberación.'), \
    ('hogar', 'Un hogar permanente.')], validators=[InputRequired()])
  requer = TextAreaField('Requerimientos que debería cumplir este nuevo lugar para el cuidado del ave:')
  contacto = StringField('Teléfono/Whatsapp:', render_kw={"placeholder": "Teléfono/Whatsapp"}, validators=[InputRequired()])
  imagen = FileField('Subir imagen')
  submit = SubmitField('Registrar ave')

class PlaceForm(FlaskForm):
  lugar = SelectMultipleField('Estás proponiendo (marcar uno o ambos)...:', [InputRequired()], \
    choices=[('transito', 'Un lugar de tránsito hasta su liberación.'), ('hogar', 'Un hogar permanente.')],\
    widget=select_multi_checkbox)
  localiz = StringField('¿En qué ubicación?:', [InputRequired()], render_kw={"placeholder": \
    "Ejemplo: 'Estomba 900, Bahía Blanca.'"})
  loc_lat = HiddenField()
  loc_long = HiddenField()
  especie = SelectMultipleField('¿Qué aves se pueden alojar aquí? (marcar una o varias):', [InputRequired()],\
    choices=[('paloma', 'Palomas (torcazas, urbanas, etc.)'), \
    ('peqsil', 'Pequeñas aves silvestres(gorriones, horneros, etc.)'),\
    ('medsil', 'Aves silvestres medianas (loros, búhos, chimangos, etc.)'), ('corral', 'Aves de granja \
    (gallinas, patos, etc.)')], widget=select_multi_checkbox)
  contacto = StringField('Contacto:', render_kw={"placeholder": "Celular/Whatsapp"}, validators=[InputRequired()])
  submit = SubmitField('Registrar refugio')


