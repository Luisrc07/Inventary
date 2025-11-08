# Sistema de Inventario InvWEB

Un sistema de gestión de inventario basado en la web, construido con Django y Tailwind CSS. Diseñado para gestionar el stock multi-departamento, controlar los movimientos y administrar usuarios basados en roles.

Este proyecto fue desarrollado como parte de [Menciona si fue para tu pasantía, un proyecto personal, etc.].

## 🚀 Características Principales

**Gestión de Roles:** Sistema de autenticación con 3 niveles de usuario (Administrador, Gerente, Operador).

**Permisos Dinámicos:** Los Gerentes y Operadores solo pueden ver y gestionar el stock de sus departamentos asignados.

**Control de Movimientos:** Funcionalidad completa de Entradas, Salidas y Transferencias entre departamentos.

**Lógica de Costos Avanzada:** Cálculo en tiempo real del costo por paquete y por unidad individual (ej. costo por guante) basado en la tasa de cambio.

**Gestión de Departamentos:** Creación y "Desactivación" (Soft Delete) de departamentos.

**Gestión de Usuarios:** Creación, edición y desactivación (Soft Delete) de usuarios por parte del Admin.

**Formularios Dinámicos:** La interfaz de creación de movimientos cambia dinámicamente según el tipo de movimiento y el rol del usuario (usando JavaScript).

**Generación de Reportes PDF:** Creación de reportes de stock por departamento usando WeasyPrint.

## 💻 Stack Tecnológico

**Backend:** Python 3.12, Django 5.2

**Frontend:** HTML, JavaScript (Vanilla y jQuery)

**Estilos:** Tailwind CSS (gestionado con django-tailwind)

**Base de Datos:** Postgres

**Reportes:** WeasyPrint

##    🛠️ Instalación y Ejecución Local (Versión Corregida)

Sigue estos pasos para clonar y ejecutar el proyecto en una nueva computadora.

Prerrequisitos del Sistema
Antes de empezar, asegúrate de tener instaladas las siguientes herramientas en tu máquina:

**Python:** (Versión 3.10 o superior). Puedes descargarlo aquí.

**Node.js y npm:** (Versión LTS recomendada). django-tailwind necesita npm para instalar las dependencias de frontend (como DaisyUI). Puedes descargarlo aquí.

**Git:** Para clonar el repositorio.

## Pasos de Instalación

    