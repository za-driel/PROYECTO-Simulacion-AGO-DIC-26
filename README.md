# English Practice — Simulador de examen de inglés

Aplicación web para practicar inglés y ubicar al alumno en un nivel **básico, intermedio o avanzado**. Proyecto de parcial 2 y ordinario, desarrollado en **Python + Flask** con base de datos **MySQL 8.4**, arquitectura **MVC** y ejecución completa en **Docker**.

## Estado del proyecto

| Módulo | Estado |
|---|---|
| Base de datos (modelo normalizado + banco de 80 preguntas) | Listo |
| Inicio de sesión con roles (alumno y administrador) | Listo |
| Panel de administración (creación de cuentas) | Listo |
| Menú principal del alumno | Listo |
| Simulador de práctica (20 preguntas, 1 min c/u, hasta 5 intentos) | Listo |
| Simulador final (40 preguntas, hasta 2 intentos, cada reactivo = 2.5 pts) | Listo |
| Dashboard administrativo (práctica vs. final) | Listo |
| Ejecución con Docker | Listo |
| Datos simulados | Pendiente |

## Tecnologías

- Python 3.12 y Flask (servidor web y plantillas Jinja)
- PyMySQL (conexión a la BD) y gunicorn (servidor de producción dentro del contenedor)
- MySQL 8.4
- Docker y Docker Compose
- Chart.js (gráficas del dashboard)

## Cómo correrlo con Docker

Todo el proyecto corre en contenedores: la aplicación y la base de datos. Así el equipo usa exactamente la misma versión de MySQL sin instalar nada más que Docker.

### 1. Descargar Docker Desktop

**Antes de iniciar con la instalacion**, abre PowerShell como administrador y ejecuta:

```powershell
wsl --install
```
Una vez realizado el comando en PowerShell, proceder con la instalación de Docker

Descárgalo desde https://www.docker.com/products/docker-desktop/ e instálalo. Ábrelo y espera a que indique que está en ejecución.

Reinicia el equipo, vuelve a abrir Docker Desktop (o instálalo de nuevo si no se había instalado) y continúa.

### 2. Obtener el proyecto

Clona el repositorio o descarga el ZIP y descomprímelo:

```bash
git clone <[URL-DEL-REPOSITORIO](https://github.com/za-driel/PROYECTO-Simulacion-AGO-DIC-26)>
cd <carpeta-del-repositorio>
```

Abre una terminal **dentro de la carpeta que contiene `docker-compose.yml`**.

### 3. Crear el archivo `.env`

En esa misma carpeta crea un archivo llamado `.env` (sin nombre antes del punto) con este contenido:

```
SECRET_KEY=cualquierkey
DB_HOST=db
DB_PORT=3306
DB_NAME=simulador_ingles
DB_USER=simulador
DB_PASSWORD=simulador_password
MYSQL_ROOT_PASSWORD=root_password
FINAL_MODO_PRUEBA=0
```

También puedes copiar el ejemplo que viene en el repositorio y editarlo:

```powershell
Copy-Item .env.example .env
```

| Variable | Para qué sirve |
|---|---|
| `SECRET_KEY` | Clave con la que Flask firma las sesiones. Pon cualquier texto largo. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Base de datos y usuario que crea MySQL la primera vez. |
| `MYSQL_ROOT_PASSWORD` | Contraseña del usuario `root` de MySQL. |
| `DB_HOST`, `DB_PORT` | Docker Compose los fija por su cuenta (la app se conecta al servicio `db`), así que no necesitas cambiarlos. |
| `FINAL_MODO_PRUEBA` | `0` = examen final real de 40 preguntas. `1` = modo prueba de 10 preguntas. |

El archivo `.env` **no se sube a Git** (ya está en `.gitignore`). Cada integrante crea el suyo.

### 4. Levantar la aplicación

```bash
docker compose up -d --build
```

La primera vez tarda unos minutos porque descarga las imágenes y construye la aplicación. MySQL carga automáticamente el script `database/simulador_ingles_mysql.sql` (tablas, 80 preguntas y la cuenta de administrador inicial).

### 5. Abrir la aplicación

Entra a http://localhost:5000

## Acceso y cuentas

- **Los alumnos no se registran solos.** Las cuentas las crea un administrador desde el panel `/administracion` (nombre, correo, contraseña de al menos 8 caracteres y rol).
- **Cuenta de administrador inicial** (solo para desarrollo y pruebas): correo `dev@dev.dev`, contraseña `simulacion`. Con ella entras, creas las cuentas de tus alumnos y de otros administradores.
- Al iniciar sesión, el administrador entra al dashboard y el alumno entra al menú de exámenes. Un administrador no puede presentar exámenes.

## Comandos útiles de Docker

| Qué quieres hacer | Comando |
|---|---|
| Ver el estado de los contenedores | `docker compose ps` |
| Ver los mensajes y errores de la app | `docker compose logs -f web` |
| Detener todo (se conservan los datos) | `docker compose down` |
| Volver a iniciar sin reconstruir | `docker compose up -d` |
| Aplicar cambios de código | `docker compose up -d --build` |
| **Reiniciar la BD desde cero** (borra todos los datos) | `docker compose down -v` y luego `docker compose up -d --build` |
| Entrar a MySQL desde la terminal | `docker compose exec db mysql -u root -p simulador_ingles` |

