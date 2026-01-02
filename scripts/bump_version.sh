#!/bin/bash
# Bump version and update badge version parameters in README.md
# Usage: ./scripts/bump_version.sh [patch|minor|major]

set -e

BUMP_TYPE=${1:-patch}

echo "🔄 Bumping $BUMP_TYPE version..."
NEW_VERSION=$(poetry version $BUMP_TYPE | awk '{print $6}')

if [ -z "$NEW_VERSION" ]; then
    echo "❌ Failed to bump version"
    exit 1
fi

echo "✅ Version bumped to: $NEW_VERSION"

echo "🔄 Updating badge versions in README.md..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/?v=[0-9]\+\.[0-9]\+\.[0-9]\+/?v=$NEW_VERSION/g" README.md
else
    # Linux
    sed -i "s/?v=[0-9]\+\.[0-9]\+\.[0-9]\+/?v=$NEW_VERSION/g" README.md
fi

echo "✅ Badges updated"

echo ""
echo "📝 Next steps:"
echo "   1. Update CHANGELOG.md with release notes"
echo "   2. Review changes: git diff"
echo "   3. Commit: git add -A && git commit -m 'Bump version to $NEW_VERSION'"
echo "   4. Push: git push origin main"
echo "   5. Release: gh release create v$NEW_VERSION --generate-notes"
echo ""
echo "Or use the automated release:"
echo "   gh release create v$NEW_VERSION --title 'Release v$NEW_VERSION' --notes '...'"
