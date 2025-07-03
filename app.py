import datetime
from flask import Flask, flash, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from flask import render_template

app = Flask(__name__)

app.secret_key = 'mapachespeludos_69'
MESES_COMPLETOS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]
# Iniciar Firebase con el JSoN de configuración
cred = credentials.Certificate("firebase_config.json")
# Inicializar la aplicación de Firebase
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
    todos_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    for doc in usuarios_ref:
        data = doc.to_dict()
        nombre = data.get('Nombre_completo', '').lower()
        colonia = data.get('Colonia', '').lower()
        folio = data.get('Folio', '').lower()

        if not busqueda or (busqueda in nombre or busqueda in colonia or busqueda in folio):
            # Obtener todos los pagos del usuario
            pagos_ref = db.collection('pagos').where('Folio_usuario', '==', data['Folio']).stream()
            
            meses_pagados = set()
            for pago in pagos_ref:
                pago_data = pago.to_dict()
                if 'Periodo' in pago_data:
                    meses_pago = pago_data['Periodo'].split(', ')
                    meses_pagados.update(meses_pago)
            
            # Determinar estado
            estado = 'Pagado' if len(meses_pagados) == len(todos_meses) else 'Debe'
            
            data['EstadoPago'] = estado
            usuarios_con_estado.append(data)
    
    return render_template('pagos.html', usuarios=usuarios_con_estado)


@app.route('/registrar_pago/<folio>', methods=['GET', 'POST'])
def registrar_pago(folio):
    # Obtener usuario
    usuarios_ref = db.collection('usuarios').where('Folio', '==', folio).limit(1).stream()
    usuario = next(usuarios_ref, None)
    
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('pagos'))
    
    # Obtener meses ya pagados
    pagos_ref = db.collection('pagos').where('Folio_usuario', '==', folio).stream()
    meses_pagados = set()
    
    for pago in pagos_ref:
        pago_data = pago.to_dict()
        if 'Periodo' in pago_data:
            meses_pago = pago_data['Periodo'].split(', ')
            meses_pagados.update(meses_pago)
    
    # Meses pendientes
    meses_pendientes = [mes for mes in MESES_COMPLETOS if mes not in meses_pagados]
    meses_seleccionados = []  # Inicializada aquí para todas las peticiones
    
    if request.method == 'POST':
        try:
            monto = float(request.form['monto'])
            meses_seleccionados = request.form.getlist('meses')  # Actualizada en POST
            
            # Validaciones
            if not meses_seleccionados:
                flash('Debe seleccionar al menos un mes', 'danger')
                return redirect(url_for('registrar_pago', folio=folio))
                
            for mes in meses_seleccionados:
                if mes not in meses_pendientes:
                    flash(f'El mes {mes} ya fue pagado anteriormente', 'danger')
                    return redirect(url_for('registrar_pago', folio=folio))
            
            # Registrar pago
            pago_data = {
                'Folio_usuario': folio,
                'Monto': monto,
                'Estado_pago': 'Completo' if len(meses_seleccionados) == len(meses_pendientes) else 'Parcial',
                'Fecha_pago': datetime.now().strftime("%d/%m/%Y, %H:%M"),
                'Periodo': ', '.join(meses_seleccionados),
                'Timestamp': datetime.now().isoformat()
            }
            
            db.collection('pagos').add(pago_data)
            
            # Mensaje de confirmación
            if len(meses_pagados) + len(meses_seleccionados) == len(MESES_COMPLETOS):
                flash('¡Pago completo registrado (todos los meses cubiertos)!', 'success')
            else:
                flash(f'Pago registrado para {len(meses_seleccionados)} mes(es)', 'success')
            
            return redirect(url_for('pagos'))
            
        except ValueError:
            flash('Monto inválido', 'danger')
        except Exception as e:
            flash(f'Error al registrar pago: {str(e)}', 'danger')
    
    return render_template('registrar_pago.html',
                         usuario=usuario.to_dict(),
                         meses=meses_pendientes,
                         fecha_actual=datetime.now().strftime("%d/%m/%Y, %H:%M"))





if __name__ == '__main__':
    app.run(debug=True)
