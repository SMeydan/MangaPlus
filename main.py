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

class WishlistCart(BaseModel):
    wishlist_id: str
    user_id: str
    manga_id: str
    price: float
    status: int
 

@app.get("/user/del/{user_id}",dependencies=[Depends(JWTBearer())], tags=["user"])
def user_del(user_id:str):
    given_user = redis.get(user_id)
    user_data = json.loads(given_user)
    user = UserSchema(**user_data)
    user.is_active = False
    redis.set(user_id, user.json())
    return {"data":f"User is deleted with title as {user.name}"}


@app.post("/user/update/{user_id}",dependencies=[Depends(JWTBearer())], tags=["user"])
def user_update(user_id:str,update: UpdatedUser):
    given_user = redis.get(user_id)
    user_data = json.loads(given_user)
    
    if update.name is not None:
        user_data["name"] = update.name
    if update.surname is not None:
        user_data["surname"] = update.surname
    if update.email is not None:
        user_data["email"] = update.email    
    if update.password is not None:
        user_data["password"] = update.password
    if update.age is not None:
        user_data["is_active"] = update.age
    if update.country is not None:
        user_data["is_active"] = update.country

    redis.set(user_id, json.dumps(user_data))
    
    return {"data":f"User is updated with title as {user_id}"}

#####################################################################

#Manga
######################################################################
@app.get("/manga",response_model=List[Manga], tags=["manga"])
def get_all_manga():
            
            manga_ids = redis.lrange("mangas", 0, -1)
            
            mangas = []
            for id in manga_ids:
                # Fetch each manga by ID
                manga_data = redis.get(id)
                if manga_data is not None:
                    manga = Manga.parse_raw(manga_data)
                    mangas.append(manga)
    
            return mangas

@app.post("/manga/new", dependencies=[Depends(JWTBearer())], tags=["manga"])
async def create_manga(
    file: UploadFile = File(...), 
    manga_id: str = Form(...), 
    category_id: str = Form(...), 
    subcategory_id: str = Form(...), 
    name: str = Form(...), 
    description: str = Form(...), 
    publish_time: date = Form(...)
    ):
    str = f"manga_id: {manga_id}, category_id: {category_id}, subcategory_id: {subcategory_id}, name: {name}, description: {description}, publish_time: {publish_time}"
    if not all([manga_id, category_id, subcategory_id, name, description, publish_time]):
        return {"data": "Please fill all the fields"}
    # Create a Manga object from the form data

    connection_string = "DefaultEndpointsProtocol=https;AccountName="+ account_name +";AccountKey="+ account_key +";EndpointSuffix=core.windows.net"
    
    storage_connection_string = connection_string
    container_name = "mangaplus"

    # Generate a unique blob name
    blob_name = file.filename

    # Upload the file and get the blob URL
    pub_link = upload_blob(storage_connection_string, container_name, blob_name, file.file)
    #pub_link="aaaa"
    # Set the pub_link field of the Manga object
    manga = Manga(
        manga_id=manga_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
        name=name,
        description=description,
        pub_link=pub_link,
        publish_time=publish_time,
    )

    try:
        redis.set(manga.manga_id, manga.json())
        redis.rpush("mangas", manga.manga_id)
    except Exception as e:
        logging.error(f"Error saving to Redis: {e}")
        raise

    return {"data":f"Manga is created with title as {manga.name}"}

def upload_blob(storage_connection_string, container_name, blob_name, file):
    # Create a BlobServiceClient object
    try:
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
    except Exception as e:
        logging.error("Error creating BlobServiceClient: %s", e)

    # Create a ContainerClient object
    try:
        container_client = blob_service_client.get_container_client(container_name)
    except Exception as e:
        logging.error("Error creating ContainerServiceClient: %s", e)
    

    # Create a BlobClient object
    try:
        blob_client = container_client.get_blob_client(blob_name)
    except Exception as e:
        logging.error("Error creating bLOBServiceClient: %s", e)
   

    # Upload the file to Azure Blob Storage
    try:
        blob_client.upload_blob(file)
    except Exception as e:
        logging.error("Error creating BLOBUPLOAD: %s", e)
    

    # Get the blob URL
    blob_url = blob_client.url

    return blob_url

