"""No exception text, input bodies, query strings, tokens or customer names in logs."""
import json
import logging
from uuid import uuid4
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

log=logging.getLogger("profit_radar.events")
MESSAGES={400:"入力を確認してください",401:"ログインしてください",402:"試用期間または契約状態を確認してください",
          403:"この操作は許可されていません",404:"対象が見つかりません",409:"処理中または状態が変更されています。状態を確認してください",
          413:"入力が長すぎます",422:"入力形式を確認してください",423:"アカウント削除処理中です。運営者へ状態を確認してください",429:"利用上限に達しました",503:"一時的に利用できません。時間をおいて状態を確認してください"}


def install(app):
    async def respond(request,exc):
        status=exc.status_code if isinstance(exc,HTTPException) else (422 if isinstance(exc,RequestValidationError) else 503)
        correlation=str(uuid4())
        log.warning(json.dumps({"event":"request_failed","status":status,"correlation_id":correlation,"exception_type":type(exc).__name__}))
        return JSONResponse(status_code=status,content={"detail":MESSAGES.get(status,"処理を完了できませんでした"),"code":f"HTTP_{status}","correlation_id":correlation},headers={"X-Correlation-ID":correlation})
    app.add_exception_handler(HTTPException,respond)
    app.add_exception_handler(RequestValidationError,respond)
    app.add_exception_handler(Exception,respond)
