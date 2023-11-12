import time
import hashlib
import hmac
import requests as r
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db, HCXProcessSyncStatus_TM
from schemas import OrderUpdate, OrderSubmitURL, OrderUpdateDatePayload
from static import SHOPEE_SUCCESS_HTML, SHOPEE_FAILED_SHOPID_WRONG_HTML, SHOPEE_FAILED_GENERAL_ERROR_HTML
from _cred import ShopeeCred

router = APIRouter(
    tags=['API Sync'],
    prefix="/api_sync"
)
@router.get('/shopee/get_token_expiry_period')
def get_shopee_token_url(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    # Authorize.jwt_required()
    shopeeSync = db.query(HCXProcessSyncStatus_TM).filter(HCXProcessSyncStatus_TM.platform_name == "SHOPEE").first()

    if not shopeeSync:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='ShopeeSync Data was not found in DB', error='asd')

    return {
        "platform_name"                 : shopeeSync.platform_name,
        "refresh_token_expire_YYYYMMDD" : shopeeSync.refresh_token_expire_YYYYMMDD
    }


@router.get('/shopee/get_auth_url')
def get_shopee_token_url(Authorize: AuthJWT = Depends()):
    # Authorize.jwt_required()
    return ShopeeModule().get_auth_url()

@router.get('/shopee/get_access_token')
def get_access_token(code: str, shop_id: str, db: Session = Depends(get_db)):
    s = ShopeeModule()

    if shop_id != s.shopId:
        # raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail='Wrong Shopee Account was used!')
        return HTMLResponse(content=SHOPEE_FAILED_SHOPID_WRONG_HTML)

    accessToken, refreshToken = s.get_tokens(code)

    # Update to DB
    shopeeSync = db.query(HCXProcessSyncStatus_TM).filter(HCXProcessSyncStatus_TM.platform_name == "SHOPEE").first()

    if not shopeeSync:
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='ShopeeSync Data was not found in DB')
        return HTMLResponse(content=SHOPEE_FAILED_GENERAL_ERROR_HTML)

    shopeeSync.access_token     = accessToken
    shopeeSync.refresh_token    = refreshToken
    shopeeSync.refresh_token_expire_YYYYMMDD = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")

    db.commit()
    db.refresh(shopeeSync)

    return HTMLResponse(content=SHOPEE_SUCCESS_HTML)

class ShopeeModule:
    def __init__(self):
        self.partnerId  = ShopeeCred['partner_id']
        self.partnerKey = ShopeeCred['partner_key']
        self.shopId     = ShopeeCred['shop_id']
        self.baseURL    = 'https://partner.shopeemobile.com'
        # self.baseURL    = 'https://partner.test-stable.shopeemobile.com'

    def get_auth_url(self):
        url_path = '/api/v2/shop/auth_partner'
        ts = int(time.time()) + 2

        base_string = self.create_base_string(self.partnerId, url_path, ts).encode()
        sign = hmac.new(self.partnerKey.encode(), base_string, hashlib.sha256).hexdigest()

        redirect_url = "http://127.0.0.1:8000/api_v1/api_sync/shopee/get_access_token"
        auth_url = self.baseURL + url_path + f"?partner_id={self.partnerId}&timestamp={ts}&sign={sign}&redirect={redirect_url}"

        return {"auth_url" : auth_url}

    def create_base_string(self, partner_id, api_path, ts, access_token=None, custom_id=None):
        # custom_id can be shop_id/merchant_id
        base_string = f"{partner_id}{api_path}{ts}{access_token if access_token else ''}{custom_id if custom_id else ''}"
        return base_string

    def get_tokens(self, code):
        try:
            timest = int(time.time())
            path = "/api/v2/auth/token/get"
            body = {"code": code, "shop_id": int(self.shopId), "partner_id": int(self.partnerId)}
            tmp_base_string = "%s%s%s" % (self.partnerId, path, timest)
            base_string = tmp_base_string.encode()
            partner_key = self.partnerKey.encode()
            sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
            url = self.baseURL + path + "?partner_id=%s&timestamp=%s&sign=%s" % (self.partnerId, timest, sign)
            headers = {"Content-Type": "application/json"}
            resp = r.post(url, json=body, headers=headers)
            resp.raise_for_status()  # Raise an exception for non-2xx status codes
            ret = json.loads(resp.content)
            access_token = ret.get("access_token")
            new_refresh_token = ret.get("refresh_token")
            return access_token, new_refresh_token
        except Exception as e:
            raise Exception(f"Error while getting tokens: {str(e)}")
# 