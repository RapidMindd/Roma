#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null || ! command -v make >/dev/null; then
    echo 'Установите Python 3 и make. Команды для Linux приведены в README.md.' >&2
    exit 1
fi

compiler="${CXX:-g++}"
if [[ "$(uname -s)" == Darwin && -z "${CXX:-}" ]]; then
    compiler=''
    for version in 16 15 14 13; do
        if command -v "g++-$version" >/dev/null; then
            compiler="g++-$version"
            break
        fi
    done
fi
if [[ -z "$compiler" ]] || ! command -v "$compiler" >/dev/null; then
    echo 'Не найден GCC C++. На macOS: brew install gcc; на Linux см. README.md.' >&2
    exit 1
fi
if "$compiler" --version | head -n 1 | grep -qi clang; then
    echo 'Нужен GCC с OpenMP. Укажите компилятор через CXX=g++-16 ./setup.sh.' >&2
    exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make clean
make -j4 CXX="$compiler"
printf '%s\n' "$compiler" > .venv/compiler
echo 'Готово. Демонстрация: ./run.sh; обработка изображения: ./run.sh blur input.jpg output.png'
