from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import psycopg2

# Словари
dict_ls = {
	"Безработные": "unemployed",
	"Беременность и роды": "pregnancy_and_childbirth",
	"Болезнь": "disease",
	"Выезд за границу": "travel_abroad",
	"Выход на пенсию": "retirement",
	"Декларирование доходов": "declaration",
	"Жильё": "housing",
	"Организация бизнеса": "business_organization",
	"Организация работы офиса": "office_work",
	"Организуем приусадебное хозяйство": "garden_land",
	"Открываем собственный бизнес": "own_business",
	"Оформление документов": "paperwork",
	"Покупка квартиры": "apartment_purchase",
	"Получение информации": "receiving_the_information",
	"Получение компенсаций": "obtaining_compensation",
	"Потеря и поиск работы": "job_search",
	"Предпринимательство": "business",
	"Прочее": "other",
	"Работа с персоналом": "work_personal",
	"Регистрация актов гражданского состояния": "civil_registration",
	"Смерть": "death",
	"Создание семьи": "marry",
	"Спорт и физическая культура": "sport",
	"Строим дом": "building_house",
	"Студенты": "students",
	"Транспортные средства": "vehicles",
}

dict_org = {
	'АУ "МФЦ" Алатырского района': 'alatrdistr',
	'АУ "МФЦ" Аликовского района': 'alikov',
	'АУ "МФЦ" Батыревского района': 'batyr',
	'АУ "МФЦ" Вурнарского района': 'vurnar',
	'АУ "МФЦ" г. Алатыря': 'alatr',
	'АУ "МФЦ" г. Канаша': 'gkan',
	'АУ "МФЦ" г. Новочебоксарска': 'novocheb',
	'АУ "МФЦ" г.Чебоксары': 'cheb',
	'АУ "МФЦ" г. Шумерли': 'shumerlya',
	'АУ "МФЦ" Ибресинского района': 'ibresi',
	'АУ "МФЦ" Канашского района': 'gkan',
	'АУ "МФЦ" Козловского района': 'kozlov',
	'АУ "МФЦ" Комсомольского района': 'komsml',
	'АУ "МФЦ" Красноармейского района': 'krarm',
	'АУ "МФЦ" Красночетайского района': 'krchet',
	'АУ "МФЦ" Мариинско-Посадского района': 'marpos',
	'АУ "МФЦ" Моргаушского района ЧР': 'morgau',
	'АУ "МФЦ" Порецкого района': 'porezk',
	'АУ "МФЦ" Урмарского района': 'urmary',
	'АУ "МФЦ" Цивильского района': 'zivil', # Сайта нет
	'АУ "МФЦ" Чебоксарского района': 'chebs',
	'АУ "МФЦ" Шемуршинского района': 'shemur',
	'АУ "МФЦ" Шумерлинского района': 'shumerdis',
	'АУ "МФЦ" Ядринского района': 'yadrin',
	'АУ "МФЦ" Яльчикского района': 'yaltch',
	'АУ "МФЦ" Янтиковского района': 'yantik',
}
# Соединение с БД
conn = psycopg2.connect("dbname='mfc' user='travis' host='localhost' password='scarsonbroadway'")
cur = conn.cursor()

main_link = "http://gosuslugi.cap.ru/"

# Список жизненных ситуаций
def get_lifesituations_list(url):
	soup = url_open(url)
	if soup == None:
		print("Страница не найдена")
	else:
		try:
			ls_list = soup.findAll("td", {"class": "ItemText"})[1:2]
			_id = 0
			for ls in ls_list:
				_id += 1
				situation = ls.find("a") 
				title = situation.get_text()
				alias = dict_ls[title]
				link = situation.attrs['href']
				print("\n\n<-- Жизненная ситуация -->\n" + title + "\n\n")
				get_serv_by_ls(link, alias)
				# cur.execute('INSERT INTO public.main_lifesituations (id, title, alias) VALUES(%s, %s, %s)', (_id, title, alias))
				# conn.commit()
		finally:
			cur.close()
			conn.close()

