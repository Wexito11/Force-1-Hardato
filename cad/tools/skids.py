# Полозья (У1): фанера 6 мм, 2 шт. 240 x 12, оси шарниров через 226 (= 2 x 113)
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import drawings as D, track as TR, corpus as C

def skid(name):
    o = C.rect(0, 0, 240, 12)
    h = [(7, 6, 1.65), (233, 6, 1.65)]
    return (name, o, [], h, (120, 6))

parts = [C.place(skid("П-1 полоз A"), 10, 10), C.place(skid("П-2 полоз B"), 10, 30)]
if __name__ == "__main__":
    with PdfPages("out/ФОРС1_Полозья_фанера6.pdf") as pdf:
        fig, ax, ox, oy = D.sheet_layout(pdf, parts, "Полозья модулей.\nРаскладка", "ФОРС1.01.02.001",
                                         "Фанера 6 ГОСТ 3916.1-2018", 1, 1,
                                         ["1. Полоз 240x12, 2 шт.; отв. Ø3,3 - шарниры звеньев (ось M3).",
                                          "2. Межосевое 226 = расстоянию между валами MG996R."])
        pdf.savefig(fig); plt.close(fig)
    D.to_dxf("out/Лазер DXF/ФОРС1_полозья_фанера6.dxf", parts)
    print(TR.net_area(parts))
