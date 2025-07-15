echo "removing mariadb/data/ content..."
if rm -rf mariadb/data/*; then
    echo "everything has been cleaned up!"
else
    echo "something went wrong while executing: rm -rf mariadb/data/*"
fi