# Admin Backend Inspection and Frontend Environment Report

**Date:** 18 October 2026

---

# Part 0 — Frontend environment example

## `.env.local` variables

`frontend/.env.local` defines:

```text
NEXT_PUBLIC_API_URL=***
```

Its working value shape includes the complete `/api/v1` prefix:

```text
http://127.0.0.1:8000/api/v1
```

No value from `.env.local` was copied as a secret, and `.env.local` was not modified.

## Previous `.env.example`

Before correction, `frontend/.env.example` contained:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

That variable was incorrect because application code reads `NEXT_PUBLIC_API_URL`.

## Corrected `.env.example`

`frontend/.env.example` now contains:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

## Old-name grep result

The requested search returned no matches:

```text
$ grep -rn "NEXT_PUBLIC_API_BASE_URL" frontend/src frontend/*.ts frontend/*.js frontend/*.json 2>/dev/null
```

Result:

```text
(no matches)
```

Confirmed: `frontend/.env.local` was read but not modified.

---

# Part A — Admin authentication and JWT

## A1. Login endpoint

The router has an `/admin` prefix:

`backend/app/api/v1/admin.py:9`

```python
router = APIRouter(prefix="/admin", tags=["admin"])
```

The login handler is:

`backend/app/api/v1/admin.py:12-26`

```python
@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    """Exchange admin credentials for a JWT."""
    if not verify_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides.",
        )

    token = create_access_token()
    return LoginResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )
```

The API router is mounted under `/api/v1`, so the exact URL is:

```text
POST /api/v1/admin/login
```

The login endpoint itself is public and has no `Depends(get_current_admin)` dependency.

Invalid credentials return HTTP 401:

```json
{
  "detail": "Identifiants invalides."
}
```

## A2. Login request body

`backend/app/schemas/admin.py:4-6`

```python
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
```

Request JSON:

```json
{
  "username": "string",
  "password": "string"
}
```

Both fields are required. There is no email field.

## A3. Login response body

`backend/app/schemas/admin.py:9-12`

```python
class LoginResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT to send as Bearer token on admin requests.",
    )
    token_type: str = Field("bearer", description="Always 'bearer'.")
    expires_in: int = Field(..., description="Token lifetime in seconds.")
```

Response JSON:

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 28800
}
```

No admin user object or profile data is returned.

Although the route constructs `LoginResponse` without explicitly supplying `token_type`, its schema default is `"bearer"`.

## A4. JWT details

### Algorithm

`backend/app/core/security.py:10`

```python
ALGORITHM = "HS256"
```

Encoding occurs at `backend/app/core/security.py:40-50`:

```python
def create_access_token(
    extra_claims: dict[str, Any] | None = None
) -> str:
    now = int(time.time())
    payload = {
        "sub": settings.admin_username,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )
```

### Secret source

`backend/app/config.py:40-43`

```python
jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
jwt_expire_minutes: int = Field(480, alias="JWT_EXPIRE_MINUTES")
```

The signing secret comes from:

```text
JWT_SECRET_KEY
```

### Expiry

The configured default is 480 minutes:

```text
480 minutes = 8 hours = 28,800 seconds
```

The effective local configuration also reported:

```text
JWT_EXPIRE_MINUTES=480
```

The login response converts this to seconds:

`backend/app/api/v1/admin.py:23-25`

```python
return LoginResponse(
    access_token=token,
    expires_in=settings.jwt_expire_minutes * 60,
)
```

### Claims

The JWT sets standard claims:

- `sub`: configured admin username.
- `iat`: issued-at Unix timestamp.
- `exp`: expiration Unix timestamp.

Optional custom claims can be supplied through `extra_claims`, although login does not add any.

No `iss`, `aud`, `jti`, or explicit role claim is set.

## A5. Protected-route dependency

Admin routes use:

```python
dependencies=[Depends(get_current_admin)]
```

For example, `backend/app/api/v1/admin.py:35-39`:

```python
@router.get(
    "/orders",
    response_model=AdminOrderListResponse,
    dependencies=[Depends(get_current_admin)],
)
```

The dependency is defined in `backend/app/api/deps.py:7-33`:

```python
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer_scheme
    ),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
