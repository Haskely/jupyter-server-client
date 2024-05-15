mkdir -p jupyter_workdir

jupyter lab \
    --IdentityProvider.token="" \
    --ServerApp.allow_credentials=True \
    --ServerApp.allow_external_kernels=True \
    --ServerApp.allow_origin="*" \
    --ServerApp.allow_remote_access=True \
    --ServerApp.disable_check_xsrf=True \
    --ServerApp.ip="0.0.0.0" \
    --ServerApp.open_browser=False \
    --ServerApp.port=8888 \
    --ServerApp.root_dir="./jupyter_workdir"