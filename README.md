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

### Pasos para ejecutar

Antes de que nada, es necesario que la base de datos esté inicializada. Para ello, se puede utilizar docker-compose:

```bash
docker-compose up -d
```

Con eso listo, podemos avanzar con el setup de la aplicación:

1. Instalar las dependencias del sistema:

- En Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install libpq-dev gcc
```

- En MacOS con brew:

```bash
brew install postgresql
```

2. Instalar pipenv:

```bash
pip install pipenv
```

3. Instalar las dependencias del proyecto:

```bash
pipenv install
```

4. Configurar variable de entorno del sistema:

```bash
export PYTHONPATH=<path al repositorio>/app
```

5. Crear un archivo .env en el root del repositorio con el siguiente contenido:

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
SECRET_KEY=4SUbOhgTqwF5AAzR0SLooM3jrc2Q1gt9cgqgoiKVRb8 #generar una nueva con `secrets.token_urlsafe()`
SECURITY_PASSWORD_SALT='146320669432092624164254231479252972359' #generar una nueva con `str(secrets.SystemRandom().getrandbits(128))`
```

6. Correr la aplicación:

```bash
python ./app/start.py
```

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


