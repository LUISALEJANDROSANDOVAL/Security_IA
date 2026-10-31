# **Honey-Agent: Guía de Instalación, Despliegue y Operación**

* **Documento:** Deployment & Operations Guide (DOG)
* **Código de Documento:** HA-OPS-03
* **Versión:** 1.0.0
* **Estado:** Aprobado para Despliegue en Laboratorio y Producción
* **Clasificación:** Confidencial / Operaciones de Ciberseguridad

---

## **1. Requisitos Previos del Sistema**

Para garantizar el rendimiento en tiempo real, la contención estricta y la baja latencia en la emulación de la terminal, se deben cumplir los siguientes requisitos:

### **1.1. Especificaciones de Hardware**

| Perfil de Despliegue | CPU | Memoria RAM | GPU / Aceleración | Almacenamiento |
| :--- | :--- | :--- | :--- | :--- |
| **Modo API Externa** (Gemini / OpenAI) | 2 vCPU | 4 GB RAM | No requerida | 20 GB SSD |
| **Modo Local Cuantizado** (Ollama 8B Q4) | 4 vCPU | 16 GB RAM | Opcional (NVIDIA 6GB+ VRAM) | 30 GB SSD |
| **Modo Local Producción** (vLLM FP16) | 8 vCPU | 32 GB RAM | 1x NVIDIA RTX 3090 / A4000 (16GB+) | 50 GB NVMe |

### **1.2. Requisitos de Software**
* **Sistema Operativo:** Ubuntu Server 22.04 LTS / 24.04 LTS o Debian 12 Bookworm (Kernel Linux $\ge$ 5.15).
* **Python:** Versión 3.11 o superior.
* **Subsistema de Red:** `iptables` / `nftables` e `ipset` instalados.
* **Motor de Contenedores (Opcional):** Docker 24.0+ y Docker Compose v2.20+.
* **Servicio In-Memory:** Redis Server 7.0+.

---

## **2. Preparación Crítica de Red y Puertos del Servidor Host**

> [!CAUTION]
> **PREVENCIÓN DE BLOQUEO DE ACCESO ADMINISTRATIVO (LOCKOUT):**
> Dado que Honey-Agent ocupará el puerto TCP 22 para atraer y capturar a los atacantes, **DEBE** migrar previamente el puerto del servicio SSH real del sistema a un puerto alternativo (e.g., 22222) antes de levantar el señuelo.

### **2.1. Reubicación del SSH Real del Administrador**

1. Edite el archivo de configuración de OpenSSH del servidor:
   ```bash
   sudo nano /etc/ssh/sshd_config
   ```
2. Modifique la directiva `Port`:
   ```text
   # Cambiar puerto predeterminado 22 por un puerto alto administrativo
   Port 22222
   ```
3. Verifique la sintaxis y reinicie el servicio SSH:
   ```bash
   sudo sshd -t
   sudo systemctl restart ssh
   ```
4. **Comprobación:** Abra una **nueva** terminal sin cerrar la actual y confirme el acceso administrativo:
   ```bash
   ssh -p 22222 usuario_admin@IP_SERVIDOR
   ```

### **2.2. Configuración de Reglas de Firewall (UFW / iptables)**

Permita el puerto administrativo y el puerto señuelo:
```bash
sudo ufw allow 22222/tcp comment "SSH Real Administrativo"
sudo ufw allow 22/tcp comment "Honey-Agent SSH Seuelo"
sudo ufw allow 80/tcp comment "Honey-Agent HTTP Seuelo"
sudo ufw allow 8501/tcp comment "SOC Dashboard Streamlit (Restringir por IP si es prod)"
sudo ufw enable
```

---

## **3. Instalación Standalone en el Host (Bare-Metal / VM)**

### **3.1. Creación de Usuario de Sistema sin Privilegios**

Cree un usuario dedicado con shell restringida para ejecutar el proceso del señuelo:
```bash
sudo useradd -r -s /bin/false -d /opt/honey-agent -m honeyagent
```

### **3.2. Clonación del Repositorio y Entorno Virtual**

```bash
cd /opt/honey-agent
sudo git clone https://github.com/tu-organizacion/honey-agent.git .
sudo chown -R honeyagent:honeyagent /opt/honey-agent

# Crear entorno virtual de Python 3.11
sudo -u honeyagent python3 -m venv venv
sudo -u honeyagent ./venv/bin/pip install --upgrade pip
sudo -u honeyagent ./venv/bin/pip install -r requirements.txt
```

### **3.3. Configuración de Permisos Sudo para Mitigación Perimetral**

El proceso de Honey-Agent corre bajo el usuario `honeyagent` sin privilegios. Para que el motor pueda aislar atacantes mediante `iptables` sin requerir contraseña interactiva, agregue una regla sudoers:

```bash
sudo visudo -f /etc/sudoers.d/honey-agent-iptables
```

