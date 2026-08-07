# AdsoLab Backend

## ¿Qué es AdsoLab?

Es una plataforma para el modelado y validación del equilibrio en los procesos de adsorción de contaminantes.

La misma está implementada en dos partes:

- Backend: el presente repositorio.
- Frontend: https://github.com/federicorossini09/adsolab-front

## Descripción

AdsoLab Backend es un servicio web desarrollado en Python utilizando Flask que permite:

- Ajuste de modelos no lineales para datos de adsorción.
- Comparación entre modelos con análisis estadístico detallado.

## Ejecutar la aplicación localmente

### Requisitos

- Python 3.10 instalado (se recomienda usar `pyenv` o similar).
- Docker compose https://docs.docker.com/compose/install/ (recomendado para la base de datos).

### Paso 1 — Levantar la base de datos

Esto levanta PostgreSQL y aplica las migraciones automáticamente:

```bash
docker-compose up -d
```

### Paso 2 — Instalar dependencias del sistema

- En Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install libpq-dev gcc
```

- En MacOS con brew:

```bash
brew install postgresql
```

- En Windows: no se requieren dependencias adicionales del sistema.

### Paso 3 — Instalar pipenv y dependencias del proyecto

```bash
pip install pipenv
pipenv install
```

### Paso 4 — Crear el archivo `.env`

Crear un archivo `.env` en la raíz del repositorio con el siguiente contenido:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/adsolab?sslmode=disable
REACTORAPP_ADSORBATES=/api/adsorbato/
REACTORAPP_ADSORBENTS=/api/adsorbente/
REACTORAPP_AUTH=/api/auth/login
REACTORAPP_BASE_URL=https://laquisihereactorapp.fi.uba.ar
REACTORAPP_PASS=12345678
REACTORAPP_USER=frossini@fi.uba.ar
DEV_USER_EMAIL=adsolab@dev.com
DEV_USER_PASSWORD=password
SECRET_KEY=<generar con: python -c "import secrets; print(secrets.token_urlsafe())">
SECURITY_PASSWORD_SALT=<generar con: python -c "import secrets; print(secrets.SystemRandom().getrandbits(128))">
env=development
```

### Paso 5 — Correr la aplicación

#### Linux / MacOS

Activar el entorno virtual y ejecutar:

```bash
source .venv/bin/activate
python app/start.py
```

O sin activar el entorno:

```bash
.venv/bin/python app/start.py
```

#### Windows (PowerShell)

Activar el entorno virtual una vez por sesión de terminal y ejecutar:

```powershell
.venv\Scripts\Activate.ps1
python app/start.py
```

O sin activar el entorno:

```powershell
.venv\Scripts\python.exe app/start.py
```

El servidor quedará disponible en **http://127.0.0.1:5000**.

---

## Especificación de la API

La lista de servicios que se exponen se encuentra en este archivo:
[openapi-spec.yml](openapi-spec.yml)

Para visualizarla, se puede acceder a https://editor.swagger.io/ y luego pegar el contenido del archivo.

## Detalles de implementación

### Autenticación y autorización

La aplicación utiliza la librería [flask-security](https://flask-security-too.readthedocs.io/en/stable/index.html) para
la autenticación y autorización de algunos servicios.  
Se admiten dos formas de autenticación: basada en sesión y token. La primera es utilizada desde el frontend mientras que
la segunda es más conveniente para cuando se ejecuta la API desde otro servicio web.

Para obtener un token, se puede utilizar el servicio `POST /auth-token` cuyo body debe incluir email y password del
usuario.

**Ejemplo de autenticación con token:**

```bash
# 1. Obtener el token
curl -X POST http://127.0.0.1:5000/auth-token \
  -H "Content-Type: application/json" \
  -d '{"email":"tu_email@example.com","password":"tu_password"}'

# Respuesta:
# {"token":"eyJ2ZXIiOiI1IiwidWlkIjoiNzY0MDI2Njk0YTY2NDEyZmI2YzVmMTYwZmNmYjUxNDgiLCJmc19wYWEiOjE3ODIyNzQxNDYuODgzNzA5LCJleHAiOjB9.ajtYYg.dHf8xLo3OMpm1rRizzWYaq69JCA","user_id":1,"email":"tu_email@example.com"}

# 2. Usar el token en endpoints protegidos (Header Authorization)
curl http://127.0.0.1:5000/kinetics/sample \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"time":[0,5,10],"qt":[0,12.5,22.3],"adsorbate_id":1,"adsorbent_id":1}'

# 3. Alternativamente, usar el token como query parameter
curl "http://127.0.0.1:5000/kinetics/sample?auth_token=TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"time":[0,5,10],"qt":[0,12.5,22.3],"adsorbate_id":1,"adsorbent_id":1}'
```

### Migraciones de base de datos

Para el manejo de las migraciones se utilizó la herramienta [dbmate](https://github.com/amacneil/dbmate). Las mismas se
ejecutan localmente vía docker-compose y en los entornos de prueba y producción vía actions de Github.

Para crear una nueva migración, ejecutar el siguiente comando:

```bash
dbmate new <nombre de la migración>
```

Esto creará un nuevo archivo .sql dentro de la carpeta `db/migrations`. El mismo está compuesto por dos partes:

- `migrate:up`: donde se debe agregar la sentencia con el cambio a aplicar.
- `migrate:down`: donde se agrega la sentencia para deshacer los cambios en la sección anterior. La sección debe estar,
  aunque no es obligatorio completarla.


