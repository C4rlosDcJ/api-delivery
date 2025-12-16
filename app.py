"""
================================================================================
API REST - DeliveryApp Backend
================================================================================

Descripcion:
    API REST principal para la aplicacion de delivery de alimentos.
    Proporciona endpoints para autenticacion, gestion de usuarios, restaurantes,
    platillos, pedidos, resenas, cupones, repartidores y notificaciones.

Tecnologias:
    - Flask: Framework web principal
    - Flask-JWT-Extended: Autenticacion basada en tokens JWT
    - Flask-CORS: Manejo de Cross-Origin Resource Sharing
    - PyMongo: Driver para conexion con MongoDB
    - Werkzeug: Utilidades de seguridad para hash de contrasenas

Base de Datos:
    MongoDB - Colecciones principales:
    - users: Usuarios del sistema (clientes, admins, owners, delivery)
    - restaurants: Informacion de restaurantes
    - dishes: Platillos disponibles
    - orders: Pedidos realizados
    - reviews: Resenas y calificaciones
    - coupons: Cupones de descuento
    - delivery_persons: Informacion de repartidores
    - notifications: Notificaciones del sistema
    - addresses: Direcciones de entrega
    - categories: Categorias de platillos

Version: 1.0.0
================================================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient, GEOSPHERE
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime, timedelta
import os
from functools import wraps
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACION DE LA APLICACION
# ============================================================================

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

CORS(app)
jwt = JWTManager(app)

# Conexión a MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['delivery']

# Colecciones
users_collection = db['users']
addresses_collection = db['addresses']
restaurants_collection = db['restaurants']
categories_collection = db['categories']
dishes_collection = db['dishes']
orders_collection = db['orders']
reviews_collection = db['reviews']
coupons_collection = db['coupons']
delivery_persons_collection = db['delivery_persons']
notifications_collection = db['notifications']

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def serialize_doc(doc):
    """
    Serializa documentos de MongoDB para respuestas JSON.
    
    Convierte tipos de datos especificos de MongoDB (ObjectId, datetime)
    a formatos compatibles con JSON. Maneja documentos anidados y listas
    de forma recursiva.
    
    Args:
        doc: Documento de MongoDB (dict), lista de documentos, o None.
    
    Returns:
        dict/list/None: Documento serializado listo para JSON.
        - ObjectId se convierte a string
        - datetime se convierte a formato ISO 8601
        - El campo '_id' se duplica como 'id' para compatibilidad frontend
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if key == '_id':
                # Duplicar _id como 'id' para compatibilidad con frontend
                serialized['id'] = str(value)  
                serialized['_id'] = str(value)  
            elif isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = serialize_doc(value)
            elif isinstance(value, list):
                serialized[key] = serialize_doc(value)
            else:
                serialized[key] = value
        return serialized
    return doc

