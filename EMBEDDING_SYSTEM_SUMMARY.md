# Product Embeddings System with Hash-Based Change Detection

## ✅ Completed Implementation

### 1. Database Schema (Migration 003)
**File:** `backend/migrations/003_add_product_hash_tracking.sql`

**What it does:**
- Adds `content_hash` VARCHAR(64) to both `products` and `product_embeddings` tables
- Creates `compute_product_hash()` function that generates SHA256 hash from:
  - title
  - enriched_description
  - category
  - base_price
  - discount_price
  - city
  - tags
- Auto-updates hash via trigger whenever product is modified
- Backfilled all 458 existing products with content_hash

**Key Benefits:**
- Automatic change detection - no manual tracking needed
- Database handles hash computation for consistency
- Triggers fire on INSERT/UPDATE automatically

### 2. Updated Embedding Script
**File:** `backend/refresh_embeddings.py`

**New Features:**
- **Hash-based change detection**: Only processes products where `product.content_hash != embedding.content_hash`
- **Selective processing**: New `product_ids` parameter to process specific products
- **Three modes:**
  ```bash
  # Smart mode: Only changed/new products
  python3 refresh_embeddings.py

  # Full rebuild: All products
  python3 refresh_embeddings.py --full

  # Specific products (for admin dashboard)
  # Via Python API: refresh_product_embeddings(product_ids=[1,2,3])
  ```

**How Hash Detection Works:**
```sql
-- Selects products that need embedding refresh:
SELECT p.id, p.content_hash, ...
FROM products p
LEFT JOIN product_embeddings pe ON p.id = pe.product_id
WHERE pe.product_id IS NULL                    -- New products
   OR pe.content_hash IS NULL                  -- Old embeddings without hash
   OR pe.content_hash != p.content_hash        -- Changed products
```

**Embedding Storage:**
- Stores `content_hash` with each embedding
- When product changes → hash changes → detected on next run
- Completely automatic!

## 📋 Remaining Work

### 3. Admin API Endpoints (IN PROGRESS)
**File to create:** `backend/admin_embedding_routes.py`

**Required Endpoints:**

```python
# GET /api/admin/products/embedding-status
# Returns list of products with embedding status
{
  "products": [
    {
      "id": 1,
      "title": "Product Name",
      "has_embedding": true,
      "needs_refresh": false,  # hash mismatch
      "product_hash": "abc123...",
      "embedding_hash": "abc123...",
      "last_updated": "2025-11-12T10:00:00"
    }
  ],
  "stats": {
    "total": 458,
    "with_embeddings": 0,
    "needs_refresh": 458
  }
}

# POST /api/admin/products/regenerate-embeddings
# Body: {"product_ids": [1, 2, 3]} or {"all": true}
# Triggers background embedding generation
{
  "status": "started",
  "job_id": "uuid",
  "product_count": 3
}

# GET /api/admin/embeddings/job-status/{job_id}
# Check progress of embedding generation
{
  "status": "processing",  # or "completed", "failed"
  "progress": {
    "total": 100,
    "processed": 45,
    "succeeded": 43,
    "failed": 2
  }
}
```

### 4. Admin Dashboard UI Updates
**Files to modify:**
- Admin products list page
- Add embedding status column
- Add bulk selection checkboxes
- Add "Regenerate Embeddings" button

**UI Features Needed:**

1. **Products List Enhancement:**
   ```vue
   <table>
     <thead>
       <th><input type="checkbox" @change="selectAll"></th>
       <th>ID</th>
       <th>Title</th>
       <th>Embedding Status</th>  <!-- NEW -->
       <th>Actions</th>
     </thead>
     <tbody>
       <tr v-for="product in products">
         <td><input type="checkbox" v-model="selected[product.id]"></td>
         <td>{{ product.id }}</td>
         <td>{{ product.title }}</td>
         <td>
           <span v-if="!product.has_embedding" class="badge badge-warning">
             No Embedding
           </span>
           <span v-else-if="product.needs_refresh" class="badge badge-info">
             Needs Refresh
           </span>
           <span v-else class="badge badge-success">
             Up to Date
           </span>
         </td>
         <td>...</td>
       </tr>
     </tbody>
   </table>
   ```

