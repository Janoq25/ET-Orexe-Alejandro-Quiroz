# Evaluación Técnica: Automatización y Monitoreo (Orexe)

Este repositorio contiene la solución a la evaluación técnica de Orexe, enfocada en la automatización del despliegue de un servidor de base de datos Percona, integración con PMM (Percona Monitoring and Management) y pruebas de resiliencia mediante Ansible.


## Requisitos Previos

Para ejecutar este proyecto, es necesario contar con:
- Ansible: Motor de automatización.
- Multipass: Para la creación de entornos de prueba aislados.
- Python 3: Para scripts de validación.

### Instalación de herramientas (Linux)

```bash
# Instalar Ansible
sudo apt update && sudo apt install ansible

# Instalar Multipass
sudo snap install multipass
```

## Configuración del Entorno de Pruebas

Sigue estos pasos para preparar la infraestructura antes de ejecutar los playbooks de Ansible:

### 1. Crear la Instancia con Multipass
Lanzamos una máquina virtual con Ubuntu:
```bash
multipass launch --name servidor-orexe --disk 10G --memory 2G
```

### 2. Configurar Acceso SSH
Generamos un par de llaves (si no tienes una) y la inyectamos en la VM para permitir el acceso sin contraseña:

```bash
# Generar llaves SSH
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Inyectar llave pública en la VM
multipass exec servidor-orexe -- bash -c "echo '$(cat ~/.ssh/id_rsa.pub)' >> ~/.ssh/authorized_keys"
```

### 3. Configurar el Inventario
El archivo inventory.yaml contiene la dirección IP de la instancia y los parámetros de conexión necesarios para Ansible.

---


