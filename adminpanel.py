from typing import List
from datetime import date
import uuid, json, logging
from pydantic import BaseModel
from redis_om import get_redis_connection
from fastapi.responses import JSONResponse
from azure.storage.blob import BlobServiceClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, Depends, FastAPI, Form, HTTPException, Request,UploadFile, File

from models.starsModel import Stars
from models.commentModel import Comment
from models.userModel import User, UpdatedUser
from models.adminModel import Admin, UpdateAdmin
from models.mangaModel import Manga, UpdateManga
from models.categoryModel import Category, SubCategory
from app.jwtModel import UserSchema, UserLoginSchema, AdminSchema, AdminLoginSchema

from app.auth.jwtBearer import JWTBearer
from app.auth.jwtHandler import create_jwt_token, decode_jwt_token


#Azure Blob Storage
account_name = "mangaplus"
account_key = "zZ+KRIhbjw+Rz0u4cbFfmcN9VOd8r7ykx33z0Jleq18nJEbT5lxOQqK0Ddsm0KxLzbSnOUTZdDcE+AStsHiR3A==" 
container_name = "mangaplus"

# Create a BlobServiceClient object
connection_string = "DefaultEndpointsProtocol=https;AccountName="+ account_name +";AccountKey="+ account_key +";EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

container_client = blob_service_client.get_container_client(container_name)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*']
)

redis = get_redis_connection(
    host = "redis-10788.c282.east-us-mz.azure.cloud.redislabs.com",
    port = 10788,
    password = "yKCjtyQum735j4UL1FeO914Ci9etLHwf",
    decode_responses = True
)


@app.get("/admin",response_model=List[AdminSchema], dependencies=[Depends(JWTBearer())], tags=["admin"])
def get_all_admin():
    
    admin_ids = redis.lrange("admins", 0, -1)
    
    admins = []
    for id in admin_ids:
        admin_data = redis.get(id)  # If IDs are strings, use them directly
        if admin_data is not None:
            admin = Admin.parse_raw(admin_data)  # Parsing the data into Pydantic model
            admins.append(admin)

    return admins


@app.get("/admin/del/{admin_id}", dependencies=[Depends(JWTBearer())], tags=["admin"])
def admin_del(admin_id:str):
    given_admin = redis.get(admin_id)
    admin_data = json.loads(given_admin)
    admin = Admin(**admin_data)
    admin.is_active = False
    redis.set(admin_id, admin.json())
    return {"data":f"Admin is deleted with title as {admin.name}"}


@app.post("/admin/update/{admin_id}", dependencies=[Depends(JWTBearer())], tags=["admin"])
def admin_update(admin_id:str,update: UpdateAdmin):
    given_admin = redis.get(admin_id)
    admin_data = json.loads(given_admin)
    
    if update.name is not None:
        admin_data["name"] = update.name
    if update.surname is not None:
        admin_data["surname"] = update.surname
    if update.email is not None:
        admin_data["email"] = update.email    
    if update.password is not None:
        admin_data["password"] = update.password

    redis.set(admin_id, json.dumps(admin_data))
    
    return {"data":f"Admin is updated with title as {admin_id}"}

######################################################################

#User
######################################################################
#There is a user root page get method get from redis cloud
users=[]
@app.get("/admin/user",response_model=List[UserSchema], tags=["admin"])
def get_all_user():
        
        user_ids = redis.lrange("users", 0, -1)
        
        users = []
        for id in user_ids:
            # Fetch each user by ID
            user_data = redis.get(id)
            if user_data is not None:
                user = UserSchema.parse_raw(user_data)
                users.append(user)

        return users            

@app.post("/category/new",dependencies=[Depends(JWTBearer())], tags=["category"])
def create_category(category: Category,categories: List[Category] = Body(...)):
    categories.append(category)
    return category




@app.post("/admin/signup", tags=["admin"])
def create_user(user: AdminSchema = Body(...)):
    users.append(user) # replace with db call, making sure to hash the password first
    return create_jwt_token(user.email)

@app.post("/admin/login", tags=["admin"])
def user_login(user: AdminLoginSchema = Body(...)):
    if check_user(user):
        return create_jwt_token(user.email)
    return {
        "error": "Wrong login details!"
    }


def check_user(data: AdminLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False



@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )