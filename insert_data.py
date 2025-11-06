# insert_data.py
import os
import sys
from datetime import datetime, timedelta, UTC
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from bson import ObjectId

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

def clear_database():
    """Limpiar datos existentes"""
    print("🧹 Limpiando datos existentes...")
    collections = [
        'users', 'addresses', 'restaurants', 'categories', 'dishes',
        'orders', 'reviews', 'coupons', 'delivery_persons', 'notifications'
    ]
    
    for collection in collections:
        db[collection].delete_many({})
    print("✅ Datos limpiados")

def get_or_create_users():
    """Obtener usuarios existentes o crear nuevos"""
    print("👥 Procesando usuarios...")
    
    users_data = [
        {
            'email': 'cliente@ejemplo.com',
            'password': generate_password_hash('cliente123'),
            'name': 'Juan Pérez',
            'phone': '+525511112222',
            'role': 'customer',
            'avatar': '',
            'isActive': True,
            'emailVerified': True,
            'phoneVerified': True,
            'preferences': {
                'notifications': True,
                'language': 'es',
                'theme': 'light'
            },
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC),
            'lastLogin': datetime.now(UTC)
        },
        {
            'email': 'restaurante@ejemplo.com',
            'password': generate_password_hash('restaurante123'),
            'name': 'María García',
            'phone': '+525533334444',
            'role': 'restaurant_owner',
            'avatar': '',
            'isActive': True,
            'emailVerified': True,
            'phoneVerified': True,
            'preferences': {
                'notifications': True,
                'language': 'es',
                'theme': 'light'
            },
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC),
            'lastLogin': datetime.now(UTC)
        },
        {
            'email': 'repartidor@ejemplo.com',
            'password': generate_password_hash('repartidor123'),
            'name': 'Carlos López',
            'phone': '+525555556666',
            'role': 'delivery',
            'avatar': '',
            'isActive': True,
            'emailVerified': True,
            'phoneVerified': True,
            'preferences': {
                'notifications': True,
                'language': 'es',
                'theme': 'light'
            },
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC),
            'lastLogin': datetime.now(UTC)
        },
        {
            'email': 'cliente2@ejemplo.com',
            'password': generate_password_hash('cliente123'),
            'name': 'Ana Rodríguez',
            'phone': '+525577778888',
            'role': 'customer',
            'avatar': '',
            'isActive': True,
            'emailVerified': True,
            'phoneVerified': True,
            'preferences': {
                'notifications': True,
                'language': 'es',
                'theme': 'light'
            },
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC),
            'lastLogin': datetime.now(UTC)
        }
    ]
    
    user_ids = []
    for user_data in users_data:
        # Verificar si el usuario ya existe
        existing_user = users_collection.find_one({'email': user_data['email']})
        if existing_user:
            print(f"   ✅ Usuario existente: {user_data['email']}")
            user_ids.append(existing_user['_id'])
        else:
            # Crear nuevo usuario
            result = users_collection.insert_one(user_data)
            user_ids.append(result.inserted_id)
            print(f"   ✅ Nuevo usuario creado: {user_data['email']}")
    
    print(f"✅ {len(user_ids)} usuarios procesados")
    return user_ids

