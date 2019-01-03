redo-ifchange "$2.image"
./need.sh docker
docker load <$2.image
