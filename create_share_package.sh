#!/bin/bash

echo "🚀 Creating TeleConnect Sharing Package..."

# Create a temporary directory for the clean project
TEMP_DIR="telecom_share_temp"
SHARE_NAME="telecom_application_share"

# Remove existing temp directory if it exists
rm -rf ../$TEMP_DIR
rm -rf ../$SHARE_NAME.zip
rm -rf ../$SHARE_NAME.tar.gz

# Create temp directory
mkdir ../$TEMP_DIR

echo "📁 Copying essential project files..."

# Copy main project structure (excluding large/unnecessary files)
rsync -av --progress . ../$TEMP_DIR/ \
  --exclude='backend/telecom/' \
  --exclude='backend/instance/' \
  --exclude='logs/' \
  --exclude='frontend/node_modules/' \
  --exclude='.env' \
  --exclude='nginx/ssl/' \
  --exclude='*.pyc' \
  --exclude='__pycache__/' \
  --exclude='.DS_Store'

echo "📦 Creating ZIP archive..."

# Create ZIP file
cd ..
zip -r $SHARE_NAME.zip $TEMP_DIR/
mv $SHARE_NAME.zip $SHARE_NAME.zip

# Clean up temp directory
rm -rf $TEMP_DIR

echo "✅ Share package created: $SHARE_NAME.zip"
echo "📊 Archive size:"
ls -lh $SHARE_NAME.zip

echo ""
echo "🎯 Ready to share!"
echo "📧 Send the ZIP file: $SHARE_NAME.zip"
echo "📋 Include the SHARING_INSTRUCTIONS.md for setup guide"
