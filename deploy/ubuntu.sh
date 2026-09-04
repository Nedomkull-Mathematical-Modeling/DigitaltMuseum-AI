#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Kör skriptet som root, till exempel med sudo." >&2
  exit 1
fi

if [[ $# -ne 2 ]]; then
  echo "Användning: DIMU_SERVICE_TOKEN=... $0 <domän> <e-post>" >&2
  exit 1
fi

DOMAIN=$1
EMAIL=$2
: "${DIMU_SERVICE_TOKEN:?Sätt DIMU_SERVICE_TOKEN innan skriptet körs.}"
DIMU_API_KEY=${DIMU_API_KEY:-demo}
SOURCE_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

if [[ ! $DOMAIN =~ ^([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$ ]]; then
  echo "Ogiltigt domännamn: $DOMAIN" >&2
  exit 1
fi

if [[ ! $EMAIL =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
  echo "Ogiltig e-postadress: $EMAIL" >&2
  exit 1
fi

if [[ $DIMU_API_KEY == demo ]]; then
  echo "VARNING: DIMU_API_KEY är inte satt; DigitaltMuseums demo-nyckel används." >&2
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx supervisor python3-venv snapd
systemctl enable --now snapd.socket
snap list core >/dev/null 2>&1 || snap install core
snap refresh core
snap list certbot >/dev/null 2>&1 || snap install --classic certbot
ln -sf /snap/bin/certbot /usr/local/bin/certbot

if ! id -u dimu >/dev/null 2>&1; then
  useradd --system --home-dir /opt/dimu --create-home --shell /usr/sbin/nologin dimu
fi

install -d -o dimu -g dimu /opt/dimu
python3 -m venv /opt/dimu/venv
/opt/dimu/venv/bin/pip install --upgrade pip
/opt/dimu/venv/bin/pip install --upgrade "${SOURCE_DIR}[api]"
chown -R dimu:dimu /opt/dimu

{
  printf 'DIMU_API_KEY=%q\n' "$DIMU_API_KEY"
  printf 'DIMU_SERVICE_TOKEN=%q\n' "$DIMU_SERVICE_TOKEN"
} > /etc/dimu.env
chown root:dimu /etc/dimu.env
chmod 640 /etc/dimu.env

cat > /etc/supervisor/conf.d/dimu.conf <<'EOF'
[program:dimu]
directory=/opt/dimu
command=/bin/bash -c "set -a && source /etc/dimu.env && exec /opt/dimu/venv/bin/uvicorn dimu.api:app --host 127.0.0.1 --port 8000"
user=dimu
autostart=true
autorestart=true
startsecs=5
stopsignal=TERM
stopasgroup=true
killasgroup=true
stdout_logfile=/var/log/dimu.log
stderr_logfile=/var/log/dimu.err.log
environment=PYTHONUNBUFFERED="1"
EOF

cat > /etc/nginx/sites-available/dimu <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    client_max_body_size 25m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 40s;
    }
}
EOF

ln -sfn /etc/nginx/sites-available/dimu /etc/nginx/sites-enabled/dimu
nginx -t
systemctl enable --now supervisor nginx
supervisorctl reread
supervisorctl update
supervisorctl restart dimu
systemctl reload nginx

certbot --nginx --non-interactive --agree-tos --redirect --email "$EMAIL" -d "$DOMAIN"

echo "dimu körs nu på https://$DOMAIN"
echo "Status: supervisorctl status dimu"
echo "Loggar: tail -f /var/log/dimu.err.log"
