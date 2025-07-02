from flask import Flask, render_template, request, redirect
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Iniciar Firebase con el JSoN de configuración
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Ruta de menu principal
@app.route('/')
def menu():
    return render_template('menu.html')

# Ruta de pagina de usuarios
#Agregar restriciones de busqueda en numeros, CP...
@app.route('/usuarios')
def usuarios():
    busqueda = request.args.get('busqueda', '').strip().lower()
    usuarios_ref = db.collection('usuarios').stream()
    usuarios = []

    for doc in usuarios_ref:
        data = doc.to_dict()
        # Convertir campos a minúsculas
        nombre = data.get('Nombre_completo', '').lower()
        colonia = data.get('Colonia', '').lower()
        folio = data.get('Folio', '').lower()

        if not busqueda or (busqueda in nombre or busqueda in colonia or busqueda in folio):
            usuarios.append(data)
    return render_template('usuarios.html', usuarios=usuarios)


#Ruta de registro de usuarios
@app.route('/registrar_usuario', methods=['GET', 'POST'])
def registrar_usuario():
    if request.method == 'POST':
        data = {
            'Nombre_completo': request.form['nombre_completo'],
            'Curp': request.form['curp'],
            'Folio': request.form['folio'],
            'Numero_contacto': int(request.form['numero_contacto']),
            'Email': request.form['email'],
            'Direccion': request.form['direccion'],
            'Colonia': request.form['colonia'],
            'Codigo_postal': int(request.form['codigo_postal']),
            'Genero': request.form['genero'],
            'Estatus': request.form['estatus']
        }
        db.collection('usuarios').add(data)
        return redirect('/usuarios')
    return render_template('registrar_usuario.html')


# Ruta de edicion de usuarios
@app.route('/editar_usuario/<folio>', methods=['GET', 'POST'])
def editar_usuario(folio):
    usuarios_ref = db.collection('usuarios')
    query = usuarios_ref.where('Folio', '==', folio).limit(1).stream()
    doc = next(query, None)
# Complememtar
    if not doc:
        return "Usuario no encontrado", 404
    doc_id = doc.id
    usuario_data = doc.to_dict()

    if request.method == 'POST':
        nuevo_data = {
            'Nombre_completo': request.form['nombre_completo'],
            'Curp': request.form['curp'],
            'Folio': request.form['folio'],
            'Numero_contacto': int(request.form['numero_contacto']),
            'Email': request.form['email'],
            'Direccion': request.form['direccion'],
            'Colonia': request.form['colonia'],
            'Codigo_postal': int(request.form['codigo_postal']),
            'Genero': request.form['genero'],
            'Estatus': request.form['estatus']
        }
        db.collection('usuarios').document(doc_id).set(nuevo_data)
        return redirect('/usuarios')
    return render_template('editar_usuario.html', usuario=usuario_data)


# Ruta de eliminar de usuarios
@app.route('/eliminar_usuario/<folio>')
def eliminar_usuario(folio):
    usuarios_ref = db.collection('usuarios')
    query = usuarios_ref.where('Folio', '==', folio).limit(1).stream()
    doc = next(query, None)
    if doc:
        db.collection('usuarios').document(doc.id).delete()
    return redirect('/usuarios')


# Ruta de pagina de pagos
@app.route('/pagos')
def pagos():
    return render_template('pagos.html')

if __name__ == '__main__':
    app.run(debug=True)