Agregue exactamente las siguientes líneas:
```text
honeyagent ALL=(ALL) NOPASSWD: /usr/sbin/iptables -I INPUT -s * -j DROP
honeyagent ALL=(ALL) NOPASSWD: /usr/sbin/iptables -D INPUT -s * -j DROP
honeyagent ALL=(ALL) NOPASSWD: /usr/sbin/ipset add honey_blocked_ips *
honeyagent ALL=(ALL) NOPASSWD: /usr/sbin/ipset del honey_blocked_ips *
honeyagent ALL=(ALL) NOPASSWD: /usr/sbin/iptables -C INPUT *
```

Guarde con permisos estrictos:
```bash
sudo chmod 0440 /etc/sudoers.d/honey-agent-iptables
```

---

## **4. Despliegue Contenerizado con Docker Compose**

El método más recomendado para aislar la infraestructura es el uso de contenedores Docker con capacidades de red compartidas para orquestación de Netfilter.

### **4.1. Estructura de `docker-compose.yml`**

Cree el archivo `/opt/honey-agent/docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: honey-redis
    restart: unless-stopped
    command: redis-server --save "" --appendonly no --maxmemory 512mb --maxmemory-policy allkeys-lru
    networks:
      - honey-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3

  honey-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: honey-agent-core
    restart: unless-stopped
    network_mode: "host" # Requerido para inspección y DROP directo con iptables
    cap_add:
      - NET_ADMIN
      - NET_RAW
    environment:
      - HONEY_SSH_PORT=22
      - HONEY_HTTP_PORT=80
      - REDIS_HOST=127.0.0.1
      - REDIS_PORT=6379
      - LLM_PROVIDER=gemini # Opciones: gemini, ollama, openai
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - LOG_LEVEL=INFO
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/opt/honey-agent/logs

  honey-dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    container_name: honey-dashboard
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - REDIS_HOST=127.0.0.1
      - REDIS_PORT=6379
    network_mode: "host"
    depends_on:
      - honey-agent

networks:
  honey-net:
    driver: bridge
```

---

## **5. Archivo de Configuración Maestro (`config.yaml`)**

Honey-Agent lee su configuración central desde `/opt/honey-agent/config.yaml`:

```yaml
# ==============================================================================
# HONEY-AGENT: ARCHIVO DE CONFIGURACIÓN MAESTRO
# ==============================================================================

system:
  environment: "production" # production | staging | lab
  debug: false
  session_timeout_seconds: 600 # 10 minutos de inactividad cierran la sesión
  max_concurrent_sessions: 100

network:
  ssh:
    enabled: true
    bind_address: "0.0.0.0"
    port: 22
    server_banner: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.4"
    auth_policy: "ACCEPT_ALL" # ACCEPT_ALL | MATCH_WORDLIST
    host_key_path: "/opt/honey-agent/keys/ssh_host_rsa_key"
  http:
    enabled: true
    bind_address: "0.0.0.0"
    port: 80
    server_header: "nginx/1.18.0 (Ubuntu)"

# ------------------------------------------------------------------------------
# MOTOR COGNITIVO LLM
# ------------------------------------------------------------------------------
llm:
  provider: "gemini" # gemini | ollama | vllm | openai
  gemini:
    model: "gemini-2.5-flash"
    temperature: 0.2 # Baja temperatura para máxima coherencia POSIX
    max_tokens: 512
  ollama:
    base_url: "http://127.0.0.1:11434"
    model: "llama3:8b-instruct-q4_K_M"
  fallback_to_cache: true

# ------------------------------------------------------------------------------
# PARÁMETROS DEL TARPIT COGNITIVO
# ------------------------------------------------------------------------------
tarpit:
  enabled: true
  alpha_fatigue_coefficient: 0.65 # Factor α en: T_espera = T_base + α * ln(1+N)
  gaussian_jitter_sigma: 0.20 # Desviación estándar σ para ruido gaussiano
  max_delay_seconds: 12.0 # Límite superior para evitar desconexión del cliente
  base_delays:
    trivial: 0.05 # whoami, id, pwd
    recon: 0.40 # ls -la, ps, uname, env
    heavy: 3.80 # find /, grep -r, cat archivos largos, tar, curl

# ------------------------------------------------------------------------------
# INOCULADOR DE CANARY TOKENS (CONTRA-INTELIGENCIA)
# ------------------------------------------------------------------------------
canary_tokens:
  enabled: true
  organization_prefix: "CORP-SEC"
  signature_secret: "CAMBIAR_ESTE_SECRETO_CRIPTOGRAFICO_HEX_64"
  types:
    aws_key:
      enabled: true
      prefix: "AKIAIOSFODNN7"
    database_uri:
      enabled: true
      dummy_host: "10.0.4.15"
      dummy_db: "production_master"
    ssh_private_key:
      enabled: true
      comment: "admin@corp-bastion-internal"
  alert_webhook_url: "https://soar.empresa.internal/hooks/canary-tripped"

# ------------------------------------------------------------------------------
# MOTOR TÁCTICO MITRE & MITIGACIÓN PERIMETRAL
# ------------------------------------------------------------------------------
mitigation:
  auto_isolate_enabled: true
  threat_score_threshold: 80.0 # Puntaje para disparar DROP en iptables
  block_duration_seconds: 86400 # 24 horas de aislamiento
  allowlist_ips: # IPs que jamás deben ser bloqueadas (defensa ante DoS)
    - "127.0.0.1"
    - "192.168.1.1" # Gateway local
    - "10.0.0.50"   # Estación de monitoreo SOC
  critical_technique_triggers:
    - "T1059.001" # Descarga de scripts y ejecución (curl | bash)
    - "T1003"     # Extracción de hashes de contraseñas de /etc/shadow
    - "T1021"     # Intentos activos de pivotaje a la red interna

# ------------------------------------------------------------------------------
# TELEMETRÍA Y OBSERVABILIDAD
# ------------------------------------------------------------------------------
telemetry:
  redis:
    host: "127.0.0.1"
    port: 6379
    channel_name: "honey_events"
  log_file: "/opt/honey-agent/logs/telemetry.jsonl"
  stix_export_enabled: true
```

