from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from flask-cors import CORS

app = Flask(__name__)
CORS(app)

# Configurar MongoDB Atlas
client = MongoClient("mongodb+srv://honoka:honoka343@flaskapi.rvw7w.mongodb.net/")
db = client['sistema']
users_collection = db['empleados']

@app.route("/")
def index():
    return "API de Gestión de Asistencia"

@app.route('/user', methods=['POST'])
def add_user():
    data = request.get_json()
    
    new_user = {
        'nombre': data.get('nombre'),
        'apellidos': data.get('apellidos'),
        'email': data.get('email'),
        'telefono': data.get('telefono'),
        'asistencia': []
    }
    
    result = users_collection.insert_one(new_user)
    return jsonify({
        '_id': str(result.inserted_id),
        'nombre': new_user['nombre'],
        'apellidos': new_user['apellidos'],
        'email': new_user['email'],
        'telefono': new_user['telefono']
    }), 201

@app.route('/user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user_id = ObjectId(user_id)
    except InvalidId:
        return jsonify({"error": "ID de usuario inválido"}), 400
    
    user = users_collection.find_one({'_id': user_id})
    if user:
        user['_id'] = str(user['_id'])
        return jsonify(user)
    return jsonify({"error": "Usuario no encontrado"}), 404

@app.route('/user/<string:user_id>/entrada', methods=['POST'])
def registrar_entrada(user_id):
    try:
        user_id = ObjectId(user_id)
    except InvalidId:
        return jsonify({"error": "ID inválido"}), 400
    
    # Verificar última asistencia
    user = users_collection.find_one({'_id': user_id})
    if user and user['asistencia'] and user['asistencia'][-1]['salida'] is None:
        return jsonify({"error": "Debe registrar salida primero"}), 400
    
    users_collection.update_one(
        {'_id': user_id},
        {'$push': {'asistencia': {'entrada': datetime.now(), 'salida': None}}}
    )
    return jsonify({"mensaje": "Entrada registrada"}), 200

@app.route('/user/<string:user_id>/salida', methods=['POST'])
def registrar_salida(user_id):
    try:
        user_id = ObjectId(user_id)
    except InvalidId:
        return jsonify({"error": "ID inválido"}), 400
    
    result = users_collection.update_one(
        {'_id': user_id, 'asistencia.salida': None},
        {'$set': {'asistencia.$.salida': datetime.now()}}
    )
    
    if result.modified_count == 0:
        return jsonify({"error": "No hay entradas pendientes"}), 400
    return jsonify({"mensaje": "Salida registrada"}), 200

if __name__ == "__main__":
    app.run(debug=True)
