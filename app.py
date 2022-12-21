import sqlite3, os, helpers

from flask import Flask, render_template, url_for, redirect, request, flash, g, current_app, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models import User
from forms import LoginForm, SignupForm, BirdForm, PlaceForm
from urllib.parse import urlparse, urljoin
from flask_uploads import configure_uploads, IMAGES, UploadSet

app = Flask(__name__)

#uploading images configuration
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
app.config["UPLOADED_PHOTOS_DEST"] = 'static/upload'
photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)

app.config['UPLOAD_FOLDER'] = 'static/upload'

# max file size: 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 
app.config['MAX_CONTENT_PATH'] =  16 * 1000 * 1000


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
 
@app.route('/search', methods=['GET','POST'])
def search():
    nombre = 'Mi cuenta'
    if current_user.is_authenticated:
        nombre = current_user.name
    cur = get_db().cursor()
    ubicaciones = cur.execute("SELECT Id, Latitud, Longitud, Direccion FROM UBICACIONES").fetchall()
    aves = cur.execute("SELECT Id, Especie, Edad, Foto, EstSalud, Requer, Id_ESPECIES, Id_TELEFONOS, Id_TIPOREFUGIO, Id_UBICACIONES FROM AVES").fetchall()
    refugios = cur.execute("SELECT Id, Id_ESPECIES1, Id_ESPECIES2, Id_ESPECIES3, Id_ESPECIES4, Id_UBICACIONES, Id_TELEFONOS, Id_TIPOREFUGIO1, Id_TIPOREFUGIO2 FROM REFUGIOS").fetchall()
    telefonos = cur.execute("SELECT Id, Telefono FROM TELEFONOS").fetchall()
    especies = cur.execute("SELECT Id, Categoria FROM ESPECIES").fetchall()
    tiporef = cur.execute("SELECT Id, TipoRefug FROM TIPOREFUGIO").fetchall()
    get_db().commit()
    
    ubic_dict = helpers.make_dict(ubicaciones)
    aves_dict = helpers.make_dict(aves)
    refug_dict = helpers.make_dict(refugios)
    telef_dict = helpers.make_dict(telefonos)
    espe_dict = helpers.make_dict(especies)
    tiporef_dict = helpers.make_dict(tiporef)

    return render_template('search.html', ubic_dict=ubic_dict,
     aves_dict=aves_dict, refug_dict=refug_dict, telef_dict=telef_dict,
     espe_dict=espe_dict, tiporef_dict=tiporef_dict, nombre=nombre)
    
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
        idEspecies = curs.execute("SELECT Id FROM ESPECIES WHERE Categoria = (?)", (especie,)).fetchone()

        lista2 = curs.execute("SELECT Telefono FROM TELEFONOS").fetchall()
        idTelefonos = 'none'
        for i in lista2:
            if i[0] == "('{0}',)".format(contacto):
                idEspecies = curs.execute("SELECT Id FROM TELEFONOS WHERE Telefono = (?)", (contacto,)).fetchone()
                break
        if idTelefonos == 'none':
            curs.execute("INSERT INTO TELEFONOS (Telefono) VALUES (?)", (contacto,))
            idTelefonos = curs.execute("SELECT MAX(Id) FROM TELEFONOS").fetchone()
            connection.commit()

        lista3 = curs.execute("SELECT TipoRefug FROM TIPOREFUGIO").fetchall()
        idTipoRefug = curs.execute("SELECT Id FROM TIPOREFUGIO WHERE TipoRefug = (?)", (lugar,)).fetchone()

        lista4 = curs.execute("SELECT Direccion FROM UBICACIONES").fetchall()
        idUbicaciones = 'none'
        for i in lista4:
            if i[0] == "('{0}',)".format(localiz):
                idUbicaciones = curs.execute("SELECT Id FROM UBICACIONES WHERE Direccion = (?)", (localiz,)).fetchone()
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
        tipoespecie = form.especie.data
        contacto = form.contacto.data
        localiz = form.localiz.data
        loc_lat = form.loc_lat.data
        loc_long = form.loc_long.data
        tiporef = form.lugar.data

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
        
        tipoRef1 = 'NULL'
        tipoRef2 = 'NULL'
        for i in range (len(tiporef)):
            if tiporef[i] == 'hogar':
                tipoRef1 = 1 #Si tildó hogar, eso va a la col 1 de la DB
                if len(tiporef) > 1:
                    tipoRef2 = 2 #Si tildó ambas opciones
                    break
            elif tiporef[i] == 'transito':
                tipoRef1 = 2 #Si sólo tildó tránsito, eso va a la col 1

        lista2 = curs.execute("SELECT Telefono FROM TELEFONOS").fetchall()
        idTelefonos = 'none'
        for i in lista2:
            if i[0] == "('{0}',)".format(contacto):
                idTelefonos = curs.execute("SELECT Id FROM TELEFONOS WHERE Telefono = (?)", (contacto,))
                break
        if idTelefonos == 'none':
            curs.execute("INSERT INTO TELEFONOS (Telefono) VALUES (?)", (contacto,))
            connection.commit()
            idTelefonos = curs.execute("SELECT MAX(Id) FROM TELEFONOS").fetchone()

        especie1 = 0
        especie2 = 'NULL'
        especie3 = 'NULL'
        especie4 = 'NULL'

        if tipoespecie[0] == 'paloma':
            especie1 = 1 #Si tildó paloma, eso va a la col 1 de la DB
            if len(tipoespecie) > 1:
                if tipoespecie[1] == 'peqsil':
                    especie2 = 2 #Si además de paloma tildó peqsil, eso además va a la col 2
                    if len(tipoespecie) > 2:
                        if tipoespecie[2] == 'medsil':
                            especie3 = 3  #Si además de paloma y peqsil tildó medsil, eso además va a la col 3
                            if len(tipoespecie) > 3:
                                if tipoespecie[3] == 'corral':
                                    especie4 = 4  #Si además tildó corral, esto va en col 4                            
                elif tipoespecie[1] == 'medsil':
                    especie2 = 3 #Si además de paloma tildó medsil, eso además va a la col 2
                    if len(tipoespecie) > 2:
                        if tipoespecie[2] == 'corral':
                            especie3 = 4 #Si además de paloma y medsil tildó corral, este va a la col 3
                elif tipoespecie[1] == 'corral':
                    especie2 = 4 #Si además de paloma tildó corral, eso además va a la col 2
        elif tipoespecie[0] == 'peqsil':
            especie1 = 2 #Si sólo tildó peqsil, eso va a la col 1
            if len(tipoespecie) > 1:
                if tipoespecie[1] == 'medsil':
                    especie2 = 3  #Si además de paloma y peqsil tildó medsil, eso además va a la col 2
                    if len(tipoespecie) > 2:
                        if tipoespecie[2] == 'corral':
                            especie3 = 4  #Si además tildó corral, esto va en col 3
                if tipoespecie[1] == 'corral':
                            especie2 = 4  #Si además tildó corral, esto va en col 2             
        elif tipoespecie[0] == 'medsil':
            especie1 = 3 #Si sólo tildó medsil, eso va a la col 1
            if len(tipoespecie) > 1:
                if tipoespecie[1] == 'corral':
                    especie2 = 4  #Si además tildó corral, esto va en col 2
        elif tipoespecie[0] == 'corral':
            especie1 = 4 #Si sólo tildó corral, eso va a la col 1                   

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
        
        #Check if email is already registered
        connection = sqlite3.connect("proyecto.db")
        curs = connection.cursor()
        email_exists = curs.execute("SELECT COUNT(*) FROM USUARIOS WHERE Email = (?)", [email,]).fetchone()
        email_exists = email_exists[0]
        print(email_exists)
        if email_exists == '1':
            flash('El email {email} ya está siendo utilizado por otro usuario.')
            return redirect(url_for('register'))

        #Register data in USUARIOS ('users') table 
        connection = sqlite3.connect("proyecto.db")
        curs = connection.cursor()
        curs.execute("INSERT INTO USUARIOS (Nombre, Email, Hashed_password) VALUES(?, ?, ?)", (name, email, hash))
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
     
     #Check if email and password correspond to a registered user
     if form.email.data == Us.email and check_password_hash(Us.password, form.password.data):
        login_user(Us, remember=form.remember.data) #Remember session
        flash('Iniciaste sesión.')
        next = request.args.get('next')
        return redirect(get_safe_redirect(next) or url_for('index')) #safely redirect user to last accessed page  
     else:
        flash('Usuario o contraseña inválidos.')
        return redirect(url_for('login'))
        
        
  return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    next = request.args.get('next')
    return redirect(get_safe_redirect(next) or url_for('index'))  #safely redirect user to last accessed page  

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    nombre = current_user.name
    #Get user Id
    user_id = current_user.get_id()

    #Get DB data for this user's Id
    cur = get_db().cursor()
    ubicaciones = cur.execute("SELECT Id, Latitud, Longitud, Direccion \
                FROM UBICACIONES WHERE Id IN (SELECT Id_UBICACIONES FROM \
                AVES WHERE Id_USUARIOS = (?) UNION SELECT Id_UBICACIONES \
                FROM REFUGIOS WHERE Id_USUARIOS = (?))", (user_id, user_id)).fetchall()
    aves = cur.execute("SELECT Id, Especie, Edad, Foto, EstSalud, Requer, \
         Id_ESPECIES, Id_TELEFONOS, Id_TIPOREFUGIO, Id_UBICACIONES FROM AVES \
         WHERE Id_USUARIOS = (?)", (user_id,)).fetchall()
    refugios = cur.execute("SELECT Id, Id_ESPECIES1, Id_ESPECIES2, Id_ESPECIES3, \
             Id_ESPECIES4, Id_UBICACIONES, Id_TELEFONOS, Id_TIPOREFUGIO1, \
             Id_TIPOREFUGIO2 FROM REFUGIOS WHERE Id_USUARIOS = (?)", (user_id,)).fetchall()
    telefonos = cur.execute("SELECT Id, Telefono FROM TELEFONOS WHERE Id IN \
              (SELECT Id_TELEFONOS FROM AVES WHERE Id_USUARIOS = (?) UNION \
              SELECT Id_TELEFONOS FROM REFUGIOS WHERE Id_USUARIOS = (?))", (user_id, user_id)).fetchall()
    especies = cur.execute("SELECT Id, Categoria FROM ESPECIES").fetchall()
    tiporef = cur.execute("SELECT Id, TipoRefug FROM TIPOREFUGIO").fetchall()
    get_db().commit()
    
    #Convert data from DB to dict type
    ubic_dict = helpers.make_dict(ubicaciones)
    aves_dict = helpers.make_dict(aves)
    refug_dict = helpers.make_dict(refugios)
    telef_dict = helpers.make_dict(telefonos)
    espe_dict = helpers.make_dict(especies)
    tiporef_dict = helpers.make_dict(tiporef)

    #String of types of species accepted in each refugee, to be displayed in profile.html
    def translate(esp):
        if esp == 1:
            esp = 'palomas'
        elif esp == 2:
            esp = 'pequeñas aves silvestres'
        elif esp == 3:
            esp = 'aves silvestres medianas'
        else:
            esp = 'aves de corral'
        return esp    

    i = 0
    if refug_dict:              
        for i in range(len(refug_dict)):
            if refug_dict[str(i)]["Id_ESPECIES1"] != 'NULL':
                refug_dict[str(i)]["Id_ESPECIES1"] = translate(refug_dict[str(i)]["Id_ESPECIES1"])
            if refug_dict[str(i)]["Id_ESPECIES2"] != 'NULL':
                refug_dict[str(i)]["Id_ESPECIES2"] =  translate(refug_dict[str(i)]["Id_ESPECIES2"])
            if refug_dict[str(i)]["Id_ESPECIES3"] != 'NULL':
                refug_dict[str(i)]["Id_ESPECIES3"] =  translate(refug_dict[str(i)]["Id_ESPECIES3"])
            if refug_dict[str(i)]["Id_ESPECIES4"] != 'NULL':
                refug_dict[str(i)]["Id_ESPECIES4"] =  translate(refug_dict[str(i)]["Id_ESPECIES4"])

    # String of types of refugee needed for each bird, to be displayed in profile.html
    refugios_ave = []
    if aves_dict:
        for i in range(len(aves_dict)):
            dict = aves_dict[str(i)]
            refugios_ave.append(dict['Id_TIPOREFUGIO'])

        for i in range(len(refugios_ave)):
            if (refugios_ave[i] == '1'):
                refugios_ave[i] = 'hogar'
            else:
                refugios_ave[i] = 'tránsito'
    
    if request.method == 'POST':
        editbird = request.form.get('editbird')
        session["editbird"] = editbird

        return redirect(url_for('editbird', editbird=editbird))
    
    return render_template('profile.html', ubic_dict=ubic_dict,
     aves_dict=aves_dict, refug_dict=refug_dict, telef_dict=telef_dict,
     espe_dict=espe_dict, tiporef_dict=tiporef_dict, refugios_ave=refugios_ave,
    nombre=nombre)