---

## **6. Gestión del Servicio con Systemd (Despliegue Nativo)**

Para garantizar que Honey-Agent se ejecute como un demonio persistente que inicia con el sistema operativo, configure los servicios de systemd:

### **6.1. Demonio del Core (`honey-agent.service`)**

Cree `/etc/systemd/system/honey-agent.service`:

```ini
[Unit]
Description=Honey-Agent Active Defense & Cognitive Tarpit Core
After=network.target redis-server.service
Requires=redis-server.service

[Service]
Type=simple
User=honeyagent
Group=honeyagent
WorkingDirectory=/opt/honey-agent
EnvironmentFile=/opt/honey-agent/.env
ExecStart=/opt/honey-agent/venv/bin/python -m honey_agent.main --config /opt/honey-agent/config.yaml
Restart=always
RestartSec=5s
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### **6.2. Demonio del Dashboard SOC (`honey-dashboard.service`)**

Cree `/etc/systemd/system/honey-dashboard.service`:

```ini
[Unit]
Description=Honey-Agent SOC Streamlit Dashboard
After=network.target honey-agent.service

[Service]
Type=simple
User=honeyagent
Group=honeyagent
WorkingDirectory=/opt/honey-agent
EnvironmentFile=/opt/honey-agent/.env
ExecStart=/opt/honey-agent/venv/bin/streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### **6.3. Activación y Arranque**

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now honey-agent.service
sudo systemctl enable --now honey-dashboard.service
```

---

## **7. Operaciones y Mantenimiento Diario**

### **7.1. Verificación de Estado y Logs en Vivo**

```bash
# Ver estado del servicio
sudo systemctl status honey-agent

# Trazar telemetría de eventos en tiempo real
sudo journalctl -u honey-agent -f -n 100

# Inspeccionar el log JSON estructurado
tail -f /opt/honey-agent/logs/telemetry.jsonl | jq .
```

### **7.2. Auditoría y Gestión de Cuarentena (IPs Bloqueadas)**

Para verificar las IPs que han sido expulsadas y bloqueadas dinámicamente por el kernel:

```bash
# Listar reglas de bloqueo activas generadas por Honey-Agent
sudo iptables -L INPUT -v -n --line-numbers | grep DROP

# Si se utiliza ipset:
sudo ipset list honey_blocked_ips
```

Para desbloquear manualmente una IP (en caso de falso positivo o pruebas):
```bash
# Desbloqueo manual iptables
sudo iptables -D INPUT -s 192.168.1.100 -j DROP

# O mediante ipset
sudo ipset del honey_blocked_ips 192.168.1.100
```

---

## **8. Matriz de Solución de Problemas (Troubleshooting)**

| Síntoma / Error | Causa Probable | Solución Paso a Paso |
| :--- | :--- | :--- |
| `PermissionError: [Errno 13] Permission denied: 0.0.0.0:22` | El usuario `honeyagent` no tiene permisos para enlazar puertos privilegiados (< 1024). | Ejecute: `sudo setcap 'cap_net_bind_service=+ep' /opt/honey-agent/venv/bin/python3` o use redirección iptables desde puerto 2222. |
| La sesión SSH no responde o arroja `Connection reset by peer`. | Conflicto con el servicio OpenSSH nativo en el puerto 22. | Confirme que el SSH real está en el puerto 22222 con `sudo ss -tulpn \| grep :22`. Si OpenSSH sigue en 22, reinícielo. |
| Las alertas de mitigación se disparan pero el atacante continúa conectado. | La regla de sudoers para iptables no tiene permisos de ejecución NOPASSWD. | Revise `/etc/sudoers.d/honey-agent-iptables` con `sudo visudo -c`. Compruebe los logs de journalctl para errores de sudo. |
| Inferencia LLM tarda más de 8 segundos en cada comando. | Modelo local Ollama sin soporte de GPU o timeout en la conexión a la API. | Cambie a cuantización menor (`q4_K_M`), habilite GPU passthrough, o cambie temporalmente a `provider: gemini` en `config.yaml`. |

