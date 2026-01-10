#!/bin/sh

MODE="${1:-patch}"

PYPROJECT="pyproject.toml"

# Read version
VERSION=$(sed -nE 's/^version[[:space:]]*=[[:space:]]*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/p' "$PYPROJECT")

if [ -z "$VERSION" ]; then
    echo "❌ Could not read version from $PYPROJECT"
    exit 1
fi

MAJOR=$(echo "$VERSION" | cut -d. -f1)
MINOR=$(echo "$VERSION" | cut -d. -f2)
PATCH=$(echo "$VERSION" | cut -d. -f3)

case "$MODE" in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo "Usage: $0 [major|minor|patch]"
    exit 1
    ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"

# Update
sed -i -E "s/^version[[:space:]]*=.*$/version = \"$NEW_VERSION\"/" "$PYPROJECT"

echo "✅ Version bumped: $VERSION → $NEW_VERSION"

# Ask for confirmation
printf "Create git commit \"Bump to version \\\"%s\\\"\"? [y/N]: " "$NEW_VERSION"
read answer

case "$answer" in
  y|Y|yes|YES)
    git add "$PYPROJECT"
    git commit -m "Bump to version \"$NEW_VERSION\""
    echo "✅ Git commit created"
    ;;
  *)
    echo "ℹ️ Commit skipped"
    ;;
esac