@app.route('/profile/deleteRef', methods=['POST'])
@login_required
def delete_refugio():
    # Delete refugio entry from DB
    delete_id_refugio = request.form.get("delete_id_refugio")
    
    if delete_id_refugio:
        connection = sqlite3.connect("proyecto.db")
        curs = connection.cursor()
        curs.execute("DELETE FROM UBICACIONES WHERE Id IN (SELECT Id_UBICACIONES FROM REFUGIOS WHERE Id = (?))", (delete_id_refugio,))
        curs.execute("DELETE FROM REFUGIOS WHERE Id = (?)", (delete_id_refugio,))

        connection.commit()
   
    flash('Registro de refugio eliminado.')
    return redirect(url_for('profile'))

@app.route('/profile/deleteAve', methods=['POST'])
@login_required
def delete_ave():
    # Delete ave entry from DB
    delete_id_ave = request.form.get("delete_id_ave")
    
    if delete_id_ave:
        connection = sqlite3.connect("proyecto.db")
        curs = connection.cursor()
        curs.execute("DELETE FROM UBICACIONES WHERE Id IN (SELECT Id_UBICACIONES FROM AVES WHERE Id = (?))", (delete_id_ave,))
        curs.execute("DELETE FROM AVES WHERE Id = (?)", (delete_id_ave,))

        connection.commit()
    flash('Registro de ave eliminado.')
    return redirect(url_for('profile'))

