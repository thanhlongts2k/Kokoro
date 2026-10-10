import json
from datetime import datetime, timedelta
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from app.config import Config
from app.database import get_db, get_cursor
from app.services.media_service import MediaService
from app.auth import get_current_user

def require_auth(request: Request):
    """Helper to check current user or return 401 response tuple (user, error_response)."""
    user = get_current_user(request)
    if not user:
        return None, JSONResponse({
            "status": "error",
            "message": "Vui lòng đăng nhập để xem và quản lý nhật ký 🌸",
            "authenticated": False
        }, status_code=401)
    return user, None

async def get_entries(request: Request) -> JSONResponse:
    """
    Retrieve entries from PostgreSQL database strictly scoped to the authenticated user.
    Query filters: ?mood=... &tag=... &month=... &search=...
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    query_params = request.query_params
    mood = query_params.get("mood")
    tag = query_params.get("tag")
    month = query_params.get("month")
    search = query_params.get("search")

    sql = """
        SELECT e.id, e.user_id, e.title, e.content, e.mood, e.weather, 
               e.entry_date, e.is_pinned, e.created_at, e.updated_at,
               COALESCE(
                   json_agg(DISTINCT jsonb_build_object(
                       'id', p.id,
                       'url', p.file_path,
                       'thumbUrl', p.thumb_path,
                       'name', p.file_name,
                       'order', p.sort_order
                   )) FILTER (WHERE p.id IS NOT NULL), '[]'
               ) AS photos,
               COALESCE(
                   array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL), '{}'
               ) AS tags
        FROM entries e
        LEFT JOIN entry_photos p ON e.id = p.entry_id
        LEFT JOIN entry_tags et ON e.id = et.entry_id
        LEFT JOIN tags t ON et.tag_id = t.id
        WHERE e.user_id = %s
    """
    params = [user_id]

    if mood and mood != "all":
        sql += " AND e.mood = %s"
        params.append(mood)

    if tag:
        clean_tag = tag if tag.startswith("#") else f"#{tag}"
        sql += " AND t.name = %s"
        params.append(clean_tag)

    if month:
        # Format YYYY-MM
        sql += " AND TO_CHAR(e.entry_date, 'YYYY-MM') = %s"
        params.append(month)

    if search:
        sql += " AND (e.title ILIKE %s OR e.content ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += """
        GROUP BY e.id
        ORDER BY e.is_pinned DESC, e.entry_date DESC, e.created_at DESC
    """

    try:
        with get_cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

        entries = []
        for r in rows:
            entry = dict(r)
            if entry.get("entry_date"):
                d = entry["entry_date"]
                created = entry.get("created_at")
                time_str = created.strftime("%H:%M") if created else "08:00"
                entry["displayDate"] = f"{d.strftime('%d/%m/%Y')}, {time_str}"
                entry["entryDate"] = d.isoformat()
                entry["entry_date"] = d.isoformat()
            if entry.get("created_at"):
                entry["createdAt"] = entry["created_at"].isoformat()
                entry["created_at"] = entry["created_at"].isoformat()
            if entry.get("updated_at"):
                entry["updatedAt"] = entry["updated_at"].isoformat()
                entry["updated_at"] = entry["updated_at"].isoformat()
            
            # Map mood label with icon
            mood_labels = {
                "serene": "Serene 🌸",
                "cozy": "Cozy ☕",
                "reflective": "Reflective 🌙",
                "grateful": "Grateful 🍵",
                "energetic": "Energetic ⚡",
                "melancholy": "Melancholy 🌧️"
            }
            entry["moodLabel"] = mood_labels.get(entry["mood"], entry["mood"].capitalize())
            entries.append(entry)

        return JSONResponse({"status": "success", "count": len(entries), "entries": entries})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e), "entries": []}, status_code=500)

async def create_entry(request: Request) -> JSONResponse:
    """
    Create a new journal entry with multipart/form-data belonging strictly to the authenticated user.
    Accepts: title, content, mood, weather, entry_date, tags, photos (files)
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]

    try:
        form = await request.form()
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Form parse error: {e}"}, status_code=400)

    title = form.get("title", "").strip() or "Khoảnh khắc tĩnh lặng"
    content = form.get("content", "").strip()
    if not content:
        return JSONResponse({"status": "error", "message": "Nội dung nhật ký không được để trống."}, status_code=400)

    mood = form.get("mood", "serene").strip()
    weather = form.get("weather", "sunny").strip()
    entry_date_str = form.get("entry_date", "").strip()
    if not entry_date_str:
        entry_date = datetime.now().date()
    else:
        try:
            entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
        except ValueError:
            entry_date = datetime.now().date()

    raw_tags = form.get("tags", "")
    tag_list = []
    if raw_tags:
        for t in raw_tags.replace(",", " ").split():
            clean = t.strip()
            if clean:
                tag_list.append(clean if clean.startswith("#") else f"#{clean}")

    # Process photo files
    photo_files = form.getlist("photos")
    processed_photos = []
    for idx, photo_item in enumerate(photo_files):
        if hasattr(photo_item, "read") and hasattr(photo_item, "filename") and photo_item.filename:
            file_bytes = await photo_item.read()
            if len(file_bytes) > 0:
                rel_path, thumb_path, size, w, h = MediaService.process_and_save_image(
                    file_bytes, photo_item.filename
                )
                processed_photos.append({
                    "file_path": rel_path,
                    "thumb_path": thumb_path,
                    "file_name": photo_item.filename,
                    "file_size": size,
                    "width": w,
                    "height": h,
                    "sort_order": idx
                })

    # Save to PostgreSQL in a transaction
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # 1. Insert Entry scoped to authenticated user_id
                cur.execute("""
                    INSERT INTO entries (user_id, title, content, mood, weather, entry_date, is_pinned)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                    RETURNING id, created_at;
                """, (user_id, title, content, mood, weather, entry_date))
                entry_id, created_at = cur.fetchone()

                # 2. Insert Photos
                for p in processed_photos:
                    cur.execute("""
                        INSERT INTO entry_photos (entry_id, file_path, thumb_path, file_name, file_size, width, height, sort_order)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (entry_id, p["file_path"], p["thumb_path"], p["file_name"], p["file_size"], p["width"], p["height"], p["sort_order"]))

                # 3. Insert Tags & Link
                for t_name in tag_list:
                    cur.execute("""
                        INSERT INTO tags (user_id, name)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id;
                    """, (user_id, t_name))
                    tag_id = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO entry_tags (entry_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (entry_id, tag_id))

        return JSONResponse({
            "status": "success",
            "message": "Đã lưu nhật ký thành công! 🌸",
            "entry_id": entry_id
        }, status_code=201)

    except Exception as e:
        # Cleanup uploaded files on DB failure
        if processed_photos:
            MediaService.delete_photo_files([p["file_path"] for p in processed_photos])
            MediaService.delete_photo_files([p["thumb_path"] for p in processed_photos])
        return JSONResponse({"status": "error", "message": f"Database save error: {e}"}, status_code=500)

async def delete_entry(request: Request) -> JSONResponse:
    """Delete an entry and all its associated photos, verifying user ownership."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    entry_id = request.path_params.get("id")
    try:
        entry_id = int(entry_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=400)

    try:
        # Retrieve photo paths before deleting, verifying user ownership
        photo_paths = []
        with get_cursor() as cur:
            cur.execute("""
                SELECT p.file_path, p.thumb_path 
                FROM entry_photos p
                JOIN entries e ON p.entry_id = e.id
                WHERE e.id = %s AND e.user_id = %s;
            """, (entry_id, user_id))
            rows = cur.fetchall()
            for r in rows:
                if r["file_path"]: photo_paths.append(r["file_path"])
                if r["thumb_path"]: photo_paths.append(r["thumb_path"])

        # Delete entry with user_id filter
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM entries WHERE id = %s AND user_id = %s RETURNING id;", (entry_id, user_id))
                deleted = cur.fetchone()
                if not deleted:
                    return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết hoặc bạn không có quyền xóa."}, status_code=404)

        # Delete image files on disk
        if photo_paths:
            MediaService.delete_photo_files(photo_paths)

        return JSONResponse({"status": "success", "message": "Đã xóa bài viết thành công. 🌸", "id": entry_id})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

async def toggle_pin_entry(request: Request) -> JSONResponse:
    """Toggle is_pinned status of an entry strictly owned by current user."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    entry_id = request.path_params.get("id")
    try:
        entry_id = int(entry_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=400)

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE entries 
                    SET is_pinned = NOT is_pinned, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING id, is_pinned;
                """, (entry_id, user_id))
                res = cur.fetchone()
                if not res:
                    return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết hoặc bạn không có quyền ghim."}, status_code=404)
                
                is_pinned = res[1]

        return JSONResponse({
            "status": "success",
            "id": entry_id,
            "is_pinned": is_pinned,
            "message": "Đã ghim bài viết ✨" if is_pinned else "Đã bỏ ghim bài viết"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

def calculate_streak_days(entry_dates: list) -> int:
    """Calculate consecutive active writing streak based on distinct dates."""
    if not entry_dates:
        return 0

    today = datetime.now().date()
    date_set = set()
    for d in entry_dates:
        if isinstance(d, datetime):
            date_set.add(d.date())
        elif hasattr(d, "year"):
            date_set.add(d)
        elif isinstance(d, str):
            try:
                date_set.add(datetime.strptime(d[:10], "%Y-%m-%d").date())
            except ValueError:
                pass

    if not date_set:
        return 0

    # If wrote today: streak starts today.
    # If didn't write today but wrote yesterday: streak is still active, starting yesterday.
    current_check = today
    if current_check not in date_set:
        current_check = today - timedelta(days=1)
        if current_check not in date_set:
            return 0

    streak = 0
    while current_check in date_set:
        streak += 1
        current_check -= timedelta(days=1)

    return streak

async def export_entries(request: Request) -> Response:
    """
    Export all journal entries belonging strictly to the authenticated user.
    Returns JSON file attachment: kokoro_backup_{date}.json
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]

    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT e.id, e.title, e.content, e.mood, e.weather,
                       e.entry_date, e.is_pinned, e.created_at, e.updated_at,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', ep.id,
                                   'file_path', ep.file_path,
                                   'thumb_path', ep.thumb_path,
                                   'file_name', ep.file_name,
                                   'file_size', ep.file_size,
                                   'width', ep.width,
                                   'height', ep.height,
                                   'sort_order', ep.sort_order
                               ) ORDER BY ep.sort_order
                           ) FILTER (WHERE ep.id IS NOT NULL), '[]'
                       ) AS photos
                FROM entries e
                LEFT JOIN entry_photos ep ON e.id = ep.entry_id
                WHERE e.user_id = %s
                GROUP BY e.id
                ORDER BY e.entry_date DESC, e.id DESC;
            """, (user_id,))
            raw_entries = cur.fetchall()

            cur.execute("""
                SELECT et.entry_id, t.name as tag_name
                FROM entry_tags et
                JOIN tags t ON et.tag_id = t.id
                JOIN entries e ON et.entry_id = e.id
                WHERE e.user_id = %s;
            """, (user_id,))
            tag_rows = cur.fetchall()

        tag_map = {}
        for tr in tag_rows:
            tag_map.setdefault(tr["entry_id"], []).append(tr["tag_name"])

        entries_list = []
        for r in raw_entries:
            item = dict(r)
            if item.get("entry_date"):
                item["entry_date"] = str(item["entry_date"])
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()
            if item.get("updated_at"):
                item["updated_at"] = item["updated_at"].isoformat()
            item["tags"] = tag_map.get(item["id"], [])
            entries_list.append(item)

        export_data = {
            "app": "Kokoro (心) — Nhật Ký Cảm Xúc & Kỷ Niệm",
            "version": Config.APP_VERSION,
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            },
            "total_entries": len(entries_list),
            "entries": entries_list
        }

        today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kokoro_backup_{today_str}.json"

        json_bytes = json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")
        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/json; charset=utf-8"
            }
        )
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Lỗi xuất dữ liệu: {e}"}, status_code=500)

