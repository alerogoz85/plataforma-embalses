"""Hash y verificacion de contraseñas con scrypt (biblioteca estandar). Formato: scrypt$n$r$p$sal$hash (base64)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

N, R, P = 2**14, 8, 1
LARGO_HASH = 32
# Hash de una contraseña inexistente: se verifica contra el cuando el usuario no existe, para que responder
# «usuario inexistente» tarde lo mismo que responder «contraseña incorrecta» (no revela que cuentas existen).
_SAL_FALSA = b"0" * 16


def _scrypt(contrasena: str, sal: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(contrasena.encode("utf-8"), salt=sal, n=n, r=r, p=p, dklen=LARGO_HASH, maxmem=64 * 1024 * 1024)


def hashear(contrasena: str) -> str:
    sal = secrets.token_bytes(16)
    derivado = _scrypt(contrasena, sal, N, R, P)
    return "$".join(["scrypt", str(N), str(R), str(P), base64.b64encode(sal).decode(), base64.b64encode(derivado).decode()])


def verificar(contrasena: str, almacenado: str) -> bool:
    """Compara en tiempo constante. Un hash mal formado nunca verifica (y no lanza)."""
    try:
        esquema, n, r, p, sal_b64, hash_b64 = almacenado.split("$")
        if esquema != "scrypt":
            return False
        esperado = base64.b64decode(hash_b64)
        derivado = _scrypt(contrasena, base64.b64decode(sal_b64), int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derivado, esperado)


def verificar_falso(contrasena: str) -> None:
    """Gasta el mismo tiempo que una verificacion real (usuario inexistente)."""
    _scrypt(contrasena, _SAL_FALSA, N, R, P)
