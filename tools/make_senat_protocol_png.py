# -*- coding: utf-8 -*-
"""Протокол заседания Сената 09.11.2026 - парадный PNG-документ (2 страницы).

Стиль снят с итогов заседания и обращений Сената: зелёная рамка, эмблема,
двуязычная шапка, таблицы состава и голосований.
"""
import os

from PIL import Image, ImageDraw, ImageFont

W = 3000
GREEN = (69, 137, 63)
GREEN_D = (46, 92, 42)
INK = (26, 26, 26)
MUTED = (108, 112, 116)
RULE = (203, 208, 201)
SHADE = (236, 242, 232)
BODY_L, BODY_R = 300, 2700
BODY_W = BODY_R - BODY_L
CENTER = (BODY_L + BODY_R) // 2

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "Обращения",
                      "IAD — отзыв вето (Губернатор Harlow)", "assets")
MPL = "/usr/local/lib/python3.11/dist-packages/matplotlib/mpl-data/fonts/ttf"
FR = os.path.join(MPL, "DejaVuSerif.ttf")
FB = os.path.join(MPL, "DejaVuSerif-Bold.ttf")
FI = os.path.join(MPL, "DejaVuSerif-Italic.ttf")

SIZE = 30          # подбирается автоматически
LIMIT = 3880

_cache = {}


