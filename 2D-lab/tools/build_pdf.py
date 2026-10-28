"""Fills in the Lab 1 document (Macedonian) as a PDF, matching the original's look.

Run:  python3 2D-lab/tools/build_pdf.py
Output: 2D-lab/Laboratoriska_vezba_1_PERFORATED.pdf

The original is a Google Docs export (Arial, black text, plain black tables, 72 pt
margins). All original wording is kept verbatim; only the answers, the character image
and the level sketch are added. Liberation Sans is the metric-compatible Arial stand-in.
Task 8 is not started, so its original text is left as is.
"""
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
OUT = ROOT / "Laboratoriska_vezba_1_PERFORATED.pdf"
LLM_LINK = "https://claude.ai/code/session_015REauJjEStJtMwV1bMRQav"
UPLOAD_LINK = "https://courses.finki.ukim.mk/mod/assign/view.php?id=179857"

FL = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Arial", FL + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", FL + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", FL + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic",
                              boldItalic="Arial-Bold")

BLACK = colors.black
LINKCOL = "#1155cc"   # the original's hyperlink colour

TITLE = ParagraphStyle("title", fontName="Arial-Bold", fontSize=16, leading=18.4, spaceAfter=12)
HEAD = ParagraphStyle("head", fontName="Arial-Bold", fontSize=13, leading=15, spaceBefore=17, spaceAfter=6)
BODY = ParagraphStyle("body", fontName="Arial", fontSize=11, leading=12.65, spaceAfter=0)
ANS = ParagraphStyle("ans", parent=BODY, spaceBefore=7)
BUL = ParagraphStyle("bul", parent=BODY, leftIndent=14, bulletIndent=2, spaceBefore=3)
CELL = ParagraphStyle("cell", fontName="Arial", fontSize=11, leading=12.65)
CELL_B = ParagraphStyle("cellb", parent=CELL, fontName="Arial-Bold")
ACELL = ParagraphStyle("acell", fontName="Arial", fontSize=8.8, leading=10.4)


def P(t, st=BODY):
	return Paragraph(t, st)


def link(url, label=None):
	return f'<link href="{url}" color="{LINKCOL}"><u>{label or url}</u></link>'


def grid(data, widths, header=True, valign="TOP"):
	t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
	t.setStyle(TableStyle([
		("GRID", (0, 0), (-1, -1), 0.75, BLACK),
		("VALIGN", (0, 0), (-1, -1), valign),
		("LEFTPADDING", (0, 0), (-1, -1), 5.2), ("RIGHTPADDING", (0, 0), (-1, -1), 5.2),
		("TOPPADDING", (0, 0), (-1, -1), 3.3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.3),
	]))
	return t


def picture(path, max_w, max_h, align="LEFT"):
	w, h = PILImage.open(path).size
	k = min(max_w / w, max_h / h)
	im = Image(str(path), width=w * k, height=h * k)
	im.hAlign = align
	return im


