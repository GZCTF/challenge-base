# GZCTF Challenge Base Images

This repository provides **minimal Alpine-based Docker images** for CTF challenges used with GZCTF platform. Images are published to `ghcr.io/gzctf-org/challenge-base/{name}:{tag}`.

## Architecture

### Base Images Structure
- **`base/{name}/`**: Each directory contains Dockerfiles and `config.json` defining build variants
- **Multi-variant pattern**: Single base can generate multiple tagged images (e.g., `python:alpine`, `python:3.11-alpine`, `python:3.12-alpine`)
- **Alpine-first**: All images target minimal size using Alpine Linux as foundation

### Config-Driven Workflow System
GitHub Actions workflows are **auto-generated** from `config.json` files using `scripts/gen_action.py`:

```json
{
  "action_name": "Python 3.12",          // Workflow display name
  "action_file": "python-3.12",          // Output: .github/workflows/base.python-3.12.yml
  "dockerfile": "Dockerfile.3.12",       // Which Dockerfile to build
  "tag": "3.12-alpine",                  // Docker tag
  "tier": 1,                             // Update tier (1 or 2)
  "support_multi_arch": true             // Enable arm64 builds
}
```

**Critical**: Never manually edit `.github/workflows/base.*.yml` - regenerate via `python scripts/gen_action.py`

## Key Workflows

### Adding New Base Image
1. Create `base/{name}/` directory with:
   - `Dockerfile` (or variant-specific `Dockerfile.{version}`)
   - `config.json` with array of build configs
   - Optional: `README.md` with usage example
2. Run: `python scripts/gen_action.py` to generate workflows
3. Commit both `base/{name}/` and generated `.github/workflows/base.{name}.yml`

### Triggering Rebuilds
- **Tier system**: Images are organized into tier 1 and tier 2 based on dependencies
  - **Tier 1**: Base images with no internal dependencies (e.g., socat, readflag, language runtimes)
  - **Tier 2**: Images that depend on tier 1 images (e.g., confine depends on socat, php-mariadb depends on php)
  - Tier separation ensures builds happen in correct order: tier 1 completes before tier 2 starts
- Update trigger: `python scripts/update.py -t {1|2} -c` creates timestamp in `updates/tier{n}.md`
- All workflows watch their tier file - updating it triggers rebuilds of all images in that tier

### Multi-Architecture Builds
- Set `"support_multi_arch": true` in config.json for `linux/amd64,linux/arm64`
- Disable for architecture-specific binaries (see `readflag` using x86 assembly)

## Project Conventions

### CTF Challenge Pattern
Images follow GZCTF conventions:
- User `ctf` (UID varies by base image)
- Working directory `/home/ctf`
- `init.sh` script receives `$GZCTF_FLAG` env var, writes to file, unsets var
- Challenge runs via socat or web server

Example from `base/python/src/init.sh`:
```bash
echo $GZCTF_FLAG > /home/ctf/flag
chmod 444 /home/ctf/flag
unset GZCTF_FLAG
socat TCP-LISTEN:1337,reuseaddr,fork EXEC:"python3 challenge.py"
```

### Dependency Management
- Workflows auto-watch: `base/{name}/**`, `updates/tier{n}.md`, own workflow file
- Dependencies added via `config.json["depends_on"]` array for cross-image deps

### Image Lifecycle
- **Auto-cleanup**: `dataaxiom/ghcr-cleanup-action` prunes untagged/ghost/partial images after each build
- **Concurrency**: Cleanup jobs use `group: cleanup-images-{name}` to prevent conflicts

## Common Tasks

**Test config changes locally**: `python scripts/gen_action.py` and inspect generated YAML
**Force rebuild all tier 1 images**: `python scripts/update.py -t 1 -c && git push`
**Check existing variants**: Review `base/{name}/config.json` for tag/Dockerfile mappings
**Debug workflow**: Check `base/{name}/**` paths in generated workflow match actual files