@app.get("/manga/{manga_id}", response_model=Manga,dependencies=[Depends(JWTBearer())], tags=["manga"])
def get_manga(manga_id: str):
    manga = redis.get(manga_id)
    if manga is None:
        raise HTTPException(status_code=404, detail="Manga not found")
    return Manga.parse_raw(manga)

@app.get("/manga/delete/{manga_id}",dependencies=[Depends(JWTBearer())], tags=["manga"])
def delete_manga(manga_id: str):
    manga = redis.get(manga_id)
    given_manga = json.loads(manga)
    manga = Manga(**given_manga)
    manga.is_active = False
    redis.set(manga_id, manga.json())
    if manga is None:
        raise HTTPException(status_code=404, detail="Manga not found")
    return {"data":f"Manga is deleted with title as {manga.name}"}

@app.post("/manga/update/{manga_id}",dependencies=[Depends(JWTBearer())], tags=["manga"])
def update_manga(manga_id: str, update: UpdateManga):
    manga = redis.get(manga_id)
    given_manga = json.loads(manga)
    manga = Manga(**given_manga)
    manga_data = manga.dict()

    if update.manga_id is not None:
        manga_data["manga_id"] = update.manga_id
    if update.category_id is not None:
        manga_data["category_id"] = update.category_id
    if update.subcategory_id is not None:
        manga_data["subcategory_id"] = update.subcategory_id
    if update.name is not None:
        manga_data["name"] = update.name
    if update.description is not None:
        manga_data["description]"] = update.description
    if update.publish_time is not None:
        manga_data["publish_time"] = update.publish_time

    manga = Manga(**manga_data)
    redis.set(manga_id, manga.json())
    return {"data":f"Manga is updated with title as {manga.name}"}

######################################################################
users=[]