def build():
	doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=66, rightMargin=66, topMargin=66,
	                        bottomMargin=66, title="Дизајнирање на 2D игра", author="grival900")
	s = []

	s += [P("Лабораториска вежба 1", TITLE), P("Документ за дизајн на игра на една страница", TITLE),
	      P("Целта на оваа лабораториска е да направите план за мала 2D игра што ќе ја изработувате на "
	        "следните вежби. Подоцна истата би можеле да ја проширите и за проект на предметот.")]

	# ---------------------------------------------------------------- 1
	s += [P("Задача 1 - Идеја", HEAD),
	      P("Смислете идеја за игра и опишете ја во една до две реченици ."),
	      P("PERFORATED е 2D игра со поглед одозгора во стил на Vampire Survivors, во која играчот со автоматско "
	        "пукање и брзо движење преживува бранови свети чувари, а секоја елиминација го полни бар на гревот од "
	        "нивото (на пример Гордост) за да ги изврши седумте гревови. Потоа, проколнат во Лимбо, ги поништува "
	        "гревовите во обратен редослед бегајќи од демони и на крај се раствора во светот и го чисти од омраза.",
	        ANS)]

	# ---------------------------------------------------------------- 2
	s += [P("Задача 2 - Приказна", HEAD),
	      P("Напишете ја приказната во три дела: почеток, средина и крај (по 2-3 реченици)."),
	      P("<b>Почеток:</b> Безимен човек, опиен од сопствената величина, одлучува да земе сè што ќе посака и ги "
	        "извршува седумте гревови еден по еден: Гордост, Алчност, Похот, Завист, Лакомост, Гнев и Мрзеливост. "
	        "Светите чувари, сјајни стражари на светот, го демнат во бранови за да го казнат. Секој грев му остава "
	        "светечка рупка во телото.", ANS),
	      P("<b>Средина:</b> По последниот грев е проколнат и испратен во Лимбо, каде секој грев станува свет што "
	        "мора да го поништи во обратен редослед, од Мрзеливост до Гордост. Сега го демнат демони, а секое "
	        "поправено зло му ја пополнува соодветната рупка со светлина.", ANS),
	      P("<b>Крај:</b> На последното ниво, поништувајќи ја Гордоста, сфаќа дека омразата во светот може да се "
	        "исчисти само ако се жртвува самиот себеси. Тој се раствора во светот, а светлината од рупките го "
	        "зафаќа целото тело додека не исчезне.", ANS)]

	# ---------------------------------------------------------------- 3
	s += [P("Задача 3 - Ликови", HEAD),
	      P("Пополнете ја табелата за главниот лик и барем еден непријател и NPC. Потоа нацртајте или генерирајте "
	        "слика на главниот лик (страничен профил).")]
	A = lambda t: P(t, ACELL)
	rows = [
		[P("", CELL), P("Главен лик", CELL_B), P("Непријател", CELL_B), P("NPC", CELL_B)],
		[P("Име", CELL), A("Безимениот"), A("Свет чувар (во Покајанието: демон)"), A("Превозникот")],
		[P("Улога", CELL), A("Играч: прво грешник, потоа грешник што се откупува."),
		 A("Стражар што во бранови го гони играчот."),
		 A("Водач: нуди надградби и лекува, преку фенер.")],
		[P("Личност", CELL), A("Прво горд и нагол, подоцна тивок и виновен."),
		 A("Студен, безмилосен и безличен; следи наредба."), A("Мирен, ироничен и уморен.")],
		[P("Мотивација", CELL), A("Прво: да земе сè. Потоа: да ги поправи гревовите и да го спаси светот."),
		 A("Да го казни грешникот по налог на светот (демоните: да го задржат во Лимбо)."),
		 A("Сака да се ослободи од Лимбо, а тоа е можно само ако некој се откупи.")],
		[P("Способности", CELL),
		 A("Брзо движење со импулс, автоматско пукање на пробојни стрели во најблискиот непријател, даш со "
		   "неповредливост (2 полнења), надградби."),
		 A("Го следи играчот без запирање, доаѓа во големи групи; посилните се побрзи и фрлаат светлосни копја."),
		 A("На 25%, 50% и 75% нуди избор од 3 надградби; лекува 1 срце.")],
		[P("Ограничувања", CELL),
		 A("3 срца; даш се полни 3 секунди; не цели рачно; стрелите се бавни на почеток."),
		 A("Слабо здравје (1-2 погодока); не минува низ ѕидови; бавно се врти."),
		 A("Не може да го напушти фенерот; не се бори.")],
		[P("Изглед", CELL),
		 A("Слаб, во искинат виолетов мантил со качулка, пепелно сива кожа, тиркизен шал и светечки тиркизни "
		   "рупки во телото."),
		 A("Лебдечки оклоп од бела и златна светлина, златни парчиња што кружат околу него, светечко јадро и "
		   "лице без црти."),
		 A("Висок, во дроњава сина качулка без лице, со тиркизен фенер на стап.")],
	]
	s.append(Spacer(1, 6))
	s.append(grid(rows, [93, 111, 123, 124], valign="TOP"))
	s.append(Spacer(1, 8))
	s.append(picture(IMG / "main_character_side.png", 210, 220))

	# ---------------------------------------------------------------- 4
	s.append(KeepTogether([
		P("Задача 4 - Ниво", HEAD),
		P("Нацртајте скица на нивото со почеток, пречки, награди и цел. Напишете кои можности се задолжителни за "
		  "првата верзија на играта. Тежината на нивото треба да се зголемува постепено"),
		Spacer(1, 7),
		picture(IMG / "level1_pride_sketch.png", 452, 300),
	]))
	for t in [
		"Движење од поглед одозгора (WASD или стрелки) со забрзување и инерција.",
		"Автоматско пукање на пробојни стрели кон најблискиот непријател.",
		"Даш (Shift): 2 полнења, секое се полни 3 секунди, со кратка неповредливост.",
		"Свети чувари што во бранови стигаат од рабовите и го следат играчот; допир = -1 срце (вкупно 3 срца).",
		"Секоја елиминација носи поени што го полнат Барот на гордост; на 25%, 50% и 75% се бира една надградба.",
		"Победа кога Барот е полн (се отвора излезот), пораз кога ќе се изгубат сите срца.",
		"Тежината расте во 4 етапи: бавни чувари, побрзи групи, чувари со копја, рој и елитен чувар.",
		"Почетен екран, пауза и крај на играта; 3 нивоа: Гордост, Алчност и Лимбо (откупување на Гордоста).",
	]:
		s.append(Paragraph(t, BUL, bulletText="•"))

	# ---------------------------------------------------------------- 5
	s += [P("Задача 5 - Ресурси", HEAD),
	      P("Пронајдете ги ресурсите (assets) што ќе ги користите и запишете ги во табелата."),
	      Spacer(1, 7)]
	tiny = link("https://kenney-assets.itch.io/tiny-dungeon")
	res = [
		[P("Ресурс", CELL_B), P("Извор (линк)", CELL_B)],
		[P("Главен лик", CELL), A("Kenney Tiny Dungeon (CC0), преобоен во виолетово: " + tiny +
		                          "<br/>Проектили: Bullet Collection 1 (CC0): " +
		                          link("https://opengameart.org/content/bullet-collection-1-m484"))],
		[P("Непријател", CELL), A("Свети чувари: Kenney Tiny Dungeon, оклопни ликови преобоени бело-златно: " + tiny +
		                          "<br/>Демони: Tiny Creatures (CC0): " +
		                          link("https://opengameart.org/content/tiny-creatures"))],
		[P("Подлога и платформи", CELL), A("Kenney Tiny Dungeon: подови, ѕидови и столбови: " + tiny)],
		[P("Позадина", CELL), A("Kenney Tiny Dungeon: подни плочки што се повторуваат: " + tiny)],
		[P("Предмети за собирање", CELL), A("Gems, Coins, etc. (CC0), за поените: " +
		                                    link("https://laredgames.itch.io/gems-coins-free") +
		                                    "<br/>Срца: Kenney Tiny Dungeon: " + tiny)],
		[P("Звуци", CELL), A("Kenney Sci-Fi Sounds (CC0): " + link("https://kenney.nl/assets/sci-fi-sounds") +
		                     "<br/>Kenney Interface Sounds: " + link("https://opengameart.org/content/interface-sounds") +
		                     "<br/>freesound.org (CC0): " + link("https://freesound.org/search/?q=hit+impact"))],
		[P("Музика", CELL), A("Boss Fight 2 (CC0): " + link("https://opengameart.org/content/boss-fight-2") +
		                      "<br/>Dark Cavern Ambient (CC0): " + link("https://opengameart.org/content/dark-cavern-ambient"))],
		[P("Интерфејс (поени, животи)", CELL), A("Pixel Healthbars and Hearts (CC0): " +
		                                         link("https://unbreaded.itch.io/pixel-health") +
		                                         "<br/>Kenney Pixel UI Pack: " + link("https://www.kenney.nl/assets/pixel-ui-pack"))],
	]
	s.append(grid(res, [143, 296]))
	s.append(Spacer(1, 15))
	s.append(P("Барајте на Kenney.nl, OpenGameArt.org, itch.io и freesound.org. Запазете ресурсите да ви бидат во ист "
	           "или сличен стил."))

	# ---------------------------------------------------------------- 6
	s += [P("Задача 6 - Повратна информација", HEAD),
	      P("Претставете ја играта на колегите околу вас. Побарајте едно нешто што им се допаѓа и едно што би го "
	        "смениле."),
	      P("На колегите им се допаѓа брзото движење со даш и тоа што секоја елиминација видливо го полни Барот на "
	        "гордост, па секогаш се гледа напредокот. Би смениле само едно: на почетокот на нивото да има "
	        "помалку чувари на екранот, за да има време да се научи движењето.", ANS)]

	# ---------------------------------------------------------------- 7
	summ = [
		[P("Дел", CELL_B), P("Ваш одговор", CELL_B)],
		[P("Наслов", CELL), A("PERFORATED")],
		[P("Идеја во една реченица", CELL),
		 A("Игра со поглед одозгора во стил на Vampire Survivors: убивај бранови свети чувари за да ги извршиш "
		   "седумте гревови, па поништи ги во Лимбо.")],
		[P("Целна група", CELL), A("Играчи 14+ што сакаат брзи акциони игри (Vampire Survivors, Hades) и темни приказни.")],
		[P("Приказна (почеток, средина, крај)", CELL),
		 A("<b>Почеток:</b> човек ги извршува седумте гревови, гонет од свети чувари.<br/>"
		   "<b>Средина:</b> проколнат е во Лимбо и ги поништува во обратен редослед, гонет од демони.<br/>"
		   "<b>Крај:</b> поништувајќи ја Гордоста, се жртвува и се раствора во светот, чистејќи го од омраза.")],
		[P("Главен лик", CELL), A("Безимениот: слаб, виолетов мантил, тиркизни рупки; горд, па кајлив.")],
		[P("Непријатели / NPC", CELL),
		 A("Свети чувари (Гревови), демони (Покајание). NPC: Превозникот, нуди надградби и лекува.")],
		[P("Основна механика и контроли", CELL),
		 A("WASD/стрелки: движење; Shift: даш; пукањето е автоматско. Елиминации = поени = полн бар на гревот; "
		   "на 25%, 50% и 75% се бира надградба.")],
		[P("Услов за победа", CELL), A("Барот на гордост се полни до 100% и се отвора излезот; по последното ниво "
		                               "ликот се раствора.")],
		[P("Услов за пораз", CELL), A("Се губат сите 3 срца (допир со чувар или копје); нивото почнува од почеток.")],
		[P("Скица на нивото", CELL), picture(IMG / "level1_pride_sketch.png", 255, 160)],
		[P("Што ја прави играта забавна?", CELL),
		 A("Брзо движење и даш низ рој непријатели, видлив напредок на барот, надградби и кратки нивоа.")],
		[P("Промена по повратната информација", CELL),
		 A("Етапа 1 сега почнува со само неколку бавни чувари, а поголемите групи доаѓаат подоцна.")],
		[P("Користени LLM разговори", CELL), A(link(LLM_LINK))],
	]
	s.append(KeepTogether([
		P("Задача 7 - Резиме", HEAD),
		P("Сумирајте сè од претходните задачи во табелата. Одговорите нека бидат кратки, табелата треба да собере "
		  "на една страница. Споделете ги разговорите со ВИ."),
		Spacer(1, 7),
		grid(summ, [180, 271]),
	]))

	# ---------------------------------------------------------------- 8 + instructions (original text)
	s += [P("Задача 8 - Имплементација во python", HEAD),
	      P("Со помош на ВИ, пробајте да ја имплементирате играта."),
	      P("Прикачување на вежбата и следни инструкции", HEAD),
	      P(f'Со завршување на лабораториската задача потребно е да ја прикачите на курсот - '
	        f'<link href="{UPLOAD_LINK}" color="{LINKCOL}"><u>Место за прикачување на лабораториска '
	        f'(дополнителна домашна).</u></link>'),
	      P("Дополнителна домашна од лабораториската вежба (PyGame)", HEAD),
	      P("Оние кои што сакаат, имаат можност лабораториската вежба да ја доработат како дополнителна домашна. "
	        "Со тоа што ќе треба да ја превземете вежбата од местото каде ја прикачивте и да ја доработите "
	        "најдоцна до вторник (03.11) до 23:59 часот."),
	      Spacer(1, 6),
	      P("Потребно е играта да има барем 3 нивоа, заедно со почетен екран, стопирање на играта (пауза) и "
	        "завршеток на истата. Внимавајте да се придржувате на приказната која ја дефиниравте во документот."),
	      Spacer(1, 6),
	      P("На следната лабораториска вежба ќе треба да ја испрезентирате играта, со тоа што повторно ќе ја "
	        "превземете од курсот. Соодветно, истата ќе биде оценета.")]

	doc.build(s)
	print("saved", OUT)


if __name__ == "__main__":
	build()
