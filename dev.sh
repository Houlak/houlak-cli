#!/bin/bash
# Script de ayuda para desarrollo local de houlak-cli
# Uso: source dev.sh [comando]

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Activar entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Entorno virtual no encontrado. Creándolo...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${CYAN}📦 Actualizando pip...${NC}"
    pip install --upgrade pip
    echo -e "${CYAN}📦 Instalando dependencias en modo desarrollo...${NC}"
    pip install -e .
    echo -e "${GREEN}✅ Entorno configurado correctamente!${NC}"
else
    source venv/bin/activate
    echo -e "${GREEN}✅ Entorno virtual activado${NC}"
fi

# Mostrar información
echo -e "${CYAN}📍 Ubicación: $(which houlak-cli)${NC}"
echo -e "${CYAN}📌 Versión: $(houlak-cli --version)${NC}"
echo ""
echo -e "${YELLOW}💡 Comandos disponibles:${NC}"
echo -e "  ${CYAN}houlak-cli --help${NC}   - Ver ayuda"
echo -e "  ${CYAN}houlak-cli --version${NC} - Ver versión"
echo -e "  ${CYAN}houlak-cli${NC}           - Ver mensaje de bienvenida"
echo -e "  ${CYAN}deactivate${NC}           - Desactivar entorno virtual"
echo ""