@app.route('/editbird', methods=['GET', 'POST'])
@login_required
def editbird():
    form = BirdForm()
    nombre = current_user.name

    #Get user Id
    user_id = current_user.get_id()
        
    if request.method == 'POST':
        #Get bird Id
        bird_id = request.form.get('editbird')
        session["bird_id"] = bird_id
 
        #Display info about this bird

        #Get DB data for this user's Id
        connection = sqlite3.connect("proyecto.db")
        cur = get_db().cursor()
        ubicaciones = cur.execute("SELECT Id, Latitud, Longitud, Direccion \
                      FROM UBICACIONES WHERE Id IN (SELECT Id_UBICACIONES FROM \
                      AVES WHERE Id = (?))", (bird_id,)).fetchall()
        aves = cur.execute("SELECT Id, Especie, Edad, Foto, EstSalud, Requer, \
               Id_ESPECIES, Id_TELEFONOS, Id_TIPOREFUGIO, Id_UBICACIONES FROM AVES \
               WHERE Id = (?)", (bird_id,)).fetchall()
        telefonos = cur.execute("SELECT Id, Telefono FROM TELEFONOS WHERE Id IN \
                (SELECT Id_TELEFONOS FROM AVES WHERE Id = (?))", (bird_id,)).fetchall()
        get_db().commit()
    
        #Convert data from DB to dict type
        ubic_dict = helpers.make_dict(ubicaciones)
        aves_dict = helpers.make_dict(aves)
        telef_dict = helpers.make_dict(telefonos)

        # Dict of type of refugio needed by each bird, ready to be displayed in profile.html
        refugios_ave = []
        if aves_dict:
            for i in range(len(aves_dict)):
                dict = aves_dict[str(i)]
                refugios_ave.append(dict['Id_TIPOREFUGIO'])
                
            for i in range(len(refugios_ave)):
                if (refugios_ave[i] == 1):
                    refugios_ave[i] = 'Hogar'
                else:
                    refugios_ave[i] = 'Tránsito'

        # Dict if bird categories, ready to be displayed in profile.html
        tipo_especie = []
        if aves_dict:
            for i in range(len(aves_dict)):
                dict = aves_dict[str(i)]
                tipo_especie.append(dict['Id_ESPECIES'])
        
        for i in range(len(tipo_especie)):
            if (tipo_especie[i] == 1):
                tipo_especie[i] = 'paloma'
            elif (tipo_especie[i] == 2):
                tipo_especie[i] = 'peqsil'
            elif (tipo_especie[i] == 3):
                tipo_especie[i] = 'medsil'
            elif (tipo_especie[i] == 4):
                tipo_especie[i] = 'corral'

        return render_template('editbird.html', form=form, nombre=nombre, ubic_dict=ubic_dict,
        aves_dict=aves_dict, telef_dict=telef_dict, refugios_ave=refugios_ave, tipo_especie=tipo_especie)

