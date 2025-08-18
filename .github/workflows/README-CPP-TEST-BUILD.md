# C++ Test Package Build Workflows

## Overview
Two workflows are provided for building C++ test Docker packages:

### 1. **Manual Trigger Build** (`build-cpp-test-package.yml`)
- Builds only when commit message contains `[build-cpp]` or `[cpp-test]`
- Useful for controlled releases

### 2. **Automatic Build** (`cpp-test-auto-build.yml`)
- Builds on every commit to cpp branches
- Builds for PRs (without publishing)
- Recommended for continuous testing

## Docker Image Naming Convention

All C++ test packages are published with distinguished names:
- **Registry**: `ghcr.io`
- **Repository**: `<your-org>/sdv-runtime-cpp-test`
- **Tags**: 
  - `cpp-compiler-latest` - Latest from cpp-compiler branch
  - `cpp-compiler-20240118-abc1234` - Specific version
  - `pr-123-abc1234` - Pull request builds

## Usage

### Trigger Manual Build
```bash
git commit -m "Add new feature [build-cpp]"
git push
```

### Pull Test Package
```bash
# Latest C++ test package
docker pull ghcr.io/eclipse-autowrx/sdv-runtime-cpp-test:cpp-compiler-latest

# Specific version
docker pull ghcr.io/eclipse-autowrx/sdv-runtime-cpp-test:cpp-compiler-20240118-abc1234
```

### Run Test Package
```bash
docker run -d \
  --name sdv-cpp-test \
  -p 55555:55555 \
  -p 3090:3090 \
  ghcr.io/eclipse-autowrx/sdv-runtime-cpp-test:cpp-compiler-latest
```

## Configuration

### Change Target Branch
Edit the workflow file:
```yaml
on:
  push:
    branches:
      - cpp-compiler  # Add your branch here
      - another-branch
```

### Change Image Name Pattern
Edit the `IMAGE_NAME` environment variable:
```yaml
env:
  IMAGE_NAME: ${{ github.repository }}-cpp-experimental  # Change suffix
```

## Build Status

The workflows generate detailed summaries including:
- Docker image tags
- Pull commands
- Build metadata
- Version information

Check the Actions tab in GitHub for build status and summaries.