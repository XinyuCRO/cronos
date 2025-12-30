
python -m grpc_tools.protoc \
    -I ../solidity-ibc-eureka/proto \
    --python_out=./ \
    --pyi_out=./ \
    --grpc_python_out=./ \
    ../solidity-ibc-eureka/proto/relayer/relayer.proto