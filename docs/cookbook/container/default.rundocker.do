redo-ifchange "$2.load" "$2.list.sha256"
./need.sh docker
read container_id <$2.list.sha256
docker run "$container_id"
