#!/bin/bash
set -e

echo "Building Next.js frontend..."
npm run build --prefix frontend

echo "Build complete. Static files are in frontend/out/"