Los datos de MySQL viven en el volumen de Docker `mysql_data`, así que sobreviven aunque apagues los contenedores. El script SQL **solo se ejecuta cuando el volumen está vacío**: si modificas `database/simulador_ingles_mysql.sql`, necesitas `docker compose down -v` para que se vuelva a cargar.

## Estructura del proyecto (MVC)

```
docker-compose.yml            servicios: db (MySQL 8.4) y web (Flask)
Dockerfile                    imagen de la aplicación (Python 3.12 + gunicorn)
.env.example                  ejemplo de variables de entorno
run.py                        punto de arranque
config.py                     configuración y reglas del simulador
requirements.txt              dependencias
app/
  __init__.py                 fábrica de la app; aquí se registran los controladores
  db.py                       conexión a MySQL (una por petición)
  security.py                 login_required, admin_required y protección CSRF
  models/                     M — acceso a datos y reglas de negocio
    usuario_model.py
    pregunta_model.py         selección aleatoria sin repetir
    practica_model.py         intentos de práctica, control del minuto, calificación y nivel
    final_model.py            lo mismo para el examen final (tablas *_finales)
    dashboard_model.py        indicadores del dashboard
  controllers/                C — rutas (blueprints de Flask)
    auth_controller.py        /login  /logout
    menu_controller.py        /menu
    practica_controller.py    /practica/...
    final_controller.py       /final/...
    admin_controller.py       /administracion  /administracion/dashboard
  views/templates/            V — plantillas HTML (Jinja)
  static/                     CSS y JavaScript
database/
  simulador_ingles_mysql.sql  script oficial de la BD (esquema + datos); lo carga Docker
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

**Modo prueba (10 preguntas):** para probar sin tardar 40 minutos, cambia `FINAL_MODO_PRUEBA=1` en tu `.env` y aplica el cambio con:

```bash
docker compose up -d
```

Los intentos de prueba se guardan en la BD como cualquier otro. Si te quedas sin intentos, reinicia la BD con `docker compose down -v` y `docker compose up -d --build`.

## Dashboard administrativo

Disponible para administradores en `/administracion/dashboard`. Muestra totales de alumnos y administradores, prácticas y finales terminados, promedios, y gráficas de práctica vs. examen final, calificación por intento, aprobados y niveles obtenidos en el examen final.

## Base de datos

Tablas principales:

| Tabla | Contenido |
|---|---|
| `niveles` | Básico, Intermedio, Avanzado |
| `usuarios` | Cuenta (contraseña con hash) y rol: `alumno` o `administrador` |
| `preguntas` | Banco de 80 preguntas, con `imagen_url` opcional |
| `opciones` | 4 opciones por pregunta; exactamente una correcta |
| `intentos_practica` / `detalle_intentos_practica` | Intentos de práctica y sus 20 preguntas |
| `intentos_finales` / `detalle_intentos_finales` | Intentos del simulador final y sus 40 preguntas |

Restricciones importantes que ya están en la BD: no se puede repetir una pregunta dentro del mismo intento, los límites de 5 y 2 intentos, el tiempo máximo de 60 s y la coherencia entre calificación y `aprobado`.

## Cómo agregar una funcionalidad nueva

Se sigue el mismo patrón que el módulo de práctica:

1. **Modelo:** crea `app/models/<nombre>_model.py` con las consultas SQL. Obtén la conexión con `get_db()` de `app/db.py`.
2. **Controlador:** crea `app/controllers/<nombre>_controller.py` con un `Blueprint` y sus rutas. Protege las rutas con `@login_required` (o `@admin_required` si son de administración).
3. **Vista:** crea las plantillas en `app/views/templates/` extendiendo `base.html`. Todo formulario POST debe incluir `<input type="hidden" name="_csrf" value="{{ csrf_token() }}">`.
4. **Registro:** agrega el blueprint en `app/__init__.py` (junto a los que ya están).
5. Si necesitas cambiar tablas, modifica `database/simulador_ingles_mysql.sql`, avisa al equipo y reinicia tu BD con `docker compose down -v` y `docker compose up -d --build`.
6. Para ver tus cambios de código ejecuta `docker compose up -d --build`.

## Trabajo en equipo

- Cada integrante tiene su propia base de datos local (en su volumen de Docker); los datos de prueba no se comparten por Git.
- Trabaja en una rama por funcionalidad (`git checkout -b feature/nombre`) y abre un Pull Request hacia `main`.
- No subas tu `.env` ni contraseñas reales.

## Problemas frecuentes

- **`Cannot connect to the Docker daemon` / `docker: command not found`:** Docker Desktop no está abierto o aún no termina de iniciar. Ábrelo y espera a que diga que está en ejecución.
- **Error de WSL 2 en Windows:** ejecuta `wsl --install` en PowerShell como administrador y reinicia el equipo.
- **`variable is not set` o la app no inicia:** falta el archivo `.env` o está en otra carpeta. Debe estar junto a `docker-compose.yml`.
- **El puerto 5000 ya está en uso:** en `docker-compose.yml` cambia `"5000:5000"` por `"5001:5000"` y entra a http://localhost:5001.
- **Cambié el script SQL y no se nota:** el script solo corre con el volumen vacío. Usa `docker compose down -v` y vuelve a levantar.
- **La app falla al arrancar:** revisa `docker compose logs -f web`. Si dice que no conecta a la BD, espera unos segundos: MySQL tarda en estar listo la primera vez.
- **Error 400 al enviar un formulario:** la sesión caducó; recarga la página e inténtalo de nuevo.