2. **Bulk Actions Toolbar:**
   ```vue
   <div v-if="selectedCount > 0" class="bulk-actions">
     <p>{{ selectedCount }} products selected</p>
     <button @click="regenerateSelected">
       Regenerate Embeddings
     </button>
     <button @click="clearSelection">
       Clear Selection
     </button>
   </div>
   ```

3. **Regenerate All Button:**
   ```vue
   <button @click="regenerateAll" class="btn-danger">
     🔄 Regenerate ALL Product Embeddings
   </button>
   ```

## 🔄 How The Complete System Works

### Automatic Change Detection Flow:

1. **Admin edits product** in dashboard
   - Updates title, category, price, etc.
   - PostgreSQL trigger automatically recomputes `content_hash`
   - New hash stored in `products.content_hash`

2. **Admin uploads new products**
   - Trigger computes hash for each new product
   - `product_embeddings` table has no record yet

3. **Admin clicks "Regenerate Embeddings"** (for changed products)
   - Frontend calls: `POST /api/admin/products/regenerate-embeddings`
   - Backend runs: `refresh_product_embeddings()`
   - Script queries products where hash differs
   - Only changed products are processed
   - New embedding stored with matching `content_hash`

4. **Scheduled/Manual Full Refresh**
   ```bash
   cd backend
   python3 refresh_embeddings.py  # Smart mode - only changes
   ```

### Database Triggers Handle Everything:

```sql
-- Automatically runs before INSERT or UPDATE
CREATE TRIGGER products_content_hash_trigger
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_content_hash();

-- This means:
-- - No need to manually compute hash in Python
-- - No need to remember to update hash
-- - Works for bulk imports, admin edits, API updates
-- - Completely transparent to application code
```

## 📊 System Status

**Database:**
- ✅ Migration 003 applied successfully
- ✅ All 458 products have content_hash
- ✅ Triggers active and working
- ✅ 0 embeddings generated (ready to start)

**Scripts:**
- ✅ refresh_embeddings.py updated with hash detection
- ✅ Supports selective processing by product_ids
- ✅ Smart mode detects changes automatically

**APIs:**
- ⏳ Admin endpoints not yet created
- ⏳ Need to add routes to Flask app

**Frontend:**
- ⏳ Admin UI updates not yet implemented
- ⏳ Need bulk selection interface
- ⏳ Need embedding status display

## 🚀 Next Steps for You

1. **Create Admin API Routes** (`backend/admin_embedding_routes.py`):
   - `/api/admin/products/embedding-status` - GET product list with status
   - `/api/admin/products/regenerate-embeddings` - POST to trigger refresh
   - Import and register in `app.py` or `routes.py`

2. **Update Admin Dashboard** (in frontend):
   - Add embedding status column to products table
   - Add checkboxes for bulk selection
   - Add "Regenerate" button that calls API
   - Show progress/status feedback

3. **Test the Complete Flow**:
   - Edit a product → verify hash changes
   - Run `python3 refresh_embeddings.py` → verify only changed products processed
   - Check `product_embeddings` table → verify hash stored correctly

## 💡 Key Design Decisions

**Why separate table for embeddings?**
- Performance: vector operations don't slow down product queries
- Flexibility: Can regenerate without touching products table
- Maintainability: Clear separation of concerns

**Why hash-based detection?**
- Automatic: No manual "needs_refresh" flags to manage
- Reliable: Cryptographic hash detects any content change
- Efficient: Database handles computation via triggers

**Which fields are hashed?**
- All fields that affect the embedding:
  - title (user-facing name)
  - enriched_description (AI-generated)
  - category (semantic context)
  - prices (product context)
  - city (location context)
  - tags (additional metadata)
- NOT hashed: id, views, created_at (don't affect semantics)

## 🧪 Testing Hash Detection

```bash
# 1. Check current hash
docker exec -i pgvector psql -U postgres -d ai_pijaca -c \
  "SELECT id, title, content_hash FROM products LIMIT 1;"

# 2. Update a product
docker exec -i pgvector psql -U postgres -d ai_pijaca -c \
  "UPDATE products SET title = 'New Title' WHERE id = 1;"

# 3. Verify hash changed
docker exec -i pgvector psql -U postgres -d ai_pijaca -c \
  "SELECT id, title, content_hash FROM products WHERE id = 1;"

# 4. Run embedding refresh
cd backend
python3 refresh_embeddings.py

# Should see: "Found 1 products to process" (the changed one)
```