def role_required(required_roles):
    """
    Decorador para restringir acceso a endpoints segun rol de usuario.
    
    Verifica que el usuario autenticado tenga uno de los roles permitidos
    antes de ejecutar la funcion decorada. Debe usarse junto con @jwt_required().
    
    Args:
        required_roles (list): Lista de roles permitidos (ej: ['admin', 'restaurant_owner'])
    
    Returns:
        function: Decorador que valida el rol del usuario.
    
    Raises:
        403 Forbidden: Si el usuario no tiene un rol permitido.
    
    Ejemplo:
        @app.route('/api/admin/resource')
        @jwt_required()
        @role_required(['admin'])
        def admin_only_resource():
            return jsonify({'data': 'solo para admins'})
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = users_collection.find_one({'_id': ObjectId(current_user_id)})
            
            if not user or user.get('role') not in required_roles:
                return jsonify({'message': 'Acceso denegado'}), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def generate_order_number():
    """
    Genera un numero de pedido unico con formato estandarizado.
    
    El formato es: ORD-YYYYMMDD-XXXX donde:
    - ORD: Prefijo de identificacion
    - YYYYMMDD: Fecha actual
    - XXXX: Numero secuencial del dia (con ceros a la izquierda)
    
    Returns:
        str: Numero de pedido unico (ej: 'ORD-20241210-0001')
    """
    today = datetime.now().strftime('%Y%m%d')
    count = orders_collection.count_documents({'orderNumber': {'$regex': f'^ORD-{today}'}})
    return f'ORD-{today}-{str(count + 1).zfill(4)}'

# ============================================================================
# RUTAS DE AUTENTICACIÓN
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Registro de nuevos usuarios"""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'Campo {field} es requerido'}), 400
        
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'message': 'El email ya está registrado'}), 409
        
        user = {
            'email': data['email'],
            'password': generate_password_hash(data['password']),
            'name': data['name'],
            'phone': data.get('phone', ''),
            'role': data.get('role', 'customer'),
            'avatar': data.get('avatar', ''),
            'isActive': True,
            'emailVerified': False,
            'phoneVerified': False,
            'preferences': {
                'notifications': True,
                'language': 'es',
                'theme': 'light'
            },
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'lastLogin': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user)
        user['_id'] = result.inserted_id
        
        token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name'],
                'phone': user.get('phone', ''),
                'role': user['role'],
                'avatar': user.get('avatar', '')
            }
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login de usuarios"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email y contraseña requeridos'}), 400
        
        user = users_collection.find_one({'email': data['email']})
        
        if not user:
            return jsonify({'message': 'Credenciales inválidas'}), 401
        
        if not check_password_hash(user['password'], data['password']):
            return jsonify({'message': 'Credenciales inválidas'}), 401
        
        if not user.get('isActive', True):
            return jsonify({'message': 'Cuenta desactivada'}), 403
        
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'lastLogin': datetime.utcnow()}}
        )
        
        token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'message': 'Login exitoso',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name'],
                'phone': user.get('phone', ''),
                'role': user['role'],
                'avatar': user.get('avatar', '')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtener información del usuario actual"""
    try:
        current_user_id = get_jwt_identity()
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        return jsonify(serialize_doc({
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'phone': user.get('phone', ''),
            'role': user['role'],
            'avatar': user.get('avatar', ''),
            'preferences': user.get('preferences', {})
        })), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE ADMINISTRACIÓN
# ============================================================================

@app.route('/api/admin/restaurants', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_all_restaurants_admin():
    try:
        restaurants = list(restaurants_collection.find())
        return jsonify([serialize_doc(r) for r in restaurants]), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/restaurants', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_restaurant_admin():
    try:
        data = request.get_json()
        # Basic validation
        if not data.get('name') or not data.get('phone'):
             return jsonify({'message': 'Nombre y teléfono son requeridos'}), 400

        coordinates = data.get('coordinates', [0, 0])
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            coordinates = [0, 0]

        new_restaurant = {
            'name': data['name'],
            'slug': data['name'].lower().replace(' ', '-'),
            'description': data.get('description', ''),
            'logo': data.get('logo', ''),
            'coverImage': data.get('coverImage', ''),
            'email': data.get('email', ''),
            'phone': data['phone'],
            'website': data.get('website', ''),
            'address': data.get('address', {}),
            'location': {
                'type': 'Point',
                'coordinates': coordinates
            },
            'isActive': data.get('isActive', True),
            'isOpen': data.get('isOpen', False),
            'workingHours': data.get('workingHours', []),
            'deliveryConfig': data.get('deliveryConfig', {
                'hasDelivery': True,
                'deliveryRadius': 5,
                'deliveryFee': 30,
                'minOrderAmount': 100,
                'estimatedDeliveryTime': '30-45 min'
            }),
            'cuisineTypes': data.get('cuisineTypes', []),
            'rating': 0,
            'totalReviews': 0,
            'totalOrders': 0,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        # Si se proporciona ownerId, asignarlo
        if data.get('ownerId'):
            new_restaurant['ownerId'] = ObjectId(data['ownerId'])
        
        result = restaurants_collection.insert_one(new_restaurant)
        new_restaurant['_id'] = result.inserted_id
        
        return jsonify(serialize_doc(new_restaurant)), 201
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/restaurants/<restaurant_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
def update_restaurant_admin(restaurant_id):
    try:
        data = request.get_json()
        
        update_data = {
            'updatedAt': datetime.utcnow()
        }
        
        # Actualizar campos básicos
        if 'name' in data:
            update_data['name'] = data['name']
            update_data['slug'] = data['name'].lower().replace(' ', '-')
        if 'description' in data:
            update_data['description'] = data.get('description', '')
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'email' in data:
            update_data['email'] = data.get('email', '')
        if 'website' in data:
            update_data['website'] = data.get('website', '')
        if 'logo' in data:
            update_data['logo'] = data.get('logo', '')
        if 'coverImage' in data:
            update_data['coverImage'] = data.get('coverImage', '')
        if 'address' in data:
            update_data['address'] = data['address']
        if 'coordinates' in data:
            coordinates = data['coordinates']
            if isinstance(coordinates, list) and len(coordinates) >= 2:
                update_data['location'] = {
                    'type': 'Point',
                    'coordinates': coordinates
                }
        if 'isActive' in data:
            update_data['isActive'] = data['isActive']
        if 'isOpen' in data:
            update_data['isOpen'] = data['isOpen']
        if 'deliveryConfig' in data:
            update_data['deliveryConfig'] = data['deliveryConfig']
        if 'cuisineTypes' in data:
            update_data['cuisineTypes'] = data['cuisineTypes']
        if 'ownerId' in data and data['ownerId']:
            update_data['ownerId'] = ObjectId(data['ownerId'])
        
        restaurants_collection.update_one({'_id': ObjectId(restaurant_id)}, {'$set': update_data})
        updated_restaurant = restaurants_collection.find_one({'_id': ObjectId(restaurant_id)})
        return jsonify(serialize_doc(updated_restaurant)), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/restaurants/<restaurant_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_restaurant_admin(restaurant_id):
    try:
        restaurants_collection.delete_one({'_id': ObjectId(restaurant_id)})
        return jsonify({'message': 'Restaurante eliminado exitosamente'}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE ADMINISTRACIÓN - USUARIOS
# ============================================================================

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_all_users_admin():
    """Obtener todos los usuarios (solo admin)"""
    try:
        users = list(users_collection.find())
        
        # Enriquecer usuarios con información de restaurantes si son owners
        for user in users:
            if user.get('role') == 'restaurant_owner':
                restaurant = restaurants_collection.find_one({'ownerId': user['_id']})
                if restaurant:
                    user['ownedRestaurantId'] = str(restaurant['_id'])
                    user['ownedRestaurantName'] = restaurant.get('name', '')
        
        return jsonify([serialize_doc(u) for u in users]), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/users', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_user_admin():
    """Crear nuevo usuario (solo admin)"""
    try:
        data = request.get_json()
        
        # Validación
        if not data.get('email') or not data.get('name'):
            return jsonify({'message': 'Email y nombre son requeridos'}), 400
        
        if not data.get('password'):
            return jsonify({'message': 'Contraseña es requerida'}), 400
        
        # Verificar si el email ya existe
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'message': 'El email ya está registrado'}), 409
        
        user = {
            'email': data['email'],
            'password': generate_password_hash(data['password']),
            'name': data['name'],
            'phone': data.get('phone', ''),
            'role': data.get('role', 'customer'),
            'avatar': data.get('avatar', ''),
            'isActive': data.get('isActive', True),
            'emailVerified': data.get('emailVerified', False),
            'phoneVerified': data.get('phoneVerified', False),
            'preferences': data.get('preferences', {
                'notifications': True,
                'language': 'es',
                'theme': 'light'
            }),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'lastLogin': None
        }
        
        result = users_collection.insert_one(user)
        user['_id'] = result.inserted_id
        
        # Si es restaurant_owner y tiene restaurantId, actualizar el restaurante
        if user['role'] == 'restaurant_owner' and data.get('restaurantId'):
            restaurants_collection.update_one(
                {'_id': ObjectId(data['restaurantId'])},
                {'$set': {'ownerId': user['_id']}}
            )
        
        return jsonify(serialize_doc(user)), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/users/<user_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
def update_user_admin(user_id):
    """Actualizar usuario (solo admin)"""
    try:
        data = request.get_json()
        
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        update_data = {
            'updatedAt': datetime.utcnow()
        }
        
        if 'name' in data:
            update_data['name'] = data['name']
        if 'email' in data:
            # Verificar si el nuevo email ya existe en otro usuario
            existing = users_collection.find_one({
                'email': data['email'],
                '_id': {'$ne': ObjectId(user_id)}
            })
            if existing:
                return jsonify({'message': 'El email ya está en uso'}), 409
            update_data['email'] = data['email']
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'role' in data:
            update_data['role'] = data['role']
        if 'isActive' in data:
            update_data['isActive'] = data['isActive']
        if 'avatar' in data:
            update_data['avatar'] = data.get('avatar', '')
        if 'emailVerified' in data:
            update_data['emailVerified'] = data['emailVerified']
        if 'phoneVerified' in data:
            update_data['phoneVerified'] = data['phoneVerified']
        if 'preferences' in data:
            update_data['preferences'] = data['preferences']
        if 'password' in data and data['password']:
            update_data['password'] = generate_password_hash(data['password'])
        
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        
        # Si es restaurant_owner y tiene restaurantId, actualizar el restaurante
        if data.get('role') == 'restaurant_owner' and data.get('restaurantId'):
            restaurants_collection.update_one(
                {'_id': ObjectId(data['restaurantId'])},
                {'$set': {'ownerId': ObjectId(user_id)}}
            )
        
        updated_user = users_collection.find_one({'_id': ObjectId(user_id)})
        return jsonify(serialize_doc(updated_user)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_user_admin(user_id):
    """Eliminar usuario (solo admin)"""
    try:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        # No permitir eliminar el último admin
        if user.get('role') == 'admin':
            admin_count = users_collection.count_documents({'role': 'admin'})
            if admin_count <= 1:
                return jsonify({'message': 'No se puede eliminar el último administrador'}), 400
        
        users_collection.delete_one({'_id': ObjectId(user_id)})
        return jsonify({'message': 'Usuario eliminado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE DIRECCIONES
# ============================================================================

@app.route('/api/addresses', methods=['GET'])
@jwt_required()
def get_addresses():
    """Obtener direcciones del usuario"""
    try:
        current_user_id = get_jwt_identity()
        addresses = list(addresses_collection.find({'userId': ObjectId(current_user_id)}))
        
        return jsonify({
            'addresses': serialize_doc(addresses),
            'total': len(addresses)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/addresses', methods=['POST'])
@jwt_required()
def create_address():
    """Crear nueva dirección"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if data.get('isDefault', False):
            addresses_collection.update_many(
                {'userId': ObjectId(current_user_id)},
                {'$set': {'isDefault': False}}
            )
        
        address = {
            'userId': ObjectId(current_user_id),
            'label': data.get('label', 'Casa'),
            'street': data['street'],
            'exteriorNumber': data.get('exteriorNumber', ''),
            'interiorNumber': data.get('interiorNumber', ''),
            'neighborhood': data.get('neighborhood', ''),
            'city': data['city'],
            'state': data['state'],
            'zipCode': data['zipCode'],
            'country': data.get('country', 'México'),
            'location': {
                'type': 'Point',
                'coordinates': data.get('coordinates', [0, 0])
            },
            'references': data.get('references', ''),
            'phoneContact': data.get('phoneContact', ''),
            'isDefault': data.get('isDefault', False),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = addresses_collection.insert_one(address)
        address['_id'] = result.inserted_id
        
        return jsonify({
            'message': 'Dirección creada exitosamente',
            'address': serialize_doc(address)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/addresses/<address_id>', methods=['PUT'])
@jwt_required()
def update_address(address_id):
    """Actualizar dirección"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        address = addresses_collection.find_one({
            '_id': ObjectId(address_id),
            'userId': ObjectId(current_user_id)
        })
        
        if not address:
            return jsonify({'message': 'Dirección no encontrada'}), 404
        
        if data.get('isDefault', False):
            addresses_collection.update_many(
                {'userId': ObjectId(current_user_id), '_id': {'$ne': ObjectId(address_id)}},
                {'$set': {'isDefault': False}}
            )
        
        update_data = {
            'label': data.get('label', address['label']),
            'street': data.get('street', address['street']),
            'exteriorNumber': data.get('exteriorNumber', address.get('exteriorNumber')),
            'interiorNumber': data.get('interiorNumber', address.get('interiorNumber')),
            'neighborhood': data.get('neighborhood', address.get('neighborhood')),
            'city': data.get('city', address['city']),
            'state': data.get('state', address['state']),
            'zipCode': data.get('zipCode', address['zipCode']),
            'references': data.get('references', address.get('references')),
            'phoneContact': data.get('phoneContact', address.get('phoneContact')),
            'isDefault': data.get('isDefault', address.get('isDefault')),
            'updatedAt': datetime.utcnow()
        }
        
        addresses_collection.update_one(
            {'_id': ObjectId(address_id)},
            {'$set': update_data}
        )
        
        return jsonify({'message': 'Dirección actualizada exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/addresses/<address_id>', methods=['DELETE'])
@jwt_required()
def delete_address(address_id):
    """Eliminar dirección"""
    try:
        current_user_id = get_jwt_identity()
        
        result = addresses_collection.delete_one({
            '_id': ObjectId(address_id),
            'userId': ObjectId(current_user_id)
        })
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Dirección no encontrada'}), 404
        
        city = request.args.get('city')
        cuisine_type = request.args.get('cuisine')
        is_open = request.args.get('isOpen')
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        max_distance = request.args.get('maxDistance', 5000, type=int)
        
        query = {'isActive': True}
        
        if city:
            query['address.city'] = city
        
        if cuisine_type:
            query['cuisineTypes'] = cuisine_type
        
        if is_open == 'true':
            query['isOpen'] = True
        
        if lat and lng:
            query['location'] = {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [lng, lat]
                    },
                    '$maxDistance': max_distance
                }
            }
        
        restaurants = list(restaurants_collection.find(query).sort('rating', -1).limit(50))
        
        return jsonify({
            'restaurants': serialize_doc(restaurants),
            'total': len(restaurants)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/restaurants/<restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    """Obtener un restaurante específico"""
    try:
        restaurant = restaurants_collection.find_one({'_id': ObjectId(restaurant_id)})
        
        if not restaurant:
            return jsonify({'message': 'Restaurante no encontrado'}), 404
        
        return jsonify(serialize_doc(restaurant)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/restaurants', methods=['POST'])
@jwt_required()
@role_required(['admin', 'restaurant_owner'])
def create_restaurant():
    """Crear nuevo restaurante"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        restaurant = {
            'ownerId': ObjectId(current_user_id),
            'name': data['name'],
            'slug': data['name'].lower().replace(' ', '-'),
            'description': data.get('description', ''),
            'logo': data.get('logo', ''),
            'coverImage': data.get('coverImage', ''),
            'email': data.get('email', ''),
            'phone': data['phone'],
            'website': data.get('website', ''),
            'address': data['address'],
            'location': {
                'type': 'Point',
                'coordinates': data.get('coordinates', [0, 0])
            },
            'isActive': True,
            'isOpen': False,
            'workingHours': data.get('workingHours', []),
            'deliveryConfig': data.get('deliveryConfig', {
                'hasDelivery': True,
                'deliveryRadius': 5,
                'deliveryFee': 30,
                'minOrderAmount': 100,
                'estimatedDeliveryTime': '30-45 min'
            }),
            'cuisineTypes': data.get('cuisineTypes', []),
            'rating': 0,
            'totalReviews': 0,
            'totalOrders': 0,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = restaurants_collection.insert_one(restaurant)
        restaurant['_id'] = result.inserted_id
        
        return jsonify({
            'message': 'Restaurante creado exitosamente',
            'restaurant': serialize_doc(restaurant)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/my/restaurants', methods=['GET'])
@jwt_required()
@role_required(['restaurant_owner'])
def get_my_restaurants():
    """Obtener restaurantes del usuario actual (restaurant_owner)"""
    try:
        current_user_id = get_jwt_identity()
        
        restaurants = list(restaurants_collection.find({'ownerId': ObjectId(current_user_id)}))
        
        return jsonify({
            'restaurants': serialize_doc(restaurants),
            'total': len(restaurants)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/my/restaurants/<restaurant_id>', methods=['PUT'])
@jwt_required()
@role_required(['restaurant_owner'])
def update_my_restaurant(restaurant_id):
    """Actualizar restaurante del usuario actual (restaurant_owner)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Verificar que el restaurante pertenece al usuario
        restaurant = restaurants_collection.find_one({
            '_id': ObjectId(restaurant_id),
            'ownerId': ObjectId(current_user_id)
        })
        
        if not restaurant:
            return jsonify({'message': 'Restaurante no encontrado o no tienes permiso'}), 404
        
        update_data = {
            'updatedAt': datetime.utcnow()
        }
        
        # Campos editables por el restaurant_owner
        if 'name' in data:
            update_data['name'] = data['name']
            update_data['slug'] = data['name'].lower().replace(' ', '-')
        if 'description' in data:
            update_data['description'] = data['description']
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'email' in data:
            update_data['email'] = data['email']
        if 'website' in data:
            update_data['website'] = data['website']
        if 'logo' in data:
            update_data['logo'] = data['logo']
        if 'coverImage' in data:
            update_data['coverImage'] = data['coverImage']
        if 'address' in data:
            update_data['address'] = data['address']
        if 'coordinates' in data:
            coordinates = data['coordinates']
            if isinstance(coordinates, list) and len(coordinates) >= 2:
                update_data['location'] = {
                    'type': 'Point',
                    'coordinates': coordinates
                }
        if 'isOpen' in data:
            update_data['isOpen'] = data['isOpen']
        if 'workingHours' in data:
            update_data['workingHours'] = data['workingHours']
        if 'deliveryConfig' in data:
            update_data['deliveryConfig'] = data['deliveryConfig']
        if 'cuisineTypes' in data:
            update_data['cuisineTypes'] = data['cuisineTypes']
        
        restaurants_collection.update_one(
            {'_id': ObjectId(restaurant_id)},
            {'$set': update_data}
        )
        
        updated_restaurant = restaurants_collection.find_one({'_id': ObjectId(restaurant_id)})
        
        return jsonify({
            'message': 'Restaurante actualizado exitosamente',
            'restaurant': serialize_doc(updated_restaurant)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE CATEGORÍAS
# ============================================================================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Obtener todas las categorías"""
    try:
        categories = list(categories_collection.find({'isActive': True}).sort('order', 1))
        
        return jsonify({
            'categories': serialize_doc(categories),
            'total': len(categories)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/categories', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_category():
    """Crear nueva categoría"""
    try:
        data = request.get_json()
        
        category = {
            'name': data['name'],
            'slug': data['name'].lower().replace(' ', '-'),
            'description': data.get('description', ''),
            'icon': data.get('icon', ''),
            'image': data.get('image', ''),
            'color': data.get('color', '#000000'),
            'isActive': True,
            'order': data.get('order', 0),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = categories_collection.insert_one(category)
        category['_id'] = result.inserted_id
        
        return jsonify({
            'message': 'Categoría creada exitosamente',
            'category': serialize_doc(category)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE PLATILLOS
# ============================================================================

@app.route('/api/dishes', methods=['GET'])
def get_dishes():
    """Obtener platillos con paginación"""
    try:
        restaurant_id = request.args.get('restaurantId')
        category_id = request.args.get('categoryId')
        search = request.args.get('search', '').lower()
        is_available = request.args.get('isAvailable')
        
        # Parámetros de paginación
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        
        query = {}
        
        if restaurant_id:
            query['restaurantId'] = ObjectId(restaurant_id)
        
        if category_id:
            query['categoryId'] = ObjectId(category_id)
        
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}}
            ]
        
        if is_available == 'true':
            query['isAvailable'] = True
        
        # Obtener total de documentos
        total = dishes_collection.count_documents(query)
        
        # Obtener platillos con paginación
        dishes = list(dishes_collection.find(query).sort('totalOrders', -1).skip(skip).limit(limit))
        
        # Enriquecer platillos con información del restaurante
        for dish in dishes:
            if dish.get('restaurantId'):
                restaurant = restaurants_collection.find_one({'_id': dish['restaurantId']})
                if restaurant:
                    dish['restaurant'] = {
                        'id': str(restaurant['_id']),
                        'name': restaurant.get('name', ''),
                        'logo': restaurant.get('logo', ''),
                        'rating': restaurant.get('rating', 0),
                        'totalReviews': restaurant.get('totalReviews', 0)
                    }
        
        return jsonify({
            'dishes': serialize_doc(dishes),
            'total': total,
            'page': page,
            'limit': limit,
            'hasMore': (skip + limit) < total,
            'totalPages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/dishes/<dish_id>', methods=['GET'])
def get_dish(dish_id):
    """Obtener un platillo específico con información del restaurante"""
    try:
        dish = dishes_collection.find_one({'_id': ObjectId(dish_id)})
        
        if not dish:
            return jsonify({'message': 'Platillo no encontrado'}), 404
        
        # Enriquecer con información del restaurante
        if dish.get('restaurantId'):
            restaurant = restaurants_collection.find_one({'_id': dish['restaurantId']})
            if restaurant:
                dish['restaurant'] = serialize_doc(restaurant)
        
        # Enriquecer con información de la categoría
        if dish.get('categoryId'):
            category = categories_collection.find_one({'_id': dish['categoryId']})
            if category:
                dish['category'] = serialize_doc(category)
        
        return jsonify(serialize_doc(dish)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/restaurants/<restaurant_id>/dishes', methods=['POST'])
@jwt_required()
@role_required(['admin', 'restaurant_owner'])
def create_dish(restaurant_id):
    """Crear nuevo platillo"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        restaurant = restaurants_collection.find_one({
            '_id': ObjectId(restaurant_id),
            'ownerId': ObjectId(current_user_id)
        })
        
        if not restaurant:
            return jsonify({'message': 'Restaurante no encontrado'}), 404
        
        dish = {
            'restaurantId': ObjectId(restaurant_id),
            'categoryId': ObjectId(data['categoryId']) if data.get('categoryId') else None,
            'name': data['name'],
            'slug': data['name'].lower().replace(' ', '-'),
            'description': data.get('description', ''),
            'images': data.get('images', []),
            'price': float(data['price']),
            'originalPrice': float(data.get('originalPrice', data['price'])),
            'discount': float(data.get('discount', 0)),
            'isAvailable': data.get('isAvailable', True),
            'isPopular': data.get('isPopular', False),
            'isFeatured': data.get('isFeatured', False),
            'stock': data.get('stock'),
            'calories': data.get('calories'),
            'preparationTime': data.get('preparationTime', ''),
            'servingSize': data.get('servingSize', ''),
            'customizations': data.get('customizations', []),
            'tags': data.get('tags', []),
            'allergens': data.get('allergens', []),
            'rating': 0,
            'totalReviews': 0,
            'totalOrders': 0,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = dishes_collection.insert_one(dish)
        dish['_id'] = result.inserted_id
        
        return jsonify({
            'message': 'Platillo creado exitosamente',
            'dish': serialize_doc(dish)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/dishes/<dish_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'restaurant_owner'])
def update_dish(dish_id):
    """Actualizar platillo"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        dish = dishes_collection.find_one({'_id': ObjectId(dish_id)})
        if not dish:
            return jsonify({'message': 'Platillo no encontrado'}), 404
        
        restaurant = restaurants_collection.find_one({
            '_id': dish['restaurantId'],
            'ownerId': ObjectId(current_user_id)
        })
        
        if not restaurant:
            return jsonify({'message': 'No tienes permiso para editar este platillo'}), 403
        
        update_data = {
            'name': data.get('name', dish['name']),
            'description': data.get('description', dish.get('description')),
            'price': float(data.get('price', dish['price'])),
            'isAvailable': data.get('isAvailable', dish.get('isAvailable')),
            'updatedAt': datetime.utcnow()
        }
        
        dishes_collection.update_one(
            {'_id': ObjectId(dish_id)},
            {'$set': update_data}
        )
        
        return jsonify({'message': 'Platillo actualizado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE PEDIDOS
# ============================================================================

@app.route('/api/orders', methods=['POST'])
@jwt_required()
def create_order():
    """Crear nuevo pedido"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('items') or len(data['items']) == 0:
            return jsonify({'message': 'El pedido debe tener al menos un item'}), 400
        
        if not data.get('deliveryAddress'):
            return jsonify({'message': 'Dirección de entrega requerida'}), 400
        
        subtotal = sum(item['subtotal'] for item in data['items'])
        delivery_fee = data.get('deliveryFee', 35)
        discount = data.get('discount', 0)
        tax = subtotal * 0.16
        tip = data.get('tip', 0)
        total = subtotal + delivery_fee - discount + tax + tip
        
        order = {
            'orderNumber': generate_order_number(),
            'customerId': ObjectId(current_user_id),
            'restaurantId': ObjectId(data['items'][0].get('restaurantId')),
            'items': data['items'],
            'deliveryAddress': data['deliveryAddress'],
            'subtotal': round(subtotal, 2),
            'deliveryFee': round(delivery_fee, 2),
            'discount': round(discount, 2),
            'tax': round(tax, 2),
            'tip': round(tip, 2),
            'total': round(total, 2),
            'coupon': data.get('coupon'),
            'status': 'pending',
            'statusHistory': [
                {
                    'status': 'pending',
                    'timestamp': datetime.utcnow(),
                    'note': 'Pedido recibido'
                }
            ],
            'paymentMethod': data.get('paymentMethod', 'cash'),
            'paymentStatus': 'pending',
            'estimatedDeliveryTime': data.get('estimatedDeliveryTime', '30-45 min'),
            'customerNotes': data.get('customerNotes', ''),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = orders_collection.insert_one(order)
        order['_id'] = result.inserted_id
        
        restaurants_collection.update_one(
            {'_id': order['restaurantId']},
            {'$inc': {'totalOrders': 1}}
        )
        
        for item in data['items']:
            if 'dishId' in item:
                dishes_collection.update_one(
                    {'_id': ObjectId(item['dishId'])},
                    {'$inc': {'totalOrders': item['quantity']}}
                )
        
        notifications_collection.insert_one({
            'userId': ObjectId(current_user_id),
            'type': 'order',
            'title': 'Pedido confirmado',
            'message': f'Tu pedido {order["orderNumber"]} ha sido recibido',
            'data': {
                'orderId': str(order['_id']),
                'orderNumber': order['orderNumber']
            },
            'isRead': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({
            'message': 'Pedido creado exitosamente',
            'order': serialize_doc(order)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Obtener pedidos del usuario"""
    try:
        current_user_id = get_jwt_identity()
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        query = {}
        
        if user['role'] == 'customer':
            query['customerId'] = ObjectId(current_user_id)
        elif user['role'] == 'restaurant_owner':
            restaurant_ids = [r['_id'] for r in restaurants_collection.find({'ownerId': ObjectId(current_user_id)})]
            query['restaurantId'] = {'$in': restaurant_ids}
        elif user['role'] == 'delivery':
            query['deliveryPersonId'] = ObjectId(current_user_id)
        
        status = request.args.get('status')
        if status:
            query['status'] = status
        
        orders = list(orders_collection.find(query).sort('createdAt', -1).limit(50))
        
        return jsonify({
            'orders': serialize_doc(orders),
            'total': len(orders)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Obtener un pedido específico"""
    try:
        current_user_id = get_jwt_identity()
        order = orders_collection.find_one({'_id': ObjectId(order_id)})
        
        if not order:
            return jsonify({'message': 'Pedido no encontrado'}), 404
        
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        if user['role'] == 'customer' and str(order['customerId']) != current_user_id:
            return jsonify({'message': 'No tienes permiso para ver este pedido'}), 403
        
        return jsonify(serialize_doc(order)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/orders/<order_id>/status', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'restaurant_owner', 'delivery'])
def update_order_status(order_id):
    """Actualizar estado del pedido"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'message': 'Estado requerido'}), 400
        
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'on_delivery', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'message': 'Estado inválido'}), 400
        
        order = orders_collection.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'message': 'Pedido no encontrado'}), 404
        
        update_data = {
            'status': new_status,
            'updatedAt': datetime.utcnow()
        }
        
        if new_status == 'confirmed':
            update_data['confirmedAt'] = datetime.utcnow()
        elif new_status == 'preparing':
            update_data['preparingAt'] = datetime.utcnow()
        elif new_status == 'ready':
            update_data['readyAt'] = datetime.utcnow()
        elif new_status == 'on_delivery':
            update_data['onDeliveryAt'] = datetime.utcnow()
        elif new_status == 'delivered':
            update_data['deliveredAt'] = datetime.utcnow()
            update_data['paymentStatus'] = 'paid'
        
        orders_collection.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': update_data,
                '$push': {
                    'statusHistory': {
                        'status': new_status,
                        'timestamp': datetime.utcnow(),
                        'note': data.get('note', '')
                    }
                }
            }
        )
        
        notification_messages = {
            'confirmed': 'Tu pedido ha sido confirmado',
            'preparing': 'Tu pedido está siendo preparado',
            'ready': 'Tu pedido está listo',
            'on_delivery': 'Tu pedido está en camino',
            'delivered': 'Tu pedido ha sido entregado',
            'cancelled': 'Tu pedido ha sido cancelado'
        }
        
        notifications_collection.insert_one({
            'userId': order['customerId'],
            'type': 'order',
            'title': f'Pedido {order["orderNumber"]}',
            'message': notification_messages.get(new_status, 'Estado actualizado'),
            'data': {
                'orderId': str(order['_id']),
                'orderNumber': order['orderNumber'],
                'status': new_status
            },
            'isRead': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({'message': 'Estado actualizado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/orders/<order_id>/assign-delivery', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'restaurant_owner'])
def assign_delivery_person(order_id):
    """Asignar repartidor a un pedido"""
    try:
        data = request.get_json()
        delivery_person_id = data.get('deliveryPersonId')
        
        if not delivery_person_id:
            return jsonify({'message': 'ID de repartidor requerido'}), 400
        
        delivery_person = delivery_persons_collection.find_one({
            '_id': ObjectId(delivery_person_id),
            'isAvailable': True,
            'isOnline': True
        })
        
        if not delivery_person:
            return jsonify({'message': 'Repartidor no disponible'}), 404
        
        orders_collection.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'deliveryPersonId': ObjectId(delivery_person_id),
                    'status': 'on_delivery',
                    'onDeliveryAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        delivery_persons_collection.update_one(
            {'_id': ObjectId(delivery_person_id)},
            {'$set': {'isAvailable': False}}
        )
        
        return jsonify({'message': 'Repartidor asignado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE RESEÑAS
# ============================================================================

@app.route('/api/reviews', methods=['POST'])
@jwt_required()
def create_review():
    """Crear nueva reseña"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        order = orders_collection.find_one({
            '_id': ObjectId(data['orderId']),
            'customerId': ObjectId(current_user_id),
            'status': 'delivered'
        })
        
        if not order:
            return jsonify({'message': 'Pedido no encontrado o no entregado'}), 404
        
        existing_review = reviews_collection.find_one({'orderId': ObjectId(data['orderId'])})
        if existing_review:
            return jsonify({'message': 'Ya has calificado este pedido'}), 400
        
        overall_rating = (data['foodRating'] + data['deliveryRating']) / 2
        
        review = {
            'orderId': ObjectId(data['orderId']),
            'customerId': ObjectId(current_user_id),
            'restaurantId': order['restaurantId'],
            'dishId': ObjectId(data['dishId']) if data.get('dishId') else None,
            'foodRating': data['foodRating'],
            'deliveryRating': data['deliveryRating'],
            'overallRating': round(overall_rating, 1),
            'comment': data.get('comment', ''),
            'images': data.get('images', []),
            'isVerified': True,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = reviews_collection.insert_one(review)
        review['_id'] = result.inserted_id
        
        orders_collection.update_one(
            {'_id': ObjectId(data['orderId'])},
            {
                '$set': {
                    'rating': {
                        'foodRating': data['foodRating'],
                        'deliveryRating': data['deliveryRating'],
                        'comment': data.get('comment', ''),
                        'ratedAt': datetime.utcnow()
                    }
                }
            }
        )
        
        restaurant_reviews = list(reviews_collection.find({'restaurantId': order['restaurantId']}))
        if restaurant_reviews:
            avg_rating = sum(r['overallRating'] for r in restaurant_reviews) / len(restaurant_reviews)
            restaurants_collection.update_one(
                {'_id': order['restaurantId']},
                {
                    '$set': {'rating': round(avg_rating, 1)},
                    '$inc': {'totalReviews': 1}
                }
            )
        
        if data.get('dishId'):
            dish_reviews = list(reviews_collection.find({'dishId': ObjectId(data['dishId'])}))
            if dish_reviews:
                avg_dish_rating = sum(r['foodRating'] for r in dish_reviews) / len(dish_reviews)
                dishes_collection.update_one(
                    {'_id': ObjectId(data['dishId'])},
                    {
                        '$set': {'rating': round(avg_dish_rating, 1)},
                        '$inc': {'totalReviews': 1}
                    }
                )
        
        return jsonify({
            'message': 'Reseña creada exitosamente',
            'review': serialize_doc(review)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/restaurants/<restaurant_id>/reviews', methods=['GET'])
def get_restaurant_reviews(restaurant_id):
    """Obtener reseñas de un restaurante"""
    try:
        reviews = list(reviews_collection.find(
            {'restaurantId': ObjectId(restaurant_id)}
        ).sort('createdAt', -1).limit(50))
        
        return jsonify({
            'reviews': serialize_doc(reviews),
            'total': len(reviews)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE CUPONES
# ============================================================================

@app.route('/api/coupons/validate', methods=['POST'])
@jwt_required()
def validate_coupon():
    """Validar cupón de descuento"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        code = data.get('code', '').upper()
        order_amount = data.get('orderAmount', 0)
        restaurant_id = data.get('restaurantId')
        
        if not code:
            return jsonify({'message': 'Código de cupón requerido'}), 400
        
        coupon = coupons_collection.find_one({
            'code': code,
            'isActive': True
        })
        
        if not coupon:
            return jsonify({'message': 'Cupón no válido'}), 404
        
        now = datetime.utcnow()
        if coupon.get('validFrom') and now < coupon['validFrom']:
            return jsonify({'message': 'Cupón aún no es válido'}), 400
        
        if coupon.get('validUntil') and now > coupon['validUntil']:
            return jsonify({'message': 'Cupón expirado'}), 400
        
        if coupon.get('usageLimit') and coupon.get('usageCount', 0) >= coupon['usageLimit']:
            return jsonify({'message': 'Cupón agotado'}), 400
        
        if coupon.get('minOrderAmount', 0) > order_amount:
            return jsonify({
                'message': f'Monto mínimo de ${coupon["minOrderAmount"]} requerido'
            }), 400
        
        if coupon.get('isForNewUsersOnly'):
            user_orders = orders_collection.count_documents({'customerId': ObjectId(current_user_id)})
            if user_orders > 0:
                return jsonify({'message': 'Este cupón es solo para nuevos usuarios'}), 400
        
        if coupon.get('applicableTo') == 'specific_restaurants':
            restaurant_ids = [ObjectId(rid) for rid in coupon.get('restaurantIds', [])]
            if ObjectId(restaurant_id) not in restaurant_ids:
                return jsonify({'message': 'Cupón no válido para este restaurante'}), 400
        
        discount = 0
        if coupon['discountType'] == 'percentage':
            discount = order_amount * (coupon['discountValue'] / 100)
        else:
            discount = coupon['discountValue']
        
        if coupon.get('maxDiscountAmount'):
            discount = min(discount, coupon['maxDiscountAmount'])
        
        return jsonify({
            'valid': True,
            'discount': round(discount, 2),
            'coupon': {
                'code': coupon['code'],
                'description': coupon.get('description', ''),
                'discountType': coupon['discountType'],
                'discountValue': coupon['discountValue']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/coupons', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_coupon():
    """Crear nuevo cupón"""
    try:
        data = request.get_json()
        
        coupon = {
            'code': data['code'].upper(),
            'description': data.get('description', ''),
            'discountType': data['discountType'],
            'discountValue': float(data['discountValue']),
            'minOrderAmount': float(data.get('minOrderAmount', 0)),
            'maxDiscountAmount': float(data.get('maxDiscountAmount', 0)) if data.get('maxDiscountAmount') else None,
            'usageLimit': data.get('usageLimit'),
            'usageCount': 0,
            'validFrom': datetime.fromisoformat(data['validFrom']) if data.get('validFrom') else datetime.utcnow(),
            'validUntil': datetime.fromisoformat(data['validUntil']) if data.get('validUntil') else None,
            'isActive': True,
            'applicableTo': data.get('applicableTo', 'all'),
            'restaurantIds': data.get('restaurantIds', []),
            'categoryIds': data.get('categoryIds', []),
            'isForNewUsersOnly': data.get('isForNewUsersOnly', False),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = coupons_collection.insert_one(coupon)
        coupon['_id'] = result.inserted_id
        
        return jsonify({
            'message': 'Cupón creado exitosamente',
            'coupon': serialize_doc(coupon)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE REPARTIDORES
# ============================================================================

@app.route('/api/delivery-persons', methods=['GET'])
@jwt_required()
@role_required(['admin', 'restaurant_owner'])
def get_delivery_persons():
    """Obtener repartidores disponibles"""
    try:
        is_available = request.args.get('isAvailable')
        is_online = request.args.get('isOnline')
        
        query = {}
        if is_available == 'true':
            query['isAvailable'] = True
        if is_online == 'true':
            query['isOnline'] = True
        
        delivery_persons = list(delivery_persons_collection.find(query).sort('rating', -1))
        
        for dp in delivery_persons:
            user = users_collection.find_one({'_id': dp['userId']})
            if user:
                dp['user'] = {
                    'name': user['name'],
                    'phone': user['phone'],
                    'avatar': user.get('avatar', '')
                }
        
        return jsonify({
            'deliveryPersons': serialize_doc(delivery_persons),
            'total': len(delivery_persons)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/delivery-persons/register', methods=['POST'])
@jwt_required()
def register_as_delivery():
    """Registrarse como repartidor"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        existing = delivery_persons_collection.find_one({'userId': ObjectId(current_user_id)})
        if existing:
            return jsonify({'message': 'Ya estás registrado como repartidor'}), 400
        
        delivery_person = {
            'userId': ObjectId(current_user_id),
            'vehicleType': data['vehicleType'],
            'vehiclePlate': data.get('vehiclePlate', ''),
            'vehicleModel': data.get('vehicleModel', ''),
            'vehicleColor': data.get('vehicleColor', ''),
            'driverLicense': data.get('driverLicense', ''),
            'vehicleRegistration': data.get('vehicleRegistration', ''),
            'insurance': data.get('insurance', ''),
            'isAvailable': False,
            'isOnline': False,
            'isVerified': False,
            'currentLocation': {
                'type': 'Point',
                'coordinates': [0, 0]
            },
            'workingZones': data.get('workingZones', []),
            'totalDeliveries': 0,
            'rating': 0,
            'totalReviews': 0,
            'earnings': {
                'today': 0,
                'week': 0,
                'month': 0,
                'total': 0
            },
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = delivery_persons_collection.insert_one(delivery_person)
        delivery_person['_id'] = result.inserted_id
        
        users_collection.update_one(
            {'_id': ObjectId(current_user_id)},
            {'$set': {'role': 'delivery'}}
        )
        
        return jsonify({
            'message': 'Registro como repartidor exitoso',
            'deliveryPerson': serialize_doc(delivery_person)
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/delivery-persons/status', methods=['PUT'])
@jwt_required()
@role_required(['delivery'])
def update_delivery_status():
    """Actualizar estado de disponibilidad del repartidor"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        delivery_person = delivery_persons_collection.find_one({'userId': ObjectId(current_user_id)})
        if not delivery_person:
            return jsonify({'message': 'No estás registrado como repartidor'}), 404
        
        update_data = {}
        if 'isAvailable' in data:
            update_data['isAvailable'] = data['isAvailable']
        if 'isOnline' in data:
            update_data['isOnline'] = data['isOnline']
        
        if update_data:
            update_data['updatedAt'] = datetime.utcnow()
            delivery_persons_collection.update_one(
                {'_id': delivery_person['_id']},
                {'$set': update_data}
            )
        
        return jsonify({'message': 'Estado actualizado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/delivery-persons/location', methods=['PUT'])
@jwt_required()
@role_required(['delivery'])
def update_delivery_location():
    """Actualizar ubicación del repartidor"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('coordinates') or len(data['coordinates']) != 2:
            return jsonify({'message': 'Coordenadas inválidas'}), 400
        
        delivery_persons_collection.update_one(
            {'userId': ObjectId(current_user_id)},
            {
                '$set': {
                    'currentLocation': {
                        'type': 'Point',
                        'coordinates': data['coordinates']
                    },
                    'lastLocationUpdate': datetime.utcnow()
                }
            }
        )
        
        return jsonify({'message': 'Ubicación actualizada'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE PEDIDOS PARA REPARTIDORES
# ============================================================================
@app.route('/api/delivery/orders/available', methods=['GET'])
@jwt_required()
def get_available_delivery_orders():
    """Obtener pedidos disponibles para repartidores (sin asignar)"""
    try:
        current_user_id = get_jwt_identity()
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        if user['role'] != 'delivery':
            return jsonify({'message': 'Acceso denegado'}), 403
        
        query = {
            '$or': [
                {'deliveryPersonId': {'$exists': False}},
                {'deliveryPersonId': None}
            ],
            'status': {'$in': ['pending', 'confirmed', 'preparing', 'ready']}
        }
        
        orders = list(orders_collection.find(query).sort('createdAt', -1).limit(50))
        
        return jsonify({
            'orders': serialize_doc(orders),
            'total': len(orders)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
@app.route('/api/delivery/orders/<order_id>/accept', methods=['POST'])
@jwt_required()
@role_required(['delivery'])
def accept_delivery_order(order_id):
    """Aceptar un pedido y cambiar estado a 'on_delivery'"""
    try:
        current_user_id = get_jwt_identity()
        
        order = orders_collection.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'message': 'Pedido no encontrado'}), 404
        
        if order.get('deliveryPersonId'):
            return jsonify({'message': 'Pedido ya asignado a otro repartidor'}), 400
        
        orders_collection.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'deliveryPersonId': ObjectId(current_user_id),
                    'status': 'on_delivery',
                    'acceptedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        return jsonify({'message': 'Pedido aceptado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
@app.route('/api/orders/<order_id>/confirm-delivery', methods=['PUT'])
@jwt_required()
@role_required(['delivery'])
def confirm_delivery(order_id):
    """Repartidor confirma que entregó el pedido"""
    try:
        current_user_id = get_jwt_identity()
        
        order = orders_collection.find_one({
            '_id': ObjectId(order_id),
            'deliveryPersonId': ObjectId(current_user_id)
        })
        
        if not order:
            return jsonify({'message': 'Pedido no encontrado o no asignado a ti'}), 404
        
        # Actualizar estado y agregar al historial
        orders_collection.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': 'delivering_confirmation',
                    'deliveredAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                },
                '$push': {
                    'statusHistory': {
                        'status': 'delivering_confirmation',
                        'timestamp': datetime.utcnow(),
                        'note': 'Repartidor confirmó la entrega, esperando confirmación del cliente'
                    }
                }
            }
        )
        
        # Crear notificación para el cliente
        notifications_collection.insert_one({
            'userId': order['customerId'],
            'type': 'order',
            'title': f'Pedido {order.get("orderNumber", "")} entregado',
            'message': 'El repartidor confirmó la entrega. Por favor confirma que recibiste tu pedido.',
            'data': {
                'orderId': str(order['_id']),
                'orderNumber': order.get('orderNumber', ''),
                'status': 'delivering_confirmation'
            },
            'isRead': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({'message': 'Entrega confirmada, esperando confirmación del cliente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
@app.route('/api/orders/<order_id>/confirm-received', methods=['PUT'])
@jwt_required()
def confirm_received(order_id):
    """Cliente confirma que recibió el pedido - Solo el cliente que hizo el pedido puede confirmar"""
    try:
        current_user_id = get_jwt_identity()
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        # Verificar que el usuario es un cliente
        if not user or user.get('role') != 'customer':
            return jsonify({'message': 'Solo los clientes pueden confirmar la recepción del pedido'}), 403
        
        # Primero verificar que el pedido existe
        order = orders_collection.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'message': 'Pedido no encontrado'}), 404
        
        # Verificar que el pedido pertenece al cliente actual
        if str(order.get('customerId')) != current_user_id:
            return jsonify({'message': 'No tienes permiso para confirmar este pedido. Solo el cliente que realizó el pedido puede confirmar la recepción.'}), 403
        
        # Verificar que el estado es delivering_confirmation (el repartidor ya marcó como entregado)
        if order.get('status') != 'delivering_confirmation':
            return jsonify({'message': 'El pedido no está en estado de confirmación de entrega. El repartidor debe confirmar la entrega primero.'}), 400
        
        # Verificar que el pedido tiene un repartidor asignado (el repartidor ya confirmó)
        if not order.get('deliveryPersonId'):
            return jsonify({'message': 'El pedido no tiene un repartidor asignado. El repartidor debe confirmar la entrega primero.'}), 400
        
        # Actualizar estado y agregar al historial
        orders_collection.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': 'delivered',
                    'receivedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow(),
                    'paymentStatus': 'paid'
                },
                '$push': {
                    'statusHistory': {
                        'status': 'delivered',
                        'timestamp': datetime.utcnow(),
                        'note': 'Cliente confirmó la recepción del pedido'
                    }
                }
            }
        )
        
        # Crear notificación para el repartidor
        if order.get('deliveryPersonId'):
            notifications_collection.insert_one({
                'userId': order['deliveryPersonId'],
                'type': 'order',
                'title': f'Pedido {order.get("orderNumber", "")} completado',
                'message': 'El cliente confirmó la recepción del pedido. ¡Gracias por tu entrega!',
                'data': {
                    'orderId': str(order['_id']),
                    'orderNumber': order.get('orderNumber', ''),
                    'status': 'delivered'
                },
                'isRead': False,
                'createdAt': datetime.utcnow()
            })
        
        return jsonify({'message': 'Pedido marcado como entregado'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
@app.route('/api/orders/<order_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_order(order_id):
    """Cancelar un pedido"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        reason = data.get('reason', 'Sin razón especificada')
        cancelled_by = data.get('cancelled_by', 'customer')
        
        order = orders_collection.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'message': 'Pedido no encontrado'}), 404
        
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        if cancelled_by == 'customer' and str(order['customerId']) != current_user_id:
            return jsonify({'message': 'No autorizado'}), 403
        elif cancelled_by == 'delivery' and str(order.get('deliveryPersonId', '')) != current_user_id:
            return jsonify({'message': 'No autorizado'}), 403
        
        orders_collection.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': 'cancelled',
                    'cancellationReason': reason,
                    'cancelledBy': cancelled_by,
                    'cancelledAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        return jsonify({'message': 'Pedido cancelado exitosamente'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
@app.route('/api/orders/<order_id>/track', methods=['GET'])
@jwt_required()
def track_order(order_id):
    """Obtener ubicación del repartidor en tiempo real"""
    try:
        current_user_id = get_jwt_identity()
        
        order = orders_collection.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'message': 'Pedido no encontrado'}), 404
        
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        is_customer = str(order.get('customerId')) == current_user_id
        is_delivery = str(order.get('deliveryPersonId')) == current_user_id
        is_admin = user.get('role') == 'admin'
        
        if not (is_customer or is_delivery or is_admin):
            return jsonify({'message': 'No autorizado para ver este pedido'}), 403
        
        delivery_person_info = None
        if order.get('deliveryPersonId'):
            delivery_person = delivery_persons_collection.find_one({
                'userId': order['deliveryPersonId']
            })
            
            if delivery_person:
                delivery_user = users_collection.find_one({'_id': order['deliveryPersonId']})
                
                delivery_person_info = {
                    'id': str(delivery_person['_id']),
                    'name': delivery_user.get('name', 'Repartidor') if delivery_user else 'Repartidor',
                    'phone': delivery_user.get('phone', '') if delivery_user else '',
                    'avatar': delivery_user.get('avatar', '') if delivery_user else '',
                    'vehicleType': delivery_person.get('vehicleType', ''),
                    'vehiclePlate': delivery_person.get('vehiclePlate', ''),
                    'rating': delivery_person.get('rating', 0),
                    'currentLocation': delivery_person.get('currentLocation', {
                        'type': 'Point',
                        'coordinates': [0, 0]
                    }),
                    'lastLocationUpdate': delivery_person.get('lastLocationUpdate')
                }
        
        response_data = {
            'orderId': str(order['_id']),
            'orderNumber': order.get('orderNumber', ''),
            'status': order.get('status', ''),
            'deliveryPerson': serialize_doc(delivery_person_info),
            'restaurant': {
                'name': order.get('restaurant', {}).get('name', ''),
                'address': order.get('restaurant', {}).get('address', ''),
                'coordinates': order.get('restaurant', {}).get('coordinates', [0, 0])
            },
            'deliveryAddress': order.get('address', {}),
            'estimatedDeliveryTime': order.get('estimatedDeliveryTime'),
            'acceptedAt': order.get('acceptedAt'),
            'deliveredAt': order.get('deliveredAt')
        }
        
        return jsonify(serialize_doc(response_data)), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE NOTIFICACIONES
# ============================================================================

@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Obtener notificaciones del usuario"""
    try:
        current_user_id = get_jwt_identity()
        is_read = request.args.get('isRead')
        
        query = {'userId': ObjectId(current_user_id)}
        if is_read is not None:
            query['isRead'] = is_read == 'true'
        
        notifications = list(notifications_collection.find(query).sort('createdAt', -1).limit(50))
        
        return jsonify({
            'notifications': serialize_doc(notifications),
            'total': len(notifications),
            'unread': notifications_collection.count_documents({
                'userId': ObjectId(current_user_id),
                'isRead': False
            })
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/notifications/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    """Marcar notificación como leída"""
    try:
        current_user_id = get_jwt_identity()
        
        result = notifications_collection.update_one(
            {
                '_id': ObjectId(notification_id),
                'userId': ObjectId(current_user_id)
            },
            {
                '$set': {
                    'isRead': True,
                    'readAt': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({'message': 'Notificación no encontrada'}), 404
        
        return jsonify({'message': 'Notificación marcada como leída'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_read():
    """Marcar todas las notificaciones como leídas"""
    try:
        current_user_id = get_jwt_identity()
        
        notifications_collection.update_many(
            {
                'userId': ObjectId(current_user_id),
                'isRead': False
            },
            {
                '$set': {
                    'isRead': True,
                    'readAt': datetime.utcnow()
                }
            }
        )
        
        return jsonify({'message': 'Todas las notificaciones marcadas como leídas'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE ESTADÍSTICAS Y DASHBOARD
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Obtener estadísticas para el dashboard"""
    try:
        current_user_id = get_jwt_identity()
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        stats = {}
        
        if user['role'] == 'customer':
            stats = {
                'totalOrders': orders_collection.count_documents({'customerId': ObjectId(current_user_id)}),
                'activeOrders': orders_collection.count_documents({
                    'customerId': ObjectId(current_user_id),
                    'status': {'$in': ['pending', 'confirmed', 'preparing', 'ready', 'on_delivery']}
                }),
                'completedOrders': orders_collection.count_documents({
                    'customerId': ObjectId(current_user_id),
                    'status': 'delivered'
                }),
                'totalSpent': sum(
                    order.get('total', 0) 
                    for order in orders_collection.find({
                        'customerId': ObjectId(current_user_id),
                        'status': 'delivered'
                    })
                ),
                'favoriteRestaurants': []
            }
            
        elif user['role'] == 'restaurant_owner':
            restaurant_ids = [r['_id'] for r in restaurants_collection.find({'ownerId': ObjectId(current_user_id)})]
            
            stats = {
                'totalRestaurants': len(restaurant_ids),
                'totalOrders': orders_collection.count_documents({'restaurantId': {'$in': restaurant_ids}}),
                'activeOrders': orders_collection.count_documents({
                    'restaurantId': {'$in': restaurant_ids},
                    'status': {'$in': ['pending', 'confirmed', 'preparing', 'ready', 'on_delivery']}
                }),
                'totalRevenue': sum(
                    order.get('subtotal', 0) 
                    for order in orders_collection.find({
                        'restaurantId': {'$in': restaurant_ids},
                        'status': 'delivered'
                    })
                ),
                'averageRating': 0,
                'totalReviews': 0
            }
            
            restaurants = list(restaurants_collection.find({'_id': {'$in': restaurant_ids}}))
            if restaurants:
                total_rating = sum(r.get('rating', 0) for r in restaurants)
                stats['averageRating'] = round(total_rating / len(restaurants), 1)
                stats['totalReviews'] = sum(r.get('totalReviews', 0) for r in restaurants)
            
        elif user['role'] == 'delivery':
            delivery_person = delivery_persons_collection.find_one({'userId': ObjectId(current_user_id)})
            
            if delivery_person:
                stats = {
                    'totalDeliveries': delivery_person.get('totalDeliveries', 0),
                    'rating': delivery_person.get('rating', 0),
                    'totalReviews': delivery_person.get('totalReviews', 0),
                    'earnings': delivery_person.get('earnings', {}),
                    'activeDelivery': orders_collection.find_one({
                        'deliveryPersonId': ObjectId(current_user_id),
                        'status': 'on_delivery'
                    }) is not None
                }
        
        elif user['role'] == 'admin':
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            stats = {
                'totalUsers': users_collection.count_documents({}),
                'totalRestaurants': restaurants_collection.count_documents({}),
                'totalOrders': orders_collection.count_documents({}),
                'ordersToday': orders_collection.count_documents({'createdAt': {'$gte': today}}),
                'activeOrders': orders_collection.count_documents({
                    'status': {'$in': ['pending', 'confirmed', 'preparing', 'ready', 'on_delivery']}
                }),
                'totalRevenue': sum(
                    order.get('total', 0) 
                    for order in orders_collection.find({'status': 'delivered'})
                ),
                'revenueToday': sum(
                    order.get('total', 0) 
                    for order in orders_collection.find({
                        'status': 'delivered',
                        'createdAt': {'$gte': today}
                    })
                )
            }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE BÚSQUEDA
# ============================================================================

@app.route('/api/search', methods=['GET'])
def search():
    """Búsqueda global de restaurantes y platillos"""
    try:
        query = request.args.get('q', '').lower()
        search_type = request.args.get('type', 'all')
        
        if not query or len(query) < 2:
            return jsonify({'message': 'Query de búsqueda muy corto'}), 400
        
        results = {}
        
        if search_type in ['all', 'restaurants']:
            restaurants = list(restaurants_collection.find({
                'isActive': True,
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}},
                    {'cuisineTypes': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(10))
            results['restaurants'] = serialize_doc(restaurants)
        
        if search_type in ['all', 'dishes']:
            dishes = list(dishes_collection.find({
                'isAvailable': True,
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}},
                    {'tags': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(20))
            results['dishes'] = serialize_doc(dishes)
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ============================================================================
# RUTAS DE CONFIGURACIÓN Y UTILIDADES
# ============================================================================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración de la aplicación"""
    return jsonify({
        'appName': 'DeliveryApp',
        'version': '1.0.0',
        'supportedPaymentMethods': ['cash', 'card', 'paypal', 'mercadopago'],
        'deliveryFeeRange': {'min': 20, 'max': 50},
        'minOrderAmount': 50,
        'currency': 'MXN',
        'taxRate': 0.16,
        'contactEmail': 'soporte@del.com',
        'contactPhone': '+525512345678'
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check de la API"""
    try:
        client.admin.command('ping')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Ruta principal"""
    return jsonify({
        'message': 'DeliveryApp API v1.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth',
            'users': '/api/users',
            'addresses': '/api/addresses',
            'restaurants': '/api/restaurants',
            'categories': '/api/categories',
            'dishes': '/api/dishes',
            'orders': '/api/orders',
            'reviews': '/api/reviews',
            'coupons': '/api/coupons',
            'delivery': '/api/delivery-persons',
            'notifications': '/api/notifications',
            'search': '/api/search',
            'dashboard': '/api/dashboard',
            'health': '/health'
        },
        'documentation': 'https://github.com/C4rlosDcJ/delivery-api'
    }), 200

# ============================================================================
# MANEJO DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Error interno del servidor'}), 500

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'message': 'No autorizado'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'message': 'Acceso prohibido'}), 403

# ============================================================================
# INICIALIZACIÓN DE LA BASE DE DATOS
# ============================================================================

def init_database():
    """Inicializar índices y datos de prueba"""
    try:
        print(" Inicializando base de datos...")
        
        # Crear índices
        users_collection.create_index([('email', 1)], unique=True)
        users_collection.create_index([('role', 1)])
        
        addresses_collection.create_index([('userId', 1)])
        addresses_collection.create_index([('location', GEOSPHERE)])
        
        restaurants_collection.create_index([('slug', 1)], unique=True)
        restaurants_collection.create_index([('ownerId', 1)])
        restaurants_collection.create_index([('location', GEOSPHERE)])
        restaurants_collection.create_index([('isActive', 1), ('isOpen', 1)])
        restaurants_collection.create_index([('rating', -1)])
        
        categories_collection.create_index([('slug', 1)], unique=True)
        categories_collection.create_index([('isActive', 1), ('order', 1)])
        
        dishes_collection.create_index([('restaurantId', 1)])
        dishes_collection.create_index([('categoryId', 1)])
        dishes_collection.create_index([('isAvailable', 1)])
        dishes_collection.create_index([('rating', -1)])
        
        orders_collection.create_index([('orderNumber', 1)], unique=True)
        orders_collection.create_index([('customerId', 1), ('createdAt', -1)])
        orders_collection.create_index([('restaurantId', 1), ('status', 1)])
        orders_collection.create_index([('deliveryPersonId', 1), ('status', 1)])
        
        reviews_collection.create_index([('orderId', 1)])
        reviews_collection.create_index([('restaurantId', 1)])
        
        coupons_collection.create_index([('code', 1)], unique=True)
        
        delivery_persons_collection.create_index([('userId', 1)], unique=True)
        delivery_persons_collection.create_index([('currentLocation', GEOSPHERE)])
        
        notifications_collection.create_index([('userId', 1), ('createdAt', -1)])
        
        print(" Indices creados correctamente")
        
        # Insertar categorías por defecto si no existen
        if categories_collection.count_documents({}) == 0:
            default_categories = [
                {'name': 'Pizzas', 'slug': 'pizzas', 'icon': '', 'color': '#FF6B6B', 'isActive': True, 'order': 1},
                {'name': 'Hamburguesas', 'slug': 'hamburguesas', 'icon': '', 'color': '#4ECDC4', 'isActive': True, 'order': 2},
                {'name': 'Sushi', 'slug': 'sushi', 'icon': '', 'color': '#FFE66D', 'isActive': True, 'order': 3},
                {'name': 'Tacos', 'slug': 'tacos', 'icon': '', 'color': '#FF6B35', 'isActive': True, 'order': 4},
                {'name': 'Postres', 'slug': 'postres', 'icon': '', 'color': '#FF1654', 'isActive': True, 'order': 5},
                {'name': 'Bebidas', 'slug': 'bebidas', 'icon': '', 'color': '#95E1D3', 'isActive': True, 'order': 6},
                {'name': 'Ensaladas', 'slug': 'ensaladas', 'icon': '', 'color': '#38B000', 'isActive': True, 'order': 7},
                {'name': 'Comida China', 'slug': 'comida-china', 'icon': '', 'color': '#F38181', 'isActive': True, 'order': 8}
            ]
            
            for cat in default_categories:
                cat['createdAt'] = datetime.utcnow()
                cat['updatedAt'] = datetime.utcnow()
                cat['description'] = f'Deliciosas opciones de {cat["name"].lower()}'
            
            categories_collection.insert_many(default_categories)
            print(" Categorias por defecto creadas")
        
        # Crear usuario admin por defecto
        if users_collection.count_documents({'role': 'admin'}) == 0:
            admin_user = {
                'email': 'admin@del.com',
                'password': generate_password_hash('admin123'),
                'name': 'Administrador',
                'phone': '+525512345678',
                'role': 'admin',
                'isActive': True,
                'emailVerified': True,
                'phoneVerified': True,
                'preferences': {
                    'notifications': True,
                    'language': 'es',
                    'theme': 'light'
                },
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow(),
                'lastLogin': datetime.utcnow()
            }
            users_collection.insert_one(admin_user)
            print(" Usuario admin creado: admin@del.com / admin123")
        
        print(" Base de datos inicializada correctamente\n")
        
    except Exception as e:
        print(f" Error al inicializar base de datos: {str(e)}")

# ============================================================================
# EJECUTAR LA APLICACIÓN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print(" DELIVERYAPP API")
    print("="*70 + "\n")
    
    # Inicializar base de datos
    init_database()
    
    print(" Servidor iniciando...")
    print(" Accede a: http://localhost:5000")
    print(" Health check: http://localhost:5000/health")
    print(" API Docs: http://localhost:5000/\n")
    print("  Para uso en dispositivos móviles, cambia 'localhost' por tu IP local")
    print("    Ejemplo: http://192.168.0.17:5000\n")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)