@app.route('/editbird/updatebird', methods=['GET', 'POST'])
@login_required
def update_bird():
    nombre = current_user.name    
    
    #Get bird Id
    bird_id = request.form.get('updatebird')
    session["bird_id"] = bird_id

    #Get user Id
    user_id = current_user.get_id()

    tipoespecie = request.form.get('tipoEspecies')
    especie = request.form.get('especie')
    edad = request.form.get('edad')
    estsalud = request.form.get('estsalud')
    requer = request.form.get('requer')
    tiporef = request.form.get('tiporef')
    ubicacion = request.form.get('ubicacion')
    telef = request.form.get('telef')

    connection = sqlite3.connect('proyecto.db')
    curs = connection.cursor()   
    
    if (tipoespecie != ''):
        if tipoespecie == 'paloma':
            id_especie = curs.execute("SELECT Id FROM ESPECIES WHERE Categoria = 'paloma'").fetchone()
            id_especie = id_especie[0]
            curs.execute("UPDATE AVES SET Id_ESPECIES = (?) WHERE Id = (?)", (id_especie, bird_id,))
            connection.commit()
        if tipoespecie == 'peqsil':
            id_especie = curs.execute("SELECT Id FROM ESPECIES WHERE Categoria = 'peqsil'").fetchone()
            id_especie = id_especie[0]
            curs.execute("UPDATE AVES SET Id_ESPECIES = (?) WHERE Id = (?)", (id_especie, bird_id,))
            connection.commit()
        if tipoespecie == 'medsil':
            id_especie = curs.execute("SELECT Id FROM ESPECIES WHERE Categoria = 'medsil'").fetchone()
            id_especie = id_especie[0]
            curs.execute("UPDATE AVES SET Id_ESPECIES = (?) WHERE Id = (?)", (id_especie, bird_id,))
            connection.commit()
        if tipoespecie == 'corral':
            id_especie = curs.execute("SELECT Id FROM ESPECIES WHERE Categoria = 'corral'").fetchone()
            id_especie = id_especie[0]
            curs.execute("UPDATE AVES SET Id_ESPECIES = (?) WHERE Id = (?)", (id_especie, bird_id,))
            connection.commit()    
    if (especie != ''):
        curs.execute("UPDATE AVES SET Especie = (?) WHERE Id = (?)", (especie, bird_id,))
        connection.commit()
    if (edad != ''):
        curs.execute("UPDATE AVES SET Edad = (?) WHERE Id = (?)", (edad, bird_id,))
        connection.commit()
    if (estsalud != ''):
        curs.execute("UPDATE AVES SET EstSalud = (?) WHERE Id = (?)", (estsalud, bird_id,))
        connection.commit()
    if (requer != ''):            
        curs.execute("UPDATE AVES SET Requer = (?) WHERE Id = (?)", (requer, bird_id,))
        connection.commit()
    if (tiporef != ''):
        if tiporef == 'hogar':
            id_tiporef = curs.execute("SELECT Id FROM TIPOREFUGIO WHERE TipoRefug = 'hogar'").fetchone()
            id_tiporef = id_tiporef[0]
            curs.execute("UPDATE AVES SET Id_TIPOREFUGIO = (?) WHERE Id = (?)", (id_tiporef, bird_id,))
            connection.commit()
        else:
            id_tiporef = curs.execute("SELECT Id FROM TIPOREFUGIO WHERE TipoRefug = 'transito'").fetchone()
            id_tiporef = id_tiporef[0]
            curs.execute("UPDATE AVES SET Id_TIPOREFUGIO = (?) WHERE Id = (?)", (id_tiporef, bird_id,))
            connection.commit()    
    if (ubicacion != ''):
        id_ubicaciones = curs.execute("SELECT Id_UBICACIONES FROM AVES WHERE Id = (?)", (bird_id,)).fetchone()
        id_ubicaciones = id_ubicaciones[0]
        curs.execute("UPDATE UBICACIONES SET Direccion = (?) WHERE Id = (?)", (ubicacion, id_ubicaciones,))
        connection.commit()
    if (telef != ''):
        id_telefonos = curs.execute("SELECT Id_TELEFONOS FROM AVES WHERE Id = (?)", (bird_id,)).fetchone()
        id_telefonos = id_telefonos[0]
        curs.execute("UPDATE TELEFONOS SET Telefono = (?) WHERE Id = (?)", (telef, id_telefonos,))
        connection.commit()

    #New image upload
    f = request.files['file']
    print(f)
    if request.files['file'].filename != '':
        #f.save(secure_filename(f.filename))
        base_path = os.path.abspath(os.path.dirname(__file__))
        upload_path = os.path.join(base_path, app.config['UPLOAD_FOLDER'])
        f.save(os.path.join(upload_path, secure_filename(f.filename)))
        image = secure_filename(f.filename)
        print(image, bird_id)
        connection = sqlite3.connect('proyecto.db')
        curs = connection.cursor()   
        curs.execute("UPDATE AVES SET Foto = (?) WHERE Id = (?)", (image, bird_id,))
        connection.commit()

    return redirect(url_for('profile'))

