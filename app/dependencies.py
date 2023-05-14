import os
from fastapi.security import OAuth2PasswordBearer

from passlib.context import CryptContext


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# runner has to run from root dir, so this has to be added to the path.
DOTENV_PATH = os.getcwd() + "/app/.env"


