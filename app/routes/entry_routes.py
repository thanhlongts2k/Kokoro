import json
from datetime import datetime, timedelta
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from app.config import Config
from app.database import get_db, get_cursor
from app.services.media_service import MediaService
from app.auth import get_current_user


NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}

def require_auth(request: Request):
    """Helper to check current user or return 401 response tuple (user, error_response)."""
    user = get_current_user(request)
    if not user:
        return None, JSONResponse({
            "status": "error",
            "message": "Vui lòng đăng nhập để xem và quản lý nhật ký 🌸",
            "authenticated": False
        }, status_code=401, headers=NO_CACHE_HEADERS)
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
    category_param = query_params.get("category_id") or query_params.get("category")

    sql = """
        SELECT e.id, e.user_id, e.category_id,
               c.name AS category_name, c.icon AS category_icon, c.color AS category_color,
               e.title, e.content, e.mood, e.weather, 
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
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN entry_photos p ON e.id = p.entry_id
        LEFT JOIN entry_tags et ON e.id = et.entry_id
        LEFT JOIN tags t ON et.tag_id = t.id
        WHERE e.user_id = %s
    """
    params = [user_id]

    if mood and mood != "all":
        sql += " AND e.mood = %s"
        params.append(mood)

    if category_param and category_param != "all":
        if category_param in ("uncategorized", "null", "none"):
            sql += " AND e.category_id IS NULL"
        else:
            try:
                cat_id = int(category_param)
                sql += " AND e.category_id = %s"
                params.append(cat_id)
            except (ValueError, TypeError):
                pass

    if tag:
        clean_tag = tag if tag.startswith("#") else f"#{tag}"
        sql += " AND t.name = %s"
        params.append(clean_tag)

    if month:
        # Format YYYY-MM
        sql += " AND TO_CHAR(e.entry_date, 'YYYY-MM') = %s"
        params.append(month)

    if search:
        clean_search = search.strip()
        tag_search = clean_search if clean_search.startswith("#") else f"#{clean_search}"
        sql += " AND (e.title ILIKE %s OR e.content ILIKE %s OR t.name ILIKE %s OR t.name ILIKE %s)"
        params.extend([f"%{clean_search}%", f"%{clean_search}%", f"%{clean_search}%", f"%{tag_search}%"])

    sql += """
        GROUP BY e.id, c.id
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
            
            entry["categoryId"] = entry.get("category_id")
            entry["category_id"] = entry.get("category_id")
            entry["categoryName"] = entry.get("category_name")
            entry["category_name"] = entry.get("category_name")
            entry["categoryIcon"] = entry.get("category_icon")
            entry["category_icon"] = entry.get("category_icon")
            entry["categoryColor"] = entry.get("category_color")
            entry["category_color"] = entry.get("category_color")

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

        return JSONResponse({"status": "success", "count": len(entries), "entries": entries}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e), "entries": []}, status_code=500, headers=NO_CACHE_HEADERS)

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
    photo_files = form.getlist("photos")
    has_photos = any(hasattr(p, "filename") and p.filename for p in photo_files)

    if not content and not has_photos:
        return JSONResponse({"status": "error", "message": "Vui lòng nhập nội dung hoặc đính kèm ít nhất một hình ảnh 🌸"}, status_code=400)

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

    created_at_str = form.get("created_at", "").strip()
    custom_created_at = None
    if created_at_str:
        try:
            custom_created_at = datetime.fromisoformat(created_at_str)
        except Exception:
            custom_created_at = None

    raw_tags = form.get("tags", "")
    tag_list = []
    if raw_tags:
        for t in raw_tags.replace(",", " ").split():
            clean = t.strip()
            if clean:
                tag_list.append(clean if clean.startswith("#") else f"#{clean}")

    # Parse category_id
    category_id_raw = form.get("category_id")
    category_id = None
    if category_id_raw and str(category_id_raw).strip() and str(category_id_raw).strip().lower() != "null":
        try:
            val = int(category_id_raw)
            with get_cursor() as check_cur:
                check_cur.execute("SELECT id FROM categories WHERE id = %s AND user_id = %s;", (val, user_id))
                if check_cur.fetchone():
                    category_id = val
        except (ValueError, TypeError):
            category_id = None

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
                if custom_created_at:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date, created_at, is_pinned)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                        RETURNING id, created_at;
                    """, (user_id, category_id, title, content, mood, weather, entry_date, custom_created_at))
                else:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date, is_pinned)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
                        RETURNING id, created_at;
                    """, (user_id, category_id, title, content, mood, weather, entry_date))
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

async def update_entry(request: Request) -> JSONResponse:
    """
    Update an existing entry, strictly scoped to current user.
    Accepts multipart/form-data:
    - title, content, mood, weather, entry_date, tags
    - photos (optional additional photos)
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    entry_id = request.path_params.get("id")
    try:
        entry_id = int(entry_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=400)

    # Verify ownership
    with get_cursor() as cur:
        cur.execute("SELECT id FROM entries WHERE id = %s AND user_id = %s;", (entry_id, user_id))
        if not cur.fetchone():
            return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết hoặc bạn không có quyền sửa."}, status_code=404)

    form = await request.form()

    # Payload integrity guard: Reject completely empty form (e.g. WebKit empty body drop)
    has_any_field = any([
        form.get("title") is not None,
        form.get("content") is not None,
        form.get("mood") is not None,
        form.get("deleted_photo_ids") is not None,
        len(form.getlist("photos")) > 0
    ])
    if not has_any_field:
        return JSONResponse({
            "status": "error",
            "message": "Dữ liệu cập nhật không hợp lệ hoặc payload bị rỗng 🌸"
        }, status_code=400, headers=NO_CACHE_HEADERS)

    title = (form.get("title") or "").strip() or "Khoảnh khắc tĩnh lặng"
    content = (form.get("content") or "").strip()

    deleted_photo_ids_raw = form.get("deleted_photo_ids", "")
    deleted_photo_ids = []
    if deleted_photo_ids_raw:
        try:
            parsed = json.loads(deleted_photo_ids_raw)
            if isinstance(parsed, list):
                deleted_photo_ids = [int(x) for x in parsed if str(x).isdigit()]
        except Exception:
            pass

    mood = form.get("mood", "serene").strip()
    weather = form.get("weather", "sunny").strip()
    entry_date_str = form.get("entry_date", "").strip()
    entry_date = datetime.now().date()
    if entry_date_str:
        try:
            entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    created_at_str = form.get("created_at", "").strip()
    custom_created_at = None
    if created_at_str:
        try:
            custom_created_at = datetime.fromisoformat(created_at_str)
        except Exception:
            custom_created_at = None

    raw_tags = form.get("tags", "")
    tag_list = []
    if raw_tags:
        for t in raw_tags.replace(",", " ").split():
            clean = t.strip()
            if clean:
                tag_list.append(clean if clean.startswith("#") else f"#{clean}")

    # Parse category_id
    category_id_raw = form.get("category_id")
    category_id = None
    update_category = False
    if category_id_raw is not None:
        update_category = True
        raw_str = str(category_id_raw).strip()
        if raw_str and raw_str.lower() != "null" and raw_str != "":
            try:
                val = int(raw_str)
                with get_cursor() as check_cur:
                    check_cur.execute("SELECT id FROM categories WHERE id = %s AND user_id = %s;", (val, user_id))
                    if check_cur.fetchone():
                        category_id = val
            except (ValueError, TypeError):
                category_id = None

    # Process any newly uploaded photo files
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

    deleted_paths = []
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Check validation: content or remaining photos
                cur.execute("SELECT id FROM entry_photos WHERE entry_id = %s;", (entry_id,))
                existing_rows = cur.fetchall()
                existing_pids = [(r[0] if isinstance(r, (tuple, list)) else r["id"]) for r in existing_rows]
                remaining_count = len([pid for pid in existing_pids if pid not in deleted_photo_ids]) + len(processed_photos)

                if not content and remaining_count == 0:
                    return JSONResponse({"status": "error", "message": "Vui lòng nhập nội dung hoặc đính kèm ít nhất một hình ảnh 🌸"}, status_code=400)

                # 1. Update entry metadata
                if update_category:
                    if custom_created_at:
                        cur.execute("""
                            UPDATE entries
                            SET category_id = %s, title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, created_at = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (category_id, title, content, mood, weather, entry_date, custom_created_at, entry_id, user_id))
                    else:
                        cur.execute("""
                            UPDATE entries
                            SET category_id = %s, title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (category_id, title, content, mood, weather, entry_date, entry_id, user_id))
                else:
                    if custom_created_at:
                        cur.execute("""
                            UPDATE entries
                            SET title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, created_at = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (title, content, mood, weather, entry_date, custom_created_at, entry_id, user_id))
                    else:
                        cur.execute("""
                            UPDATE entries
                            SET title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (title, content, mood, weather, entry_date, entry_id, user_id))

                if cur.rowcount == 0:
                    return JSONResponse({
                        "status": "error",
                        "message": "Không tìm thấy bài viết hoặc bạn không có quyền sửa."
                    }, status_code=404, headers=NO_CACHE_HEADERS)

                # 2. Delete removed photos from DB & collect disk paths
                if deleted_photo_ids:
                    cur.execute("""
                        SELECT file_path, thumb_path 
                        FROM entry_photos 
                        WHERE entry_id = %s AND id = ANY(%s);
                    """, (entry_id, deleted_photo_ids))
                    for r in cur.fetchall():
                        fp = r[0] if isinstance(r, (tuple, list)) else r["file_path"]
                        tp = r[1] if isinstance(r, (tuple, list)) else r["thumb_path"]
                        if fp: deleted_paths.append(fp)
                        if tp: deleted_paths.append(tp)

                    cur.execute("""
                        DELETE FROM entry_photos 
                        WHERE entry_id = %s AND id = ANY(%s);
                    """, (entry_id, deleted_photo_ids))

                # 3. Append new photos if provided
                if processed_photos:
                    cur.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM entry_photos WHERE entry_id = %s;", (entry_id,))
                    row_max = cur.fetchone()
                    base_sort = (row_max[0] if isinstance(row_max, (tuple, list)) else row_max.get("coalesce", 0)) if row_max else 0
                    for p in processed_photos:
                        cur.execute("""
                            INSERT INTO entry_photos (entry_id, file_path, thumb_path, file_name, file_size, width, height, sort_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """, (entry_id, p["file_path"], p["thumb_path"], p["file_name"], p["file_size"], p["width"], p["height"], base_sort + p["sort_order"]))

                # 4. Update tags: Remove old links and add new tags
                cur.execute("DELETE FROM entry_tags WHERE entry_id = %s;", (entry_id,))
                for t_name in tag_list:
                    cur.execute("""
                        INSERT INTO tags (user_id, name)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id;
                    """, (user_id, t_name))
                    tag_row = cur.fetchone()
                    tag_id = tag_row[0] if isinstance(tag_row, (tuple, list)) else tag_row["id"]
                    cur.execute("""
                        INSERT INTO entry_tags (entry_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (entry_id, tag_id))

                # 5. Clean orphaned tags for this user
                cur.execute("""
                    DELETE FROM tags 
                    WHERE user_id = %s 
                      AND id NOT IN (SELECT tag_id FROM entry_tags WHERE tag_id IS NOT NULL);
                """, (user_id,))

        # Delete physical photo files on disk after successful DB commit
        if deleted_paths:
            MediaService.delete_photo_files(deleted_paths)

        return JSONResponse({
            "status": "success",
            "message": "Đã cập nhật bài viết thành công! ✨",
            "entry_id": entry_id
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        if processed_photos:
            MediaService.delete_photo_files([p["file_path"] for p in processed_photos])
            MediaService.delete_photo_files([p["thumb_path"] for p in processed_photos])
        return JSONResponse({"status": "error", "message": f"Lỗi cập nhật bài viết: {e}"}, status_code=500)

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

                # Clean orphaned tags for this user
                cur.execute("""
                    DELETE FROM tags 
                    WHERE user_id = %s 
                      AND id NOT IN (SELECT tag_id FROM entry_tags WHERE tag_id IS NOT NULL);
                """, (user_id,))

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
            # 1. Export custom categories of current user
            cur.execute("""
                SELECT id, name, icon, color, sort_order
                FROM categories
                WHERE user_id = %s
                ORDER BY sort_order ASC, id ASC;
            """, (user_id,))
            cat_rows = cur.fetchall()
            categories_list = [dict(c) for c in cat_rows]

            # 2. Export entries with joined category metadata
            cur.execute("""
                SELECT e.id, e.category_id,
                       c.name AS category_name, c.icon AS category_icon, c.color AS category_color,
                       e.title, e.content, e.mood, e.weather,
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
                LEFT JOIN categories c ON e.category_id = c.id
                LEFT JOIN entry_photos ep ON e.id = ep.entry_id
                WHERE e.user_id = %s
                GROUP BY e.id, c.id
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
            "export_version": "1.1",
            "exported_at": datetime.now().isoformat(),
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            },
            "total_categories": len(categories_list),
            "categories": categories_list,
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