@app.route('/editplace', methods=['GET', 'POST'])
@login_required
def editplace():
    nombre = current_user.name

    #Get user Id
    user_id = current_user.get_id()
        
    if request.method == 'POST':
        #Get refugio Id
        refugio_id = request.form.get('editplace')
        session["refugio_id"] = refugio_id

        #Get DB data for this user's refugio Id
        connection = sqlite3.connect("proyecto.db")
        cur = get_db().cursor()
        ubicaciones = cur.execute("SELECT Id, Latitud, Longitud, Direccion \
                      FROM UBICACIONES WHERE Id IN (SELECT Id_UBICACIONES FROM \
                      REFUGIOS WHERE Id = (?))", (refugio_id,)).fetchall()
        refugios = cur.execute("SELECT Id, Id_USUARIOS, Id_UBICACIONES, Id_ESPECIES1, Id_ESPECIES2, Id_ESPECIES3, Id_ESPECIES4, Id_TELEFONOS, Id_TIPOREFUGIO1, Id_TIPOREFUGIO2 \
               FROM REFUGIOS WHERE Id = (?)", (refugio_id,)).fetchall()
        telefonos = cur.execute("SELECT Id, Telefono FROM TELEFONOS WHERE Id IN \
                (SELECT Id_TELEFONOS FROM REFUGIOS WHERE Id = (?))", (refugio_id,)).fetchall()
        get_db().commit()
    
        #Convert data from DB to dict type
        ubic_dict = helpers.make_dict(ubicaciones)
        refug_dict = helpers.make_dict(refugios)
        telef_dict = helpers.make_dict(telefonos)

        # Dict of types of refugees offered, ready to be displayed
        tipo_refugio = []
        if refug_dict:
            for i in range(len(refug_dict)):
                dict = refug_dict[str(i)]
                tipo_refugio.append(dict['Id_TIPOREFUGIO1'])
                tipo_refugio.append(dict['Id_TIPOREFUGIO2'])
        
        # Dict of species that the user can take care of, ready to be displayed
        especies_ref = []
        if refug_dict:
            for i in range(len(refug_dict)):
                dict = refug_dict[str(i)]
                especies_ref.append(dict['Id_ESPECIES1'])
                especies_ref.append(dict['Id_ESPECIES2'])
                especies_ref.append(dict['Id_ESPECIES3'])
                especies_ref.append(dict['Id_ESPECIES4'])

        return render_template('editplace.html', nombre=nombre, ubic_dict=ubic_dict,
       telef_dict=telef_dict, refug_dict=refug_dict, tipo_refugio=tipo_refugio,
       especies_ref=especies_ref)

