docker ps | grep kedeai-backend-backend | awk '{print $1}' | xargs docker  logs -f