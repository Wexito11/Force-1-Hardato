import sys
import matplotlib.pyplot as plt, matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfWriter, PdfReader
from gost import sheet, frame, text
U = sys.argv[1]; U4 = sys.argv[2]
renders = [("out/1к2/Рендеры/1_на_рельсах.png", "Рис. 1. «Форс-1» (1:2) на рельсах, колея 760: инспекция пути, полозья подняты"),
           ("out/1к2/Рендеры/2_укрытие.png", "Рис. 2. Режим укрытия: робот ниже головки рельса, колёсная пара поезда 1:2 проходит над ним"),
           ("out/1к2/Рендеры/3_полозья_опущены.png", "Рис. 3. Переход: полозья опущены (2 x MG996R на модуль), колёса над рельсами, телескоп сжат"),
           (U4 + "/render_ремонтный_модуль.png", "Рис. 4. Ремонтный модуль: гайковёрт, электромагнит, маркировка"),
           ("out/1к2/Рендеры/4_модули_крупно.png", "Рис. 5. Модули крупно: телескоп из профилей П 20x20 и 15x10, рейка GT2 на Г-профиле, полозья, лидар на полке")]
W, H = 420, 297
with PdfPages("out/_front.pdf") as pdf:
    fig, ax = sheet(W, H)
    text(ax, W / 2, 200, "«ФОРС-1»", 16)
    text(ax, W / 2, 180, "Робот-путеобходчик для автономной инспекции и обслуживания железнодорожного пути", 6)
    text(ax, W / 2, 160, "Техническая документация заочного этапа Хардатона «Инженерный вызов» 2026. Прототип в масштабе 1:2", 5)
    cont = ["Содержание:", "1. 3D-модель: рис. 1-5", "2. Схема электрическая принципиальная Э3 и перечень элементов ПЭ3",
            "3. Габаритная схема робота 1:2 на пути 760 (проверка по колёсам поезда)", "4. Натурный образец: габаритная схема на пути 1520",
            "5. Чертежи деталей под лазер 1:1 в поле 500x300: корпуса (фанера 4), крышки (оргстекло 3), полозья (фанера 6)",
            "", "Команда «Форс-1», МГТУ им. Н.Э. Баумана, ноябрь 2026"]
    for i, c in enumerate(cont):
        text(ax, 60, 130 - i * 9, c, 4.5, ha="left")
    pdf.savefig(fig); plt.close(fig)
    for p, cap in renders:
        fig = plt.figure(figsize=(W / 25.4, H / 25.4))
        ax = fig.add_axes([0.03, 0.08, 0.94, 0.88]); ax.axis("off")
        from PIL import Image, ImageChops
        im = Image.open(p).convert("RGB"); bb = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
        im = im.crop((bb[0], bb[1] + (60 if p.startswith("out/") else 0), bb[2], bb[3]))
        bb2 = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox(); im = im.crop(bb2)
        ax.imshow(im)
        fig.text(0.5, 0.035, cap, ha="center", fontsize=13, fontstyle="italic")
        pdf.savefig(fig); plt.close(fig)
w = PdfWriter()
for f in ["out/_front.pdf", U + "/Участник 3/Форс-1_схема_Э3.pdf", "out/1к2/ФОРС1_1к2_Габаритная_схема.pdf",
          "out/ФОРС1_Натурный_габарит.pdf", "out/1к2/ФОРС1_1к2_Чертежи_лазер.pdf"]:
    for pg in PdfReader(f).pages:
        w.add_page(pg)
w.write("out/1к2/ФОРС1_1к2_3D_схема_чертежи.pdf")
print(len(w.pages))