async def import_entries(request: Request) -> JSONResponse:
    """
    Import entries and custom categories from a JSON backup file or payload into current user's account.
    Fully backward-compatible with v1.0 backup files (entries without category_id or categories table).
    Accepts:
    - multipart/form-data with file field 'backup_file' or 'file'
    - application/json with backup JSON payload
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    try:
        content_type = request.headers.get("content-type", "")
        payload = None

        if "multipart/form-data" in content_type:
            form = await request.form()
            upload_file = form.get("backup_file") or form.get("file")
            if not upload_file:
                return JSONResponse({"status": "error", "message": "Vui lòng chọn tệp sao lưu JSON 🌸"}, status_code=400)
            file_bytes = await upload_file.read()
            payload = json.loads(file_bytes.decode("utf-8"))
        elif "application/json" in content_type:
            payload = await request.json()
        else:
            body_bytes = await request.body()
            if body_bytes:
                payload = json.loads(body_bytes.decode("utf-8"))

        if not payload:
            return JSONResponse({"status": "error", "message": "Dữ liệu sao lưu trống hoặc không hợp lệ"}, status_code=400)

        entries_to_import = []
        if isinstance(payload, dict) and "entries" in payload:
            entries_to_import = payload["entries"]
        elif isinstance(payload, list):
            entries_to_import = payload
        else:
            return JSONResponse({"status": "error", "message": "Định dạng tệp sao lưu không đúng chuẩn Kokoro JSON"}, status_code=400)

        if not entries_to_import:
            return JSONResponse({"status": "success", "message": "Không có bài viết nào cần nhập", "imported_count": 0})

        imported_count = 0
        with get_cursor() as cur:
            # 1. Fetch current user's existing categories to avoid redundant inserts
            cur.execute("SELECT id, name FROM categories WHERE user_id = %s;", (user_id,))
            existing_cats = {r["name"]: r["id"] for r in cur.fetchall()}

            cat_id_mapping = {}   # old_id -> new_id
            cat_name_mapping = {} # name -> new_id

            # 2. Import and reconcile categories if present in backup (v1.1+)
            raw_cats = payload.get("categories") if isinstance(payload, dict) else []
            if raw_cats and isinstance(raw_cats, list):
                for cat in raw_cats:
                    cat_name = (cat.get("name") or "").strip()
                    if not cat_name:
                        continue
                    old_id = cat.get("id")
                    icon = cat.get("icon") or "📁"
                    color = cat.get("color") or "#ec4899"
                    sort_order = cat.get("sort_order") if cat.get("sort_order") is not None else 0

                    if cat_name in existing_cats:
                        new_cat_id = existing_cats[cat_name]
                    else:
                        # Fallback pre-check by name to be 100% immune to UNIQUE constraint syntax issues
                        cur.execute("SELECT id FROM categories WHERE user_id = %s AND name = %s;", (user_id, cat_name))
                        found_cat = cur.fetchone()
                        if found_cat:
                            new_cat_id = found_cat["id"]
                        else:
                            cur.execute("""
                                INSERT INTO categories (user_id, name, icon, color, sort_order)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (user_id, name) DO UPDATE SET icon = EXCLUDED.icon, color = EXCLUDED.color
                                RETURNING id;
                            """, (user_id, cat_name, icon, color, sort_order))
                            new_cat_id = cur.fetchone()["id"]
                        existing_cats[cat_name] = new_cat_id

                    if old_id is not None:
                        cat_id_mapping[old_id] = new_cat_id
                    cat_name_mapping[cat_name] = new_cat_id

            # 3. Import entries with robust fallback
            for item in entries_to_import:
                title = item.get("title") or "Nhật ký không tên"
                content = item.get("content") or ""
                mood = item.get("mood") or "serene"
                weather = item.get("weather") or "sunny"
                entry_date = item.get("entry_date") or datetime.now().date().isoformat()
                is_pinned = bool(item.get("is_pinned", False))

                # Parse creation timestamp if present, otherwise default to NOW()
                custom_created_at = None
                if item.get("created_at"):
                    try:
                        custom_created_at = datetime.fromisoformat(item["created_at"])
                    except Exception:
                        custom_created_at = None

                custom_updated_at = None
                if item.get("updated_at"):
                    try:
                        custom_updated_at = datetime.fromisoformat(item["updated_at"])
                    except Exception:
                        custom_updated_at = None

                # Resolve category_id safely
                old_cat_id = item.get("category_id")
                cat_name = (item.get("category_name") or "").strip()
                resolved_cat_id = None

                if old_cat_id is not None and old_cat_id in cat_id_mapping:
                    resolved_cat_id = cat_id_mapping[old_cat_id]
                elif cat_name and cat_name in cat_name_mapping:
                    resolved_cat_id = cat_name_mapping[cat_name]
                elif cat_name and cat_name in existing_cats:
                    resolved_cat_id = existing_cats[cat_name]
                elif old_cat_id is not None and old_cat_id in existing_cats.values():
                    resolved_cat_id = old_cat_id

                if custom_created_at:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date, is_pinned, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (user_id, resolved_cat_id, title, content, mood, weather, entry_date, is_pinned, custom_created_at, custom_updated_at or custom_created_at))
                else:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date, is_pinned, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id;
                    """, (user_id, resolved_cat_id, title, content, mood, weather, entry_date, is_pinned))

                new_entry_id = cur.fetchone()["id"]
                imported_count += 1

                tags = item.get("tags") or []
                for t in tags:
                    tag_name = t.strip()
                    if not tag_name.startswith("#"):
                        tag_name = f"#{tag_name}"
                    cur.execute("""
                        INSERT INTO tags (user_id, name)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id;
                    """, (user_id, tag_name))
                    tag_id = cur.fetchone()["id"]
                    cur.execute("""
                        INSERT INTO entry_tags (entry_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (new_entry_id, tag_id))

                photos = item.get("photos") or []
                for p in photos:
                    file_path = p.get("file_path")
                    thumb_path = p.get("thumb_path")
                    if file_path:
                        cur.execute("""
                            INSERT INTO entry_photos (entry_id, file_path, thumb_path, file_name, file_size, width, height, sort_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            new_entry_id,
                            file_path,
                            thumb_path or file_path,
                            p.get("file_name", "photo.webp"),
                            p.get("file_size", 0),
                            p.get("width", 0),
                            p.get("height", 0),
                            p.get("sort_order", 0)
                        ))

        return JSONResponse({
            "status": "success",
            "message": f"Đã khôi phục thành công {imported_count} bài viết! 🌸",
            "imported_count": imported_count
        })
    except json.JSONDecodeError:
        return JSONResponse({"status": "error", "message": "Tệp sao lưu không phải định dạng JSON hợp lệ"}, status_code=400)
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Lỗi khôi phục dữ liệu: {e}"}, status_code=500)

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
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

