import json
from typing import Annotated

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

# create a router
api_router = APIRouter()


@api_router.get("/jwks.json")
def get_partners(env: Annotated[Environment, Depends(odoo_env)]):
    CryptoKeySet = env["g2p.crypto.key.set"].sudo()
    key_sets = CryptoKeySet.search([("status", "=", "active")])
    jwks = [json.loads(key_set.jwk) for key_set in key_sets]
    return {"keys": jwks}
