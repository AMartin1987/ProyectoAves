from flask import Flask, render_template, url_for, redirect, request, flash, g, abort, current_app, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
import sqlite3, os, flask_login
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from models import User
from markers import Marker
from forms import LoginForm, SignupForm, BirdForm, PlaceForm
from urllib.parse import urlparse, urljoin
from flask_uploads import configure_uploads, IMAGES, UploadSet
from sqlitedict import SqliteDict

app = Flask(__name__)

app.debug=True

# Google Maps JS API Key
API_KEY = 'AIzaSyAqoKvZMX0sWGNCDPWKYyBvLNkkPrV6KvE'

#uploading images configuration
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
app.config["UPLOADED_PHOTOS_DEST"] = 'upload'
photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)

# max file size: 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 

# connect SQLite3
db = 'proyecto.db'
connection = sqlite3.connect('proyecto.db', check_same_thread=False)
cursor = connection.cursor()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('proyecto.db', check_same_thread=False)
        get_db().row_factory = make_dicts
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#select queries as dict
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

#secret key
app.config['SECRET_KEY'] = os.urandom(24)

#login setup: Flask_Login
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = u"Por favor inicie sesión para acceder a esta página."

@login_manager.user_loader
def load_user(user_id):
   connection = sqlite3.connect("proyecto.db")
   curs = connection.cursor()
   curs.execute("SELECT * from USUARIOS where id = (?)",[user_id])
   lu = curs.fetchone()
   if lu is None:
      return None
   else:
      return User(int(lu[0]), lu[1], lu[2], lu[3])

#url sanitization from https://www.pythonkitchen.com/how-prevent-open-redirect-vulnerab-flask/ 
def is_safe_redirect_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )

def get_safe_redirect(url):
    if url and is_safe_redirect_url(url):
        return url
    url = request.referrer
    if url and is_safe_redirect_url(url):
        return url
    return "/"

@app.route('/')
def index():
    if current_user.is_authenticated:
        nombre = current_user.name
        return render_template('index.html', nombre=nombre)
    return render_template('index.html')
 
@app.route('/search', methods=['GET'])
def search():
    nombre = 'Mi cuenta'
    if current_user.is_authenticated:
        nombre = current_user.name
    cur = get_db().cursor()
    ubicaciones = cur.execute("SELECT Id, Latitud, Longitud, Direccion FROM UBICACIONES").fetchall()
    aves = cur.execute("SELECT Id, Especie, Edad, Foto, EstSalud, Requer, Id_ESPECIES, Id_TELEFONOS, Id_TIPOREFUGIO, Id_UBICACIONES FROM AVES").fetchall()
    refugios = cur.execute("SELECT Id, Id_ESPECIES1, Id_ESPECIES2, Id_ESPECIES3, Id_ESPECIES4, Id_UBICACIONES, Id_TELEFONOS, Id_TIPOREFUGIO1, Id_TIPOREFUGIO2 FROM REFUGIOS").fetchall()
    telefonos = cur.execute("SELECT Id, Telefono FROM TELEFONOS").fetchall()
    get_db().commit()
    
    i = 0
    ubic_dict = { }
    for value in ubicaciones:
        ubic_dict[str(i)] = value
        i = i + 1

    i = 0
    aves_dict = { }
    for value in aves:
        aves_dict[str(i)] = value
        i = i + 1

    i = 0
    refug_dict = { }
    for value in refugios:
        refug_dict[str(i)] = value
        i = i + 1

    i = 0
    telef_dict = { }
    for value in telefonos:
        telef_dict[str(i)] = value
        i = i + 1

    return render_template('search.html', ubic_dict=ubic_dict, aves_dict=aves_dict, refug_dict=refug_dict, telef_dict=telef_dict, nombre=nombre)
    
