echo "Removing contents of mariadb/data/..."

if rm -rf mariadb/data/*; then
    echo "✅ Cleanup successful: all contents removed."
else
    echo "❌ Error: failed to remove contents of mariadb/data/."
fi