def get_or_create_categories():
    """Obtener categorías existentes o crear nuevas"""
    print("📂 Procesando categorías...")
    
    categories_data = [
        {
            'name': 'Pizzas',
            'slug': 'pizzas',
            'description': 'Deliciosas pizzas recién horneadas',
            'icon': '🍕',
            'image': '',
            'color': '#FF6B6B',
            'isActive': True,
            'order': 1,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'name': 'Hamburguesas',
            'slug': 'hamburguesas',
            'description': 'Hamburguesas jugosas y deliciosas',
            'icon': '🍔',
            'image': '',
            'color': '#4ECDC4',
            'isActive': True,
            'order': 2,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'name': 'Sushi',
            'slug': 'sushi',
            'description': 'Sushi fresco y auténtico',
            'icon': '🍣',
            'image': '',
            'color': '#FFE66D',
            'isActive': True,
            'order': 3,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'name': 'Tacos',
            'slug': 'tacos',
            'description': 'Tacos tradicionales mexicanos',
            'icon': '🌮',
            'image': '',
            'color': '#FF6B35',
            'isActive': True,
            'order': 4,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'name': 'Postres',
            'slug': 'postres',
            'description': 'Dulces tentaciones para el paladar',
            'icon': '🍰',
            'image': '',
            'color': '#FF1654',
            'isActive': True,
            'order': 5,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'name': 'Bebidas',
            'slug': 'bebidas',
            'description': 'Refrescantes bebidas',
            'icon': '🥤',
            'image': '',
            'color': '#95E1D3',
            'isActive': True,
            'order': 6,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
    ]
    
    category_ids = []
    for cat_data in categories_data:
        existing_cat = categories_collection.find_one({'slug': cat_data['slug']})
        if existing_cat:
            category_ids.append(existing_cat['_id'])
            print(f"   ✅ Categoría existente: {cat_data['name']}")
        else:
            result = categories_collection.insert_one(cat_data)
            category_ids.append(result.inserted_id)
            print(f"   ✅ Nueva categoría creada: {cat_data['name']}")
    
    print(f"✅ {len(category_ids)} categorías procesadas")
    return category_ids

def get_or_create_restaurants(user_ids):
    """Obtener restaurantes existentes o crear nuevos"""
    print("🏪 Procesando restaurantes...")
    
    restaurants_data = [
        {
            'ownerId': user_ids[1],  # María García
            'name': 'Pizzería Napoli',
            'slug': 'pizzeria-napoli',
            'description': 'Las mejores pizzas italianas en la ciudad. Ingredientes frescos y masa artesanal.',
            'logo': '',
            'coverImage': '',
            'email': 'info@pizzeria-napoli.com',
            'phone': '+525511223344',
            'website': 'https://pizzeria-napoli.com',
            'address': {
                'street': 'Av. Insurgentes Sur 123',
                'exteriorNumber': '456',
                'interiorNumber': '',
                'neighborhood': 'Roma Norte',
                'city': 'Ciudad de México',
                'state': 'CDMX',
                'zipCode': '06700',
                'country': 'México'
            },
            'location': {
                'type': 'Point',
                'coordinates': [-99.1675, 19.4194]
            },
            'isActive': True,
            'isOpen': True,
            'workingHours': [
                {'day': 'Lunes', 'open': '10:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Martes', 'open': '10:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Miércoles', 'open': '10:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Jueves', 'open': '10:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Viernes', 'open': '10:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Sábado', 'open': '11:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Domingo', 'open': '11:00', 'close': '22:00', 'isOpen': True}
            ],
            'deliveryConfig': {
                'hasDelivery': True,
                'deliveryRadius': 8,
                'deliveryFee': 35,
                'minOrderAmount': 150,
                'estimatedDeliveryTime': '30-45 min'
            },
            'cuisineTypes': ['Italiana', 'Pizza', 'Pasta'],
            'rating': 4.5,
            'totalReviews': 127,
            'totalOrders': 543,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'ownerId': user_ids[1],
            'name': 'Burger Paradise',
            'slug': 'burger-paradise',
            'description': 'Hamburguesas gourmet con ingredientes premium. Carnes 100% angus.',
            'logo': '',
            'coverImage': '',
            'email': 'contacto@burgerparadise.com',
            'phone': '+525522334455',
            'website': 'https://burgerparadise.com',
            'address': {
                'street': 'Calle Reforma 789',
                'exteriorNumber': '101',
                'interiorNumber': '',
                'neighborhood': 'Juárez',
                'city': 'Ciudad de México',
                'state': 'CDMX',
                'zipCode': '06600',
                'country': 'México'
            },
            'location': {
                'type': 'Point',
                'coordinates': [-99.1586, 19.4326]
            },
            'isActive': True,
            'isOpen': True,
            'workingHours': [
                {'day': 'Lunes', 'open': '11:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Martes', 'open': '11:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Miércoles', 'open': '11:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Jueves', 'open': '11:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Viernes', 'open': '11:00', 'close': '00:00', 'isOpen': True},
                {'day': 'Sábado', 'open': '11:00', 'close': '00:00', 'isOpen': True},
                {'day': 'Domingo', 'open': '11:00', 'close': '22:00', 'isOpen': True}
            ],
            'deliveryConfig': {
                'hasDelivery': True,
                'deliveryRadius': 6,
                'deliveryFee': 30,
                'minOrderAmount': 120,
                'estimatedDeliveryTime': '25-40 min'
            },
            'cuisineTypes': ['Americana', 'Hamburguesas', 'Comida Rápida'],
            'rating': 4.3,
            'totalReviews': 89,
            'totalOrders': 321,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'ownerId': user_ids[1],
            'name': 'Sushi Master',
            'slug': 'sushi-master',
            'description': 'Sushi tradicional japonés preparado por chefs expertos. Pescado fresco diario.',
            'logo': '',
            'coverImage': '',
            'email': 'reservaciones@sushimaster.com',
            'phone': '+525533445566',
            'website': 'https://sushimaster.com',
            'address': {
                'street': 'Av. Patriotismo 456',
                'exteriorNumber': '234',
                'interiorNumber': '',
                'neighborhood': 'San Miguel Chapultepec',
                'city': 'Ciudad de México',
                'state': 'CDMX',
                'zipCode': '11850',
                'country': 'México'
            },
            'location': {
                'type': 'Point',
                'coordinates': [-99.1805, 19.4054]
            },
            'isActive': True,
            'isOpen': True,
            'workingHours': [
                {'day': 'Lunes', 'open': '12:00', 'close': '21:00', 'isOpen': True},
                {'day': 'Martes', 'open': '12:00', 'close': '21:00', 'isOpen': True},
                {'day': 'Miércoles', 'open': '12:00', 'close': '21:00', 'isOpen': True},
                {'day': 'Jueves', 'open': '12:00', 'close': '21:00', 'isOpen': True},
                {'day': 'Viernes', 'open': '12:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Sábado', 'open': '12:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Domingo', 'open': '12:00', 'close': '20:00', 'isOpen': True}
            ],
            'deliveryConfig': {
                'hasDelivery': True,
                'deliveryRadius': 10,
                'deliveryFee': 40,
                'minOrderAmount': 200,
                'estimatedDeliveryTime': '35-50 min'
            },
            'cuisineTypes': ['Japonesa', 'Sushi', 'Asiática'],
            'rating': 4.7,
            'totalReviews': 156,
            'totalOrders': 432,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
    ]
    
    restaurant_ids = []
    for rest_data in restaurants_data:
        existing_rest = restaurants_collection.find_one({'slug': rest_data['slug']})
        if existing_rest:
            restaurant_ids.append(existing_rest['_id'])
            print(f"   ✅ Restaurante existente: {rest_data['name']}")
        else:
            result = restaurants_collection.insert_one(rest_data)
            restaurant_ids.append(result.inserted_id)
            print(f"   ✅ Nuevo restaurante creado: {rest_data['name']}")
    
    print(f"✅ {len(restaurant_ids)} restaurantes procesados")
    return restaurant_ids

def get_or_create_dishes(restaurant_ids, category_ids):
    """Obtener platillos existentes o crear nuevos"""
    print("🍽️ Procesando platillos...")
    
    # Obtener categorías por slug
    pizza_cat = categories_collection.find_one({'slug': 'pizzas'})
    burger_cat = categories_collection.find_one({'slug': 'hamburguesas'})
    sushi_cat = categories_collection.find_one({'slug': 'sushi'})
    
    dishes_data = [
        # Pizzería Napoli
        {
            'restaurantId': restaurant_ids[0],
            'categoryId': pizza_cat['_id'],
            'name': 'Pizza Margherita',
            'slug': 'pizza-margherita',
            'description': 'Pizza clásica con salsa de tomate, mozzarella fresca y albahaca',
            'images': [],
            'price': 189.00,
            'originalPrice': 189.00,
            'discount': 0,
            'isAvailable': True,
            'isPopular': True,
            'isFeatured': True,
            'stock': None,
            'calories': 850,
            'preparationTime': '20-25 min',
            'servingSize': '8 porciones',
            'customizations': [
                {
                    'name': 'Tamaño',
                    'options': [
                        {'name': 'Personal', 'price': 0},
                        {'name': 'Mediana', 'price': 50},
                        {'name': 'Grande', 'price': 80}
                    ]
                }
            ],
            'tags': ['clásica', 'vegetariana', 'italiana'],
            'allergens': ['gluten', 'lácteos'],
            'rating': 4.8,
            'totalReviews': 45,
            'totalOrders': 156,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'restaurantId': restaurant_ids[0],
            'categoryId': pizza_cat['_id'],
            'name': 'Pizza Pepperoni',
            'slug': 'pizza-pepperoni',
            'description': 'Pizza con pepperoni, queso mozzarella y salsa de tomate',
            'images': [],
            'price': 219.00,
            'originalPrice': 219.00,
            'discount': 0,
            'isAvailable': True,
            'isPopular': True,
            'isFeatured': False,
            'stock': None,
            'calories': 920,
            'preparationTime': '20-25 min',
            'servingSize': '8 porciones',
            'customizations': [],
            'tags': ['pepperoni', 'carnes', 'popular'],
            'allergens': ['gluten', 'lácteos'],
            'rating': 4.6,
            'totalReviews': 38,
            'totalOrders': 134,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        # Burger Paradise
        {
            'restaurantId': restaurant_ids[1],
            'categoryId': burger_cat['_id'],
            'name': 'Burger Clásica',
            'slug': 'burger-clasica',
            'description': 'Hamburguesa con carne angus, lechuga, tomate, cebolla y salsa especial',
            'images': [],
            'price': 129.00,
            'originalPrice': 129.00,
            'discount': 0,
            'isAvailable': True,
            'isPopular': True,
            'isFeatured': True,
            'stock': None,
            'calories': 680,
            'preparationTime': '15-20 min',
            'servingSize': '1 persona',
            'customizations': [
                {
                    'name': 'Punto de cocción',
                    'options': [
                        {'name': 'Término medio', 'price': 0},
                        {'name': 'Tres cuartos', 'price': 0},
                        {'name': 'Bien cocida', 'price': 0}
                    ]
                }
            ],
            'tags': ['clásica', 'carne angus', 'popular'],
            'allergens': ['gluten', 'lácteos'],
            'rating': 4.5,
            'totalReviews': 34,
            'totalOrders': 98,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        # Sushi Master
        {
            'restaurantId': restaurant_ids[2],
            'categoryId': sushi_cat['_id'],
            'name': 'Roll California',
            'slug': 'roll-california',
            'description': 'Roll de kanikama, aguacate y pepino, cubierto con hueva de pescado',
            'images': [],
            'price': 159.00,
            'originalPrice': 159.00,
            'discount': 0,
            'isAvailable': True,
            'isPopular': True,
            'isFeatured': True,
            'stock': None,
            'calories': 320,
            'preparationTime': '10-15 min',
            'servingSize': '8 piezas',
            'customizations': [],
            'tags': ['california', 'kanikama', 'aguacate'],
            'allergens': ['pescado', 'mariscos'],
            'rating': 4.6,
            'totalReviews': 42,
            'totalOrders': 123,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
    ]
    
    dish_ids = []
    for dish_data in dishes_data:
        existing_dish = dishes_collection.find_one({
            'restaurantId': dish_data['restaurantId'],
            'slug': dish_data['slug']
        })
        if existing_dish:
            dish_ids.append(existing_dish['_id'])
            print(f"   ✅ Platillo existente: {dish_data['name']}")
        else:
            result = dishes_collection.insert_one(dish_data)
            dish_ids.append(result.inserted_id)
            print(f"   ✅ Nuevo platillo creado: {dish_data['name']}")
    
    print(f"✅ {len(dish_ids)} platillos procesados")
    return dish_ids

def get_or_create_addresses(user_ids):
    """Obtener direcciones existentes o crear nuevas"""
    print("📍 Procesando direcciones...")
    
    addresses_data = [
        {
            'userId': user_ids[0],
            'label': 'Casa',
            'street': 'Av. Chapultepec',
            'exteriorNumber': '123',
            'interiorNumber': 'A',
            'neighborhood': 'Roma Norte',
            'city': 'Ciudad de México',
            'state': 'CDMX',
            'zipCode': '06700',
            'country': 'México',
            'location': {
                'type': 'Point',
                'coordinates': [-99.1675, 19.4194]
            },
            'references': 'Entre Durango y Colima, edificio blanco',
            'phoneContact': '+525511112222',
            'isDefault': True,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
    ]
    
    address_ids = []
    for addr_data in addresses_data:
        existing_addr = addresses_collection.find_one({
            'userId': addr_data['userId'],
            'street': addr_data['street'],
            'exteriorNumber': addr_data['exteriorNumber']
        })
        if existing_addr:
            address_ids.append(existing_addr['_id'])
            print(f"   ✅ Dirección existente: {addr_data['label']}")
        else:
            result = addresses_collection.insert_one(addr_data)
            address_ids.append(result.inserted_id)
            print(f"   ✅ Nueva dirección creada: {addr_data['label']}")
    
    print(f"✅ {len(address_ids)} direcciones procesadas")
    return address_ids

def get_or_create_delivery_persons(user_ids):
    """Obtener repartidores existentes o crear nuevos"""
    print("🚴 Procesando repartidores...")
    
    delivery_data = {
        'userId': user_ids[2],
        'vehicleType': 'moto',
        'vehiclePlate': 'ABC123',
        'vehicleModel': 'Honda CB190',
        'vehicleColor': 'Rojo',
        'driverLicense': 'DL12345678',
        'isAvailable': True,
        'isOnline': True,
        'isVerified': True,
        'currentLocation': {
            'type': 'Point',
            'coordinates': [-99.1675, 19.4194]
        },
        'workingZones': ['Roma', 'Condesa', 'Juárez', 'Polanco'],
        'totalDeliveries': 45,
        'rating': 4.8,
        'totalReviews': 38,
        'earnings': {
            'today': 350,
            'week': 1850,
            'month': 7200,
            'total': 15600
        },
        'createdAt': datetime.now(UTC),
        'updatedAt': datetime.now(UTC)
    }
    
    existing_dp = delivery_persons_collection.find_one({'userId': user_ids[2]})
    if existing_dp:
        print("   ✅ Repartidor existente: Carlos López")
        return [existing_dp['_id']]
    else:
        result = delivery_persons_collection.insert_one(delivery_data)
        print("   ✅ Nuevo repartidor creado: Carlos López")
        return [result.inserted_id]

def get_or_create_coupons():
    """Obtener cupones existentes o crear nuevos"""
    print("🎫 Procesando cupones...")
    
    coupons_data = [
        {
            'code': 'BIENVENIDA20',
            'description': '20% de descuento en tu primer pedido',
            'discountType': 'percentage',
            'discountValue': 20,
            'minOrderAmount': 150,
            'maxDiscountAmount': 100,
            'usageLimit': 1000,
            'usageCount': 234,
            'validFrom': datetime.now(UTC),
            'validUntil': datetime.now(UTC) + timedelta(days=365),
            'isActive': True,
            'applicableTo': 'all',
            'isForNewUsersOnly': True,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        },
        {
            'code': 'ENVIOGRATIS',
            'description': 'Envío gratis en pedidos mayores a $250',
            'discountType': 'fixed',
            'discountValue': 35,
            'minOrderAmount': 250,
            'maxDiscountAmount': 35,
            'usageLimit': 200,
            'usageCount': 45,
            'validFrom': datetime.now(UTC),
            'validUntil': datetime.now(UTC) + timedelta(days=90),
            'isActive': True,
            'applicableTo': 'all',
            'isForNewUsersOnly': False,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
    ]
    
    coupon_ids = []
    for coupon_data in coupons_data:
        existing_coupon = coupons_collection.find_one({'code': coupon_data['code']})
        if existing_coupon:
            coupon_ids.append(existing_coupon['_id'])
            print(f"   ✅ Cupón existente: {coupon_data['code']}")
        else:
            result = coupons_collection.insert_one(coupon_data)
            coupon_ids.append(result.inserted_id)
            print(f"   ✅ Nuevo cupón creado: {coupon_data['code']}")
    
    print(f"✅ {len(coupon_ids)} cupones procesados")
    return coupon_ids

def create_sample_orders(user_ids, restaurant_ids, dish_ids, address_ids, delivery_person_ids):
    """Crear pedidos de muestra"""
    print("📦 Creando pedidos de muestra...")
    
    # Verificar si ya existen pedidos
    existing_orders = orders_collection.count_documents({})
    if existing_orders > 0:
        print("   ⚠️  Ya existen pedidos en la base de datos")
        return []
    
    # Obtener la dirección existente
    existing_address = addresses_collection.find_one({'_id': address_ids[0]})
    if not existing_address:
        print("   ❌ No se encontró la dirección para crear pedidos")
        return []
    
    # Crear datos de dirección sin _id para el pedido
    delivery_address_data = {
        'label': existing_address['label'],
        'street': existing_address['street'],
        'exteriorNumber': existing_address['exteriorNumber'],
        'interiorNumber': existing_address['interiorNumber'],
        'neighborhood': existing_address['neighborhood'],
        'city': existing_address['city'],
        'state': existing_address['state'],
        'zipCode': existing_address['zipCode'],
        'country': existing_address['country'],
        'location': existing_address['location'],
        'references': existing_address['references'],
        'phoneContact': existing_address['phoneContact']
    }
    
    orders_data = [
        {
            'orderNumber': 'ORD-' + datetime.now(UTC).strftime('%Y%m%d') + '-0001',
            'customerId': user_ids[0],
            'restaurantId': restaurant_ids[0],
            'items': [
                {
                    'dishId': dish_ids[0],
                    'name': 'Pizza Margherita',
                    'quantity': 1,
                    'price': 189.00,
                    'subtotal': 189.00,
                    'customizations': [
                        {'name': 'Tamaño', 'selected': 'Mediana', 'price': 50}
                    ]
                }
            ],
            'deliveryAddress': delivery_address_data,
            'subtotal': 239.00,
            'deliveryFee': 35.00,
            'discount': 0,
            'tax': 38.24,
            'tip': 30.00,
            'total': 342.24,
            'status': 'delivered',
            'statusHistory': [
                {'status': 'pending', 'timestamp': datetime.now(UTC) - timedelta(hours=3), 'note': 'Pedido recibido'},
                {'status': 'confirmed', 'timestamp': datetime.now(UTC) - timedelta(hours=2, minutes=50), 'note': 'Confirmado'},
                {'status': 'preparing', 'timestamp': datetime.now(UTC) - timedelta(hours=2, minutes=30), 'note': 'En preparación'},
                {'status': 'ready', 'timestamp': datetime.now(UTC) - timedelta(hours=2, minutes=10), 'note': 'Listo'},
                {'status': 'on_delivery', 'timestamp': datetime.now(UTC) - timedelta(hours=1, minutes=45), 'note': 'En camino'},
                {'status': 'delivered', 'timestamp': datetime.now(UTC) - timedelta(hours=1, minutes=30), 'note': 'Entregado'}
            ],
            'paymentMethod': 'card',
            'paymentStatus': 'paid',
            'estimatedDeliveryTime': '30-45 min',
            'customerNotes': 'Por favor tocar timbre',
            'deliveryPersonId': delivery_person_ids[0],
            'createdAt': datetime.now(UTC) - timedelta(hours=3),
            'updatedAt': datetime.now(UTC) - timedelta(hours=1, minutes=30)
        }
    ]
    
    result = orders_collection.insert_many(orders_data)
    print(f"✅ {len(result.inserted_ids)} pedidos de muestra creados")
    return result.inserted_ids

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🚀 INSERTANDO DATOS DE PRUEBA EN DELIVERYAPP")
    print("="*70 + "\n")
    
    try:
        # Preguntar si limpiar la base de datos primero
        response = input("¿Deseas limpiar la base de datos antes de insertar? (s/N): ").lower().strip()
        if response == 's':
            clear_database()
        
        # Insertar datos en orden
        user_ids = get_or_create_users()
        category_ids = get_or_create_categories()
        restaurant_ids = get_or_create_restaurants(user_ids)
        dish_ids = get_or_create_dishes(restaurant_ids, category_ids)
        address_ids = get_or_create_addresses(user_ids)
        delivery_person_ids = get_or_create_delivery_persons(user_ids)
        coupon_ids = get_or_create_coupons()
        order_ids = create_sample_orders(user_ids, restaurant_ids, dish_ids, address_ids, delivery_person_ids)
        
        print("\n" + "="*70)
        print("✅ DATOS DE PRUEBA PROCESADOS EXITOSAMENTE")
        print("="*70)
        
        # Mostrar información de acceso
        print("\n📋 INFORMACIÓN DE ACCESO:")
        print("   👤 Cliente: cliente@ejemplo.com / cliente123")
        print("   🏪 Restaurante: restaurante@ejemplo.com / restaurante123")
        print("   🚴 Repartidor: repartidor@ejemplo.com / repartidor123")
        print("   👤 Cliente 2: cliente2@ejemplo.com / cliente123")
        
        print("\n🎫 CUPONES DISPONIBLES:")
        print("   • BIENVENIDA20 - 20% descuento primer pedido")
        print("   • ENVIOGRATIS - Envío gratis en pedidos > $250")
        
        print("\n📍 RESUMEN:")
        print(f"   • {len(user_ids)} usuarios")
        print(f"   • {len(category_ids)} categorías")
        print(f"   • {len(restaurant_ids)} restaurantes")
        print(f"   • {len(dish_ids)} platillos")
        print(f"   • {len(address_ids)} direcciones")
        print(f"   • {len(delivery_person_ids)} repartidores")
        print(f"   • {len(coupon_ids)} cupones")
        print(f"   • {len(order_ids)} pedidos de muestra")
        
        print("\n¡Listo! Puedes probar la aplicación con estos datos. 🎉\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()