```

Expected header:

```http
Authorization: Bearer <token>
```

Missing token response:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
```

```json
{
  "detail": "Jeton d'authentification manquant."
}
```

Invalid or expired token response:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
```

```json
{
  "detail": "Jeton invalide ou expiré."
}
```

JWT verification is in `backend/app/core/security.py:53-60`:

```python
def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

## A6. Admin credentials source

`backend/app/config.py:37-38`

```python
admin_username: str = Field(..., alias="ADMIN_USERNAME")
admin_password_hash: str = Field(..., alias="ADMIN_PASSWORD_HASH")
```

Credentials come from:

```text
ADMIN_USERNAME
ADMIN_PASSWORD_HASH
```

The username is stored as plain configuration and compared directly.

The password is not stored as plaintext. The submitted plaintext password is compared against a bcrypt hash.

`backend/app/core/security.py:15-25`

```python
def verify_password(plain_password: str) -> bool:
    if not plain_password:
        return False
    try:
        stored = settings.admin_password_hash.encode("utf-8")
        provided = plain_password.encode("utf-8")
        return bcrypt.checkpw(provided, stored)
    except (ValueError, TypeError):
        return False
```

`backend/app/core/security.py:28-35`

```python
def verify_credentials(username: str, password: str) -> bool:
    if not username or not password:
        return False
    if username != settings.admin_username:
        return False
    return verify_password(password)
```

Malformed password hashes fail closed.

## A7. CORS

CORS is configured in `backend/app/main.py:68-74`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The origin list is read from `CORS_ORIGINS`.

`backend/app/config.py:31-32`

```python
cors_origins_raw: str = Field("*", alias="CORS_ORIGINS")
```

Parsing occurs at `backend/app/config.py:67-69`:

```python
@property
def cors_origins(self) -> list[str]:
    return [
        o.strip()
        for o in self.cors_origins_raw.split(",")
        if o.strip()
    ]
```

Effective configured origins:

```text
http://localhost:3000
http://localhost:5173
```

Therefore `http://localhost:3000` is allowed.

Authorization headers are allowed because:

```python
allow_headers=["*"]
```

Credentials are allowed because:

```python
allow_credentials=True
```

All HTTP methods are allowed:

```python
allow_methods=["*"]
```

---

# Part B — Admin order endpoints

All order endpoints require Bearer JWT authentication through `get_current_admin`.

## B1. List orders

```text
PATH: GET /api/v1/admin/orders
AUTH: Required
```

`backend/app/api/v1/admin.py:35-51`

```python
@router.get(
    "/orders",
    response_model=AdminOrderListResponse,
    dependencies=[Depends(get_current_admin)],
)
def list_orders(
    status: str | None = Query(
        None,
        pattern="^(pending|confirmed|cancelled|delivered)$",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AdminOrderListResponse:
```

### Query parameters

| Parameter | Type | Default | Constraints |
|---|---:|---:|---|
| `status` | string/null | null | `pending`, `confirmed`, `cancelled`, `delivered` |
| `page` | integer | 1 | minimum 1 |
| `page_size` | integer | 20 | 1–100 |

### Response

`backend/app/schemas/admin.py:21-38`

```python
class AdminOrderSummary(BaseModel):
    id: int
    created_at: str
    customer_name: str
    customer_phone: str
    wilaya: str
    city: str
    total: float
    status: str
    item_count: int


class AdminOrderListResponse(BaseModel):
    items: list[AdminOrderSummary]
    total: int
    page: int
    page_size: int
    has_next: bool
```

Orders are sorted newest first in `order_service.py:230-235`.