@app.route('/editplace/updateplace', methods=['GET', 'POST'])
@login_required
def update_place():
    #Get user Id
    user_id = current_user.get_id()
    place_id = request.form.get('updateplace')

    tipoespecie = request.form.getlist('tipoespecie')
    tiporef = request.form.getlist('tiporef')
    ubicacion = request.form.get('ubicacion')
    telef = request.form.get('telef')

    connection = sqlite3.connect('proyecto.db')
    curs = connection.cursor()   

    #update accepted types of refuges
    tipoRef1 = 'NULL'
    tipoRef2 = 'NULL'
    for i in range (len(tiporef)):
        if tiporef[i] == 'hogar':
            tipoRef1 = 1 #Si tildó hogar, eso va a la col 1 de la DB
            if len(tiporef) > 1:
                tipoRef2 = 2 #Si tildó ambas opciones
                break
        elif tiporef[i] == 'transito':
            tipoRef1 = 2 #Si sólo tildó tránsito, eso va a la col 1
  
    curs.execute("UPDATE REFUGIOS SET Id_TIPOREFUGIO1 = (?), Id_TIPOREFUGIO2 = (?) WHERE Id = (?)", (tipoRef1, tipoRef2, place_id,))
    connection.commit()

    #update types of species accepted in refugees
    especie1 = 'NULL'
    especie2 = 'NULL'
    especie3 = 'NULL'
    especie4 = 'NULL'

    if tipoespecie[0] == 'paloma':
        especie1 = 1 #Si tildó paloma, eso va a la col 1 de la DB
        if len(tipoespecie) > 1:
            if tipoespecie[1] == 'peqsil':
                especie2 = 2 #Si además de paloma tildó peqsil, eso además va a la col 2
                if len(tipoespecie) > 2:
                    if tipoespecie[2] == 'medsil':
                        especie3 = 3  #Si además de paloma y peqsil tildó medsil, eso además va a la col 3
                        if len(tipoespecie) > 3:
                            if tipoespecie[3] == 'corral':
                                especie4 = 4  #Si además tildó corral, esto va en col 4                            
            elif tipoespecie[1] == 'medsil':
                especie2 = 3 #Si además de paloma tildó medsil, eso además va a la col 2
                if len(tipoespecie) > 2:
                    if tipoespecie[2] == 'corral':
                        especie3 = 4 #Si además de paloma y medsil tildó corral, este va a la col 3
            elif tipoespecie[1] == 'corral':
                especie2 = 4 #Si además de paloma tildó corral, eso además va a la col 2
    elif tipoespecie[0] == 'peqsil':
        especie1 = 2 #Si sólo tildó peqsil, eso va a la col 1
        if len(tipoespecie) > 1:
            if tipoespecie[1] == 'medsil':
                especie2 = 3  #Si además de paloma y peqsil tildó medsil, eso además va a la col 2
                if len(tipoespecie) > 2:
                    if tipoespecie[2] == 'corral':
                        especie3 = 4  #Si además tildó corral, esto va en col 3
            if tipoespecie[1] == 'corral':
                        especie2 = 4  #Si además tildó corral, esto va en col 2             
    elif tipoespecie[0] == 'medsil':
        especie1 = 3 #Si sólo tildó medsil, eso va a la col 1
        if len(tipoespecie) > 1:
            if tipoespecie[1] == 'corral':
                especie2 = 4  #Si además tildó corral, esto va en col 2
    elif tipoespecie[0] == 'corral':
        especie1 = 4 #Si sólo tildó corral, eso va a la col 1

    curs.execute("UPDATE REFUGIOS SET Id_ESPECIES1 = (?), Id_ESPECIES2 = (?), Id_ESPECIES3 = (?), Id_ESPECIES4 = (?) WHERE Id = (?)", (especie1, especie2, especie3, especie4, place_id,))
    connection.commit()

    #update ubicacion
    if (ubicacion != ''):
        id_ubicaciones = curs.execute("SELECT Id_UBICACIONES FROM REFUGIOS WHERE Id = (?)", (place_id,)).fetchone()
        id_ubicaciones = id_ubicaciones[0]
        curs.execute("UPDATE UBICACIONES SET Direccion = (?) WHERE Id = (?)", (ubicacion, id_ubicaciones,))
        connection.commit()
    
    #update teléfono
    if (telef != ''):
        id_telefonos = curs.execute("SELECT Id_TELEFONOS FROM REFUGIOS WHERE Id = (?)", (place_id,)).fetchone()
        id_telefonos = id_telefonos[0]
        curs.execute("UPDATE TELEFONOS SET Telefono = (?) WHERE Id = (?)", (telef, id_telefonos,))
        connection.commit()

    
    return redirect(url_for('profile'))

if __name__ == "__main__":
    app.run()