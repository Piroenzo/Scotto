# Scotto - Gestión de Proyectos

Scotto es una aplicación web moderna para gestión de proyectos inspirada en Trello, desarrollada con Python Flask, HTML, CSS y JavaScript. Permite organizar tareas en tableros Kanban, colaborar en equipo y recibir notificaciones por email.

## 🚀 Características

- **Sistema de Usuarios**: Registro, login y gestión de perfiles
- **Tableros Kanban**: Organiza tareas en listas visuales
- **Drag & Drop**: Mueve tarjetas entre listas con arrastrar y soltar
- **Colaboración**: Invita usuarios a tus tableros
- **Notificaciones**: Recibe alertas por email cuando las tareas vencen
- **Prioridades**: Marca tareas con diferentes niveles de prioridad
- **Fechas de Vencimiento**: Establece deadlines para tus tareas
- **Diseño Responsivo**: Funciona perfectamente en móviles y desktop

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python Flask
- **Base de Datos**: SQLite con SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Autenticación**: Flask-Login
- **Email**: Flask-Mail
- **Iconos**: Font Awesome
- **Fuentes**: Google Fonts (Inter)

## 📋 Requisitos Previos

- Python 3.7 o superior
- pip (gestor de paquetes de Python)

## 🔧 Instalación

1. **Clona el repositorio**:
```bash
git clone <url-del-repositorio>
cd scotto
```

2. **Crea un entorno virtual**:
```bash
python -m venv venv
```

3. **Activa el entorno virtual**:
   - **Windows**:
   ```bash
   venv\Scripts\activate
   ```
   - **macOS/Linux**:
   ```bash
   source venv/bin/activate
   ```

4. **Instala las dependencias**:
```bash
pip install -r requirements.txt
```

5. **Configura las variables de entorno**:
   Crea un archivo `.env` en la raíz del proyecto:
```env
SECRET_KEY=tu_clave_secreta_muy_segura
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=tu_contraseña_de_aplicacion
```

6. **Configura el email** (opcional):
   - Ve a tu cuenta de Gmail
   - Activa la verificación en dos pasos
   - Genera una contraseña de aplicación
   - Usa esa contraseña en `MAIL_PASSWORD`

7. **Ejecuta la aplicación**:
```bash
python app.py
```

8. **Abre tu navegador** y ve a `http://localhost:5000`

## 📧 Configuración de Email

Para que las notificaciones por email funcionen:

1. **Gmail**:
   - Activa la verificación en dos pasos
   - Ve a "Seguridad" > "Contraseñas de aplicación"
   - Genera una nueva contraseña para "Scotto"
   - Usa esa contraseña en `MAIL_PASSWORD`

2. **Otros proveedores**:
   - Modifica `app.py` con la configuración de tu proveedor
   - Cambia `MAIL_SERVER`, `MAIL_PORT` y `MAIL_USE_TLS` según corresponda

## 🎯 Cómo Usar Scotto

### 1. Registro e Inicio de Sesión
- Ve a la página principal y haz clic en "Registrarse"
- Completa el formulario con tu nombre de usuario, email y contraseña
- Inicia sesión con tus credenciales

### 2. Crear un Tablero
- En el dashboard, haz clic en "Nuevo Tablero"
- Completa el título y descripción
- Haz clic en "Crear Tablero"

### 3. Agregar Listas
- Dentro de tu tablero, haz clic en "Nueva Lista"
- Escribe el título de la lista (ej: "Por Hacer", "En Progreso", "Completado")
- Haz clic en "Crear Lista"

### 4. Crear Tarjetas
- En cualquier lista, haz clic en "Agregar Tarjeta"
- Completa el título, descripción, prioridad y fecha de vencimiento
- Haz clic en "Crear Tarjeta"

### 5. Mover Tarjetas
- Arrastra y suelta las tarjetas entre listas
- Las posiciones se guardan automáticamente

### 6. Invitar Usuarios
- En el dashboard, haz clic en el ícono de usuario en cualquier tablero
- Ingresa el email del usuario que quieres invitar
- El usuario recibirá una notificación por email

### 7. Editar y Eliminar
- Usa los íconos de editar (lápiz) y eliminar (basura) en tarjetas y listas
- Confirma las acciones de eliminación

## 🗄️ Estructura de la Base de Datos

La aplicación utiliza SQLite con las siguientes tablas:

- **User**: Usuarios del sistema
- **Board**: Tableros de proyectos
- **BoardMember**: Relación entre usuarios y tableros (permisos)
- **List**: Listas dentro de los tableros
- **Card**: Tarjetas/tareas dentro de las listas

## 🔒 Seguridad

- Contraseñas hasheadas con Werkzeug
- Autenticación con Flask-Login
- Validación de permisos en todas las operaciones
- Protección CSRF en formularios

## 🎨 Personalización

### Cambiar Colores
Modifica las variables CSS en `templates/base.html`:
```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #27ae60;
    --danger-color: #e74c3c;
}
```

### Agregar Nuevas Funcionalidades
- Las rutas API están en `app.py`
- Los templates están en `templates/`
- Los estilos están en `templates/base.html`

