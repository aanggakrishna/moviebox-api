import sys
import os
import traceback

# --- Diagnostic wrapper: catch ANY import error and surface it via the API ---
_import_error = None

try:
    import types
    import logging

    # Menambahkan root folder (src) ke Python path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

    # Pre-register moviebox_api as a minimal package in sys.modules BEFORE any
    # submodule imports.  This prevents Python from executing the full __init__.py
    # which eagerly imports throttlebuster, download, extras/auto — none of which
    # are needed by the API.
    if 'moviebox_api' not in sys.modules:
        _pkg = types.ModuleType('moviebox_api')
        _pkg.__path__ = [os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')), 'moviebox_api')]
        _pkg.__package__ = 'moviebox_api'
        _pkg.logger = logging.getLogger('moviebox_api')
        sys.modules['moviebox_api'] = _pkg

    from fastapi import FastAPI, HTTPException, Request, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from moviebox_api.requests import Session
    from moviebox_api.core import Search, Trending, Homepage, MovieDetails, TVSeriesDetails

except Exception:
    _import_error = traceback.format_exc()

# --- If imports failed, create a diagnostic app that shows the error ---
if _import_error:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="MovieBox API - IMPORT ERROR")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.get("/{path:path}")
    async def diagnostic(path: str = ""):
        return {
            "error": "Module import failed",
            "traceback": _import_error,
            "python_version": sys.version,
            "sys_path": sys.path,
            "cwd": os.getcwd(),
        }

else:
    # --- Normal app ---
    app = FastAPI(title="MovieBox API Server", description="Unofficial MovieBox Vercel API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    async def get_session(request: Request):
        """Dependency runtime-safe untuk koneksi proxy/serverless."""
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
