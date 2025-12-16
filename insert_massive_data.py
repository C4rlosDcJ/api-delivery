# insert_massive_data.py
import os
import sys
import random
from datetime import datetime, timedelta, UTC
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from bson import ObjectId
import time

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

# Configuración
TOTAL_DISHES = 500
TOTAL_RESTAURANTS = 20
TOTAL_CATEGORIES = 50
TOTAL_USERS = 10
TOTAL_DELIVERY_PERSONS = 10

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

def check_existing_data():
    """Verificar qué datos ya existen"""
    print("🔍 Verificando datos existentes...")
    
    existing_counts = {
        'users': users_collection.count_documents({}),
        'categories': categories_collection.count_documents({}),
        'restaurants': restaurants_collection.count_documents({}),
        'dishes': dishes_collection.count_documents({}),
        'delivery_persons': delivery_persons_collection.count_documents({}),
        'addresses': addresses_collection.count_documents({}),
        'coupons': coupons_collection.count_documents({}),
        'orders': orders_collection.count_documents({})
    }
    
    print("📊 Datos existentes:")
    for key, value in existing_counts.items():
        print(f"   • {key}: {value}")
    
    return existing_counts

def generate_users(count=100):
    """Generar usuarios de manera dinámica"""
    print(f"👥 Generando {count} usuarios...")
    
    existing_emails = set(users_collection.distinct('email'))
    new_users = 0
    
    for i in range(count):
        # Generar email único
        while True:
            username = f"user{i+1}_{random.randint(1000, 9999)}"
            email = f"{username}@ejemplo.com"
            if email not in existing_emails:
                break
        
        role = random.choice(['customer', 'customer', 'customer', 'restaurant_owner', 'delivery'])
        
        user_data = {
            'email': email,
            'password': generate_password_hash('password123'),
            'name': f"Usuario {i+1}",
            'phone': f'+5255{random.randint(10000000, 99999999)}',
            'role': role,
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
        
        try:
            users_collection.insert_one(user_data)
            existing_emails.add(email)
            new_users += 1
        except Exception as e:
            print(f"   ⚠️  Error al crear usuario {email}: {str(e)}")
    
    print(f"✅ {new_users} usuarios generados")
    return list(users_collection.find({}, {'_id': 1}).limit(count))

def generate_categories(count=50):
    """Generar categorías de platillos"""
    print(f"📂 Generando {count} categorías...")
    
    # Lista de categorías base
    base_categories = [
        {'name': 'Pizzas', 'icon': '🍕', 'color': '#FF6B6B'},
        {'name': 'Hamburguesas', 'icon': '🍔', 'color': '#4ECDC4'},
        {'name': 'Sushi', 'icon': '🍣', 'color': '#FFE66D'},
        {'name': 'Tacos', 'icon': '🌮', 'color': '#FF6B35'},
        {'name': 'Postres', 'icon': '🍰', 'color': '#FF1654'},
        {'name': 'Bebidas', 'icon': '🥤', 'color': '#95E1D3'},
        {'name': 'Ensaladas', 'icon': '🥗', 'color': '#6A994E'},
        {'name': 'Pastas', 'icon': '🍝', 'color': '#F28482'},
        {'name': 'Mariscos', 'icon': '🦞', 'color': '#84A59D'},
        {'name': 'Comida China', 'icon': '🥡', 'color': '#F77F00'},
    ]
    
    existing_slugs = set(categories_collection.distinct('slug'))
    new_categories = 0
    
    # Primero, crear categorías base si no existen
    for cat in base_categories:
        if new_categories >= count:
            break
            
        slug = cat['name'].lower().replace(' ', '-')
        
        # Verificar si ya existe
        existing = categories_collection.find_one({'slug': slug})
        if existing:
            continue
        
        category_data = {
            'name': cat['name'],
            'slug': slug,
            'description': f'Deliciosos {cat["name"].lower()} para todos los gustos',
            'icon': cat['icon'],
            'image': '',
            'color': cat['color'],
            'isActive': True,
            'order': new_categories + 1,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
        
        try:
            categories_collection.insert_one(category_data)
            existing_slugs.add(slug)
            new_categories += 1
            print(f"   ✅ Categoría creada: {cat['name']}")
        except Exception as e:
            print(f"   ⚠️  Error al crear categoría {cat['name']}: {str(e)}")
    
    # Crear categorías adicionales si es necesario
    category_names = [
        'Carnes', 'Pollo', 'Pescados', 'Vegetariano', 'Vegano', 'Mexicana',
        'Italiana', 'Asiática', 'Americana', 'Desayunos', 'Antojitos', 'Sopas',
        'Sandwiches', 'Comida Rápida', 'Gourmet', 'Saludable', 'Keto', 'Sin Gluten',
        'Para Compartir', 'Platillos Fuertes', 'Entradas', 'Botanas', 'Cocteles',
        'Jugos Naturales', 'Cafés', 'Tés', 'Licuados', 'Smoothies', 'Helados',
        'Panadería', 'Repostería', 'Internacional', 'Fusión', 'Mariscos', 'Parrilla',
        'Buffet', 'Casero', 'Tradicional', 'Moderno', 'Orgánico'
    ]
    
    for i in range(len(base_categories), count):
        if new_categories >= count:
            break
            
        # Elegir nombre único
        attempts = 0
        while True:
            name = random.choice(category_names)
            slug = name.lower().replace(' ', '-').replace('ó', 'o').replace('í', 'i')
            
            # Añadir sufijo si ya existe
            if slug in existing_slugs:
                slug = f"{slug}-{random.randint(1, 999)}"
            
            if slug not in existing_slugs:
                break
                
            attempts += 1
            if attempts > 10:
                slug = f"categoria-{i+1}-{random.randint(1000, 9999)}"
                name = f"Categoría {i+1}"
                break
        
        category_data = {
            'name': name,
            'slug': slug,
            'description': f'Variedad de {name.lower()} para disfrutar',
            'icon': random.choice(['🥘', '🍤', '🥑', '🍚', '🥠', '🍜', '🥟', '🍛', '🍢', '🍡']),
            'image': '',
            'color': f'#{random.randint(0, 0xFFFFFF):06x}',
            'isActive': True,
            'order': new_categories + 1,
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
        
        try:
            categories_collection.insert_one(category_data)
            existing_slugs.add(slug)
            new_categories += 1
            if new_categories % 10 == 0:
                print(f"   ✅ {new_categories} categorías creadas...")
        except Exception as e:
            print(f"   ⚠️  Error al crear categoría {name}: {str(e)}")
    
    print(f"✅ {new_categories} categorías generadas")
    return list(categories_collection.find({}, {'_id': 1}).limit(count))

def generate_restaurants(count=200):
    """Generar restaurantes"""
    print(f"🏪 Generando {count} restaurantes...")
    
    # Obtener usuarios restaurant_owner
    owners = list(users_collection.find({'role': 'restaurant_owner'}, {'_id': 1}))
    if not owners:
        print("   ⚠️  No hay usuarios restaurant_owner, creando algunos...")
        # Crear algunos owners
        for i in range(5):
            user_data = {
                'email': f'restowner{i+1}@ejemplo.com',
                'password': generate_password_hash('password123'),
                'name': f'Dueño Restaurante {i+1}',
                'phone': f'+5255{random.randint(10000000, 99999999)}',
                'role': 'restaurant_owner',
                'isActive': True,
                'createdAt': datetime.now(UTC),
                'updatedAt': datetime.now(UTC)
            }
            users_collection.insert_one(user_data)
        
        owners = list(users_collection.find({'role': 'restaurant_owner'}, {'_id': 1}))
    
    owner_ids = [owner['_id'] for owner in owners]
    existing_slugs = set(restaurants_collection.distinct('slug'))
    new_restaurants = 0
    
    restaurant_names = [
        "El Rincón", "La Terraza", "Sabores", "Delicias", "Gourmet", 
        "Tradición", "Fusión", "Sazón", "Bistro", "Cocina", "Mesa", 
        "Comedor", "Restaurante", "Cafetería", "Parrilla", "Asador",
        "Marisquería", "Pizzería", "Taquería", "Hamburguesería", "Sushibar"
    ]
    
    cuisine_types = ['Mexicana', 'Italiana', 'China', 'Japonesa', 'Americana', 
                    'Española', 'Francesa', 'Vegetariana', 'Mariscos', 'Carnes']
    
    for i in range(count):
        owner_id = random.choice(owner_ids)
        
        # Generar nombre y slug único
        attempts = 0
        while True:
            name = f"{random.choice(restaurant_names)} {random.choice(restaurant_names)} {i+1}"
            slug = name.lower().replace(' ', '-').replace('ó', 'o')
            
            if slug not in existing_slugs:
                break
                
            attempts += 1
            if attempts > 10:
                slug = f"restaurante-{i+1}-{random.randint(1000, 9999)}"
                break
        
        # Coordenadas en CDMX
        lat = 19.4194 + random.uniform(-0.1, 0.1)
        lng = -99.1675 + random.uniform(-0.1, 0.1)
        
        restaurant_data = {
            'ownerId': owner_id,
            'name': name,
            'slug': slug,
            'description': f'Restaurante especializado en {random.choice(cuisine_types)} con los mejores ingredientes',
            'logo': '',
            'coverImage': '',
            'email': f'contacto@{slug}.com',
            'phone': f'+5255{random.randint(10000000, 99999999)}',
            'website': f'https://{slug}.com',
            'address': {
                'street': f'Calle {random.randint(1, 200)}',
                'exteriorNumber': str(random.randint(1, 999)),
                'interiorNumber': random.choice(['', 'A', 'B', 'C']),
                'neighborhood': random.choice(['Roma', 'Condesa', 'Polanco', 'Del Valle', 'Narvarte']),
                'city': 'Ciudad de México',
                'state': 'CDMX',
                'zipCode': f'0{random.randint(6000, 6999)}',
                'country': 'México'
            },
            'location': {
                'type': 'Point',
                'coordinates': [lng, lat]
            },
            'isActive': True,
            'isOpen': random.choice([True, True, True, False]),  # 75% abierto
            'workingHours': [
                {'day': 'Lunes', 'open': '09:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Martes', 'open': '09:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Miércoles', 'open': '09:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Jueves', 'open': '09:00', 'close': '22:00', 'isOpen': True},
                {'day': 'Viernes', 'open': '09:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Sábado', 'open': '10:00', 'close': '23:00', 'isOpen': True},
                {'day': 'Domingo', 'open': '10:00', 'close': '21:00', 'isOpen': random.choice([True, False])}
            ],
            'deliveryConfig': {
                'hasDelivery': True,
                'deliveryRadius': random.randint(3, 10),
                'deliveryFee': random.choice([0, 25, 30, 35, 40]),
                'minOrderAmount': random.choice([100, 150, 200, 250]),
                'estimatedDeliveryTime': f'{random.randint(20, 35)}-{random.randint(40, 60)} min'
            },
            'cuisineTypes': random.sample(cuisine_types, k=random.randint(1, 3)),
            'rating': round(random.uniform(3.5, 5.0), 1),
            'totalReviews': random.randint(0, 500),
            'totalOrders': random.randint(0, 2000),
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
        
        try:
            restaurants_collection.insert_one(restaurant_data)
            existing_slugs.add(slug)
            new_restaurants += 1
            
            if new_restaurants % 20 == 0:
                print(f"   ✅ {new_restaurants} restaurantes creados...")
        except Exception as e:
            print(f"   ⚠️  Error al crear restaurante {name}: {str(e)}")
    
    print(f"✅ {new_restaurants} restaurantes generados")
    return list(restaurants_collection.find({}, {'_id': 1}).limit(count))

def generate_dishes(total_count=10000):
    """Generar platillos"""
    print(f"🍽️ Generando {total_count} platillos...")
    
    # Obtener restaurantes y categorías
    restaurants = list(restaurants_collection.find({}, {'_id': 1}))
    categories = list(categories_collection.find({}, {'_id': 1, 'name': 1}))
    
    if not restaurants or not categories:
        print("   ❌ No hay restaurantes o categorías para crear platillos")
        return []
    
    dish_names = [
        # Pizzas
        'Margherita', 'Pepperoni', 'Hawaiana', 'Vegetariana', 'Cuatro Quesos',
        'Mexicana', 'BBQ Chicken', 'Carnes Frías', 'Especial de la Casa',
        
        # Hamburguesas
        'Clásica', 'Doble Queso', 'Bacon', 'Pollo Crispy', 'BBQ',
        'Mexicana', 'Deluxe', 'Gourmet', 'Picante',
        
        # Sushi
        'California Roll', 'Philadelphia Roll', 'Dragon Roll', 'Rainbow Roll',
        'Spicy Tuna', 'Tempura Roll', 'Salmon Nigiri', 'Ebi Tempura',
        
        # Tacos
        'Al Pastor', 'Suadero', 'Carnitas', 'Barbacoa', 'Bistec',
        'Chorizo', 'Lengua', 'Cachete', 'Pescado',
        
        # Varios
        'Ensalada César', 'Pasta Alfredo', 'Lasagna', 'Filete Mignon',
        'Pechuga a la Parrilla', 'Camarones al Ajillo', 'Sopa de Tortilla',
        'Chiles Rellenos', 'Mole Poblano', 'Ceviche', 'Tiramisú', 'Flan'
    ]
    
    existing_slugs = set(dishes_collection.distinct('slug'))
    dishes_created = 0
    dishes_per_restaurant = max(1, total_count // len(restaurants))
    
    for i, restaurant in enumerate(restaurants):
        restaurant_id = restaurant['_id']
        
        # Número de platillos para este restaurante
        current_dishes = dishes_per_restaurant
        if i < total_count % len(restaurants):
            current_dishes += 1
        
        for j in range(current_dishes):
            # Seleccionar categoría basada en el tipo de platillo
            category = random.choice(categories)
            dish_name = random.choice(dish_names)
            
            # Generar slug único
            slug_base = f"{dish_name.lower().replace(' ', '-')}-{i+1}-{j+1}"
            slug = slug_base
            counter = 1
            while slug in existing_slugs:
                slug = f"{slug_base}-{counter}"
                counter += 1
            
            price = round(random.uniform(50, 300), 2)
            
            dish_data = {
                'restaurantId': restaurant_id,
                'categoryId': category['_id'],
                'name': f"{dish_name} Especial",
                'slug': slug,
                'description': f'Delicioso {dish_name.lower()} preparado con ingredientes frescos y de la mejor calidad',
                'images': [],
                'price': price,
                'originalPrice': price,
                'discount': random.choice([0, 0, 0, 10, 15]),  # Mayor probabilidad sin descuento
                'isAvailable': True,
                'isPopular': random.choice([True, False]),
                'isFeatured': random.choice([True, False]),
                'stock': None,
                'calories': random.randint(200, 800),
                'preparationTime': f'{random.randint(10, 25)}-{random.randint(30, 45)} min',
                'servingSize': random.choice(['1 persona', '2 personas', 'Familiar']),
                'customizations': [],
                'tags': random.sample(['popular', 'recomendado', 'nuevo', 'tradicional'], k=random.randint(1, 2)),
                'allergens': random.sample(['gluten', 'lácteos', 'huevo'], k=random.randint(0, 2)),
                'rating': round(random.uniform(3.5, 5.0), 1),
                'totalReviews': random.randint(0, 100),
                'totalOrders': random.randint(0, 300),
                'createdAt': datetime.now(UTC),
                'updatedAt': datetime.now(UTC)
            }
            
            try:
                dishes_collection.insert_one(dish_data)
                existing_slugs.add(slug)
                dishes_created += 1
                
                # Mostrar progreso
                if dishes_created % 500 == 0:
                    print(f"   ✅ {dishes_created} platillos creados...")
            except Exception as e:
                print(f"   ⚠️  Error al crear platillo: {str(e)}")
    
    print(f"✅ {dishes_created} platillos generados")
    return list(dishes_collection.find({}, {'_id': 1}).limit(total_count))

def generate_delivery_persons(count=50):
    """Generar repartidores"""
    print(f"🚴 Generando {count} repartidores...")
    
    # Obtener usuarios con rol delivery
    delivery_users = list(users_collection.find({'role': 'delivery'}, {'_id': 1}))
    
    # Crear usuarios delivery si no hay suficientes
    if len(delivery_users) < count:
        needed = count - len(delivery_users)
        print(f"   🔄 Creando {needed} usuarios repartidores...")
        
        for i in range(needed):
            user_data = {
                'email': f'repartidor{i+1}@ejemplo.com',
                'password': generate_password_hash('password123'),
                'name': f'Repartidor {i+1}',
                'phone': f'+5255{random.randint(10000000, 99999999)}',
                'role': 'delivery',
                'isActive': True,
                'createdAt': datetime.now(UTC),
                'updatedAt': datetime.now(UTC)
            }
            users_collection.insert_one(user_data)
        
        delivery_users = list(users_collection.find({'role': 'delivery'}, {'_id': 1}))
    
    delivery_persons = []
    vehicles = ['moto', 'bicicleta', 'auto']
    zones = ['Roma', 'Condesa', 'Polanco', 'Del Valle', 'Narvarte', 'Coyoacán']
    
    for i, user in enumerate(delivery_users[:count]):
        user_id = user['_id']
        
        # Verificar si ya existe
        existing = delivery_persons_collection.find_one({'userId': user_id})
        if existing:
            delivery_persons.append(existing['_id'])
            continue
        
        delivery_data = {
            'userId': user_id,
            'vehicleType': random.choice(vehicles),
            'vehiclePlate': f'ABC{random.randint(100, 999)}',
            'vehicleModel': f'Modelo {random.randint(2018, 2023)}',
            'vehicleColor': random.choice(['Rojo', 'Azul', 'Negro', 'Blanco']),
            'driverLicense': f'DL{random.randint(10000000, 99999999)}',
            'isAvailable': True,
            'isOnline': random.choice([True, False]),
            'isVerified': True,
            'currentLocation': {
                'type': 'Point',
                'coordinates': [
                    -99.1675 + random.uniform(-0.05, 0.05),
                    19.4194 + random.uniform(-0.05, 0.05)
                ]
            },
            'workingZones': random.sample(zones, k=random.randint(2, 4)),
            'totalDeliveries': random.randint(0, 500),
            'rating': round(random.uniform(4.0, 5.0), 1),
            'totalReviews': random.randint(0, 50),
            'earnings': {
                'today': random.randint(100, 500),
                'week': random.randint(1000, 3000),
                'month': random.randint(5000, 15000),
                'total': random.randint(20000, 80000)
            },
            'createdAt': datetime.now(UTC),
            'updatedAt': datetime.now(UTC)
        }
        
        try:
            result = delivery_persons_collection.insert_one(delivery_data)
            delivery_persons.append(result.inserted_id)
        except Exception as e:
            print(f"   ⚠️  Error al crear repartidor: {str(e)}")
    
    print(f"✅ {len(delivery_persons)} repartidores generados")
    return delivery_persons

def generate_sample_data():
    """Generar datos adicionales de muestra"""
    print("🎫 Generando datos adicionales...")
    
    # Cupones
    coupons_data = [
        {
            'code': 'BIENVENIDA20',
            'description': '20% de descuento en tu primer pedido',
            'discountType': 'percentage',
            'discountValue': 20,
            'minOrderAmount': 150,
            'maxDiscountAmount': 100,
            'usageLimit': 1000,
            'validFrom': datetime.now(UTC),
            'validUntil': datetime.now(UTC) + timedelta(days=365),
            'isActive': True
        },
        {
            'code': 'ENVIOGRATIS',
            'description': 'Envío gratis en pedidos mayores a $250',
            'discountType': 'fixed',
            'discountValue': 35,
            'minOrderAmount': 250,
            'maxDiscountAmount': 35,
            'usageLimit': 500,
            'validFrom': datetime.now(UTC),
            'validUntil': datetime.now(UTC) + timedelta(days=180),
            'isActive': True
        }
    ]
    
    for coupon in coupons_data:
        try:
            coupons_collection.update_one(
                {'code': coupon['code']},
                {'$setOnInsert': coupon},
                upsert=True
            )
        except Exception as e:
            print(f"   ⚠️  Error al crear cupón {coupon['code']}: {str(e)}")
    
    print("✅ Datos adicionales generados")

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🚀 GENERANDO DATOS MASIVOS PARA DELIVERYAPP")
    print("="*70 + "\n")
    
    start_time = time.time()
    
    try:
        # Verificar datos existentes
        existing_data = check_existing_data()
        
        print("\nConfiguración de datos a generar:")
        print(f"   • {TOTAL_USERS} usuarios")
        print(f"   • {TOTAL_CATEGORIES} categorías")
        print(f"   • {TOTAL_RESTAURANTS} restaurantes")
        print(f"   • {TOTAL_DISHES} platillos")
        print(f"   • {TOTAL_DELIVERY_PERSONS} repartidores")
        
        response = input("\n¿Deseas limpiar la base de datos antes de insertar? (s/N): ").lower().strip()
        if response == 's':
            clear_database()
        else:
            print("\n⚠️  Modo incremental: Se evitarán duplicados en datos existentes")
        
        print("\n⏳ Generando datos... Esto puede tomar varios minutos...\n")
        
        # Generar datos en orden
        print("1. Generando usuarios...")
        user_ids = generate_users(TOTAL_USERS)
        
        print("\n2. Generando categorías...")
        category_ids = generate_categories(TOTAL_CATEGORIES)
        
        print("\n3. Generando restaurantes...")
        restaurant_ids = generate_restaurants(TOTAL_RESTAURANTS)
        
        print("\n4. Generando platillos...")
        dish_ids = generate_dishes(TOTAL_DISHES)
        
        print("\n5. Generando repartidores...")
        delivery_person_ids = generate_delivery_persons(TOTAL_DELIVERY_PERSONS)
        
        print("\n6. Generando datos adicionales...")
        generate_sample_data()
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("✅ DATOS GENERADOS EXITOSAMENTE")
        print("="*70)
        
        # Mostrar estadísticas finales
        print("\n📊 ESTADÍSTICAS FINALES:")
        print(f"   • Usuarios: {users_collection.count_documents({}):,}")
        print(f"   • Categorías: {categories_collection.count_documents({}):,}")
        print(f"   • Restaurantes: {restaurants_collection.count_documents({}):,}")
        print(f"   • Platillos: {dishes_collection.count_documents({}):,}")
        print(f"   • Repartidores: {delivery_persons_collection.count_documents({}):,}")
        print(f"   • Direcciones: {addresses_collection.count_documents({}):,}")
        print(f"   • Cupones: {coupons_collection.count_documents({}):,}")
        print(f"   • Pedidos: {orders_collection.count_documents({}):,}")
        print(f"   • Tiempo total: {elapsed_time:.2f} segundos")
        
        print("\n👤 INFORMACIÓN DE ACCESO:")
        print("   Todos los usuarios tienen la contraseña: 'password123'")
        
        # Mostrar algunos usuarios de ejemplo
        sample_users = list(users_collection.find({}, {'email': 1, 'role': 1}).limit(3))
        print("\n📧 USUARIOS DE EJEMPLO:")
        for user in sample_users:
            print(f"   • {user['email']} ({user['role']})")
        
        print("\n🎫 CUPONES DISPONIBLES:")
        print("   • BIENVENIDA20 - 20% descuento primer pedido")
        print("   • ENVIOGRATIS - Envío gratis en pedidos > $250")
        
        print("\n¡Datos generados exitosamente! 🎉")
        print("Puedes probar la aplicación con estos datos.\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()