"""
================================================================================
ml_recommendations.py - Sistema de Recomendaciones con Machine Learning
================================================================================

Descripcion:
    Modulo de recomendaciones basado en Machine Learning para la plataforma
    de delivery. Implementa similitud de contenido usando TF-IDF y similitud
    coseno para recomendar platillos y restaurantes.

Algoritmos implementados:
    - Similitud de platillos: TF-IDF sobre nombre, descripcion y tags
    - Similitud de restaurantes: TF-IDF sobre nombre, descripcion y tipos de cocina
    - Recomendaciones personalizadas: Basadas en historial de pedidos del usuario

Dependencias:
    - pandas: Manipulacion de datos
    - numpy: Operaciones numericas
    - sklearn: TF-IDF Vectorizer y similitud coseno
    - pymongo: Conexion a base de datos

Uso:
    recommender = RecommendationSystem(db_connection)
    similar = recommender.get_similar_dishes(dish_id, limit=5)
    personalized = recommender.get_personalized_recommendations(user_id)

================================================================================
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from pymongo import MongoClient
import joblib
import os


class RecommendationSystem:
    """
    Sistema de recomendaciones para platillos y restaurantes.
    
    Utiliza tecnicas de procesamiento de lenguaje natural (TF-IDF) y
    similitud coseno para encontrar items similares y generar
    recomendaciones personalizadas basadas en el historial del usuario.
    
    Attributes:
        db: Conexion a la base de datos MongoDB
        dish_similarity_model: Modelo de similitud entre platillos
        restaurant_similarity_model: Modelo de similitud entre restaurantes
        user_preferences_model: Modelo de preferencias de usuario
    """
    
    def __init__(self, db_connection):
        """
        Inicializa el sistema de recomendaciones.
        
        Args:
            db_connection: Conexion activa a la base de datos MongoDB
        """
        self.db = db_connection
        self.dish_similarity_model = None
        self.restaurant_similarity_model = None
        self.user_preferences_model = None
        
    def build_dish_similarity_model(self):
        """
        Construye el modelo de similitud entre platillos.
        
        Procesa todos los platillos disponibles, extrae caracteristicas
        textuales (nombre, descripcion, tags) y calcula la matriz de
        similitud coseno usando vectorizacion TF-IDF.
        """
        try:
            # Obtener datos de platillos activos
            dishes = list(self.db['dishes'].find({'isAvailable': True}))
            
            if not dishes:
                print("No hay platillos para entrenar el modelo")
                return
            
            # Crear caracteristicas textuales para cada platillo
            dish_features = []
            dish_ids = []
            
            for dish in dishes:
                features = f"{dish.get('name', '')} {dish.get('description', '')} {' '.join(dish.get('tags', []))} {dish.get('categoryId', '')}"
                dish_features.append(features)
                dish_ids.append(str(dish['_id']))
            
            # Vectorizar texto usando TF-IDF con stopwords en espanol
            vectorizer = TfidfVectorizer(stop_words='spanish', max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(dish_features)
            
            # Calcular matriz de similitud coseno
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            self.dish_similarity_model = {
                'similarity_matrix': similarity_matrix,
                'dish_ids': dish_ids,
                'vectorizer': vectorizer
            }
            
            print(f"Modelo de similitud de platillos entrenado con {len(dish_ids)} platillos")
            
        except Exception as e:
            print(f"Error entrenando modelo de platillos: {e}")
    
    def build_restaurant_similarity_model(self):
        """
        Construye el modelo de similitud entre restaurantes.
        
        Similar al modelo de platillos, pero usando caracteristicas
        especificas de restaurantes como tipos de cocina y ubicacion.
        """
        try:
            restaurants = list(self.db['restaurants'].find({'isActive': True}))
            
            if not restaurants:
                print("No hay restaurantes para entrenar el modelo")
                return
            
            restaurant_features = []
            restaurant_ids = []
            
            for restaurant in restaurants:
                features = f"{restaurant.get('name', '')} {restaurant.get('description', '')} {' '.join(restaurant.get('cuisineTypes', []))} {restaurant.get('address', {}).get('city', '')}"
                restaurant_features.append(features)
                restaurant_ids.append(str(restaurant['_id']))
            
            vectorizer = TfidfVectorizer(stop_words='spanish', max_features=800)
            tfidf_matrix = vectorizer.fit_transform(restaurant_features)
            
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            self.restaurant_similarity_model = {
                'similarity_matrix': similarity_matrix,
                'restaurant_ids': restaurant_ids,
                'vectorizer': vectorizer
            }
            
            print(f"Modelo de similitud de restaurantes entrenado con {len(restaurant_ids)} restaurantes")
            
        except Exception as e:
            print(f"Error entrenando modelo de restaurantes: {e}")
    
    def get_similar_dishes(self, dish_id, limit=5):
        """
        Obtiene platillos similares a uno dado.
        
        Args:
            dish_id: ID del platillo de referencia
            limit: Numero maximo de platillos similares a retornar
            
        Returns:
            list: Lista de diccionarios con dishId y similarityScore
        """
        if not self.dish_similarity_model:
            self.build_dish_similarity_model()
        
        try:
            dish_ids = self.dish_similarity_model['dish_ids']
            similarity_matrix = self.dish_similarity_model['similarity_matrix']
            
            if str(dish_id) not in dish_ids:
                return []
            
            idx = dish_ids.index(str(dish_id))
            similarity_scores = list(enumerate(similarity_matrix[idx]))
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
            
            # Excluir el platillo mismo y obtener los mas similares
            similar_dishes = []
            for i, score in similarity_scores[1:limit+1]:
                similar_dishes.append({
                    'dishId': dish_ids[i],
                    'similarityScore': float(score)
                })
            
            return similar_dishes
            
        except Exception as e:
            print(f"Error obteniendo platillos similares: {e}")
            return []
    
    def get_similar_restaurants(self, restaurant_id, limit=5):
        """
        Obtiene restaurantes similares a uno dado.
        
        Args:
            restaurant_id: ID del restaurante de referencia
            limit: Numero maximo de restaurantes similares a retornar
            
        Returns:
            list: Lista de diccionarios con restaurantId y similarityScore
        """
        if not self.restaurant_similarity_model:
            self.build_restaurant_similarity_model()
        
        try:
            restaurant_ids = self.restaurant_similarity_model['restaurant_ids']
            similarity_matrix = self.restaurant_similarity_model['similarity_matrix']
            
            if str(restaurant_id) not in restaurant_ids:
                return []
            
            idx = restaurant_ids.index(str(restaurant_id))
            similarity_scores = list(enumerate(similarity_matrix[idx]))
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
            
            similar_restaurants = []
            for i, score in similarity_scores[1:limit+1]:
                similar_restaurants.append({
                    'restaurantId': restaurant_ids[i],
                    'similarityScore': float(score)
                })
            
            return similar_restaurants
            
        except Exception as e:
            print(f"Error obteniendo restaurantes similares: {e}")
            return []
    
    def get_personalized_recommendations(self, user_id, limit=10):
        """
        Obtiene recomendaciones personalizadas basadas en historial del usuario.
        
        Analiza los pedidos anteriores del usuario para identificar preferencias
        de categorias y restaurantes, luego sugiere platillos similares.
        
        Args:
            user_id: ID del usuario
            limit: Numero maximo de recomendaciones
            
        Returns:
            list: Lista de recomendaciones con dishId, name, reason y score
        """
        try:
            # Obtener historial de pedidos del usuario
            user_orders = list(self.db['orders'].find({
                'customerId': user_id,
                'status': 'delivered'
            }).sort('createdAt', -1).limit(50))
            
            if not user_orders:
                # Si no tiene historial, recomendar platillos populares
                popular_dishes = list(self.db['dishes'].find({
                    'isAvailable': True
                }).sort('totalOrders', -1).limit(limit))
                
                return [{
                    'dishId': str(dish['_id']),
                    'name': dish['name'],
                    'reason': 'Popular en la plataforma',
                    'score': dish.get('rating', 0)
                } for dish in popular_dishes]
            
            # Analizar preferencias del usuario
            user_preferences = self._analyze_user_preferences(user_orders)
            
            # Generar recomendaciones basadas en preferencias
            recommendations = self._generate_recommendations_from_preferences(user_preferences, limit)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generando recomendaciones personalizadas: {e}")
            return []
    
    def _analyze_user_preferences(self, user_orders):
        """
        Analiza las preferencias del usuario basado en su historial de pedidos.
        
        Extrae informacion sobre categorias favoritas, restaurantes frecuentes,
        rango de precios y preferencias de calificacion.
        
        Args:
            user_orders: Lista de pedidos del usuario
            
        Returns:
            dict: Diccionario con preferencias analizadas
        """
        preferences = {
            'favorite_categories': {},
            'favorite_restaurants': {},
            'price_range': [],
            'rating_preference': 0
        }
        
        total_orders = len(user_orders)
        total_rating = 0
        total_price = 0
        
        for order in user_orders:
            # Analizar restaurantes favoritos
            rest_id = str(order['restaurantId'])
            preferences['favorite_restaurants'][rest_id] = preferences['favorite_restaurants'].get(rest_id, 0) + 1
            
            # Analizar items y categorias
            for item in order.get('items', []):
                if 'dishId' in item:
                    dish = self.db['dishes'].find_one({'_id': item['dishId']})
                    if dish and 'categoryId' in dish:
                        cat_id = str(dish['categoryId'])
                        preferences['favorite_categories'][cat_id] = preferences['favorite_categories'].get(cat_id, 0) + 1
                
                total_price += item.get('subtotal', 0) / item.get('quantity', 1)
            
            # Analizar preferencia de rating
            if 'rating' in order and order['rating']:
                total_rating += order['rating'].get('foodRating', 0)
        
        # Calcular promedios
        if total_orders > 0:
            preferences['average_price'] = total_price / total_orders
            preferences['average_rating'] = total_rating / total_orders
        
        return preferences
    
    def _generate_recommendations_from_preferences(self, preferences, limit):
        """
        Genera recomendaciones basadas en las preferencias analizadas del usuario.
        
        Busca platillos en las categorias favoritas del usuario y los ordena
        por una combinacion de rating y popularidad.
        
        Args:
            preferences: Diccionario con preferencias del usuario
            limit: Numero maximo de recomendaciones
            
        Returns:
            list: Lista de recomendaciones ordenadas por score
        """
        try:
            # Obtener las 3 categorias favoritas
            favorite_categories = sorted(
                preferences['favorite_categories'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            category_ids = [cat[0] for cat in favorite_categories]
            
            # Buscar platillos en categorias favoritas
            query = {
                'isAvailable': True,
                'categoryId': {'$in': category_ids}
            }
            
            recommended_dishes = list(self.db['dishes'].find(query)
                .sort([('rating', -1), ('totalOrders', -1)])
                .limit(limit))
            
            recommendations = []
            for dish in recommended_dishes:
                # Calcular score combinando rating (70%) y popularidad (30%)
                recommendations.append({
                    'dishId': str(dish['_id']),
                    'name': dish['name'],
                    'reason': f"Basado en tus categorias favoritas",
                    'score': dish.get('rating', 0) * 0.7 + (dish.get('totalOrders', 0) / 100) * 0.3
                })
            
            # Ordenar por score y limitar resultados
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            print(f"Error generando recomendaciones: {e}")
            return []