The route accepts `delivered` as a filter value, but there is no endpoint in this code that changes an order to `delivered`.

## B2. Get one order

```text
PATH: GET /api/v1/admin/orders/{order_id}
REQ: Integer order_id path parameter
RES: AdminOrderDetail
AUTH: Required
```

`backend/app/api/v1/admin.py:60-70`

```python
@router.get(
    "/orders/{order_id}",
    response_model=AdminOrderDetail,
    dependencies=[Depends(get_current_admin)],
)
def get_order(order_id: int) -> AdminOrderDetail:
    result = order_service.get_order_detail(order_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Commande introuvable.",
        )
    return result
```

The order ID is an integer.

Response schema, `backend/app/schemas/admin.py:41-65`:

```python
class AdminOrderItemDetail(BaseModel):
    id: int
    category: str
    product_id: int
    brand: str
    name: str
    specification: str
    size: str | None
    unit_price: float
    quantity: int
    line_total: float


class AdminOrderDetail(BaseModel):
    id: int
    created_at: str
    customer_name: str
    customer_phone: str
    customer_email: str | None
    wilaya: str
    city: str
    notes: str | None
    total: float
    status: str
    items: list[AdminOrderItemDetail]
```

Order items use frozen snapshots. Database evidence from `backend/app/db/models/tables.py`:

```python
brand_snapshot
name_snapshot
specification_snapshot
size_snapshot
unit_price_snapshot
```

The detail serializer reads those snapshots, not current product data:

```python
"brand": it.brand_snapshot,
"name": it.name_snapshot,
"specification": it.specification_snapshot,
"size": it.size_snapshot,
"unit_price": float(it.unit_price_snapshot),
```

## B3. Confirm order

```text
PATH: POST /api/v1/admin/orders/{order_id}/confirm
REQ: Integer order_id; no request body
RES: OrderStatusResponse
AUTH: Required
```

Route, `backend/app/api/v1/admin.py:73-84`:

```python
@router.post(
    "/orders/{order_id}/confirm",
    response_model=OrderStatusResponse,
    dependencies=[Depends(get_current_admin)],
)
def confirm_order_route(order_id: int) -> OrderStatusResponse:
    try:
        result = order_service.confirm_order(order_id)
    except OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
```

Success uses the default HTTP 200 status.

Response schema:

```python
class OrderStatusResponse(BaseModel):
    order_id: int
    status: str
```

The service internally also returns `total`, but the response model contains only `order_id` and `status`; FastAPI response-model filtering omits the extra `total`.

### Stock decrement

`backend/app/services/order_service.py:168-203`

```python
with SessionLocal() as session:
    order = session.get(Order, order_id)
    ...

    # First pass: verify all items have enough stock
    for it in items:
        ...
        if row.quantity < it.quantity:
            raise OrderError(
                f"Stock insuffisant pour {it.brand_snapshot} : "
                f"{row.quantity} disponible(s), "
                f"{it.quantity} requis."
            )

    # Second pass: decrement
    for it in items:
        model = CATEGORY_MAP[it.category]
        row = session.get(model, it.product_id)
        row.quantity -= it.quantity

    order.status = "confirmed"
    session.commit()
```

All checks, decrements, status update, and commit occur in one SQLAlchemy session/transaction. There is no explicit row lock such as `SELECT ... FOR UPDATE`, so simultaneous confirmations could still have a concurrency race at the database level.

### Failure behavior

All `OrderError` cases return HTTP 400:

```json
{
  "detail": "<customer-safe French error>"
}
```

Cases include:

- Order not found.
- Already confirmed.
- Cancelled order.
- Missing product.
- Unknown category.
- Insufficient stock.

Insufficient-stock message:

```text
Stock insuffisant pour <brand> : <available> disponible(s), <required> requis.
```

## B4. Cancel order

