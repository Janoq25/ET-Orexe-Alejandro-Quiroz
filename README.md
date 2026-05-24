# Evaluación Técnica Orexe — Automatización y Monitoreo

Automatización del despliegue de **Percona Server (MySQL)**, registro en **PMM (Percona Monitoring and Management)** y simulación de resiliencia con **Ansible**. Incluye credenciales protegidas con **Ansible Vault** y un script Python de verificación.

## Estructura del proyecto

```
.
├── ansible/
│   ├── site.yml                    # Playbook principal
│   ├── inventory.yml               # Inventario de servidores
│   ├── group_vars/all/
│   │   ├── vars.yml                # Variables públicas y mapeo desde Vault
│   │   └── vault.yml               # Secretos cifrados (Ansible Vault)
│   └── roles/
│       ├── percona_server/         # Instalación y configuración de MySQL
│       ├── pmm_client/             # Cliente PMM y registro en el servidor
│       └── chaos_mysql/            # Simulación de caída controlada de MySQL
├── verify_connection.py            # Script de validación de conexión
├── requirements.txt                # Dependencias Python (pymysql)
└── README.md
```

## Requisitos previos

En la máquina de control (WSL/Ubuntu):

| Herramienta | Uso |
|-------------|-----|
| **Ansible** | Ejecutar playbooks |
| **Multipass** | Crear la VM de prueba |
| **Python 3** | Script `verify_connection.py` |
| **PMM Server** | Servidor de monitoreo accesible desde la VM |

```bash
sudo apt update && sudo apt install ansible python3-pymysql
sudo snap install multipass
```

## 1. Preparar el entorno de prueba (Multipass)

### Crear la VM

```bash
multipass launch --name servidor-orexe --disk 10G --memory 2G
multipass info servidor-orexe    # anota la IP pública
```

### Configurar acceso SSH sin contraseña

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa   # si aún no tienes llaves

multipass exec servidor-orexe -- bash -c "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
multipass exec servidor-orexe -- bash -c "echo '$(cat ~/.ssh/id_rsa.pub)' >> ~/.ssh/authorized_keys"
multipass exec servidor-orexe -- bash -c "chmod 600 ~/.ssh/authorized_keys"
```

### Actualizar el inventario

Edita `ansible/inventory.yml` con la IP de tu VM:

```yaml
dbservers:
  hosts:
    servidor-orexe:
      ansible_host: <IP_DE_TU_VM>
      ansible_user: ubuntu
```

## 2. Ansible Vault (credenciales sensibles)

Los secretos se guardan cifrados en `ansible/group_vars/all/vault.yml`:

| Variable en Vault | Uso |
|-------------------|-----|
| `vault_mysql_root_password` | Contraseña del usuario `root` de MySQL |
| `vault_ansible_test_password` | Contraseña de `ansible_test_user` |
| `vault_pmm_server_ip` | IP del PMM Server |

Las variables públicas en `ansible/group_vars/all/vars.yml` referencian esos valores:

```yaml
mysql_root_password: "{{ vault_mysql_root_password }}"
ansible_test_password: "{{ vault_ansible_test_password }}"
pmm_server_ip: "{{ vault_pmm_server_ip }}"
```

### Crear o editar secretos

```bash
# Crear vault por primera vez
ansible-vault create ansible/group_vars/all/vault.yml

# Editar vault existente
ansible-vault edit ansible/group_vars/all/vault.yml

# Ver contenido (sin modificar)
ansible-vault view ansible/group_vars/all/vault.yml
```

Contenido de ejemplo del vault:

```yaml
vault_mysql_root_password: "tu_password_root"
vault_ansible_test_password: "tu_password_test"
vault_pmm_server_ip: "192.168.x.x"
```

> **Nota:** El archivo `vault.yml` cifrado sí se commitea al repositorio. La contraseña del vault **no** debe subirse a Git.

## 3. Ejecutar el playbook

Desde la carpeta `ansible/`:

```bash
cd ansible
ansible-playbook -i inventory.yml site.yml --ask-vault-pass
```

El playbook `site.yml` aplica los tres roles en orden:

1. **`percona_server`** — instala Percona Server 8.4 LTS, configura `my.cnf` y crea `ansible_test_user`
2. **`pmm_client`** — instala el cliente PMM y registra el nodo en el servidor de monitoreo
3. **`chaos_mysql`** — simulación de caída (solo si `chaos_mode=true`)

### Verificar conectividad SSH antes del playbook

```bash
ansible -i inventory.yml dbservers -m ping --ask-vault-pass
```

## Roles Ansible

### `percona_server`

- Instala **Percona Server 8.4 LTS** desde el repositorio oficial de Percona.
- Aplica configuración personalizada en `/etc/mysql/my.cnf` (template Jinja2).
- Variables configurables en `group_vars/all/vars.yml`:
  - `mysql_max_connections` (default: `100`)
  - `mysql_innodb_buffer_pool_size` (default: `256M`)
- Configura `bind-address = 0.0.0.0` para permitir conexiones remotas (script Python y PMM).
- Establece contraseña de `root` y crea el usuario `ansible_test_user` con permisos de solo lectura (`SELECT`).

> **Compatibilidad Ubuntu:** Si la VM usa una versión de Ubuntu aún no soportada por los repos de Percona (p. ej. 26.04), el rol ajusta el repositorio a `noble` (24.04) como workaround.

### `pmm_client`

- Instala **pmm-client** (PMM 3).
- Registra el nodo contra el PMM Server definido en `pmm_server_ip` (desde Vault).
- Agrega el servicio MySQL a PMM con el nombre `mysql-orexe`.

Requisito: tener un **PMM Server** en ejecución y accesible desde la VM en el puerto `443`.

### `chaos_mysql`

Simulación de error controlado para validar resiliencia básica:

1. Detiene el servicio `mysql` (systemd)
2. Espera 60 segundos
3. Reinicia el servicio

Por defecto **no se ejecuta**. Para activarlo:

```bash
ansible-playbook -i inventory.yml site.yml --ask-vault-pass -e "chaos_mode=true"
```

## 4. Script de verificación (`verify_connection.py`)

Comprueba que `ansible_test_user` puede conectarse a MySQL y ejecutar `SELECT 1`.

### Instalar dependencias

En Ubuntu/WSL moderno, usa el paquete del sistema:

```bash
sudo apt install python3-pymysql
```

Alternativa con entorno virtual:

```bash
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Ejecutar

```bash
# Obtener la contraseña desde Vault
ansible-vault view ansible/group_vars/all/vault.yml

# Ejecutar (ajusta --host si cambió la IP de Multipass)
python3 verify_connection.py --password "TU_CONTRASEÑA"
python3 verify_connection.py --host <IP_DE_TU_VM> --password "TU_CONTRASEÑA"
```

Salida esperada:

```
Conectando a MySQL en 10.85.24.12:3306 como 'ansible_test_user'...
OK: Conexión exitosa. SELECT 1 ejecutado correctamente.
```

## 5. Validación continua (GitHub Actions)

El workflow en `.github/workflows/ansible-lint.yml` ejecuta **ansible-lint** en cada push y pull request para validar la calidad del código Ansible.

## Referencias

- [Documentación de Percona](https://docs.percona.com/)
- [Documentación de Ansible](https://docs.ansible.com/)
- [Percona Monitoring and Management](https://docs.percona.com/percona-monitoring-and-management/index.html)
- [ansible-lint](https://github.com/ansible/ansible-lint)
