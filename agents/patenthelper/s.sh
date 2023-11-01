#!/bin/bash

SCRIPT_PATH="run-docker-registry.sh"
CONTAINER_NAME="/registry"

# 执行脚本并捕获输出
output=$(sh $SCRIPT_PATH)

# 检查是否包含指定错误消息
if grep -q "Conflict. The container name '$CONTAINER_NAME' is already in use" <<< "$output"; then
    echo "Error: Container with name '$CONTAINER_NAME' already exists. Stopping and re-running script..."
    # 提取容器ID
    CONTAINER_ID=$(docker ps --filter name="$CONTAINER_NAME" --format "{{.ID}}")

    # 停止容器
    docker stop $CONTAINER_ID

    # 重新运行脚本
    sh $SCRIPT_PATH
else
    echo "Script executed successfully."
fi