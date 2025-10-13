#!/bin/bash
#
# Docker services management script for ChatBot
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}ChatBot Docker Services Manager${NC}"
echo "==============================="
echo ""

case "$1" in
  start)
    echo -e "${GREEN}Starting all services...${NC}"
    docker compose up -d
    echo ""
    echo -e "${GREEN}✓ Services started${NC}"
    echo ""
    echo "Service URLs:"
    echo "  Frontend:   http://localhost:5174"
    echo "  Backend:    http://localhost:8088"
    echo "  API Docs:   http://localhost:8088/docs"
    echo "  PostgreSQL: localhost:5432"
    echo "  Qdrant:     http://localhost:6333"
    echo "  Qdrant UI:  http://localhost:6333/dashboard"
    ;;
  
  stop)
    echo -e "${YELLOW}Stopping all services...${NC}"
    docker compose down
    echo -e "${GREEN}✓ Services stopped${NC}"
    ;;
  
  restart)
    echo -e "${YELLOW}Restarting all services...${NC}"
    docker compose restart
    echo -e "${GREEN}✓ Services restarted${NC}"
    ;;
  
  rebuild)
    echo -e "${YELLOW}Rebuilding and starting services...${NC}"
    docker compose up -d --build
    echo -e "${GREEN}✓ Services rebuilt and started${NC}"
    ;;
  
  logs)
    if [ -z "$2" ]; then
      docker compose logs -f
    else
      docker compose logs -f "$2"
    fi
    ;;
  
  status)
    echo -e "${BLUE}Service Status:${NC}"
    docker compose ps
    echo ""
    echo -e "${BLUE}Health Checks:${NC}"
    
    # Check PostgreSQL
    if docker exec chatbot-postgres pg_isready -U chatbot_user -d chatbot > /dev/null 2>&1; then
      echo -e "  PostgreSQL: ${GREEN}✓ Healthy${NC}"
    else
      echo -e "  PostgreSQL: ${RED}✗ Unhealthy${NC}"
    fi
    
    # Check Qdrant
    if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
      echo -e "  Qdrant:     ${GREEN}✓ Healthy${NC}"
    else
      echo -e "  Qdrant:     ${RED}✗ Unhealthy${NC}"
    fi
    
    # Check Backend
    if curl -s http://localhost:8088/health > /dev/null 2>&1; then
      echo -e "  Backend:    ${GREEN}✓ Healthy${NC}"
    else
      echo -e "  Backend:    ${RED}✗ Unhealthy${NC}"
    fi
    
    # Check Frontend
    if curl -s http://localhost:5174 > /dev/null 2>&1; then
      echo -e "  Frontend:   ${GREEN}✓ Healthy${NC}"
    else
      echo -e "  Frontend:   ${RED}✗ Unhealthy${NC}"
    fi
    ;;
  
  clean)
    echo -e "${RED}WARNING: This will remove all containers, volumes, and data!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      docker compose down -v
      echo -e "${GREEN}✓ All data cleaned${NC}"
    else
      echo "Cancelled"
    fi
    ;;
  
  *)
    echo "Usage: $0 {start|stop|restart|rebuild|logs|status|clean}"
    echo ""
    echo "Commands:"
    echo "  start    - Start all services"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  rebuild  - Rebuild and start services"
    echo "  logs     - Show logs (add service name for specific service)"
    echo "  status   - Show service status and health"
    echo "  clean    - Remove all containers and volumes (WARNING: deletes data)"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs backend"
    echo "  $0 status"
    exit 1
    ;;
esac

