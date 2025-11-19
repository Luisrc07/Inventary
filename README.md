# Sistema de Inventario InvWEB

Un sistema de gestión de inventario basado en la web, construido con Django y Tailwind CSS. Diseñado para gestionar el stock multi-departamento, controlar los movimientos y administrar usuarios basados en roles.

Este proyecto fue desarrollado como parte para mis pasantias informaticas, este proyecto fue ejecutado para el Centro Integral Cooperativo de Salud. Para la institucion agilizar los procesos y tener un seguimiento de productos de entrada, transferencia (departamento -> departamento) y salida. 

## 🚀 Características Principales

* **Gestión de Roles:** Sistema de autenticación con 3 niveles de usuario (Administrador, Gerente, Operador).
* **Permisos Dinámicos:** Los Gerentes y Operadores solo pueden ver y gestionar el stock de sus departamentos asignados.
* **Control de Movimientos:** Funcionalidad completa de Entradas, Salidas y Transferencias entre departamentos.
* **Lógica de Costos Avanzada:** Cálculo en tiempo real del costo por paquete y por unidad individual (ej. costo por guante) basado en la tasa de cambio.
* **Gestión de Departamentos:** Creación y "Desactivación" (Soft Delete) de departamentos.
* **Gestión de Usuarios:** Creación, edición y desactivación (Soft Delete) de usuarios por parte del Admin.
* **Formularios Dinámicos:** La interfaz de creación de movimientos cambia dinámicamente según el tipo de movimiento y el rol del usuario (usando JavaScript).
* **Generación de Reportes PDF:** Creación de reportes de stock por departamento usando WeasyPrint.

## 💻 Stack Tecnológico

* **Backend:** Python 3.12, Django 5.2
* **Frontend:** HTML, JavaScript (Vanilla y jQuery)
* **Estilos:** Tailwind CSS (gestionado con django-tailwind)
* **Base de Datos:** Postgres
* **Reportes:** WeasyPrint

## 🛠️ Instalación y Ejecución Local (Versión Corregida)

Sigue estos pasos para clonar y ejecutar el proyecto en una nueva computadora.

Prerrequisitos del Sistema
Antes de empezar, asegúrate de tener instaladas las siguientes herramientas en tu máquina:

* **Python:** (Versión 3.10 o superior).
* **Node.js y npm:** (Versión LTS recomendada).
* **Git:** Para clonar el repositorio.

---

### Pasos de Instalación
Sigue estos pasos para levantar el proyecto en un entorno de desarrollo local.

#### 1. Clonar el repositorio
    git clone https://github.com/Luisrc07/Inventary.git
    cd Inventary/InvWEB

#### 2. Crear y activar el entorno virtual
Un entorno virtual (venv) aísla las dependencias del proyecto.

##### gitbash
        python -m venv venv
        source venv/Scripts/activate

##### Windows     
        python -m venv venv
        .\venv\Scripts\activate

> *si esta activo veras (venv) al principio de la linea de tu terminal.*

#### 3. Instalar las dependencias de Python
El archivo requirements.txt contiene todas las librerías necesarias.

        pip install -r requirements.txt

#### 4.Configuración de PostgreSQL
Este proyecto usa PostgreSQL. Si no lo tienes instalado, sigue estos pasos:

###### 4.a. Instalar el Servidor PostgreSQL
Descarga: Ve al sitio web de EnterpriseDB (EDB) y descarga el instalador de PostgreSQL para Windows.

**Instala:**
Ejecuta el instalador. Deja todos los componentes por defecto (PostgreSQL Server y pgAdmin 4 son los más importantes).
¡Contraseña Maestra! Durante la instalación, te pedirá una contraseña de superusuario (para el usuario postgres). Esta es la contraseña "maestra" de tu servidor. No la olvides.
Deja el puerto por defecto (5432) y finaliza la instalación.

###### 4.b. Crear Usuario y Base de Datos
No usaremos la cuenta "maestra" en Django. Crearemos un usuario y una base de datos dedicados.

1. Abre pgAdmin 4: Búscalo en tu menú de Inicio. Te pedirá la contraseña "maestra" que acabas de crear para conectarte al servidor.

2. Crea un Usuario (Rol):

* En el panel izquierdo, haz clic derecho sobre Servers -> PostgreSQL -> Login/Group Roles -> Create -> Login/Group Role....
* Pestaña "General": Dale un nombre al usuario (Ej: inventario_user).
* Pestaña "Definition": Escribe una contraseña para este nuevo usuario (Ej: clave_django_123).
* Pestaña "Privileges": Asegúrate de que Can login? esté en Yes.
* Clic en Save.

3. Crea la Base de Datos:
* Haz clic derecho sobre Databases -> Create -> Database....
* Pestaña "General": Dale un nombre a la base de datos (Ej: inventario_db).
* Pestaña "Owner" (Propietario): Selecciona el usuario que acabas de crear (inventario_user).
* Clic en Save.

#### 5. Configurar settings.py de Django
Para esta configuracion tomaremos en cuenta que la base de datos ha sido creada con pgAdmin 4.

* Abre el archivo settings.py de tu proyecto.
* Busca la sección DATABASES y reemplaza la configuración de sqlite3 por esta:

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'inventario_db',         # El nombre de tu DB (Paso 4.b)
                'USER': 'inventario_user',         # El usuario que creaste (Paso 4.b)
                'PASSWORD': 'clave_django_123',  # La contraseña de ESE usuario (Paso 4.b)
                'HOST': 'localhost',             # O '127.0.0.1'
                'PORT': '5432',                  # El puerto por defecto
            }
        }

#### 6. Aplicar migraciones
Este comando usa la configuración de settings.py para construir las tablas de tu base de datos.

        python manage.py migrate

> *(Si ves un montón de "Applying... OK", ¡la conexión fue un éxito!)*

#### 7. Instalar y Construir TailwindCSS
Este proyecto usa django-tailwind para los estilos.

            # Instala las dependencias de Node.js que necesita Tailwind
            python manage.py tailwind install

            # Compila los archivos CSS por primera vez
            python manage.py tailwind build

#### 8. Creacion de SuperUsuario
El mismo proyecto lleva un seeder que limpia la bd y crea un superusuario administrador.
Sin embargo, como recomendacion puedes cambiar la contraseña y nombre de usuario de dicho superusuario
ya que contiene datos los cuales cualquiera podria acceder facilmente.

        python manage.py seed
>esto creara un superusuario admin la cual el user: admin contraseña: admin123

#### 9. Ejecuta los servidores:

En una Terminal 1 (compila el CSS):

            Bash

            python manage.py tailwind start
            

En una Terminal 2 (ejecuta el proyecto)
            Bash

            python manage.py runserver


¡Abre http://127.0.0.1:8000/ en tu navegador!

## 📄 Licencia

Este proyecto está distribuido bajo la **Licencia Pública General GNU v3.0 (GPLv3)**.

Esto significa que eres libre de usar, modificar y distribuir este software. Sin embargo, cualquier trabajo derivado o software que distribuyas que utilice este código **debe también ser licenciado bajo la GPLv3**, garantizando que el software permanezca libre y de código abierto para siempre.

Para ver el texto completo de la licencia, consulta el archivo [LICENSE](LICENSE) en este repositorio.