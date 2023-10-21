#!/bin/
# 执行 run-docker-registry.sh 脚本，并将输出保存到临时文件中
sh run-docker-registry.sh > output.log 2>&1
exit_code=$?

# 如果执行结果是失败状态
if [ $exit_code -ne 0 ]; then
  # 从临时文件中提取日志
  log=$(cat output.log)
  echo "log" $log
  # 提取容器ID
  container_id=$(echo $log | awk -F 'container "' '{print $2}' | awk -F '"' '{print $1}')
  echo $container_id
  # 停止容器
  docker stop $container_id
  docker rm $container_id
  
  # 重新执行 run-docker-registry.sh 脚本
  sh run-docker-registry.sh
fi

# 删除临时文件
#rm output.log