async def get_entry_by_id(request: Request) -> JSONResponse:
    """Retrieve a single entry by id strictly owned by current user."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    entry_id = request.path_params.get("id")
    try:
        entry_id = int(entry_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=400, headers=NO_CACHE_HEADERS)

    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT e.id, e.user_id, e.category_id,
                       c.name AS category_name, c.icon AS category_icon, c.color AS category_color,
                       e.title, e.content, e.mood, e.weather, 
                       e.entry_date, e.is_pinned, e.created_at, e.updated_at,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', p.id,
                                   'url', p.file_path,
                                   'thumbUrl', p.thumb_path,
                                   'filename', p.file_name,
                                   'size', p.file_size,
                                   'width', p.width,
                                   'height', p.height
                               ) ORDER BY p.sort_order
                           ) FILTER (WHERE p.id IS NOT NULL), '[]'
                       ) AS photos,
                       COALESCE(
                           array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL), '{}'
                       ) AS tags
                FROM entries e
                LEFT JOIN categories c ON e.category_id = c.id
                LEFT JOIN entry_photos p ON e.id = p.entry_id
                LEFT JOIN entry_tags et ON e.id = et.entry_id
                LEFT JOIN tags t ON et.tag_id = t.id
                WHERE e.id = %s AND e.user_id = %s
                GROUP BY e.id, c.id;
            """, (entry_id, user_id))
            row = cur.fetchone()
            if not row:
                return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết"}, status_code=404, headers=NO_CACHE_HEADERS)

            entry = dict(row)
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

            entry["categoryId"] = entry.get("category_id")
            entry["category_id"] = entry.get("category_id")
            entry["categoryName"] = entry.get("category_name")
            entry["category_name"] = entry.get("category_name")
            entry["categoryIcon"] = entry.get("category_icon")
            entry["category_icon"] = entry.get("category_icon")
            entry["categoryColor"] = entry.get("category_color")
            entry["category_color"] = entry.get("category_color")

            mood_labels = {
                "serene": "Serene 🌸",
                "cozy": "Cozy ☕",
                "reflective": "Reflective 🌙",
                "grateful": "Grateful 🍵",
                "energetic": "Energetic ⚡",
                "melancholy": "Melancholy 🌧️"
            }
            entry["moodLabel"] = mood_labels.get(entry["mood"], entry["mood"].capitalize())

            return JSONResponse({"status": "success", "entry": entry}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

# =========================================================================
# CATEGORIES CRUD REST APIS (v1.6.0)
# =========================================================================
async def get_categories(request: Request) -> JSONResponse:
    """
    Retrieve categories strictly scoped to the authenticated user with usage counts.
    Matches entries by category_id or legacy mood keys/names.
    Ordered by sort_order ASC, id ASC.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT c.id, c.user_id, c.name, c.icon, c.color, c.sort_order, c.created_at,
                       COUNT(DISTINCT e.id) AS usage_count
                FROM categories c
                LEFT JOIN entries e ON (
                    e.user_id = %s AND (
                        e.category_id = c.id
                        OR LOWER(e.mood) = LOWER(c.name)
                        OR (c.name = 'Bình yên' AND e.mood = 'serene')
                        OR (c.name = 'Ấm áp' AND e.mood = 'cozy')
                        OR (c.name = 'Chiêm nghiệm' AND e.mood = 'reflective')
                        OR (c.name = 'Biết ơn' AND e.mood = 'grateful')
                        OR (c.name = 'Năng lượng' AND e.mood = 'energetic')
                    )
                )
                WHERE c.user_id = %s
                GROUP BY c.id
                ORDER BY c.sort_order ASC, c.id ASC;
            """, (user_id, user_id))
            rows = cur.fetchall()
            categories = []
            for r in rows:
                item = dict(r)
                if item.get("created_at"):
                    item["createdAt"] = item["created_at"].isoformat()
                    item["created_at"] = item["created_at"].isoformat()
                categories.append(item)

        return JSONResponse({
            "status": "success",
            "categories": categories
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

async def create_category(request: Request) -> JSONResponse:
    """
    Create a new category for the authenticated user.
    Body: {"name": str, "icon": Optional[str], "color": Optional[str]}
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    try:
        data = await request.json()
    except Exception:
        data = {}

    name = (data.get("name") or "").strip()
    if not name:
        return JSONResponse({"status": "error", "message": "Tên danh mục không được để trống 🌸"}, status_code=400, headers=NO_CACHE_HEADERS)

    icon = (data.get("icon") or "📁").strip() or "📁"
    color = (data.get("color") or "#ec4899").strip() or "#ec4899"

    try:
        with get_cursor() as cur:
            # Check for duplicate category name for this user
            cur.execute("SELECT id FROM categories WHERE user_id = %s AND LOWER(name) = LOWER(%s);", (user_id, name))
            if cur.fetchone():
                return JSONResponse({"status": "error", "message": f"Danh mục '{name}' đã tồn tại."}, status_code=409, headers=NO_CACHE_HEADERS)

            cur.execute("""
                INSERT INTO categories (user_id, name, icon, color, sort_order)
                VALUES (%s, %s, %s, %s, COALESCE((SELECT MAX(sort_order) + 1 FROM categories WHERE user_id = %s), 0))
                RETURNING id, name, icon, color, sort_order, created_at;
            """, (user_id, name, icon, color, user_id))
            row = cur.fetchone()
            cat = dict(row)
            cat["usage_count"] = 0
            if cat.get("created_at"):
                cat["createdAt"] = cat["created_at"].isoformat()
                cat["created_at"] = cat["created_at"].isoformat()

        return JSONResponse({
            "status": "success",
            "message": "Đã tạo danh mục thành công 🌸",
            "category": cat
        }, status_code=201, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

async def update_category(request: Request) -> JSONResponse:
    """
    Update an existing category (name, icon, color, sort_order) for the authenticated user.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    cat_id = request.path_params.get("id")
    try:
        cat_id = int(cat_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=400, headers=NO_CACHE_HEADERS)

    try:
        data = await request.json()
    except Exception:
        data = {}

    name = data.get("name")
    if name is not None:
        name = name.strip()
        if not name:
            return JSONResponse({"status": "error", "message": "Tên danh mục không được để trống 🌸"}, status_code=400, headers=NO_CACHE_HEADERS)

    icon = data.get("icon")
    if icon is not None:
        icon = icon.strip() or "📁"

    color = data.get("color")
    if color is not None:
        color = color.strip() or "#ec4899"

    sort_order = data.get("sort_order")
    if sort_order is not None:
        try:
            sort_order = int(sort_order)
        except (ValueError, TypeError):
            sort_order = None

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, icon, color, sort_order FROM categories WHERE id = %s AND user_id = %s;", (cat_id, user_id))
            existing = cur.fetchone()
            if not existing:
                return JSONResponse({"status": "error", "message": "Không tìm thấy danh mục hoặc bạn không có quyền sửa."}, status_code=404, headers=NO_CACHE_HEADERS)

            if name and name.lower() != existing["name"].lower():
                cur.execute("SELECT id FROM categories WHERE user_id = %s AND LOWER(name) = LOWER(%s) AND id != %s;", (user_id, name, cat_id))
                if cur.fetchone():
                    return JSONResponse({"status": "error", "message": f"Danh mục '{name}' đã tồn tại."}, status_code=409, headers=NO_CACHE_HEADERS)

            cur.execute("""
                UPDATE categories
                SET name = COALESCE(%s, name),
                    icon = COALESCE(%s, icon),
                    color = COALESCE(%s, color),
                    sort_order = COALESCE(%s, sort_order)
                WHERE id = %s AND user_id = %s
                RETURNING id, name, icon, color, sort_order, created_at;
            """, (name, icon, color, sort_order, cat_id, user_id))
            row = cur.fetchone()
            cat = dict(row)

            # Sync entries.mood if name changed
            if name and name != existing["name"]:
                cur.execute("""
                    UPDATE entries 
                    SET mood = %s 
                    WHERE user_id = %s AND (category_id = %s OR mood = %s);
                """, (name, user_id, cat_id, existing["name"]))

            # Get current usage count
            cur.execute("""
                SELECT COUNT(DISTINCT id) AS count FROM entries 
                WHERE user_id = %s AND (
                    category_id = %s 
                    OR LOWER(mood) = LOWER(%s)
                );
            """, (user_id, cat_id, cat["name"]))
            cat["usage_count"] = cur.fetchone()["count"]
            if cat.get("created_at"):
                cat["createdAt"] = cat["created_at"].isoformat()
                cat["created_at"] = cat["created_at"].isoformat()

        return JSONResponse({
            "status": "success",
            "message": "Đã cập nhật danh mục thành công 🌸",
            "category": cat
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

async def delete_category(request: Request) -> JSONResponse:
    """
    Delete a category for the authenticated user.
    Entries belonging to this category will automatically have category_id set to NULL and mood preserved.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    cat_id = request.path_params.get("id")
    try:
        cat_id = int(cat_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=400, headers=NO_CACHE_HEADERS)

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM categories WHERE id = %s AND user_id = %s;", (cat_id, user_id))
            cat = cur.fetchone()
            if not cat:
                return JSONResponse({"status": "error", "message": "Không tìm thấy danh mục để xóa."}, status_code=404, headers=NO_CACHE_HEADERS)

            cur.execute("""
                UPDATE entries 
                SET category_id = NULL, mood = 'serene' 
                WHERE user_id = %s AND (category_id = %s OR mood = %s);
            """, (user_id, cat_id, cat["name"]))
            cur.execute("DELETE FROM categories WHERE id = %s AND user_id = %s;", (cat_id, user_id))

        return JSONResponse({
            "status": "success",
            "message": f"Đã xóa danh mục '{cat['name']}' thành công 🌸"
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

# =========================================================================
# TAGS APIS
# =========================================================================
async def get_tags(request: Request) -> JSONResponse:
    """
    Retrieve tags strictly scoped to the authenticated user with usage counts.
    Ordered by usage_count DESC, t.name ASC.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT t.id, t.name, COUNT(DISTINCT e.id) AS usage_count
                FROM tags t
                LEFT JOIN entry_tags et ON t.id = et.tag_id
                LEFT JOIN entries e ON et.entry_id = e.id AND e.user_id = %s
                WHERE t.user_id = %s
                GROUP BY t.id, t.name
                ORDER BY usage_count DESC, t.name ASC;
            """, (user_id, user_id))
            rows = cur.fetchall()
            tags = [{"id": r["id"], "name": r["name"], "usage_count": r["usage_count"]} for r in rows]

        return JSONResponse({
            "status": "success",
            "tags": tags
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

async def create_tag(request: Request) -> JSONResponse:
    """
    Proactively create a new tag for the authenticated user.
    Body: {"name": "#tagname"}
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    try:
        data = await request.json()
    except Exception:
        data = {}

    raw_name = (data.get("name") or "").strip()
    if not raw_name:
        return JSONResponse({"status": "error", "message": "Tên thẻ không được để trống 🏷️"}, status_code=400, headers=NO_CACHE_HEADERS)

    clean_name = raw_name if raw_name.startswith("#") else f"#{raw_name}"
    clean_name = "#" + clean_name.lstrip("#").strip()
    if clean_name == "#":
        return JSONResponse({"status": "error", "message": "Tên thẻ không hợp lệ 🏷️"}, status_code=400, headers=NO_CACHE_HEADERS)

    try:
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO tags (user_id, name)
                VALUES (%s, %s)
                ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id, name, created_at;
            """, (user_id, clean_name))
            row = cur.fetchone()
            tag = dict(row)

            cur.execute("SELECT COUNT(DISTINCT entry_id) AS usage_count FROM entry_tags WHERE tag_id = %s;", (tag["id"],))
            tag["usage_count"] = cur.fetchone()["usage_count"]
            if tag.get("created_at"):
                tag["createdAt"] = tag["created_at"].isoformat()
                tag["created_at"] = tag["created_at"].isoformat()

        return JSONResponse({
            "status": "success",
            "message": f"Đã tạo thẻ {clean_name} thành công 🏷️",
            "tag": tag
        }, status_code=201, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)

async def update_tag(request: Request) -> JSONResponse:
    """
    Rename an existing tag for the authenticated user.
    If the new name already exists, merges associations and removes the old tag.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    tag_id = request.path_params.get("id")

    try:
        try:
            data = await request.json()
        except Exception:
            data = {}

        raw_name = data.get("name", "").strip()
        if not raw_name:
            return JSONResponse({"status": "error", "message": "Tên thẻ không được để trống."}, status_code=400, headers=NO_CACHE_HEADERS)

        new_name = raw_name if raw_name.startswith("#") else f"#{raw_name}"

        with get_cursor() as cur:
            # Check if tag exists for this user
            cur.execute("SELECT id, name FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
            tag_row = cur.fetchone()
            if not tag_row:
                return JSONResponse({"status": "error", "message": "Không tìm thấy thẻ chủ đề."}, status_code=404, headers=NO_CACHE_HEADERS)

            # Check if target name already exists
            cur.execute("SELECT id FROM tags WHERE user_id = %s AND name = %s AND id != %s;", (user_id, new_name, tag_id))
            target_row = cur.fetchone()

            if target_row:
                target_id = target_row["id"]
                # Merge entry_tags to target_id
                cur.execute("""
                    INSERT INTO entry_tags (entry_id, tag_id)
                    SELECT entry_id, %s FROM entry_tags WHERE tag_id = %s
                    ON CONFLICT (entry_id, tag_id) DO NOTHING;
                """, (target_id, tag_id))
                cur.execute("DELETE FROM entry_tags WHERE tag_id = %s;", (tag_id,))
                cur.execute("DELETE FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
                final_id = target_id
            else:
                cur.execute("UPDATE tags SET name = %s WHERE id = %s AND user_id = %s;", (new_name, tag_id, user_id))
                final_id = tag_id

        return JSONResponse({
            "status": "success",
            "message": "Đã đổi tên thẻ chủ đề thành công.",
            "tag": {"id": final_id, "name": new_name}
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)


async def delete_tag(request: Request) -> JSONResponse:
    """
    Delete a tag and its associations for the authenticated user.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    tag_id = request.path_params.get("id")

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
            if not cur.fetchone():
                return JSONResponse({"status": "error", "message": "Không tìm thấy thẻ chủ đề."}, status_code=404, headers=NO_CACHE_HEADERS)

            cur.execute("DELETE FROM entry_tags WHERE tag_id = %s;", (tag_id,))
            cur.execute("DELETE FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))

        return JSONResponse({
            "status": "success",
            "message": "Đã xóa thẻ chủ đề thành công."
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)


async def cleanup_orphan_tags(request: Request) -> JSONResponse:
    """
    Remove all tags with usage_count = 0 for the authenticated user.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]

    try:
        with get_cursor() as cur:
            cur.execute("""
                DELETE FROM tags
                WHERE user_id = %s
                  AND id NOT IN (
                      SELECT et.tag_id
                      FROM entry_tags et
                      JOIN entries e ON et.entry_id = e.id
                      WHERE e.user_id = %s
                  );
            """, (user_id, user_id))
            deleted_count = cur.rowcount

        return JSONResponse({
            "status": "success",
            "message": f"Đã dọn dẹp {deleted_count} thẻ chủ đề mồ côi.",
            "deleted_count": deleted_count
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)


entry_routes = [
    Route("/api/entries", get_entries, methods=["GET"]),
    Route("/api/entries", create_entry, methods=["POST"]),
    Route("/api/entries/export", export_entries, methods=["GET"]),
    Route("/api/entries/import", import_entries, methods=["POST"]),
    Route("/api/entries/{id:int}", get_entry_by_id, methods=["GET"]),
    Route("/api/entries/{id:int}", update_entry, methods=["PUT"]),
    Route("/api/entries/{id:int}", delete_entry, methods=["DELETE"]),
    Route("/api/entries/{id:int}/pin", toggle_pin_entry, methods=["PATCH"]),
    Route("/api/stats/summary", get_stats, methods=["GET"]),
    Route("/api/categories", get_categories, methods=["GET"]),
    Route("/api/categories", create_category, methods=["POST"]),
    Route("/api/categories/{id:int}", update_category, methods=["PUT"]),
    Route("/api/categories/{id:int}", delete_category, methods=["DELETE"]),
    Route("/api/tags", get_tags, methods=["GET"]),
    Route("/api/tags", create_tag, methods=["POST"]),
    Route("/api/tags/cleanup-orphans", cleanup_orphan_tags, methods=["DELETE"]),
    Route("/api/tags/{id:int}", update_tag, methods=["PUT"]),
    Route("/api/tags/{id:int}", delete_tag, methods=["DELETE"]),
]
