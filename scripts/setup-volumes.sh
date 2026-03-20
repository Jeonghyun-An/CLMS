#!/bin/bash
set -e

echo "=== contract-review: 네트워크 & 볼륨 생성 ==="

docker network create contract-net 2>/dev/null || echo "[skip] contract-net 이미 존재"

volumes=(
  contract_etcd_data
  contract_milvus_data
  contract_minio_data
  contract_postgres_data
  contract_redis_data
  contract_neo4j_data
  contract_neo4j_logs
  contract_neo4j_plugins
)

for vol in "${volumes[@]}"; do
  docker volume create "$vol" 2>/dev/null || echo "[skip] $vol 이미 존재"
done

echo "=== 완료 ==="