def F(path, size):
    k = (path, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(path, size)
    return _cache[k]


def tw(d, s, font):
    b = d.textbbox((0, 0), s, font=font)
    return b[2] - b[0]


def tracked(d, y, text, font, tracking, fill=INK, center_at=CENTER, draw=True,
            left=False):
    widths = [tw(d, text[i], font) for i in range(len(text))]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = center_at - total / 2
    if left:
        x = BODY_L
    for ch, w in zip(text, widths):
        if draw:
            d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def title_mixed(d, y, parts, draw=True):
    total = 0
    for text, font, tr in parts:
        total += sum(tw(d, ch, font) for ch in text) + tr * (len(text) - 1) + 20
    total -= 20
    x = CENTER - total / 2
    for text, font, tr in parts:
        for ch in text:
            if draw:
                d.text((x, y), ch, font=font, fill=GREEN)
            x += tw(d, ch, font) + tr
        x += 20
    return total


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(d, trial, font) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def style_font(style):
    return {"r": FR, "b": FB, "i": FI}[style]


def para(d, y, runs, width=BODY_W, left=BODY_L, hang=0, lh=None,
         size=None, justify=True, draw=True, space_after=0):
    size = size or SIZE
    lh = lh or int(size * 1.62)
    tokens = []
    for text, style, color in runs:
        parts = text.split(" ")
        for i, p in enumerate(parts):
            if p:
                tokens.append((p, style, color))
            if i < len(parts) - 1:
                tokens.append((None, style, color))

    first_ind = 0          # первая строка начинается от левого края
    cont_ind = hang        # строки со второй - с висячим отступом
    lines, cur, curw = [], [], 0.0
    for tok in tokens:
        if tok[0] is None:
            if cur:
                cur.append(tok)
            continue
        limit = width - (first_ind if not lines else cont_ind)
        w = tw(d, tok[0], F(style_font(tok[1]), size))
        sp = tw(d, " ", F(style_font(tok[1]), size)) if cur else 0
        if curw + sp + w <= limit or not cur:
            if cur:
                curw += sp
            cur.append(tok)
            curw += w
        else:
            while cur and cur[-1][0] is None:
                cur.pop()
            lines.append(cur)
            cur = [tok]
            curw = w
    while cur and cur[-1][0] is None:
        cur.pop()
    if cur:
        lines.append(cur)

    for i, ln in enumerate(lines):
        ind = first_ind if i == 0 else cont_ind
        x = left + ind
        limit = width - ind
        gaps = sum(1 for t in ln if t[0] is None)
        natural = sum(tw(d, " ", F(style_font(t[1]), size)) if t[0] is None
                      else tw(d, t[0], F(style_font(t[1]), size)) for t in ln)
        extra = (limit - natural) / gaps if (gaps and justify and i < len(lines) - 1) else 0
        for tok, style, color in ln:
            font = F(style_font(style), size)
            if tok is None:
                x += tw(d, " ", font) + extra
            else:
                if draw:
                    d.text((x, y), tok, font=font, fill=color)
                x += tw(d, tok, font)
        y += lh
    return y + space_after


def heading(d, y, text, draw=True, size=32, space_before=16):
    y += space_before
    font = F(FB, size)
    tracked(d, y, text, font, 3, GREEN_D, draw=draw, left=True)
    if draw:
        d.line([(BODY_L, y + int(size * 1.9)), (BODY_R, y + int(size * 1.9))],
               fill=RULE, width=3)
    return y + int(size * 2.9)


def note(d, y, text, size=24, draw=True, space_after=8):
    font = F(FI, size)
    lines = wrap(d, text, font, BODY_W)
    if draw:
        for i, ln in enumerate(lines):
            d.text((BODY_L, y + i * int(size * 1.55)), ln, font=font, fill=MUTED)
    return y + len(lines) * int(size * 1.55) + space_after


# ------------------------------------------------------------------ таблица
def table(d, y, head, rows, widths, draw=True, size=23, pad=16, center_cols=()):
    assert abs(sum(widths) - BODY_W) < 2, sum(widths)
    head_font = F(FB, size)
    cell_font = F(FR, size)
    line_h = int(size * 1.42)

    def row_height(cells, font):
        h = 0
        for i, cell in enumerate(cells):
            inner = widths[i] - 2 * pad
            n = len(wrap(d, cell, font, inner)) if cell else 1
            h = max(h, n * line_h)
        return h + 2 * pad

    hh = row_height(head, head_font)
    if draw:
        d.rectangle([BODY_L, y, BODY_R, y + hh], fill=SHADE)
        d.line([(BODY_L, y), (BODY_R, y)], fill=GREEN_D, width=3)
    x = BODY_L
    for i, cell in enumerate(head):
        lines = wrap(d, cell, head_font, widths[i] - 2 * pad)
        if draw:
            yy = y + pad
            for ln in lines:
                wln = tw(d, ln, head_font)
                d.text((x + (widths[i] - wln) // 2, yy), ln, font=head_font, fill=GREEN_D)
                yy += line_h
        x += widths[i]
    top = y
    y += hh

    for cells in rows:
        rh = row_height(cells, cell_font)
        if draw:
            d.line([(BODY_L, y + rh), (BODY_R, y + rh)], fill=RULE, width=1)
        x = BODY_L
        for i, cell in enumerate(cells):
            lines = wrap(d, cell, cell_font, widths[i] - 2 * pad)
            if draw:
                yy = y + pad
                for ln in lines:
                    if i in center_cols:
                        wln = tw(d, ln, cell_font)
                        d.text((x + (widths[i] - wln) // 2, yy), ln, font=cell_font, fill=INK)
                    else:
                        d.text((x + pad, yy), ln, font=cell_font, fill=INK)
                    yy += line_h
            x += widths[i]
        y += rh

    if draw:
        d.rectangle([BODY_L, top + 3, BODY_R, y], outline=RULE, width=2)
        d.line([(BODY_L, top), (BODY_R, top)], fill=GREEN_D, width=3)
    return y


# ------------------------------------------------------------------ данные
SENATORS = [
    ("1", "Weazel News", "Jhonny Scoutezaki", "164317"),
    ("2", "Weazel News", "Kasandriia Scout", "160955"),
    ("3", "Полицейский департамент г. Лос-Сантос", "Afelia Suspect", "14077"),
    ("4", "Полицейский департамент г. Лос-Сантос", "Socrat Wild", "96031"),
    ("5", "Департамент шерифа о. Блэйн", "Marcus Nomad", "85028"),
    ("6", "Департамент шерифа о. Блэйн", "Aliya Nomad", "131485"),
    ("7", "Федеральное расследовательское бюро", "Eric Killa", "104068"),
    ("8", "Федеральное расследовательское бюро", "Pravik Killa", "2759"),
    ("9", "Национальная гвардия штата Сан-Андреас", "Asher Keat", "68553"),
    ("10", "Национальная гвардия штата Сан-Андреас", "Hunter Keates", "122338"),
    ("11", "Экстренная медицинская служба штата Сан-Андреас", "Kiray Fair", "37492"),
    ("12", "Экстренная медицинская служба штата Сан-Андреас", "Himeno Kartonkina", "23899"),
    ("13", "Правительство штата Сан-Андреас", "Maras Shakyr", "63823"),
    ("14", "Правительство штата Сан-Андреас", "Meow Killa", "4638"),
    ("15", "Консервативная партия «Патриоты Америки»", "Makima Killa", "864"),
    ("16", "Республиканская партия «Возрождение»", "Jonny Zakonov", "55454"),
]

VOTES = [
    ("1", "Открытие заседания", "19:19", "19:33", "16", "0", "0", "9", "Принято"),
    ("2", "Освободить Tommy Harlow от должности Председателя (Спикера) Сената и закрыть "
          "заседание", "19:53", "20:53", "6", "6", "1", "9", "Не принято"),
    ("3", "Закрытие заседания", "19:53", "20:58", "5", "9", "0", "9", "Не принято"),
    ("4", "Освободить Tommy Harlow от должности Председателя (Спикера) Сената и избрать "
          "Marcus Nomad Председателем (Спикером) Сената", "20:15", "20:17", "14", "0", "0",
     "9", "Принято"),
]

W_SEN = [80, 960, 800, 560]
W_VOT = [70, 1000, 160, 160, 100, 160, 200, 160, 390]

PAGE1_ITEMS = [
    ("1.1.", "Место проведения - зал заседаний Сената штата Сан-Андреас, г. Лос-Сантос."),
    ("1.2.", "Дата проведения - 9 ноября 2026 года. Заседание назначено 7 ноября "
             "2026 года."),
    ("1.3.", "Форма проведения - пленарное заседание с голосованием через электронную "
             "систему опроса."),
    ("1.4.", "Заседание открыто в 19:19 и признано правомочным: в голосовании об открытии "
             "участвовали шестнадцать сенаторов, что превышает половину общего числа "
             "действующих сенаторов (часть 1 статьи 9 Конституционного закона «О Сенате "
             "штата Сан-Андреас»)."),
    ("1.5.", "Председательствующий - Tommy Harlow, Председатель (Спикер) Сената штата "
             "Сан-Андреас. Полномочий сенатора не имел на основании части 3 статьи 3 "
             "Конституционного закона «О Сенате штата Сан-Андреас»."),
]

QUESTIONS = [
    ("3.1.", "Открытие заседания - внесён председательствующим в 19:19."),
    ("3.2.", "Досрочное освобождение Tommy Harlow от должности Председателя (Спикера) "
             "Сената и закрытие заседания - внесён председательствующим в 19:53."),
    ("3.3.", "Закрытие заседания - внесён председательствующим в 19:53."),
    ("3.4.", "Досрочное освобождение Tommy Harlow от должности Председателя (Спикера) "
             "Сената и избрание Marcus Nomad Председателем (Спикером) Сената - внесён "
             "председательствующим в 20:15."),
]

DECISIONS = [
    ("5.1.", "Заседание открыто и признано правомочным."),
    ("5.2.", "Предложение о досрочном освобождении Tommy Harlow от должности Председателя "
             "(Спикера) Сената и закрытии заседания не принято: шесть голосов «за», шесть "
             "«против», один «воздержался» при необходимых девяти."),
    ("5.3.", "Предложение о закрытии заседания не принято: пять голосов «за», девять "
             "«против» при необходимых девяти. Заседание продолжено."),
    ("5.4.", "Tommy Harlow досрочно освобождён от должности Председателя (Спикера) "
             "Сената, Marcus Nomad избран Председателем (Спикером) Сената штата "
             "Сан-Андреас: четырнадцать голосов «за», ноль «против», ноль "
             "«воздержавшихся» при необходимых девяти. Решение принято единогласно."),
    ("5.5.", "Полномочия Председателя (Спикера) Сената переданы Marcus Nomad в 20:19."),
]

NOTES = [
    ("6.1.", "В 19:45 председательствующий потребовал от сотрудников Секретной службы "
             "вывести сенатора Jonny Zakonov из зала заседаний. Требование основано на "
             "пункте «и» части 4 статьи 3 и части 4 статьи 15 Конституционного закона "
             "«О Сенате штата Сан-Андреас». Предупреждение не выносилось."),
    ("6.2.", "После вывода из зала сенатор Jonny Zakonov вернулся в зал заседаний по "
             "собственному решению. Распоряжение председательствующего об освобождении "
             "помещения им не исполнено."),
    ("6.3.", "В 20:10 в зале заседаний сенатор Jonny Zakonov применил наручники к "
             "сотруднику Секретной службы, осуществлявшему сопровождение Губернатора штата "
             "Сан-Андреас. Сотрудник был освобождён через 30 секунд. Начальство сотрудника "
             "и сотрудник Офиса Генерального прокурора не вызывались (статья 19 "
             "Процессуального кодекса штата Сан-Андреас)."),
    ("6.4.", "В 20:15 сенатор Jonny Zakonov участвовал в голосовании об избрании Marcus "
             "Nomad Председателем (Спикером) Сената. Решение об отстранении сенатора от "
             "участия в заседании не принималось, полномочия сенатора не "
             "приостанавливались."),
]

MAKING = [
    "Настоящий протокол составлен 12 ноября 2026 года, после окончания заседания, на "
    "основании журнала голосований, содержащего время и результаты каждого опроса. Записи "
    "в журнал голосований не вносились и не изменялись. Протокол не является документом, "
    "составленным в ходе заседания, и не заменяет журнал голосований.",

    "Сведения об отсутствии предупреждения, о возврате в зал заседаний и о применении "
    "наручников внесены на основании видеозаписей, указанных в приложении.",
]

APPENDIX = [
    ("1.", "Журнал голосований пленарного заседания 9 ноября 2026 года."),
    ("2.", "Видеозапись заседания: https://youtu.be/FhIWsJXvVP4."),
    ("3.", "Видеозапись, представленная сенатором Jonny Zakonov: "
           "https://www.youtube.com/watch?v=d_sLY2Ty6XQ, запись начата в 19:45:26."),
]


# ------------------------------------------------------------------ страницы
def header(d, draw=True):
    d.rectangle([116, 92, 2876, 4140], outline=GREEN, width=9)
    em = Image.open(os.path.join(ASSETS, "state_emblem.png")).convert("RGB")
    em = em.resize((240, 240), Image.LANCZOS)
    if draw:
        d._image.paste(em, (CENTER - 120, 150))
    title_mixed(d, 435, [("STATE", F(FB, 54), 10),
                         ("of", F(FI, 46), 2),
                         ("SAN ANDREAS", F(FB, 54), 10)], draw=draw)
    tracked(d, 532, "SENATE OF THE STATE OF SAN ANDREAS", F(FB, 25), 7, GREEN, draw=draw)
    if draw:
        d.line([(860, 606), (2140, 606)], fill=GREEN, width=3)

    tracked(d, 652, "ПРОТОКОЛ", F(FB, 62), 14, INK, draw=draw)
    tracked(d, 762, "ПЛЕНАРНОГО ЗАСЕДАНИЯ СЕНАТА", F(FR, 27), 3, MUTED, draw=draw)
    if draw:
        right = "стр. 1 из 2"
        d.text((BODY_R - tw(d, right, F(FI, 23)), 250), right, font=F(FI, 23), fill=MUTED)
    return 856


def meta(d, y, draw=True):
    left = "9 ноября 2026 года, г. Лос-Сантос"
    right = "Председательствующий: Tommy Harlow, паспорт 98650"
    if draw:
        d.text((BODY_L, y), left, font=F(FI, 25), fill=MUTED)
        d.text((BODY_R - tw(d, right, F(FI, 25)), y), right, font=F(FI, 25), fill=MUTED)
        d.line([(BODY_L, y + 46), (BODY_R, y + 46)], fill=RULE, width=2)
    return y + 74


def top_band(d, draw=True, page_no=2, total=2):
    d.rectangle([116, 92, 2876, 4140], outline=GREEN, width=9)
    tracked(d, 168, "ПРОТОКОЛ ПЛЕНАРНОГО ЗАСЕДАНИЯ СЕНАТА  ·  9 НОЯБРЯ 2026 ГОДА",
            F(FB, 26), 4, GREEN, draw=draw)
    if draw:
        d.line([(BODY_L, 228), (BODY_R, 228)], fill=GREEN, width=3)
        right = f"стр. {page_no} из {total}"
        d.text((BODY_R - tw(d, right, F(FI, 23)), 250), right, font=F(FI, 23), fill=MUTED)
    return 306


def page1(d, draw=True):
    y = header(d, draw)
    y = meta(d, y, draw)
    y = note(d, y, "Составлен 12 ноября 2026 года по журналу голосований. В ходе заседания "
                   "протокол не вёлся.", size=25, draw=draw, space_after=24)

    y = heading(d, y, "I.  МЕСТО, ВРЕМЯ И ФОРМА ПРОВЕДЕНИЯ", draw=draw)
    for num, txt in PAGE1_ITEMS:
        y = para(d, y, [(num + " ", "b", GREEN_D), (txt, "r", INK)],
                 hang=80, draw=draw, space_after=int(SIZE * 0.40))

    y += int(SIZE * 0.45)
    y = heading(d, y, "II.  СОСТАВ СЕНАТА", draw=draw)
    y = para(d, y, [("Общее число действующих сенаторов на момент открытия заседания и "
                     "перед каждым голосованием - шестнадцать. Оснований для исключения "
                     "сенаторов из подсчёта, предусмотренных частью 5 статьи 80 Конституции "
                     "штата Сан-Андреас, не устанавливалось.", "r", INK)],
             draw=draw, space_after=int(SIZE * 0.65))
    y = table(d, y, ["№", "Орган или партия", "Сенатор", "№ паспорта"], SENATORS,
              W_SEN, draw=draw, size=26, center_cols=(0, 2, 3))
    y += 10
    y = note(d, y, "В графе «№ паспорта» указаны номера паспортов сенаторов, а не "
                   "порядковые номера.", size=21, draw=draw, space_after=34)

    y = heading(d, y, "III.  ВОПРОСЫ, ПОСТАВЛЕННЫЕ НА ГОЛОСОВАНИЕ", draw=draw)
    for num, txt in QUESTIONS:
        y = para(d, y, [(num + " ", "b", GREEN_D), (txt, "r", INK)],
                 hang=80, draw=draw, space_after=int(SIZE * 0.32))
    y = para(d, y, [("3.5. ", "b", GREEN_D),
                    ("Инициатива сенатора Jonny Zakonov об избрании Председателя Сената и "
                     "его заместителя на голосование не ставилась. Инициатива "
                     "опубликована в разделе предложений Сената 9 ноября 2026 года в 19:00 "
                     "и повторно в 19:43. Подписей более чем половины действующих сенаторов "
                     "под инициативой не имелось, в связи с чем обязанность включить её в "
                     "повестку дня в качестве внеочередного вопроса, предусмотренная частью "
                     "4 статьи 9 Конституционного закона «О Сенате штата Сан-Андреас», не "
                     "возникла.", "r", INK)],
             hang=80, draw=draw, space_after=int(SIZE * 0.4))
    if draw and y < 3900:
        d.line([(BODY_L, 3966), (BODY_R, 3966)], fill=RULE, width=2)
        tracked(d, 3996, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 22), 8, MUTED)
    return y


def page2(d, draw=True, page_no=2, total=2, air=0):
    y = top_band(d, draw, page_no, total)

    y = heading(d, y, "IV.  РЕЗУЛЬТАТЫ ГОЛОСОВАНИЙ", draw=draw)
    y = table(d, y, ["№", "Вопрос", "Начало", "Конец", "За", "Против", "Воздерж.",
                     "Нужно", "Итог"], VOTES, W_VOT, draw=draw, size=24,
              center_cols=(0, 2, 3, 4, 5, 6, 7, 8))
    y += 10 + air
    y = note(d, y, "Порог принятия решения - девять голосов: половина от шестнадцати "
                   "составляет восемь, требуется превышение, то есть девять (часть 5 "
                   "статьи 80 Конституции штата Сан-Андреас).", size=21, draw=draw,
             space_after=20 + air)

    y = heading(d, y, "V.  РЕШЕНИЯ", draw=draw)
    for num, txt in DECISIONS:
        y = para(d, y, [(num + " ", "b", GREEN_D), (txt, "r", INK)],
                 hang=80, draw=draw, space_after=int(SIZE * 0.32) + air)

    y += int(SIZE * 0.4) + air
    y = heading(d, y, "VI.  ОСОБЫЕ ОТМЕТКИ", draw=draw)
    for num, txt in NOTES:
        y = para(d, y, [(num + " ", "b", GREEN_D), (txt, "r", INK)],
                 hang=80, draw=draw, space_after=int(SIZE * 0.38) + air)

    y += int(SIZE * 0.4) + air
    y = heading(d, y, "VII.  ПОРЯДОК СОСТАВЛЕНИЯ", draw=draw)
    for txt in MAKING:
        y = para(d, y, [(txt, "r", INK)], draw=draw, space_after=int(SIZE * 0.5) + air)

    y = heading(d, y, "ПРИЛОЖЕНИЕ", draw=draw)
    for num, txt in APPENDIX:
        y = para(d, y, [(num + " ", "b", GREEN_D), (txt, "r", INK)],
                 hang=48, draw=draw, space_after=int(SIZE * 0.22) + air)

    if not draw:
        return y

    sy = y + 30
    if sy + 400 > 3900:
        sy = None
    elif sy < 3160:
        sy = 3160

    if draw and sy is not None:
        d.line([(1790, sy + 150), (2660, sy + 150)], fill=INK, width=4)
        d.text((1820, sy + 172), "Marcus Nomad", font=F(FB, 34), fill=INK)
        d.text((1820, sy + 222), "Председатель (Спикер) Сената", font=F(FI, 26), fill=MUTED)
        d.text((1820, sy + 264), "штата Сан-Андреас", font=F(FI, 26), fill=MUTED)
        d.text((1820, sy + 314), "12 ноября 2026 года", font=F(FI, 24), fill=MUTED)

        seal = Image.open(os.path.join(ASSETS, "great_seal.png")).convert("RGBA")
        seal = seal.resize((340, 340), Image.LANCZOS)
        r, g, b, a = seal.split()

        r = r.point(lambda v: int(max(0, min(255, (v - 112) * 1.42 + 92))))
        g = g.point(lambda v: int(max(0, min(255, (v - 100) * 1.42 + 80))))
        b = b.point(lambda v: int(max(0, min(255, (v - 74) * 1.42 + 54))))
        seal = Image.merge("RGBA", (r, g, b, a))
        d._image.paste(seal, (1388, sy + 4), seal)

        d.line([(BODY_L, 3966), (BODY_R, 3966)], fill=RULE, width=2)
        tracked(d, 3996, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 22), 8, MUTED)
    return (sy + 400) if sy else y


def measure(builder, **kw):
    img = Image.new("RGB", (W, 4225), "white")
    d = ImageDraw.Draw(img)
    d._image = img
    return builder(d, draw=False, **kw)


def render(builder, path, **kw):
    img = Image.new("RGB", (W, 4225), "white")
    d = ImageDraw.Draw(img)
    d._image = img
    builder(d, draw=True, **kw)
    img.save(path, "PNG", dpi=(300, 300))
    print("OK", path)


OUT = os.path.join(os.path.dirname(HERE), "Сенат", "Протокол заседания (09.11.2026)")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)

    best = None
    for s in range(34, 23, -1):
        SIZE = s
        globals()["SIZE"] = s
        e1 = measure(page1)
        e2 = measure(page2, page_no=2, total=2)
        print(f"кегль {s}: стр.1 -> {e1}, стр.2 -> {e2}")
        if e1 <= 3870 and isinstance(e2, int) and e2 <= 3920:
            best = s
            break
    if best is None:
        globals()["SIZE"] = 27
        print("резерв 27")
    print("итоговый кегль:", globals()["SIZE"])

    base = measure(lambda d, **kw: page2(d, page_no=2, total=2, air=0, **kw))
    print("низ текста стр.2 без воздуха:", base)
    air = 0
    if isinstance(base, int) and base < 3180:
        air = min(14, (3180 - base) // 15)
    print("воздух страницы 2:", air)

    render(page1, os.path.join(OUT, "Протокол заседания Сената 09.11.2026 - стр. 1.png"))
    render(page2, os.path.join(OUT, "Протокол заседания Сената 09.11.2026 - стр. 2.png"),
           page_no=2, total=2, air=air)