```text
PATH: POST /api/v1/admin/orders/{order_id}/cancel
REQ: Integer order_id; no request body
RES: OrderStatusResponse
AUTH: Required
```

Route, `backend/app/api/v1/admin.py:87-98`:

```python
@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderStatusResponse,
    dependencies=[Depends(get_current_admin)],
)
def cancel_order_route(order_id: int) -> OrderStatusResponse:
    try:
        result = order_service.cancel_order(order_id)
    except OrderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
```

Success status: HTTP 200.

Response:

```json
{
  "order_id": 123,
  "status": "cancelled"
}
```

Cancellation logic, `backend/app/services/order_service.py:315-333`:

```python
if order is None:
    raise OrderError(f"Commande introuvable : #{order_id}")
if order.status == "confirmed":
    raise OrderError(
        "Impossible d'annuler une commande déjà confirmée."
    )
if order.status == "cancelled":
    raise OrderError("Cette commande est déjà annulée.")

order.status = "cancelled"
session.commit()
```

Only pending—or another unrecognized non-confirmed/non-cancelled status—can be cancelled. The implementation does not explicitly reject `delivered`, so if an order somehow already had status `delivered`, this service would currently allow it to become cancelled.

Stock is not restored because stock is only decremented on confirmation.

## B5. Other admin order endpoints

No additional admin order routes were found.

Missing:

- Delete order.
- Archive order.
- Update order notes.
- Mark delivered.
- Reopen order.
- Restore/revert confirmed stock.
- Bulk order actions.

---

# Part C — Admin product and stock endpoints

The backend calls this area “stock,” not “products.” All stock endpoints require Bearer authentication.

## C1. List stock/products

```text
PATH: GET /api/v1/admin/stock
AUTH: Required
```

`backend/app/api/v1/admin.py:111-125`

```python
@router.get(
    "/stock",
    response_model=AdminStockListResponse,
    dependencies=[Depends(get_current_admin)],
)
def list_stock(
    category: str | None = Query(
        None,
        pattern=(
            "^(engine_oil|gearbox_oil|oil_filter|additional)$"
        ),
    ),
    q: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AdminStockListResponse:
```

### Query parameters

| Parameter | Default | Constraints |
|---|---:|---|
| `category` | null | `engine_oil`, `gearbox_oil`, `oil_filter`, `additional` |
| `q` | null | maximum 200 characters |
| `page` | 1 | minimum 1 |
| `page_size` | 20 | 1–100 |

Response, `backend/app/schemas/admin.py:75-95`:

```python
class AdminStockItem(BaseModel):
    category: str
    id: int
    brand: str
    name: str
    specification: str
    viscosity: str | None = None
    size: str | None = None
    price: float
    quantity: int
    in_stock: bool
    image_front_url: str | None = None
    image_back_url: str | None = None
```

The exact stock field is:

```text
quantity
```

The paginated wrapper is:

```python
class AdminStockListResponse(BaseModel):
    items: list[AdminStockItem]
    total: int
    page: int
    page_size: int
    has_next: bool
```

The service explicitly adds `quantity`:

`backend/app/services/product_service.py:236-240`

```python
def _serialize_admin(row, category: str) -> dict:
    base = _serialize(row, category)
    base["quantity"] = row.quantity
    return base
```

The admin list includes out-of-stock products.

## C2. Get one admin product

**MISSING.**

There is no:

```text
GET /api/v1/admin/stock/{category}/{product_id}
```

The public product-detail endpoint exists, but it does not expose `quantity`. An admin dashboard requiring one-item admin detail must currently obtain the item from the paginated admin list or use the public detail without quantity.

## C3. Create product

```text
PATH: POST /api/v1/admin/stock
REQ: AdminStockCreate JSON body
RES: AdminStockItem
AUTH: Required
SUCCESS: HTTP 201
```

Route, `backend/app/api/v1/admin.py:150-163`:

