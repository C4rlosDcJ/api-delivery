"""
================================================================================
ml_demand_forecast.py - Sistema de Pronostico de Demanda
================================================================================

Descripcion:
    Modulo de prediccion de demanda para restaurantes usando Machine Learning.
    Permite pronosticar el numero de pedidos esperados y analizar patrones
    de horas pico para optimizar operaciones.

Algoritmos implementados:
    - Random Forest Regressor: Prediccion de demanda basada en dia de semana
    - Analisis de horas pico: Identificacion de patrones temporales

Caracteristicas del modelo:
    - Variables de entrada: dia de la semana, indicador de fin de semana
    - Variable objetivo: numero total de pedidos por dia
    - Metricas: MAE (Error Absoluto Medio), R2 (Coeficiente de Determinacion)

Dependencias:
    - pandas: Manipulacion de datos
    - numpy: Operaciones numericas
    - sklearn: Random Forest, Standard Scaler, metricas

Uso:
    forecaster = DemandForecast(db_connection)
    prediction = forecaster.predict_demand(restaurant_id, target_date)
    peak_analysis = forecaster.get_peak_hours_analysis(restaurant_id)

================================================================================
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import datetime, timedelta
import joblib


class DemandForecast:
    """
    Sistema de pronostico de demanda para restaurantes.
    
    Utiliza Random Forest para predecir la demanda diaria basada en
    patrones historicos de pedidos. Tambien proporciona analisis de
    horas pico para optimizar operaciones.
    
    Attributes:
        db: Conexion a la base de datos MongoDB
        models: Diccionario de modelos entrenados por restaurante
        scalers: Diccionario de escaladores por restaurante
    """
    
    def __init__(self, db_connection):
        """
        Inicializa el sistema de pronostico de demanda.
        
        Args:
            db_connection: Conexion activa a la base de datos MongoDB
        """
        self.db = db_connection
        self.models = {}
        self.scalers = {}
    
    def prepare_restaurant_data(self, restaurant_id, days=30):
        """
        Prepara datos historicos para entrenar el modelo de un restaurante.
        
        Obtiene los pedidos de los ultimos N dias y los agrupa por dia,
        calculando metricas como total de pedidos, ingresos y valor promedio.
        
        Args:
            restaurant_id: ID del restaurante
            days: Numero de dias de historial a considerar
            
        Returns:
            DataFrame: Dataset con metricas diarias o None si no hay datos
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Obtener pedidos entregados del restaurante
            orders = list(self.db['orders'].find({
                'restaurantId': restaurant_id,
                'status': 'delivered',
                'createdAt': {'$gte': start_date, '$lte': end_date}
            }))
            
            if not orders:
                return None
            
            # Crear dataset diario
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            daily_data = []
            
            for date in date_range:
                day_orders = [o for o in orders if o['createdAt'].date() == date.date()]
                
                daily_data.append({
                    'date': date,
                    'day_of_week': date.weekday(),
                    'is_weekend': 1 if date.weekday() >= 5 else 0,
                    'total_orders': len(day_orders),
                    'total_revenue': sum(o.get('total', 0) for o in day_orders),
                    'avg_order_value': np.mean([o.get('total', 0) for o in day_orders]) if day_orders else 0
                })
            
            return pd.DataFrame(daily_data)
            
        except Exception as e:
            print(f"Error preparando datos: {e}")
            return None
    
    def train_restaurant_model(self, restaurant_id):
        """
        Entrena un modelo de prediccion de demanda para un restaurante.
        
        Utiliza Random Forest con 100 arboles para capturar patrones
        no lineales en la demanda. Requiere al menos 7 dias de datos.
        
        Args:
            restaurant_id: ID del restaurante
            
        Returns:
            dict: Diccionario con modelo, scaler y metricas de rendimiento
        """
        try:
            data = self.prepare_restaurant_data(restaurant_id)
            
            if data is None or len(data) < 7:
                print(f"No hay suficientes datos para entrenar modelo del restaurante {restaurant_id}")
                return None
            
            # Preparar caracteristicas
            features = ['day_of_week', 'is_weekend']
            X = data[features]
            y = data['total_orders']
            
            # Escalar caracteristicas para mejor rendimiento
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Entrenar modelo Random Forest
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            
            # Guardar modelo y scaler
            self.models[restaurant_id] = model
            self.scalers[restaurant_id] = scaler
            
            # Evaluar modelo
            predictions = model.predict(X_scaled)
            mae = mean_absolute_error(y, predictions)
            r2 = r2_score(y, predictions)
            
            print(f"Modelo entrenado para restaurante {restaurant_id}")
            print(f"   MAE: {mae:.2f}, R2: {r2:.2f}")
            
            return {
                'model': model,
                'scaler': scaler,
                'performance': {'mae': mae, 'r2': r2}
            }
            
        except Exception as e:
            print(f"Error entrenando modelo: {e}")
            return None
    
    def predict_demand(self, restaurant_id, date):
        """
        Predice la demanda para un restaurante en una fecha especifica.
        
        Si el modelo no existe, lo entrena automaticamente. La prediccion
        se basa en el dia de la semana y si es fin de semana.
        
        Args:
            restaurant_id: ID del restaurante
            date: Fecha para la prediccion (datetime)
            
        Returns:
            int: Numero de pedidos predichos o None si hay error
        """
        try:
            # Entrenar modelo si no existe
            if restaurant_id not in self.models:
                model_info = self.train_restaurant_model(restaurant_id)
                if not model_info:
                    return None
            
            model = self.models[restaurant_id]
            scaler = self.scalers[restaurant_id]
            
            # Preparar caracteristicas para la fecha objetivo
            day_of_week = date.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            
            features = np.array([[day_of_week, is_weekend]])
            features_scaled = scaler.transform(features)
            
            # Realizar prediccion
            prediction = model.predict(features_scaled)[0]
            
            # Asegurar que la prediccion no sea negativa
            return max(0, round(prediction))
            
        except Exception as e:
            print(f"Error prediciendo demanda: {e}")
            return None
    
    def get_peak_hours_analysis(self, restaurant_id):
        """
        Analiza las horas pico de un restaurante.
        
        Examina los ultimos 14 dias de pedidos para identificar
        las horas con mayor volumen de ordenes.
        
        Args:
            restaurant_id: ID del restaurante
            
        Returns:
            dict: Analisis con horas pico, total de pedidos y promedio diario
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=14)
            
            orders = list(self.db['orders'].find({
                'restaurantId': restaurant_id,
                'status': 'delivered',
                'createdAt': {'$gte': start_date, '$lte': end_date}
            }))
            
            if not orders:
                return None
            
            # Analizar distribucion por hora
            hour_counts = {}
            for order in orders:
                hour = order['createdAt'].hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # Identificar las 3 horas pico
            total_orders = sum(hour_counts.values())
            peak_hours = []
            
            for hour, count in sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                percentage = (count / total_orders) * 100
                peak_hours.append({
                    'hour': hour,
                    'orders': count,
                    'percentage': round(percentage, 1)
                })
            
            return {
                'peak_hours': peak_hours,
                'total_analysis_period': len(orders),
                'average_daily_orders': len(orders) / 14
            }
            
        except Exception as e:
            print(f"Error analizando horas pico: {e}")
            return None