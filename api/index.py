from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from moviebox_api.requests import Session
from moviebox_api.core import Search, Trending, Homepage, MovieDetails, TVSeriesDetails

app = FastAPI(title="MovieBox API Server", description="Unofficial MovieBox Vercel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_session(request: Request):
    """Dependency runtime-safe untuk koneksi proxy/serverless.
    Di HTTPX versi baru, inisialisasi langsung obj AsyncClient() dari luar siklus async bisa error.
    """
    if not hasattr(request.app.state, "session"):
        request.app.state.session = Session()
    return request.app.state.session

@app.get("/")
async def root():
    return {"message": "MovieBox API Server running on Vercel", "status": "success"}

@app.get("/api/homepage")
async def get_homepage(session: Session = Depends(get_session)):
    try:
        home = Homepage(session)
        return await home.get_content()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search(query: str, subject_type: int = 0, page: int = 1, per_page: int = 24, session: Session = Depends(get_session)):
    try:
        search_obj = Search(session, query=query, subject_type=subject_type, page=page, per_page=per_page)
        return await search_obj.get_content()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trending")
async def trending(page: int = 0, per_page: int = 18, session: Session = Depends(get_session)):
    try:
        trend = Trending(session, page=page, per_page=per_page)
        return await trend.get_content()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/movie/{movie_id}")
async def get_movie(movie_id: int, session: Session = Depends(get_session)):
    try:
        movie = MovieDetails(session, str(movie_id))
        return await movie.get_content()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/series/{series_id}")
async def get_series(series_id: int, session: Session = Depends(get_session)):
    try:
        series = TVSeriesDetails(session, str(series_id))
        return await series.get_content()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
