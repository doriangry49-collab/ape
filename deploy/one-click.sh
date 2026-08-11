#!/usr/bin/env bash
# APE MVP One-Click Installer — ORION-101 Week 6 Specification
# Installs and launches APE Cloud MVP in under 60 seconds.

set -e

echo "============================================================"
echo "    APE Cloud — Autonomous Software Production Platform     "
echo "  'Hire your first AI Engineering Department in 5 minutes'  "
echo "============================================================"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "[!] Docker is not installed. Installing via Docker Compose..."
fi

echo "[*] Pulling APE Cloud MVP Container images..."
docker-compose -f deploy/docker-compose.yml up -d

echo ""
echo "[✓] APE Cloud MVP is successfully deployed and running!"
echo "    • Web Dashboard UI : http://localhost:8080"
echo "    • REST API Gateway : http://localhost:8080/api/v1/status"
echo "    • Swagger Docs     : http://localhost:8080/docs"
echo "============================================================"