@app.route('/addbird', methods=['GET', 'POST'])
@login_required
def addbird():
    form = BirdForm()
    nombre = current_user.name
    if form.validate_on_submit():
        #Get user Id
        user_id = current_user.get_id()
        
        #Image upload
        file = form.imagen.data
        file_ext = os.path.splitext(file.filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
            raise BadRequest('Por favor suba un archivo de imagen válido (JPG, GIF o PNG). Tamaño máximo: 4 MB.')
        file = photos.save(form.imagen.data)
        
        #WTForms
        especie = form.especie.data
        espEsp = form.espEsp.data
        edad = form.edad.data
        salud = form.salud.data
        requer = form.requer.data
        contacto = form.contacto.data
        localiz = form.localiz.data
        loc_lat = form.loc_lat.data
        loc_long = form.loc_long.data
        lugar = form.lugar.data

        #Registering in database
        connection = sqlite3.connect("proyecto.db")
        curs = connection.cursor()

        lista1 = curs.execute("SELECT Categoria FROM ESPECIES").fetchall()
        idEspecies = 'none'
        for i in lista1:
            if i[0] == "('{0}',)".format(especie):
                idEspecies = curs.execute("SELECT Id FROM ESPECIES WHERE Categoria = (?)", (especie,))
                break
        if idEspecies == 'none':
            curs.execute("INSERT INTO ESPECIES (Categoria) VALUES (?)", (especie,))
            connection.commit()
            idEspecies = curs.execute("SELECT MAX(Id) FROM ESPECIES").fetchone()

        lista2 = curs.execute("SELECT Telefono FROM TELEFONOS").fetchall()
        idTelefonos = 'none'
        for i in lista2:
            if i[0] == "('{0}',)".format(contacto):
                idEspecies = curs.execute("SELECT Id FROM TELEFONOS WHERE Telefono = (?)", (contacto,))
                break
        if idTelefonos == 'none':
            curs.execute("INSERT INTO TELEFONOS (Telefono) VALUES (?)", (contacto,))
            idTelefonos = curs.execute("SELECT MAX(Id) FROM TELEFONOS").fetchone()
            connection.commit()

        lista3 = curs.execute("SELECT TipoRefug FROM TIPOREFUGIO").fetchall()
        idTipoRefug = 'none'
        for i in lista3:
            if i[0] == "('{0}',)".format(lugar):
                idTipoRefug = curs.execute("SELECT Id FROM TIPOREFUGIO WHERE TipoRefug = (?)", (lugar,))
                break
        if idTipoRefug == 'none':
            curs.execute("INSERT INTO TIPOREFUGIO (TipoRefug) VALUES (?)", (lugar,))
            idTipoRefug = curs.execute("SELECT MAX(Id) FROM TIPOREFUGIO").fetchone()
            connection.commit()

        lista4 = curs.execute("SELECT Direccion FROM UBICACIONES").fetchall()
        idUbicaciones = 'none'
        for i in lista4:
            if i[0] == "('{0}',)".format(localiz):
                idUbicaciones = curs.execute("SELECT Id FROM UBICACIONES WHERE Direccion = (?)", (localiz,))
                break
        if idUbicaciones == 'none':
            curs.execute("INSERT INTO UBICACIONES (Latitud, Longitud, Direccion) VALUES (?, ?, ?)", (
            loc_lat, loc_long, localiz,))
            connection.commit()
            idUbicaciones = curs.execute("SELECT MAX(Id) FROM UBICACIONES").fetchone()

        curs.execute(
            "INSERT INTO AVES (Especie, Edad, EstSalud, Requer, Foto, Id_USUARIOS, Id_ESPECIES, Id_TELEFONOS, Id_TIPOREFUGIO, Id_UBICACIONES) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            espEsp, edad, salud, requer, file, user_id, idEspecies[0], idTelefonos[0], idTipoRefug[0], idUbicaciones[0]))
        connection.commit()
        
        flash('¡Registraste un ave caida!')
        return redirect(url_for('search'))
    return render_template('addbird.html', form=form, nombre=nombre)

@app.route('/addplace', methods=['GET', 'POST'])
@login_required
def addplace():
    form = PlaceForm()
    nombre = current_user.name    
    if form.validate_on_submit():
        #Get user Id
        user_id = current_user.get_id()
        
        #WTForms
        especie = form.especie.data
        contacto = form.contacto.data
        localiz = form.localiz.data
        loc_lat = form.loc_lat.data
        loc_long = form.loc_long.data
        lugar = form.lugar.data

        #Registering in database
        connection = sqlite3.connect("proyecto.db")
        curs = connection.cursor()

        lista1 = curs.execute("SELECT Direccion FROM UBICACIONES").fetchall()
        idUbicaciones = 'none'
        for i in lista1:
            if i[0] == "('{0}',)".format(localiz):
                idUbicaciones = curs.execute("SELECT Id FROM UBICACIONES WHERE Direccion = (?)", (localiz,))
                break
        if idUbicaciones == 'none':
            curs.execute("INSERT INTO UBICACIONES (Latitud, Longitud, Direccion) VALUES (?, ?, ?)", (
            loc_lat, loc_long, localiz,))
            connection.commit()
            idUbicaciones = curs.execute("SELECT MAX(Id) FROM UBICACIONES").fetchone()
        
        tipoRef1 = 0
        tipoRef2 = 'NULL'
        if lugar[0] == 'hogar':
            tipoRef1 = 1 #Si tildó hogar, eso va a la col 1 de la DB
            if len(lugar) > 1:
                tipoRef2 = 2 #Si además de hogar tildó tránsito, eso además va a la col 2
        elif lugar[0] == 'transito':
            tipoRef1 = 2 #Si sólo tildó tránsito, eso va a la col 1

        lista2 = curs.execute("SELECT Telefono FROM TELEFONOS").fetchall()
        idTelefonos = 'none'
        for i in lista2:
            if i[0] == "('{0}',)".format(contacto):
                idEspecies = curs.execute("SELECT Id FROM TELEFONOS WHERE Telefono = (?)", (contacto,))
                break
        if idTelefonos == 'none':
            curs.execute("INSERT INTO TELEFONOS (Telefono) VALUES (?)", (contacto,))
            connection.commit()
            idTelefonos = curs.execute("SELECT MAX(Id) FROM TELEFONOS").fetchone()

        especie1 = 0
        especie2 = 'NULL'
        especie3 = 'NULL'
        especie4 = 'NULL'
        if especie[0] == 'paloma':
            especie1 = 'paloma' #Si tildó paloma, eso va a la col 1 de la DB
            if len(especie) > 1:
                if especie[1] == 'peqsil':
                    especie2 = 'peqsil' #Si además de paloma tildó peqsil, eso además va a la col 2
                    if len(especie) > 2:
                        if especie[2] == 'medsil':
                            especie3 = 'medsil'  #Si además de paloma y peqsil tildó medsil, eso además va a la col 3
                            if len(especie) > 3:
                                if especie[3] == 'corral':
                                    especie4 = 'corral'  #Si además tildó corral, esto va en col 4                            
                elif especie[1] == 'medsil':
                    especie2 = 'medsil' #Si además de paloma tildó medsil, eso además va a la col 2
                    if len(especie) > 2:
                        if especie[2] == 'corral':
                            especie3 = 'corral' #Si además de paloma y medsil tildó corral, este va a la col 3
                elif especie[1] == 'corral':
                    especie2 = 'corral' #Si además de paloma tildó corral, eso además va a la col 2
        elif lugar[0] == 'peqsil':
            especie1 = 'peqsil' #Si sólo tildó peqsil, eso va a la col 1
        elif lugar[0] == 'medsil':
            especie1 = 'medsil' #Si sólo tildó medsil, eso va a la col 1
        elif lugar[0] == 'corral':
            especie1 = 'corral' #Si sólo tildó corral, eso va a la col 1                     

        curs.execute(
            "INSERT INTO REFUGIOS (Id_USUARIOS, Id_UBICACIONES, Id_ESPECIES1, Id_ESPECIES2, Id_ESPECIES3, Id_ESPECIES4, Id_TELEFONOS, Id_TIPOREFUGIO1, Id_TIPOREFUGIO2) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            user_id, idUbicaciones[0], especie1, especie2, especie3, especie4, idTelefonos[0], tipoRef1, tipoRef2))
        connection.commit()

        flash('¡Registraste un nuevo refugio!')
        return redirect(url_for('search'))
    return render_template('addplace.html', form=form, nombre=nombre)    

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        hash = generate_password_hash(password)
        
        #if confirmation != password:
        #    return apology("passwords don't match", 403)
        #if not request.form.get("username") or not request.form.get("password"):
        #    return apology("must provide username and password", 403)

        #registrar datos en tabla USUARIOS
        connection = sqlite3.connect("proyecto.db")
        curs = connection.cursor()
        curs.execute("INSERT INTO USUARIOS (Nombre, Email, Hashed_password) VALUES(?, ?, ?)", (name, email, hash)
                    )
        connection.commit()
                    
        flash('Registraste tu cuenta!')
        return redirect(url_for('index'))

    else:
        return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
     return redirect(url_for('index'))
  form = LoginForm()
  if form.validate_on_submit():
     connection = sqlite3.connect('proyecto.db')
     curs = connection.cursor()
     curs.execute("SELECT * FROM USUARIOS where Email = (?)", [form.email.data])
     user = list(curs.fetchone())
     Us = load_user(user[0])
     
     if form.email.data == Us.email and check_password_hash(Us.password, form.password.data):
        login_user(Us, remember=form.remember.data)
        Umail = list({form.email.data})[0].split('@')[0]
        flash('Has iniciado sesión.'+Umail)
        next = request.args.get('next')
        return redirect(get_safe_redirect(next) or url_for('index'))
     else:
        flash('Usuario o contraseña inválidos.')
  return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    next = request.args.get('next')
    return redirect(get_safe_redirect(next) or url_for('index'))  

if __name__ == "__main__":
    app.run(ssl_context='adhoc')