# Список услуг(процедур) для конкретной жизненной ситуации
def get_serv_by_ls(url, ls):
	soup =  url_open(url)
	if soup == None:
		print("Страница с данной услугой не найдена")
	else:
		serv_list = soup.find("a", {"id": "Spisok_predostavlyaemyh_uslug"})
		if serv_list != None:
			serv_list = serv_list.next_siblings
			for serv in serv_list:
				title = serv.get_text()
				link = serv.find("a").attrs["href"]
				print("\n<-- Услуга -->\n" + title + "\n")
				list_org = get_procedure_info(link) # Список организаций
				# if list_org != None:
				# 	for org in list_org:
				# 		if org in dict_org:
				# 			print(dict_org[org])

# Информация по данной процедуре
def get_procedure_info(url):
	soup = url_open(url)
	if soup == None:
		print("Страница с данной процедурой не найдена")
	else:
		# Название
		title = regex_table(soup, "Полное наименование услуги")
		if title != None:
			print("-- Полное наименование процедуры --\n" + title)
		
		# Список организаций
		list_org = None
		current_org = regex_table(soup, "Наименование органа власти, предоставляющего услугу")
		ls_orgs = soup.find("div", text = re.compile("Иные организации"), attrs = {"class": "Caption"})
		if ls_orgs != None:
			ls_orgs = ls_orgs.next_siblings
			list_org = [current_org,]
			for org in ls_orgs:
				org_link = org.find("a") 
				if org_link != None and not isinstance(org_link, int ):
					list_org.append(org_link.get_text())
			# Выведим список организации, предоставляющих данную процедуру
			print("\n-- Список организации --")
			for org in list_org:
				if org in dict_org:
					print(dict_org[org])			

		# Ссылки на общую информацию
		order_response = get_section_links(soup, "Порядок предоставления")
		appel = get_section_links(soup, "Обжалование")
		dop_info = get_section_links(soup, "Дополнительно")

		# Информация по разделам для процедуры
		if order_response != None:
			soup2 = url_open(order_response)
			if soup2 == None:
				print("-- Порядок предоставления отсутствует --")
			else:
				recipients = regex_table(soup2, "Кому предназначено")
				# print("-- Кому предназначено --")
				# print(recipients)
				docs = regex_table(soup2, "Перечень документов")
				# docs = soup.find("div", text = re.compile("Перечень документов"), attrs = {"class": "SICaption"})
				# if docs != None:
				# 	doc_text = docs.findNext('table').contents[0].find("strong", text = re.compile("Шаблоны документов:")).parent.previous_sibling.get_text()
				# 	print("Документы текст------\n" + doc_text)
				# print("-- Перечень документов --")
				# print(docs)
				cost = regex_table(soup2, "Стоимость и порядок оплаты")
				# print("-- Стоимость и порядок оплаты --")
				# print(cost)
				result = regex_table(soup2, "Результат предоставления услуги")
				# print("-- Результат предоставления услуги --")
				# print(result)
				time = regex_table(soup2, "Сроки предоставления услуги")
				# print("-- Сроки предоставления услуги --")
				# print(time)
				delay_cause = regex_table(soup2, "Основания для приостановления услуги или отказа в её предоставлении")
				# print("-- Основания для приостановления услуги или отказа в её предоставлении --")
				# print(delay_cause)

		if appel != None:
			soup2 = url_open(appel)
			if soup2 == None:
				print("-- Обжалование отсутствует --")
			else:
				order_appel = regex_table(soup2, "Обжалование")
				# print("-- Обжалование --")
				# print(order_appel)

		if dop_info != None:
			soup2 = url_open(dop_info)
			if soup2 == None:
				print("-- Дополнительная информация отсутствует --")
			else:
				info = regex_table(soup2, "Дополнительная информация")
				# print("-- Дополнительная информация --")
				# print(info)
		return list_org

			
# Попытка установить соединение по переданному url
def url_open(url):
	try:
		url = main_link + url
		html = urlopen(url)
		soup = BeautifulSoup(html, "html.parser")
		return soup
	except HTTPError as e:
		return None

# Поиск текста по заголовку
def regex_table(soup, regx):
	bs = soup.find("div", text = re.compile(regx), attrs = {"class": "SICaption"})
	if bs != None:
		return bs.findNext('table').contents[0].get_text()
	else:
		return None

# Ссылки на подразделы
def get_section_links(soup, name):
	link = soup.find("a", {"title": re.compile(name)})
	if link != None:
		return link.attrs["href"]
	else:
		return None

lf ="LifeSituations.aspx"
get_lifesituations_list(lf)