async def get_stats(request: Request) -> JSONResponse:
    """Calculate summary statistics strictly scoped to the authenticated user."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    try:
        with get_cursor() as cur:
            # 1. Total entries
            cur.execute("SELECT count(*) as total FROM entries WHERE user_id = %s;", (user_id,))
            total = cur.fetchone()["total"]

            # 2. Total photos
            cur.execute("""
                SELECT count(*) as total_photos 
                FROM entry_photos ep 
                JOIN entries e ON ep.entry_id = e.id 
                WHERE e.user_id = %s;
            """, (user_id,))
            total_photos = cur.fetchone()["total_photos"]

            # 3. Mood breakdown for 5 standard moods
            cur.execute("""
                SELECT mood, count(*) as count 
                FROM entries 
                WHERE user_id = %s
                GROUP BY mood;
            """, (user_id,))
            raw_moods = {r["mood"]: r["count"] for r in cur.fetchall()}

            all_moods = ["serene", "cozy", "reflective", "grateful", "energetic"]
            mood_breakdown = {}
            for m in all_moods:
                cnt = raw_moods.get(m, 0)
                pct = round((cnt / total * 100), 1) if total > 0 else 0
                mood_breakdown[m] = {"count": cnt, "percent": pct}

            serene_percent = mood_breakdown["serene"]["percent"]

            # 4. Streak calculation
            cur.execute("""
                SELECT DISTINCT entry_date 
                FROM entries 
                WHERE user_id = %s 
                ORDER BY entry_date DESC;
            """, (user_id,))
            entry_dates = [r["entry_date"] for r in cur.fetchall()]
            streak_days = calculate_streak_days(entry_dates)

        return JSONResponse({
            "status": "success",
            "totalEntries": total,
            "totalPhotos": total_photos,
            "streakDays": streak_days,
            "serenePercent": serene_percent,
            "moodBreakdown": mood_breakdown,
            "moodCounts": raw_moods
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

entry_routes = [
    Route("/api/entries", get_entries, methods=["GET"]),
    Route("/api/entries", create_entry, methods=["POST"]),
    Route("/api/entries/export", export_entries, methods=["GET"]),
    Route("/api/entries/{id:int}", delete_entry, methods=["DELETE"]),
    Route("/api/entries/{id:int}/pin", toggle_pin_entry, methods=["PATCH"]),
    Route("/api/stats/summary", get_stats, methods=["GET"]),
]
