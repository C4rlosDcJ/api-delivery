
# API REST - DeliveryApp Backend

## Descripcion
API REST principal para la aplicacion de delivery. Proporciona endpoints para autenticacion, gestion de usuarios, restaurantes, platillos, pedidos, resenas, cupones, repartidores y notificaciones.

Este backend esta construido con Flask y MongoDB, implementando autenticacion JWT y diseño modular.

## Tecnologias
- **Flask**: Framework web principal
- **Flask-JWT-Extended**: Autenticacion basada en tokens JWT
- **Flask-CORS**: Manejo de Cross-Origin Resource Sharing
- **PyMongo**: Driver para conexion con MongoDB
- **Werkzeug**: Utilidades de seguridad para hash de contraseñas
- **Scikit-learn / Numpy**: Modulos para Machine Learning (prediccion de demanda y recomendaciones)

## Estructura de Base de Datos (MongoDB)
Colecciones principales:
- `users`: Usuarios del sistema (clientes, admins, owners, delivery)
- `restaurants`: Informacion de restaurantes y su configuracion
- `dishes`: Platillos disponibles y precios
- `orders`: Registro de pedidos y estados
- `reviews`: Resenas y calificaciones de servicio
- `coupons`: Cupones de descuento activos
- `delivery_persons`: Informacion y ubicacion de repartidores
- `notifications`: Notificaciones del sistema
- `addresses`: Direcciones de entrega de usuarios
- `categories`: Categorias de platillos

## Instalacion y Configuracion

### 1. Requisitos Previos
- Python 3.8 o superior
- MongoDB (Local o Atlas)

### 2. Instalacion de Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configuracion de Variables de Entorno
Crea un archivo `.env` en la raiz del proyecto con la siguiente configuracion:

```properties
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu-clave-secreta
JWT_SECRET_KEY=tu-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=2592000

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
DB_NAME=deliveryhub

# Server Configuration
HOST=0.0.0.0
PORT=5000

# CORS Configuration
CORS_ORIGINS=*

# Environment
ENV=development
```

### 4. Ejecucion
```bash
python app.py
```
El servidor iniciara en `http://localhost:5000`.

## Endpoints Principales

### Autenticacion
- `POST /api/auth/register`: Registro de nuevos usuarios
- `POST /api/auth/login`: Inicio de sesion
- `GET /api/auth/me`: Obtener perfil del usuario actual

### Restaurantes
- `GET /api/restaurants`: Listar restaurantes (con filtros)
- `GET /api/restaurants/<id>`: Detalles de un restaurante
- `POST /api/restaurants`: Crear restaurante (Admin/Owner)

### Pedidos
- `POST /api/orders`: Crear nuevo pedido
- `GET /api/orders`: Historial de pedidos
- `PUT /api/orders/<id>/status`: Actualizar estado (Admin/Restaurant/Delivery)

### Machine Learning
- **Forecast**: Prediccion de demanda basada en historico.
- **Recommendations**: Sugerencias personalizadas para usuarios.

## Contribucion
1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request
