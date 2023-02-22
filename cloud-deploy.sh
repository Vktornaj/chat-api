#! /bin/bash

set -e

remote_host="3.129.45.65"
remote_port=22
remote_user="admin"
local_dir=$(pwd)/
remote_dir="/home/${remote_user}/chat_api"
ssh_key="~/Desktop/Files/aws_keys/key_001.pem"

b_flag=''

while getopts 'b' flag; do
  case "${flag}" in
    b) b_flag='true' ;;
    *) print_usage
       exit 1 ;;
  esac
done

ssh -i ${ssh_key} ${remote_user}@${remote_host} sudo rm -rf chat_api/
rsync -avzr --exclude='.git/' --exclude='app/venv/' --exclude='queue/venv/' --delete -e "ssh -p ${remote_port} -i ${ssh_key} -o StrictHostKeyChecking=no" ${local_dir} ${remote_user}@${remote_host}:${remote_dir}
# rsync -avzr --exclude-from='.gitignore' --exclude='.git/' --delete -e "ssh -p ${remote_port} -i ${ssh_key} -o StrictHostKeyChecking=no" ${local_dir} ${remote_user}@${remote_host}:${remote_dir}

if [ $b_flag ];
then
    echo "rebuild mode"
    ssh -tt -i ${ssh_key} ${remote_user}@${remote_host} << EOF 
docker compose -f chat_api/compose.yml down || true
docker compose -f chat_api/compose.yml build 
docker compose -f chat_api/compose.yml --env-file ~/chat_api/config/prod.env up -d
exit
EOF
else
    echo "restart mode"
    ssh -i ${ssh_key} ${remote_user}@${remote_host} docker restart chat_api-web-1
    # ssh -i ${ssh_key} ${remote_user}@${remote_host} docker restart chat_api-queue-1
fi

say "deploy done"