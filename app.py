import datetime
from flask import Flask, flash, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

app.secret_key = 'mapachespeludos_69'
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
    busqueda = request.args.get('busqueda', '').strip().lower()
    usuarios_ref = db.collection('usuarios').stream()
    
    usuarios_con_estado = []
    
    for doc in usuarios_ref:
        data = doc.to_dict()
        # Convertir campos a minúsculas para búsqueda
        nombre = data.get('Nombre_completo', '').lower()
        colonia = data.get('Colonia', '').lower()
        folio = data.get('Folio', '').lower()

        if not busqueda or (busqueda in nombre or busqueda in colonia or busqueda in folio):
            # Consulta para verificar si el usuario tiene pagos registrados
            pagos_ref = db.collection('pagos').where('Folio_usuario', '==', data['Folio']).limit(1).stream()
            pago_existe = next(pagos_ref, None)
            
            # Determinar el estado basado en si existe pago registrado
            estado = "Pagado" if pago_existe else "Debe"
            
            # Agregar el estado a los datos del usuario
            data['EstadoPago'] = estado
            usuarios_con_estado.append(data)
    
    return render_template('pagos.html', usuarios=usuarios_con_estado)

from datetime import datetime
from flask import render_template

@app.route('/registrar_pago/<folio>', methods=['GET', 'POST'])
def registrar_pago(folio):
    # Obtener usuario
    usuarios_ref = db.collection('usuarios').where('Folio', '==', folio).limit(1).stream()
    usuario = next(usuarios_ref, None)
    
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('pagos'))
    
    # Formatear fecha actual
    ahora = datetime.now()
    fecha_actual = ahora.strftime("%d de %B de %Y, %H:%M %p ")  # Ej: "30 de mayo de 2025, 12:00:00 a.m. UTC-6"
    fecha_actual_iso = ahora.isoformat()  # Para almacenar en la base de datos
    
    if request.method == 'POST':
        try:
            monto = float(request.form['monto'])
            meses_seleccionados = request.form.getlist('meses')
            fecha_pago = request.form['fecha_pago']
            
            if not meses_seleccionados:
                flash('Debe seleccionar al menos un mes', 'danger')
                return redirect(url_for('registrar_pago', folio=folio))
            
            # Registrar el pago
            pago_data = {
                'Folio_usuario': folio,
                'Monto': monto,
                'Estado_pago': 'Pagado',
                'Fecha_pago': fecha_actual,
                'Periodo': ', '.join(meses_seleccionados),
                'Timestamp': fecha_actual_iso
            }
            
            db.collection('pagos').add(pago_data)
            flash('Pago registrado exitosamente', 'success')
            return redirect(url_for('pagos'))
        
        except Exception as e:
            flash(f'Error al registrar pago: {str(e)}', 'danger')
    
    return render_template('registrar_pago.html', 
                         usuario=usuario.to_dict(),
                         fecha_actual=fecha_actual,
                         fecha_actual_iso=fecha_actual_iso)
if __name__ == '__main__':
    app.run(debug=True)