```python
@router.post(
    "/stock",
    response_model=AdminStockItem,
    status_code=201,
    dependencies=[Depends(get_current_admin)],
)
def create_stock(payload: AdminStockCreate) -> AdminStockItem:
```

Request schema, `backend/app/schemas/admin.py:107-119`:

```python
class AdminStockCreate(BaseModel):
    category: str = Field(
        ...,
        pattern=(
            "^(engine_oil|gearbox_oil|oil_filter|additional)$"
        ),
    )
    brand: str = Field(..., min_length=1, max_length=64)
    specification: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )
    viscosity: str | None = Field(None, max_length=16)
    size: str | None = Field(None, max_length=16)
    price: float = Field(..., ge=0)
    quantity: int = Field(0, ge=0)
    category_type: str | None = Field(
        None,
        max_length=64,
        description=(
            "Required for 'additional' category "
            "(e.g., 'liquide de frein', 'additif')."
        ),
    )
```

### Required fields

- `category`
- `brand`
- `specification`
- `price`

### Optional/defaulted fields

- `viscosity`: null
- `size`: null
- `quantity`: defaults to 0
- `category_type`: null generally, but service-required for `additional`

There is no request `name` field. The display name is computed by the service from brand, viscosity, and size.

Valid categories:

```text
engine_oil
gearbox_oil
oil_filter
additional
```

For `additional`, `category_type` is enforced in the service:

```python
if not ct:
    raise ValueError(
        "category_type is required for 'additional' items "
        "(e.g., 'liquide de frein', 'additif')."
    )
```

## C4. Update product

```text
PATH: PATCH /api/v1/admin/stock/{category}/{product_id}
REQ: AdminStockUpdate JSON body
RES: AdminStockItem
AUTH: Required
```

Route, `backend/app/api/v1/admin.py:128-147`:

```python
@router.patch(
    "/stock/{category}/{product_id}",
    response_model=AdminStockItem,
    dependencies=[Depends(get_current_admin)],
)
def update_stock(
    category: str,
    product_id: int,
    payload: AdminStockUpdate,
) -> AdminStockItem:
    result = product_service.update_stock_item(
        category,
        product_id,
        payload.model_dump(exclude_unset=True),
    )
```

This is a partial update, not a full replacement.

Request schema:

```python
class AdminStockUpdate(BaseModel):
    brand: str | None = ...
    specification: str | None = ...
    viscosity: str | None = ...
    size: str | None = ...
    price: float | None = ...
    quantity: int | None = ...
    category_type: str | None = ...
```

All fields are optional.

The category itself cannot be changed because it is a path parameter and is not part of `AdminStockUpdate`.

The service silently ignores update fields that do not apply to the selected category. It also skips fields whose value is `None`, so this endpoint cannot use JSON `null` to clear an existing optional field.

Responses:

- 200 with updated `AdminStockItem`.
- 400 for unknown category/validation errors.
- 404 `{"detail":"Produit introuvable."}` when absent.

## C5. Delete product

```text
PATH: DELETE /api/v1/admin/stock/{category}/{product_id}
REQ: Category and integer product_id path parameters
RES: Empty body
AUTH: Required
SUCCESS: HTTP 204
```

Route, `backend/app/api/v1/admin.py:166-178`:

```python
@router.delete(
    "/stock/{category}/{product_id}",
    status_code=204,
    dependencies=[Depends(get_current_admin)],
)
def delete_stock(category: str, product_id: int) -> None:
```

Deletion is a hard database delete:

`backend/app/services/product_service.py:326-338`

```python
row = session.get(model, product_id)
if row is None:
    return False
session.delete(row)
session.commit()
return True
```

There is no soft-delete flag.

There is no pre-delete check for existing orders.

Order history remains possible because `OrderItem.product_id` is a plain integer, not a foreign key to each category table, and order items retain frozen snapshots:

`backend/app/db/models/tables.py:172-193`

