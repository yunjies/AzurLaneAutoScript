FROM python:3.13-slim

LABEL maintainer="yunjies"
LABEL description="ALAS MCP Server - 远程控制 ALAS 的 MCP 服务"

# 安装依赖
RUN pip install --no-cache-dir \
    mcp>=1.0.0 \
    httpx \
    starlette \
    uvicorn

# 创建应用目录
WORKDIR /app

# 复制 mcp_server.py（构建时需要 ALAS 仓库上下文）
COPY mcp_server.py /app/mcp_server.py

# 暴露 SSE 端口
EXPOSE 8080

# 默认环境变量（可在 docker-compose 或运行时覆盖）
ENV ALAS_API_BASE=http://192.168.1.100:22267
ENV EMULATOR_API_BASE=http://192.168.1.100:22333

# 启动 SSE 模式
CMD ["python", "mcp_server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8080"]