## 🚀 Despliegue

### Heroku
1. Crea un `Procfile`:
```
web: gunicorn app:app
```

2. Agrega `gunicorn` a `requirements.txt`

3. Configura las variables de entorno en Heroku

### VPS/Docker
1. Usa Gunicorn como servidor WSGI
2. Configura Nginx como proxy reverso
3. Usa PostgreSQL en lugar de SQLite para producción

## 🐛 Solución de Problemas

### Error de Base de Datos
```bash
# Elimina la base de datos y recréala
rm scotto.db
python app.py
```

### Error de Email
- Verifica las credenciales de Gmail
- Asegúrate de tener la verificación en dos pasos activada
- Usa una contraseña de aplicación, no tu contraseña normal

### Error de Dependencias
```bash
# Reinstala las dependencias
pip uninstall -r requirements.txt
pip install -r requirements.txt
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

Desarrollado con ❤️ para facilitar la gestión de proyectos y la colaboración en equipo.

---

**¡Disfruta organizando tus proyectos con Scotto!** 🎉 

## Despliegue en Render

### Opción 1: Despliegue Automático (Recomendado)

1. **Fork o clona este repositorio** en tu cuenta de GitHub

2. **Conecta con Render:**
   - Ve a [render.com](https://render.com)
   - Crea una cuenta o inicia sesión
   - Haz clic en "New +" y selecciona "Blueprint"

3. **Configura el Blueprint:**
   - Conecta tu repositorio de GitHub
   - Render detectará automáticamente el archivo `render.yaml`
   - Haz clic en "Apply"

4. **Configura las variables de entorno:**
   - Ve a tu servicio web en Render
   - En la sección "Environment", configura:
     - `MAIL_PASSWORD`: Tu contraseña de aplicación de Gmail
     - `SECRET_KEY`: Una clave secreta (se genera automáticamente)

5. **Espera el despliegue:**
   - Render creará automáticamente la base de datos PostgreSQL
   - Desplegará tu aplicación
   - Te dará una URL para acceder

### Opción 2: Despliegue Manual

1. **Crea una base de datos PostgreSQL:**
   - En Render, ve a "New +" → "PostgreSQL"
   - Elige el plan gratuito
   - Anota la URL de conexión

2. **Crea el servicio web:**
   - Ve a "New +" → "Web Service"
   - Conecta tu repositorio de GitHub
   - Configura:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app`
     - **Environment Variables:**
       - `DATABASE_URL`: URL de tu base de datos PostgreSQL
       - `SECRET_KEY`: Una clave secreta
       - `MAIL_USERNAME`: scottoadm@gmail.com
       - `MAIL_PASSWORD`: Tu contraseña de aplicación de Gmail
       - `SQLALCHEMY_TRACK_MODIFICATIONS`: false

## Configuración Local

### Requisitos

- Python 3.9+
- MySQL o PostgreSQL (opcional, usa SQLite por defecto)

### Instalación

1. **Clona el repositorio:**
   ```bash
   git clone <tu-repositorio>
   cd scotto
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura las variables de entorno:**
   Crea un archivo `.env` con:
   ```env
   SECRET_KEY=tu_clave_secreta_aqui
   DATABASE_URL=mysql://usuario:contraseña@localhost/scotto
   MAIL_USERNAME=tu_email@gmail.com
   MAIL_PASSWORD=tu_contraseña_de_aplicacion
   SQLALCHEMY_TRACK_MODIFICATIONS=False
   ```

4. **Ejecuta la aplicación:**
   ```bash
   python app.py
   ```

5. **Accede a la aplicación:**
   - Abre http://localhost:5000
   - Registra un usuario y comienza a usar Scotto

## Configuración de Email

Para que las notificaciones por email funcionen:

1. **Habilita la verificación en dos pasos** en tu cuenta de Gmail
2. **Genera una contraseña de aplicación:**
   - Ve a Configuración de Google Account
   - Seguridad → Verificación en dos pasos
   - Contraseñas de aplicación
   - Genera una nueva contraseña
3. **Usa esa contraseña** en la variable `MAIL_PASSWORD`

## Estructura del Proyecto

```
scotto/
├── app.py                 # Aplicación principal Flask
├── requirements.txt       # Dependencias de Python
├── render.yaml           # Configuración para Render
├── Procfile              # Configuración para Heroku/Render
├── runtime.txt           # Versión de Python
├── templates/            # Plantillas HTML
├── static/              # Archivos estáticos
├── uploads/             # Archivos subidos
├── migrations/          # Migraciones de base de datos
└── tests/               # Tests unitarios
```

## Tecnologías Utilizadas

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Base de Datos:** MySQL/PostgreSQL/SQLite
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Email:** Flask-Mail
- **Despliegue:** Render, Gunicorn

## Licencia

Este proyecto está bajo la Licencia MIT.

## Soporte

Si tienes problemas con el despliegue o la aplicación, puedes:
- Revisar los logs en Render
- Verificar la configuración de las variables de entorno
- Asegurarte de que la base de datos esté correctamente configurada 