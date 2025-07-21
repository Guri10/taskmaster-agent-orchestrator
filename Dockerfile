# --- Stage 1: Python agent build ---
FROM python:3.11-slim AS agent-build
WORKDIR /app/agent
COPY agent/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/ ./

# --- Stage 2: C# API build ---
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS api-build
WORKDIR /src
COPY src/TaskMaster.Api/ ./TaskMaster.Api/
RUN dotnet publish TaskMaster.Api/TaskMaster.Api.csproj -c Release -o /app/api

# --- Stage 3: Final runtime image ---
FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS final
WORKDIR /app
# Copy published C# API
COPY --from=api-build /app/api ./TaskMaster.Api/
# Copy Python agent
COPY --from=agent-build /app/agent ./agent/
# Set environment for Python
ENV PYTHONUNBUFFERED=1
# Expose default ASP.NET port
EXPOSE 5000
# Entrypoint: run the C# API
ENTRYPOINT ["dotnet", "TaskMaster.Api/TaskMaster.Api.dll"]
