"""Configuración de las reglas del simulador."""
import os


class Config:
    # --- Reglas del simulador de práctica ---
    # nivel_id -> cantidad de preguntas (1 = Básico, 2 = Intermedio, 3 = Avanzado)
    PRACTICA_PREGUNTAS_POR_NIVEL = {1: 6, 2: 7, 3: 7}      # total = 20
    PRACTICA_MAX_INTENTOS = 5
    PRACTICA_PUNTOS_POR_PREGUNTA = 5                        # 20 x 5 = 100
    # --- Reglas del simulador final ---
    # Modo prueba (10 preguntas) para probar rápido:  FINAL_MODO_PRUEBA=1   (PowerShell: $env:FINAL_MODO_PRUEBA = "1")
    FINAL_MODO_PRUEBA = os.environ.get("FINAL_MODO_PRUEBA") == "1"
    FINAL_PREGUNTAS_POR_NIVEL = {1: 3, 2: 3, 3: 4} if FINAL_MODO_PRUEBA else {1: 13, 2: 13, 3: 14}   # real: total = 40
    FINAL_MAX_INTENTOS = 2          # cada reactivo vale 100 / total (40 x 2.5 = 100)

    # --- Reglas comunes ---
    # Preguntas con imagen en cada bloque de nivel: (mínimo, máximo). Se sortea la cantidad dentro del rango.
    IMAGENES_POR_NIVEL = (2, 4)
    SEGUNDOS_POR_PREGUNTA = 60
    SEGUNDOS_GRACIA = 3          # tolerancia por latencia de red al enviar la respuesta
    PORCENTAJE_APROBATORIO = 70