def check_user(data: UserLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False

@app.post("/user/signup", tags=["user"])
def create_user(user: UserSchema = Body(...)):
    users.append(user) # replace with db call, making sure to hash the password first
    return create_jwt_token(user.email)

@app.post("/user/login", tags=["user"])
def user_login(user: UserLoginSchema = Body(...)):
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
######################################################################

#Stars
######################################################################
@app.get("/{manga_id}/stars",response_model=List[Stars], tags=["stars"])
def get_all_stars(manga_id: str):               
    stars_ids = redis.lrange("stars", 0, -1)
    stars = []
    for id in stars_ids:
        # Fetch each stars by ID
        stars_data = redis.get(id)
        if stars_data is not None:
            star_obj = Stars.parse_raw(stars_data)
            if star_obj.manga_id == manga_id:
                stars.append(star_obj)

    return stars

@app.post("/{manga_id}/{user_id}/stars/new",response_model=Stars,dependencies=[Depends(JWTBearer())], tags=["stars"])
def create_stars(manga_id,
                 user_id,
                 stars: Stars = Body(...)):
    # Create a new ID for the stars
    stars_id = str( uuid.uuid4())
    stars.stars_id = stars_id
    stars.manga_id = manga_id
    stars.user_id = user_id

    # Save the stars data in Redis
    redis.set(stars_id, stars.json())

    # Add the stars ID to the list of stars IDs
    redis.rpush("stars", stars_id)

    return stars

######################################################################


#Comment
######################################################################
@app.get("/{manga_id}/comments",response_model=List[Comment], tags=["comments"])
def get_all_comments(manga_id: str):               
    comment_ids = redis.lrange("stars", 0, -1)
    comments = []
    for id in comment_ids:
        # Fetch each stars by ID
        comments_data = redis.get(id)
        if comments_data is not None:
            comment_obj = Stars.parse_raw(comments_data)
            if comment_obj.manga_id == manga_id:
                comments.append(comment_obj)

    return comments

@app.post("/{manga_id}/{user_id}/category/new",response_model=Comment, tags=["comments"])
def create_comments(manga_id,
                 user_id,
                 comments : Comment = Body(...)):
    # Create a new ID for the stars
    cmt_id = str( uuid.uuid4())
    comments.comment_id = cmt_id
    comments.manga_id = manga_id
    comments.user_id = user_id

    # Save the stars data in Redis
    redis.set(cmt_id, comments.json())

    # Add the stars ID to the list of stars IDs
    redis.rpush("comments", cmt_id)

    return comments

######################################################################

#Wishlist
######################################################################

@app.get("/{user_id}/wishlist",response_model=List[WishlistCart], tags=["wishlist"])    
def get_all_wishlist(user_id: str):
    wishlist_ids = redis.lrange("wishlist", 0, -1)
    wishlist = []
    for id in wishlist_ids:
        # Fetch each wishlist by ID
        wishlist_data = redis.get(id)
        if wishlist_data is not None:
            wishlist_obj = WishlistCart.parse_raw(wishlist_data)
            if wishlist_obj.user_id == user_id:
                manga_data = redis.get(wishlist_obj.manga_id)
                if manga_data is not None:
                    manga_obj = Manga.parse_raw(manga_data)
                    wishlist_obj.price = manga_obj.price
                wishlist.append(wishlist_obj)

    return wishlist

@app.post("/{manga_id}/{user_id}/wishlist/new",response_model=WishlistCart, tags=["wishlist"])
def create_wishlist(wishlist: WishlistCart,manga_id,user_id):
    # Create a new ID for the wishlist
    wishlist_id = str( uuid.uuid4())
    wishlist.wishlist_id = wishlist_id
    wishlist.manga_id = manga_id
    wishlist.user_id = user_id
    wishlist.status = 1
    if wishlist.user_id == user_id:
        manga_data = redis.get(wishlist.manga_id)
        if manga_data is not None:
            manga_obj = Manga.parse_raw(manga_data)
            wishlist.price = manga_obj.price
    # Save the wishlist data in Redis
    redis.set(wishlist_id, wishlist.json())

    # Add the wishlist ID to the list of wishlist IDs
    redis.rpush("wishlist", wishlist_id)

    return wishlist

@app.post("/{manga_id}/{user_id}/wishlist/delete",response_model=WishlistCart, tags=["wishlist"])
def delete_wishlist(wishlist: WishlistCart,manga_id,user_id):
      wishlist.status = 0
      redis.set(wishlist.wishlist_id, wishlist.json())
      return wishlist                                       

      
######################################################################

#Cart
######################################################################

@app.get("/{user_id}/cart",response_model=List[WishlistCart], tags=["cart"])    
def get_all_wishlist(user_id: str):
    cart_ids = redis.lrange("cart", 0, -1)
    cart = []
    for id in cart_ids:
        # Fetch each wishlist by ID
        cart_data = redis.get(id)
        if cart_data is not None:
            cart_obj = WishlistCart.parse_raw(cart_data)
            if cart_obj.user_id == user_id:
                manga_data = redis.get(cart_obj.manga_id)
                if manga_data is not None:
                    manga_obj = Manga.parse_raw(manga_data)
                    cart_obj.price = manga_obj.price
                cart.append(cart_obj)

    return cart

@app.post("/{manga_id}/{user_id}/cart/new",response_model=WishlistCart, tags=["cart"])
def create_wishlist(cart: WishlistCart,manga_id,user_id):
    # Create a new ID for the wishlist
    cart_id = str( uuid.uuid4())
    cart.wishlist_id = cart_id
    cart.manga_id = manga_id
    cart.user_id = user_id
    if cart.user_id == user_id:
        manga_data = redis.get(cart.manga_id)
        if manga_data is not None:
            manga_obj = Manga.parse_raw(manga_data)
            cart.price = manga_obj.price
    # Save the wishlist data in Redis
    redis.set(cart_id, cart.json())

    # Add the wishlist ID to the list of wishlist IDs
    redis.rpush("cart", cart_id)

    return cart

@app.post("/{manga_id}/{user_id}/cart/delete",response_model=WishlistCart, tags=["cart"])
def delete_wishlist(wishlist: WishlistCart,manga_id,user_id):
        wishlist.status = 1
        redis.set(wishlist.wishlist_id, wishlist.json())
        return wishlist
      
######################################################################

#Category
######################################################################

app.get("/category",response_model=List[Category], tags=["category"])
def get_all_category():
                
                category_ids = redis.lrange("category", 0, -1)
                
                category = []
                for id in category_ids:
                    # Fetch each category by ID
                    category_data = redis.get(id)
                    if category_data is not None:
                        category_obj = Category.parse_raw(category_data)
                        category.append(category_obj)
        
                return category


######################################################################
#SubCategory
######################################################################
######################################################################

@app.get("/")
async def root():
    return {"data":{"message": "Hello World","name":"Sudenur Meydan"}}
