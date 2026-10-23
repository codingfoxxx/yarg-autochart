#!/bin/bash
# Cria (uma vez) o certificado local que assina o YARG.app no Mac.
#
# Por quê: o build do Unity sai com assinatura ad-hoc, que muda a cada compilação. O macOS guarda as
# permissões (microfone etc.) presas à assinatura, então depois de cada build ele pergunta de novo, e
# o jogo congela na tela de carregamento esperando a resposta (a janela fica atrás do jogo em tela
# cheia; sem resposta, o pedido expira em 5 min). Com um certificado fixo, a resposta vale para
# todos os builds.
#
# O certificado é autoassinado e fica num chaveiro próprio (não no chaveiro de login), com senha
# aleatória guardada em _tools/assinatura/ (fora do git). Uso: scripts/assinatura-mac.sh
set -euo pipefail

raiz="$(cd "$(dirname "$0")/.." && pwd)"
dir="$raiz/_tools/assinatura"
chaveiro="$HOME/Library/Keychains/yarg-assinatura.keychain-db"
nome="YARG Local (assinatura do build)"

if [ -f "$chaveiro" ] && [ -f "$dir/senha" ] && [ -f "$dir/identidade" ]; then
    echo "Certificado já existe: $(cat "$dir/identidade") em $chaveiro"
    exit 0
fi

mkdir -p "$dir"
chmod 700 "$dir"
senha="$(openssl rand -hex 24)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cat > "$tmp/cert.cnf" <<EOF
[req]
distinguished_name = dn
x509_extensions = ext
prompt = no
[dn]
CN = $nome
[ext]
basicConstraints = critical,CA:false
keyUsage = critical,digitalSignature
extendedKeyUsage = critical,codeSigning
EOF
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -config "$tmp/cert.cnf" \
    -keyout "$tmp/key.pem" -out "$tmp/cert.pem" 2>/dev/null
openssl pkcs12 -export -inkey "$tmp/key.pem" -in "$tmp/cert.pem" -name "$nome" \
    -out "$tmp/id.p12" -passout pass:"$senha"

security create-keychain -p "$senha" "$chaveiro"
security set-keychain-settings "$chaveiro"            # sem bloqueio automático
security unlock-keychain -p "$senha" "$chaveiro"
security import "$tmp/id.p12" -k "$chaveiro" -P "$senha" -T /usr/bin/codesign >/dev/null
# Deixa o codesign usar a chave sem janela de confirmação
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$senha" "$chaveiro" >/dev/null
# O chaveiro precisa estar na lista de busca para o codesign achar a identidade
security list-keychains -d user -s "$HOME/Library/Keychains/login.keychain-db" "$chaveiro"

hash="$(openssl x509 -in "$tmp/cert.pem" -noout -fingerprint -sha1 | sed 's/.*=//; s/://g')"
printf '%s' "$senha" > "$dir/senha"
printf '%s' "$hash" > "$dir/identidade"
chmod 600 "$dir/senha" "$dir/identidade"
echo "Certificado criado: $nome ($hash)"
