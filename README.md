# English Practice — Simulador de examen de inglés

Aplicación web para practicar inglés y ubicar al alumno en un nivel **básico, intermedio o avanzado**. Proyecto de parcial 2 y ordinario, desarrollado en **Python + Flask** con base de datos **MariaDB/MySQL** y arquitectura **MVC**.

## Estado del proyecto

| Módulo | Estado |
|---|---|
| Base de datos (modelo normalizado + banco de 80 preguntas) | Listo |
| Registro e inicio de sesión | Listo |
| Menú principal | Listo |
| Simulador de práctica (20 preguntas, 1 min c/u, hasta 5 intentos) | Listo |
| Simulador final (40 preguntas, hasta 2 intentos, cada reactivo = 2.5 pts) | Listo |
| Datos simulados | Pendiente |
| Dashboard (práctica vs. final) | Pendiente |

## Tecnologías

- Python 3.10 o superior
- Flask (servidor web y plantillas Jinja)
- PyMySQL (conexión a la BD)
- MariaDB 10.4 / MySQL (probado en MariaDB 10.4.32)

## Cómo correrlo

### 1. Clonar el repositorio

```bash
git clone <URL-DEL-REPOSITORIO>
cd <carpeta-del-repositorio>
```

### 2. Tener MariaDB/MySQL encendido

Si usas XAMPP, inicia el módulo **MySQL** desde su panel de control.

### 3. Crear la base de datos

El script crea la base `simulador_ingles` con todas las tablas y las 80 preguntas.

> **Ojo:** el script borra y recrea la base `simulador_ingles`. Si ya tenías datos ahí, se pierden.

Desde consola:

```bash
mysql -u root -p --default-character-set=utf8mb4 < database/simulador_ingles_mysql.sql
```

En XAMPP para Windows el ejecutable está en `C:\xampp\mysql\bin\mysql.exe`. También puedes importar el archivo desde phpMyAdmin (pestaña *Importar*).

Al final del script se ejecutan tres consultas de verificación; deben mostrar 25 / 35 / 20 preguntas por nivel y un total de 80.

### 4. Crear el entorno virtual e instalar dependencias

**Windows (PowerShell):**

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

En VS Code, selecciona ese intérprete con `Ctrl+Shift+P` → *Python: Select Interpreter*.

### 5. Configurar la conexión

Los valores por defecto sirven para una instalación local típica (XAMPP): host `localhost`, usuario `root`, contraseña vacía, base `simulador_ingles`.

Si tu configuración es distinta, cámbiala en `config.py` o con variables de entorno:

| Variable | Valor por defecto |
|---|---|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `3306` |
| `DB_USER` | `root` |
| `DB_PASSWORD` | *(vacía)* |
| `DB_NAME` | `simulador_ingles` |
| `SECRET_KEY` | clave de ejemplo (cámbiala en cualquier entorno real) |

Ejemplo en PowerShell:

```powershell
$env:DB_PASSWORD = "mi_contraseña"
```

### 6. Ejecutar

```bash
python run.py
```

Abre http://127.0.0.1:5000, crea una cuenta y presenta el examen de práctica.

## Ejecutar con Docker

Docker Desktop debe estar iniciado. Después, crea las variables locales a partir del ejemplo:

```powershell
Copy-Item .env.example .env
```

Edita las contraseñas de `.env` y ejecuta la aplicación con:

```powershell
docker compose up --build -d
```

La aplicación estará disponible en http://localhost:5000. Los datos de MySQL se conservan en el volumen Docker `mysql_data`. Para reiniciarlos desde cero:

```powershell
docker compose down -v
docker compose up --build -d
```

## Estructura del proyecto (MVC)

```
run.py                        punto de arranque
config.py                     configuración y reglas del simulador
requirements.txt              dependencias
app/
  __init__.py                 fábrica de la app; aquí se registran los controladores
  db.py                       conexión a MariaDB (una por petición)
  security.py                 login_required y protección CSRF
  models/                     M — acceso a datos y reglas de negocio
    usuario_model.py
    pregunta_model.py         selección aleatoria sin repetir
    practica_model.py         intentos de práctica, control del minuto, calificación y nivel
    final_model.py            lo mismo para el examen final (tablas *_finales)
  controllers/                C — rutas (blueprints de Flask)
    auth_controller.py        /registro  /login  /logout
    menu_controller.py        /menu
    practica_controller.py    /practica/...
    final_controller.py       /final/...
  views/templates/            V — plantillas HTML (Jinja)
  static/                     CSS y JavaScript
database/
  simulador_ingles_mysql.sql  script oficial de la BD (esquema + datos)
  sqlite_pruebas/             versión SQLite usada solo para pruebas locales
```

## Reglas del simulador de práctica

