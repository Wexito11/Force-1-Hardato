import sys, math
import render as R
import half as H
UP, DN = 50.81, -42.45
def V(items): return [(s.val(), c) for s, c in items]
w = sys.argv[1:] or ["1", "2", "3"]
if "1" in w:
    R.render(V(H.track() + H.robot(0, UP)), "out/1к2/Рендеры/1_на_рельсах.png", 32, -55, tol=0.6,
             title="«Форс-1» 1:2 на рельсах (колея 760): инспекция, полозья подняты")
if "2" in w:
    R.render(V(H.track(wagon=True) + H.robot(1, UP)), "out/1к2/Рендеры/2_укрытие.png", 14, -22, tol=0.6,
             title="Режим укрытия: робот ниже головки рельса, колёсная пара поезда проходит над ним")
if "3" in w:
    R.render(V(H.track() + H.robot(2, DN)), "out/1к2/Рендеры/3_полозья_опущены.png", 24, -140, tol=0.6,
             title="Переход: полозья опущены, колёса над рельсами, телескоп сжат")
if "4" in w:
    R.render(V(H.robot(0, UP)), "out/1к2/Рендеры/4_модули_крупно.png", 38, -120, tol=0.4,
             title="Модули A и B: телескоп (П + прямоугольный профиль), рейка на Г-профиле, полозья")
print("ok")
