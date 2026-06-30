#!/bin/sh
unset STREAMLIT_SERVER_PORT
exec streamlit run app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0 --server.headless true