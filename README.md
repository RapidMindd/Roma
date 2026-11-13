# Gaussian Blur

C++ выполняет размытие, Python загружает и сохраняет изображения через Pillow,
передаёт массивы NumPy в динамическую библиотеку через ctypes.

Текущий этап: Базовое размытие. Вариант по умолчанию: `scalar_o0`.

Используется ядро 3×3 `[1, 2, 1; 2, 4, 2; 1, 2, 1] / 16`.
Два прохода по строкам и столбцам дают ту же свёртку. На границах повторяется
крайний пиксель. Каналы RGB обрабатываются независимо, вычисления идут в float.
Каждая следующая итерация размывает результат предыдущей.

## Сборка и запуск

GNU/Linux: нужны GCC с поддержкой OpenMP, make и Python 3.
На Fedora: `sudo dnf install gcc-c++ make python3 python3-pip`.
На macOS Makefile использует Homebrew GCC 16; другой GCC можно указать через `CXX`.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make
python3 main.py blur input.jpg output.png --iterations 1
make test
python3 main.py benchmark --width 64 --height 48 --iterations 2
```

Доступные варианты: `scalar_o0`.
Выбор: `python3 main.py blur input.jpg output.png --variant scalar_o0`.
Библиотеки находятся в `build/`. `libgaussian_blur.so` содержит текущую версию.

Полный замер из отчёта запускается отдельно:

```sh
python3 main.py benchmark --width 1920 --height 1080 --iterations 1000 --threads 4
```

Вместо случайного изображения можно передать `--input image.png`.
Результаты сохраняются в `results/benchmark.csv`, параметры запуска в соседний JSON.
Время включает вызов C++ с выделением памяти и копированием данных, но не чтение
и сохранение изображения. Perf = 1/T, Comp = число непустых строк C++ файла,
P = целая часть (Perf / Comp × 1000000). Замеры из отчёта не подставляются.

## Переключение версий

```sh
git log --oneline
git switch --detach <хеш-коммита>
make clean
make
```

Вернуться к последней версии: `git switch main`, затем `make clean && make`.
Перед переключением сохраните свои изменения. В каждой версии доступны
текущий и предыдущие варианты алгоритма.
