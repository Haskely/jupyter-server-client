set -e

cd "$(dirname $0)"

echo "Use rye to manage python environment"

# 检查是否安装了 rye
if ! command -v rye &> /dev/null then
    echo "Installing rye ..."
    curl -sSf https://rye-up.com/get | bash --yes
    echo "rye docs: https://rye-up.com/"
fi

rye sync
source .venv/bin/activate

echo "FINISHED"
