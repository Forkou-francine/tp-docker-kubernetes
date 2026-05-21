FROM python:3.12-slim

# Création d'un utilisateur non-root 
RUN useradd --create-home --shell /bin/bash appuser

# Répertoire de travail
WORKDIR /app

# Installation des dépendances 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Permissions
RUN chown -R appuser:appuser /app
USER appuser

# Port exposé
EXPOSE 5000

# Variables d'env par défaut (surchargées par ConfigMap/Secret en K8s)
ENV APP_ENV=docker \
    APP_PORT=5000

# Lancement
CMD ["python", "app.py"]
