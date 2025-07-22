
# --- Stage 1: Python agent build ---
FROM python:3.11-slim AS agent-build
WORKDIR /app/agent
COPY agent/ ./

# --- Stage 2: C# API build ---
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS api-build
WORKDIR /src
COPY src/TaskMaster.Api/TaskMaster.Api/ ./TaskMaster.Api/
RUN echo "Listing TaskMaster.Api contents:" && ls -l TaskMaster.Api/ && dotnet publish TaskMaster.Api/TaskMaster.Api.csproj -c Release -o /app/api

# --- Stage 3: Final runtime image ---
FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS final
WORKDIR /app
RUN apk add --no-cache python3 py3-pip python3-dev build-base
RUN ln -sf python3 /usr/bin/python && ln -sf pip3 /usr/bin/pip
COPY --from=api-build /app/api ./TaskMaster.Api/
COPY agent/ ./agent/
RUN pip install --no-cache-dir --break-system-packages -r agent/requirements.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
ENTRYPOINT ["dotnet", "TaskMaster.Api/TaskMaster.Api.dll"]