```python
product_id: Mapped[int] = mapped_column(Integer)

brand_snapshot
name_snapshot
specification_snapshot
size_snapshot
unit_price_snapshot
```

Therefore deleting a stock item does not erase the historical order snapshot.

Potential image behavior: `delete_stock_item` does not explicitly remove associated Cloudinary images before deleting the row. This can leave Cloudinary assets orphaned.

## C6. Category-specific endpoints

There are no separate admin route families for engine oil, gearbox oil, filters, or additional products.

All categories use generic routes with `{category}` where needed:

```text
PATCH  /admin/stock/{category}/{product_id}
DELETE /admin/stock/{category}/{product_id}
POST   /admin/stock/{category}/{product_id}/images
DELETE /admin/stock/{category}/{product_id}/images/{position}
```

Creation includes category in the JSON body.

---

# Part D — Admin image endpoints

## D1. Upload front image

There is no separate front-only URL. Front and back share one endpoint:

```text
PATH: POST /api/v1/admin/stock/{category}/{product_id}/images
AUTH: Required
CONTENT-TYPE: multipart/form-data
FILE FIELD: front
RES: AdminStockItem
```

`backend/app/api/v1/admin.py:184-213`

```python
front: UploadFile | None = File(
    None,
    description="Face avant (JPEG/PNG/WEBP, max 5 MB)",
)
back: UploadFile | None = File(
    None,
    description="Face arrière (JPEG/PNG/WEBP, max 5 MB)",
)
```

Accepted MIME types, `product_service.py:344-358`:

```python
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
```

Validation rejects:

- Empty files.
- Unsupported content types.
- Files larger than 5 MiB.

Response is the complete updated `AdminStockItem`, including:

```text
image_front_url
image_back_url
```

No Cloudinary public ID is returned.

Old front image replacement logic, `product_service.py:391-397`:

```python
new_url = cloudinary_client.upload_image(front_bytes)
old_url = row.image_front_url
row.image_front_url = new_url
if old_url and old_url != new_url:
    cloudinary_client.delete_image_by_url(old_url)
```

The old asset is deleted only after a successful new upload.

Possible errors:

- 400 for invalid file/category/no images.
- 404 if product is absent.
- 503 if Cloudinary is not configured.

## D2. Upload back image

Same endpoint:

```text
POST /api/v1/admin/stock/{category}/{product_id}/images
```

Multipart field:

```text
back
```

Back-image replacement, `product_service.py:399-405`:

```python
new_url = cloudinary_client.upload_image(back_bytes)
old_url = row.image_back_url
row.image_back_url = new_url
if old_url and old_url != new_url:
    cloudinary_client.delete_image_by_url(old_url)
```

Constraints and response are identical to front image upload.

## D3. Delete image

```text
PATH: DELETE /api/v1/admin/stock/{category}/{product_id}/images/{position}
AUTH: Required
POSITION: front | back
RES: AdminStockItem
```

Route, `backend/app/api/v1/admin.py:216-233`:

```python
@router.delete(
    "/stock/{category}/{product_id}/images/{position}",
    response_model=AdminStockItem,
    dependencies=[Depends(get_current_admin)],
)
```

Position validation, `product_service.py:417-423`:

```python
if position not in ("front", "back"):
    raise ValueError("position must be 'front' or 'back'")

column = (
    "image_front_url"
    if position == "front"
    else "image_back_url"
)
```

Deletion behavior, lines 425–435:

```python
url = getattr(row, column)
if url:
    cloudinary_client.delete_image_by_url(url)
setattr(row, column, None)
session.commit()
```

It performs a best-effort Cloudinary deletion and clears the DB URL. The endpoint does not accept a public ID.

`delete_image_by_url` derives the Cloudinary public ID from the stored URL and calls:

```python
cloudinary.uploader.destroy(public_id, resource_type="image")
```

