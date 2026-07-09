# Private S3 Photo Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move uploaded and existing photo files to the private Yandex Object Storage bucket `s3-gribovka` while keeping the site's existing authenticated `/person_data/...` URLs.

**Architecture:** The backend owns all S3 access. Photo metadata stays in the current JSON files, while photo bytes are written to and read from S3 keys under `photos/<person_id>/<filename>`. Browser traffic continues to hit the app origin, so private S3 objects are not exposed directly.

**Tech Stack:** Python stdlib HTTP server, `boto3`/botocore, Yandex Object Storage S3-compatible endpoint `https://storage.yandexcloud.net`, Docker Compose, GitHub Actions.

## Global Constraints

- Bucket name: `s3-gribovka`.
- S3 credentials come from `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.
- Bucket remains private; CORS does not grant access and the browser does not call S3 directly.
- Existing JSON metadata format remains compatible with `/person_data/photos/<person_id>/<filename>` URLs.
- Existing local files remain as a fallback until migration and deployment are verified.

---

### Task 1: Storage Interface and Photo Writes

**Files:**
- Create: `site/storage/object_storage.py`
- Modify: `site/services/photo_service.py`
- Test: `tests/test_person_data_services.py`

**Interfaces:**
- Produces: `S3ObjectStorage.put_bytes(key, data, content_type)`, `S3ObjectStorage.get_object(key)`, `S3ObjectStorage.delete(key)`.
- Consumes: `PhotoService(photos_dir, object_storage=None)` writes photo bytes to `object_storage` when provided.

- [ ] Write failing tests for object-storage-backed upload and delete.
- [ ] Run `python3 -m unittest tests.test_person_data_services.PhotoServiceTest -v`; expected new storage tests fail.
- [ ] Implement minimal object storage interface and wire `PhotoService`.
- [ ] Re-run the focused test class; expected pass.

### Task 2: Authenticated Object Serving

**Files:**
- Modify: `site/utils/file_utils.py`
- Modify: `site/handlers/http_handler.py`
- Test: `tests/test_server_architecture.py`

**Interfaces:**
- Consumes: `serve_file(handler, path, data_dir=None, object_storage=None)`.
- Produces: `/person_data/photos/...` can stream from S3 after normal auth checks.

- [ ] Write a failing test that `serve_file` can return `photos/node1/face.png` from a fake object storage.
- [ ] Run `python3 -m unittest tests.test_server_architecture.FileServingTest -v`; expected new storage test fails.
- [ ] Implement S3-backed branch in `serve_file`, preserving local fallback.
- [ ] Re-run the focused test class; expected pass.

### Task 3: Runtime Configuration and Deployment

**Files:**
- Modify: `site/config/settings.py`
- Modify: `site/api/person_api.py`
- Modify: `site/handlers/http_handler.py`
- Modify: `requirements.txt`
- Modify: `docker-compose.yml`
- Modify: `.github/workflows/deploy.yml`
- Modify: `.env.example`
- Modify: `README.md`
- Test: `tests/test_server_architecture.py`

**Interfaces:**
- Produces: `Settings.object_storage` with S3 config when all required env vars are present.
- Consumes: GitHub Actions secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

- [ ] Write settings tests for enabled and disabled S3 config.
- [ ] Run settings tests; expected new S3 tests fail.
- [ ] Add settings dataclass and construction helper.
- [ ] Pass object storage into `PersonAPI` and static file serving.
- [ ] Update deploy/runtime configuration.
- [ ] Run full unit tests.

### Task 4: Migration and Verification

**Files:**
- No repo files required.

**Interfaces:**
- Consumes: server path `/home/user/family_tree/person_data/photos`.
- Produces: private S3 objects under `s3://s3-gribovka/photos/...`.

- [ ] Confirm server has S3 credentials after deploy writes `.env`.
- [ ] Upload existing image files with content types to `s3://s3-gribovka/photos/...`.
- [ ] Compare local image count with bucket object count.
- [ ] Deploy app and verify `/api/health` plus a representative authenticated photo URL.

