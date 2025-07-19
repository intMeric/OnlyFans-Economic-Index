#!/bin/bash

if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

FILE="$1"
GIST_ID="$2"

if [ -z "$FILE" ]; then
    echo "Usage: $0 <file> [gist_id]"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "❌ File '$FILE' not found"
    exit 1
fi

FILENAME=$(basename "$FILE")

if file "$FILE" | grep -q "text\|ASCII"; then
    echo "📝 Text file detected"
    CONTENT=$(cat "$FILE" | jq -R -s .)
else
    echo "📦 Binary file detected"
    CONTENT=$(base64 -w 0 "$FILE" | jq -R -s .)
    FILENAME="${FILENAME}.b64"
fi

# Calculate size
SIZE=$(stat -c%s "$FILE")
SIZE_MB=$((SIZE / 1024 / 1024))

echo "📊 Size: ${SIZE_MB}MB"

if [ $SIZE_MB -gt 10 ]; then
    echo "⚠️  Warning: File > 10MB, may fail"
fi

# Create temporary JSON file to avoid "Argument list too long"
TEMP_JSON=$(mktemp)
trap "rm -f $TEMP_JSON" EXIT

# Upload
if [ -z "$GIST_ID" ]; then
    echo "🚀 Creating new gist..."
    cat > "$TEMP_JSON" << EOF
{
  "description": "Binary file: $(basename "$FILE")",
  "public": true,
  "files": {
    "$FILENAME": {
      "content": $CONTENT
    }
  }
}
EOF
    RESPONSE=$(curl -s -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "Content-Type: application/json" \
      --data-binary @"$TEMP_JSON" \
      https://api.github.com/gists)
else
    echo "🔄 Updating gist $GIST_ID..."
    cat > "$TEMP_JSON" << EOF
{
  "files": {
    "$FILENAME": {
      "content": $CONTENT
    }
  }
}
EOF
    RESPONSE=$(curl -s -X PATCH \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "Content-Type: application/json" \
      --data-binary @"$TEMP_JSON" \
      https://api.github.com/gists/$GIST_ID)
fi

# Check and display result
if echo "$RESPONSE" | jq -e '.html_url' > /dev/null 2>&1; then
    ID=$(echo "$RESPONSE" | jq -r '.id')
    GIST_URL=$(echo "$RESPONSE" | jq -r '.html_url')
    RAW_URL=$(echo "$RESPONSE" | jq -r '.files."'$FILENAME'".raw_url')
    
    echo "✅ Success!"
    echo "🆔 ID: $ID"
    echo "🌐 Gist: $GIST_URL"
    echo "📥 Raw: $RAW_URL"
    echo ""
    
    if [[ "$FILENAME" == *.b64 ]]; then
        echo "📋 Download and decode:"
        echo "curl -s '$RAW_URL' | base64 -d > '$(basename "$FILE")'"
    else
        echo "📋 Download:"
        echo "curl -O '$RAW_URL'"
    fi
else
    echo "❌ Error:"
    echo "$RESPONSE" | jq -r '.message // "Unknown error"'
    exit 1
fi