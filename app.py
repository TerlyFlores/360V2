import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'clave_secreta'


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'PayDeManzana$'
app.config['MYSQL_DB'] = 'tour_virtual'
mysql = MySQL(app)

IMAGES_FOLDER = 'static/images'

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    codigo = request.form['codigo']
    contraseña = request.form['contraseña']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, codigo FROM usuarios WHERE codigo=%s AND contraseña=%s", (codigo, contraseña))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user[0]
        session['codigo'] = user[1]

        if codigo == "A002": 
            return redirect(url_for('admin_utp360'))
        else:
            return redirect(url_for('listado_cursos'))
    else:
        return "Usuario o contraseña incorrectos", 401

@app.route('/admin_utp360')
def admin_utp360():
    if 'user_id' not in session or session['codigo'] != "A002":
        return redirect(url_for('login'))

    imagenes = os.listdir(IMAGES_FOLDER)
    imagenes = [img for img in imagenes if img.endswith('.jpg')]

    return render_template('admin_utp360.html', imagenes=imagenes)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'user_id' not in session or session['codigo'] != "A002":
        return redirect(url_for('login'))

    if 'image' not in request.files:
        return "No file part", 400

    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400

    if file and file.filename.endswith('.jpg'):
        file.save(os.path.join(IMAGES_FOLDER, file.filename))
        return redirect(url_for('admin_utp360'))
    else:
        return "Formato no permitido", 400

@app.route('/listado_cursos')
def listado_cursos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT c.id, c.nombre, c.horario
        FROM cursos c
        JOIN alumno_curso ac ON ac.id_curso = c.id
        WHERE ac.id_alumno = %s
    """, (session['user_id'],))
    cursos = cursor.fetchall()

    return render_template('listado_cursos.html', cursos=cursos)

@app.route('/detalle_curso/<int:curso_id>')
def detalle_curso(curso_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT c.nombre, c.horario, p.nombre AS profesor
        FROM cursos c
        LEFT JOIN usuarios p ON p.id = c.id_profesor
        WHERE c.id = %s
    """, (curso_id,))
    curso = cursor.fetchone()

    if curso:
        return render_template('detalle_curso.html', curso=curso)
    else:
        return "Curso no encontrado", 404

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/rename_image', methods=['POST'])
def rename_image():
    data = request.get_json()  
    
   
    if not data or 'old_name' not in data or 'new_name' not in data:
        return jsonify({'error': 'Faltan datos en la solicitud.'}), 400
    
    old_name = data['old_name']
    new_name = data['new_name']
    
   
    try:
        
        old_path = os.path.join('static/images', old_name)
        new_path = os.path.join('static/images', new_name)
        
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            return jsonify({'success': True, 'new_name': new_name}), 200
        else:
            return jsonify({'error': 'La imagen no existe.'}), 404
    except Exception as e:
        return jsonify({'error': f'Error al renombrar la imagen: {str(e)}'}), 500


@app.route('/delete_image', methods=['POST'])
def delete_image():
    if 'user_id' not in session or session['codigo'] != "A002":
        return redirect(url_for('login'))

    data = request.get_json()
    image_name = data.get('image_name')

    if not image_name:
        return jsonify({'status': 'error', 'message': 'Nombre de imagen no proporcionado'}), 400

    image_path = os.path.join(IMAGES_FOLDER, image_name)
    try:
        os.remove(image_path)
        return jsonify({'status': 'success', 'message': f'Imagen {image_name} eliminada con éxito.'})
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Imagen no encontrada.'}), 404


@app.route('/scan_qr')
def scan_qr():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('scan_qr.html')

@app.route('/process_qr', methods=['POST'])
def process_qr():
    data = request.get_json()
    aula_id = data.get('aula_id')

 
    if aula_id == 'valid_code':  
        image_path = 'path/to/image.jpg'  
        return jsonify({'status': 'success', 'image_path': image_path})
    else:
        return jsonify({'status': 'error'})
    
@app.route('/viewer')
def viewer():
    image_path = request.args.get('image_path')  
    if image_path:
        
        image_file = image_path  
        print(f"Intentando cargar la imagen desde: {image_file}")

       
        if os.path.exists(os.path.join('static', 'images', f'{image_file}.jpg')):
            return render_template('viewer.html', image_path=image_file)
        else:
            return render_template('error.html', error_message="Imagen no encontrada.")
    else:
        return render_template('error.html', error_message="No se proporcionó un nombre de imagen.")

if __name__ == '__main__':
    app.run(debug=True)
