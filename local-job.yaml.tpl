APIVersion: V1beta1
Spec:
    Deal:
        Concurrency: 1
    Docker:
        Entrypoint:
            - python3
            - /app/run.py
            - /inputs
            - /outputs
            - /inputs/uniswap_predictions_preprocessor
            - '$query_variables'
            - $flight_address
        Image: ghcr.io/cod-demo/bacalhau_runner:m1
        EnvironmentVariables:
            - SPICE_API_KEY=$api_key
    Engine: Docker
    Network:
        Type: Full
    PublisherSpec:
        Type: Estuary
    Timeout: 1800
    Verifier: Noop
    inputs:
        - Name: script
          StorageSource: IPFS
          CID: $input_cid
          path: /inputs/uniswap_predictions_preprocessor
    outputs:
        - Name: outputs
          StorageSource: IPFS
          path: /outputs
