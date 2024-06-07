from asyncio import Queue
from os import getenv
from typing import Optional, Union
from fastapi import FastAPI, HTTPException, status, Query, Response
from pydantic import BaseModel
from typing import Optional
from random import randrange
from prometheus_client import Counter, Histogram


# Loki 
import logging
from logging_loki import LokiQueueHandler

# Prometheus FastAPI instrumentor
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Loki Integration
loki_logs_handler = LokiQueueHandler(
    Queue(-1),
    url=getenv("LOKI_ENDPOINT"),
    tags={"application": "kubefast"},
    version="1",
)

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addHandler(loki_logs_handler)


# Instruments the app with default metrics and exposes the metrics (Prometheus)
Instrumentator().instrument(app).expose(app)

class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    ratings: Optional[int] = None
    
    
my_list = [
    {"title": "title of post 1", "content": "content of post 1", "id": 1},
    {"title": "title of post 2", "content": "content of post 2", "id": 2}
]

def find_post(id):
    for p in my_list:
        if p["id"] == id:
            return p
          
def find_index_post(id):
    for i, p in enumerate(my_list):
        if p['id'] == id:
            return i

@app.get("/")
def read_root():
    return {"status": "healthy"}

# Implementation of Prometheus Histogram and Counter
request_counter = Counter('fastapi_request_count', 'Total number of requests')
request_latency = Histogram('fastapi_request_latency_seconds', 'Request latency in seconds')
  
@app.get("/posts")
def get_all_posts():
    request_counter.inc()  # Increment request counter
    with request_latency.time():  # Measure latency
        return {"data": my_list}
    
    
@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(post: Post):
    request_counter.inc()  # Increment request counter
    post_dict = post.model_dump()
    with request_latency.time():  # Measure latency
        post_dict["id"] = randrange(0, 1000000)
        my_list.append(post_dict)
        return {"data": post_dict}
  
@app.get("/posts/latest")
def get_latest_post():
    post = my_list[-1]
    return {"post_detail": post}
  
@app.get("/posts/{id}")
def get_post_by_id(id: int):
    post = find_post(id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID {id} not found")
    return {"post_detail": post}
  
@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):
    indx = find_index_post(id)
    if indx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID {id} does not exist")
    my_list.pop(indx)
    return {"message": f"Post with ID {id} successfully deleted"}

@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    indx = find_index_post(id)
    if indx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID {id} does not exist")
    post_dict = post.model_dump()
    post_dict['id'] = id
    my_list[indx] = post_dict
    return {"message": f"Post with ID {id} successfully updated"}


# Example for creating custom Metrics

# Custom Prometheus metric
fast_api_workload_count = Counter('fast_api_workload_count', 'Number of times workload endpoint is called')

@app.get("/workload")
def workload():
    fast_api_workload_count.inc()  # Increment the custom Prometheus counter
    return {"message": "This is a workload endpoint"}