- Cada intento sortea **20 preguntas al azar**: 6 de nivel Básico, 9 Intermedio y 5 Avanzado. No se repiten dentro de la misma prueba.
- Cada pregunta tiene **60 segundos**. El tiempo lo controla el servidor (columna `fecha_presentada`), así que recargar la página no reinicia el reloj. Si se agota, la pregunta cuenta como incorrecta y se pasa a la siguiente.
- Cada pregunta vale **5 puntos**. Se aprueba con **70 % o más**.
- Máximo **5 intentos** por usuario. Si hay un examen sin terminar, el menú permite continuarlo.
- Las opciones se muestran en orden aleatorio.
- **Nivel alcanzado:** el más alto en el que el alumno logra al menos 70 % de las preguntas de ese nivel, exigiéndolo también en los niveles inferiores (Básico → Intermedio → Avanzado). Está implementado en `finalizar()` de `practica_model.py`.

## Reglas del simulador final

- Cada intento sortea **40 preguntas al azar**: 12 Básico, 18 Intermedio y 10 Avanzado. No se repiten dentro de la misma prueba.
- Máximo **2 intentos** por usuario. Cada pregunta vale **2.5 puntos** (100 / 40) y se aprueba con **70 % o más**.
- Funciona igual que la práctica: 60 segundos por pregunta controlados por el servidor, opciones en orden aleatorio, continuar un examen abierto y resultado con porcentaje, aprobado y nivel.
- El nivel se calcula con la misma regla que en la práctica, para que ambos exámenes sean comparables en el dashboard.

**Modo prueba (10 preguntas):** para probar sin tardar 40 minutos, arranca la app con la variable `FINAL_MODO_PRUEBA=1`. En PowerShell:

```powershell
$env:FINAL_MODO_PRUEBA = "1"
python run.py
```

Sin la variable, el examen es el real de 40 preguntas. Los intentos de prueba se guardan en la BD como cualquier otro; si te quedas sin intentos, borra los registros de `intentos_finales` de tu usuario o vuelve a cargar el script de `database/`.

Los parámetros (cantidad por nivel, segundos, intentos, porcentaje aprobatorio) están en `config.py`.

## Base de datos

Tablas principales:

| Tabla | Contenido |
|---|---|
| `niveles` | Básico, Intermedio, Avanzado |
| `usuarios` | Cuenta del alumno (contraseña con hash) |
| `preguntas` | Banco de 80 preguntas, con `imagen_url` opcional |
| `opciones` | 4 opciones por pregunta; exactamente una correcta |
| `intentos_practica` / `detalle_intentos_practica` | Intentos de práctica y sus 20 preguntas |
| `intentos_finales` / `detalle_intentos_finales` | Intentos del simulador final y sus 40 preguntas |

Restricciones importantes que ya están en la BD: no se puede repetir una pregunta dentro del mismo intento, los límites de 5 y 2 intentos, el tiempo máximo de 60 s y la coherencia entre calificación y `aprobado`.

El banco de preguntas se edita en `database/sqlite_pruebas/datos_preguntas.py` (fuente de los datos).

## Cómo agregar una funcionalidad nueva

Se sigue el mismo patrón que el módulo de práctica:

1. **Modelo:** crea `app/models/<nombre>_model.py` con las consultas SQL. Obtén la conexión con `get_db()` de `app/db.py`.
2. **Controlador:** crea `app/controllers/<nombre>_controller.py` con un `Blueprint` y sus rutas. Protege las rutas con `@login_required`.
3. **Vista:** crea las plantillas en `app/views/templates/` extendiendo `base.html`. Todo formulario POST debe incluir `<input type="hidden" name="_csrf" value="{{ csrf_token() }}">`.
4. **Registro:** agrega el blueprint en `app/__init__.py` (junto a los que ya están).
5. Si necesitas cambiar tablas, modifica `database/simulador_ingles_mysql.sql` y avisa al equipo para que todos vuelvan a cargarlo.

## Trabajo en equipo

- Cada integrante tiene su propia base de datos local; los datos de prueba (usuarios, intentos) no se comparten por Git.
- Trabaja en una rama por funcionalidad (`git checkout -b feature/simulador-final`) y abre un Pull Request hacia `main`.
- No subas la carpeta `venv/` ni contraseñas reales (el `.gitignore` ya los excluye).

## Problemas frecuentes

- **`ModuleNotFoundError: No module named 'flask'`**: falta instalar las dependencias o no está activo el entorno virtual. Activa `venv` y ejecuta `pip install -r requirements.txt`.
- **`Can't connect to MySQL server` / `Access denied`**: MariaDB no está encendido o la contraseña de `root` no coincide con la de `config.py`.
- **`Unknown database 'simulador_ingles'`**: falta cargar el script de `database/`.
- **Error 400 al enviar un formulario**: la sesión caducó; recarga la página e inténtalo de nuevo.
