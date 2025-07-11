# app/core/seguridad/esquemas_oauth2.py
from fastapi.security import OAuth2PasswordBearer

# Define el esquema de seguridad OAuth2 con flujo de contraseña.
# La URL 'tokenUrl' apunta a tu endpoint de login RELATIVO a la raíz de la API.
# FastAPI usa esta información para que Swagger UI sepa dónde enviar la solicitud de token.
# Prefijo con barra inicial para que la URL sea absoluta en el esquema OpenAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/login")