Cloudinary deletion failures are swallowed by `delete_image_by_url`; the database field is still cleared.

## D4. Combined image endpoint

Yes. The same upload endpoint accepts either or both files:

```text
POST /api/v1/admin/stock/{category}/{product_id}/images
```

Request:

```text
multipart/form-data
front: optional file
back: optional file
```

At least one must be supplied:

```python
if front_bytes is None and back_bytes is None:
    raise ValueError("Aucune image fournie.")
```

There are no separate front/back upload routes.

---

# Part E — Frontend admin scaffolding

Commands returned:

```text
--- APP ADMIN ---
(no output)

--- ADMIN DIRECTORIES ---
(no output)

--- ADMIN REFERENCES ---
(no output)
```

## E1. Does `frontend/src/app/admin` exist?

No. `frontend/src/app/admin` does not exist.

## E2. Existing admin components, hooks, or types

None were found under `frontend/src`.

There are no:

- Admin routes.
- Admin login components.
- JWT storage helpers.
- Auth guards.
- Admin API helpers.
- Order-management components.
- Inventory-management components.
- Image-upload components.
- Admin types/hooks.

## E3. User-visible admin links

No `/admin`, `Admin`, or admin-related references were found in frontend TypeScript/TSX files.

The customer Navbar and Footer do not expose an admin link. This matches the requirement that the admin panel remain a separate URL.

---

# Admin endpoint coverage summary

| Method | Path | Auth | Shape OK |
|---|---|---:|---:|
| POST | `/api/v1/admin/login` | No | Yes |
| GET | `/api/v1/admin/orders` | Yes | Yes |
| GET | `/api/v1/admin/orders/{order_id}` | Yes | Yes |
| POST | `/api/v1/admin/orders/{order_id}/confirm` | Yes | Yes |
| POST | `/api/v1/admin/orders/{order_id}/cancel` | Yes | Yes |
| GET | `/api/v1/admin/stock` | Yes | Yes |
| POST | `/api/v1/admin/stock` | Yes | Yes |
| PATCH | `/api/v1/admin/stock/{category}/{product_id}` | Yes | Yes |
| DELETE | `/api/v1/admin/stock/{category}/{product_id}` | Yes | Yes |
| POST | `/api/v1/admin/stock/{category}/{product_id}/images` | Yes | Yes |
| DELETE | `/api/v1/admin/stock/{category}/{product_id}/images/{position}` | Yes | Yes |

“Shape OK” means the route has a sufficiently explicit request/response schema for building the corresponding frontend action. The 204 delete route intentionally has no response schema.

---

# Gaps

The following capabilities do not have corresponding backend endpoints:

1. **Get one admin stock item with quantity**
   - Missing `GET /api/v1/admin/stock/{category}/{product_id}`.

2. **Mark an order delivered**
   - `delivered` is accepted by the list filter, but no route changes an order to that status.

3. **Delete or archive orders**
   - No delete/archive endpoint.

4. **Update order notes or general order fields**
   - No admin order-edit endpoint.

5. **Bulk order or stock actions**
   - None.

6. **Restore/revert a confirmed order**
   - No route restores decremented stock or reopens confirmation.

7. **Dedicated front/back upload endpoints**
   - Not strictly required because the combined endpoint supports both positions.

8. **Cloudinary cleanup during product deletion**
   - Product deletion hard-deletes the DB row but does not delete its stored image assets.

9. **Explicit database concurrency locking during confirmation**
   - Confirmation uses one transaction but no row-level lock, so simultaneous confirmation requests may race.

10. **Strict cancellation check for `delivered`**
    - Cancellation rejects only `confirmed` and `cancelled`; it does not explicitly reject `delivered`.

The core frontend admin specification—login, list/detail orders, confirm/cancel, stock list/create/update/delete, and front/back image management—is otherwise covered.

Only `frontend/.env.example` was modified. No backend file or other frontend source file was changed for this task.
