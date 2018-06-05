from flask import Flask, request, abort
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os, random, requests, re, time, threading, configparser, psycopg2, datetime, urllib.parse as urlparse

from linebot import (
	LineBotApi, WebhookHandler
)
from linebot.exceptions import (
	InvalidSignatureError
)
from linebot.models import*

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

# we can get config from the file named 'config.ini'
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])

dburl = urlparse.urlparse(os.environ['DATABASE_URL'])

# our website is named "app's name.herokuapp.com/"
@app.route('/')
def show():
	out = """<html>
	<head>
		<!-- Required meta tags -->
		<meta charset="utf-8">
		<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
		<style type="text/css">
			 body {
			 	padding-top: 20px;
			 	overflow-x: hidden;
			 }
			 .image{
			 	display: inline-block;
			 	float: left;
			 }
			 .modal:before {
			 	content: '';
			 	display: inline-block;
			 	height: 100%;
			 	vertical-align: middle;
			 }
			 .modal-dialog{
				display: inline-block;
				vertical-align: middle;
			}
			.paginationjs{
				padding-bottom: 20px;
			}
			.page-item.first.disabled,
			.page-item.prev.disabled,
			.page-item.last.disabled,
			.page-item.next.disabled{
				display: none;
			}
		</style>

		<!-- Bootstrap CSS -->
		<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
		<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.13.0/umd/popper.min.js"></script>
		<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/twbs-pagination/1.4.1/jquery.twbsPagination.min.js"></script>
		<title>PTT 表特</title>
	</head>
	<body style="background-color:gray;">
		<script defer>
			$(document).ready(function(){
				var pagination = $('#pagination'),
					totalRecords = 0,
					records = [],
					displayRecords = [],
					recPerPage = 24,
					nowPage = 1,
					totalPages = 1;

				$.ajax({
						url: "./data.json",
						async: true,
						dataType: 'json',
						cache: false,
						success: function (data) {
							records = data;
							console.log(records);
							totalRecords = records.length;
							totalPages = Math.ceil(totalRecords / recPerPage);
							pagination_init();
						}
					});

				function DataReload(){
					$.ajax({
							url: "../data.json",
							async: true,
							dataType: 'json',
							cache: false,
							success: function (data) {
								records = data;
								console.log(records);
								totalRecords = records.length;
								totalPages = Math.ceil(totalRecords / recPerPage);
								pagination_init();
							}
					});
				}

				function add_to_html(){
					var dataHtml = '';
					for (var i = 0; i < displayRecords.length; i++) {
							dataHtml += '<div class="col-lg-3 col-md-4 col-xs-6"><div class="image card border-info mb-3"><a href="#"><img class="card-img" src="' + displayRecords[i].url + 
								'" ptt_url="' + displayRecords[i].PTT_url + 
								'" title="' + special_char(displayRecords[i].title) + '"></a></div></div>';
					};
					$('#list').html(dataHtml);
				}

				function special_char(text){
					return text.replace(/ /g,'&nbsp;').replace(/'/g, '&#39;').replace(/"/g, '&quot;');
				}

				function pagination_init(){
					pagination.twbsPagination('destroy');
					pagination.twbsPagination({
						totalPages: totalPages,
						visiblePages: 6,
						startPage: nowPage,
						first: "&lt;&lt;",
						prev: "&lt;",
						next: "&gt;",
						last: "&gt;&gt;",
						onPageClick: function (event, page) {
							displayRecordsIndex = Math.max(page - 1, 0) * recPerPage;
							endRec = (displayRecordsIndex) + recPerPage;

							displayRecords = records.slice(displayRecordsIndex, endRec);
							add_to_html();
							if(nowPage != page){
								$('body').scrollTop(0);
								nowPage = page;
								DataReload();
								add_to_html();
							}

							var imagesArray = $("img.card-img").map(function(){
								return $(this);
							}).get();

							$(".carousel-item").remove();

							function get_modal_img_size(url){
								var webWidth = document.body.clientWidth;
								var webHeight = document.body.clientHeight;
								var maxW = webWidth * 0.9;
								var maxH = webHeight * 0.9 - 100;
								var img = new Image();
								img.src = url;
								img.onload = function(){}
								var ratioW = img.width / maxW;
								var ratioH = img.height / maxH;

								if(ratioH > 1 || ratioW > 1){
									if(ratioH > ratioW){
										img.height = maxH;
										img.width /= ratioH;
									}
									else{
										img.width = maxW;
										img.height /= ratioW;
									}
								}
								return { width: img.width, height: img.height };
							}

							function set_modal_size(size){
								$('body').css('overflow', 'auto');
								$('.modal-body').css('overflow', 'auto');
								$('.modal-content').css('height', size.height + 100);
								$('.modal-body').css('height', size.height);

								var movW = size.width + 50;
								$('.modal-content').css('width', movW);
								$('.modal-header').css('width', movW);
								$('.modal-body').css('width', movW);
								$('#header-container').css('width', movW);
								$('#myModal').modal('show');

								$('#myModal').css('padding-left', (document.body.clientWidth - movW) / 2);
							}

							function set_modal_detail(t){
								var ptt_url = t.attr('PTT_url');
								var imgsrc= t.attr('src');
								var title = t.attr('title');
								
								$("#open-in-PTT").attr('href', ptt_url);
								$("#open-in-PTT").text(title);
								$('#open-source-img').attr('href', imgsrc);
							};

							var item_array = $(".carousel-item > img").map(function(){
								return $(this);
							}).get();

							$(".card-img").click(function(e){
								e.preventDefault(); // make sure it would not auto scroll to top
								$('#myCarousel').carousel('cycle');
								var this_imgsrc = $(this).attr('src');
								if(item_array.length <= 1){
									var size = get_modal_img_size(this_imgsrc);
									$(".carousel-inner").html('<div class="carousel-item active"><img id="full-img">');
									var clickImg = $('#full-img');
									clickImg.attr('src', this_imgsrc);
									clickImg.attr('PTT_url', $(this).attr('PTT_url'));
									clickImg.attr('title', $(this).attr('title'));
									clickImg.height(size.height);
									clickImg.width(size.width);
									var doc = '';
									for(var i = 0; i < imagesArray.length; ++i){
										if(imagesArray[i][0].src == this_imgsrc){
											for(var j = i + 1; ; ++j){
												if(j >= imagesArray.length) j = 0;
												var img = imagesArray[j];
												if(img.attr('src') == this_imgsrc)break;
												size = get_modal_img_size(img.attr('src'));
												doc += '<div class="carousel-item"><img id="full-img" src="' +
													 img.attr('src') + '" PTT_url="' + img.attr('PTT_url') + '" title="' +
													 img.attr('title') + '" style="height: ' + size.height + 'px; width: ' +
													 size.width + 'px;"' + '"></div>';
											}
											break;
										}
									}
									$(".carousel-inner").append(doc);
									item_array = $(".carousel-item > img").map(function()
									{
										return $(this);
									}).get();
								}
								else{
									$('.carousel-item').removeClass('active');
									for(var i = 0; i < item_array.length; ++i){
										if(item_array[i][0].src == this_imgsrc){
											item_array[i].parent().attr('class', 'carousel-item active');
											break;
										}
									}
								}
								$('.active > img').on("load", function(){
									set_modal_detail($(this));
									set_modal_size({ width: $(this).width(), height: $(this).height() });
								}).attr('src', this_imgsrc);
							});

							$('#myCarousel').on('slide.bs.carousel', function (e) {
								$('.carousel-item > .active').removeClass('active');
								var item = $(e.relatedTarget).children();
								set_modal_detail(item);
								set_modal_size({ width: item.width(), height: item.height() });
							});

							$("#myModal").click(function(e){
								$('body').css('overflow', 'auto');
								if(!$(e.target).closest('.modal-content').length) {
									for(var i = 0; i < imagesArray.length; ++i){
										if($('.carousel-item.active > #full-img').attr('src') == imagesArray[i].attr('src')){
											var img_item = imagesArray[i];
											var window_top = $(window).scrollTop();
											var window_bottom = window_top + document.body.clientHeight;
											var img_top = img_item.offset().top;
											var img_bottom = img_top + img_item.height();
											if(img_top < window_top || img_bottom > window_bottom)
												$("body").animate({
													scrollTop: img_item.offset().top - 20
												}, 300);
											$('#myCarousel').carousel('pause');
											break;
										}
									}
								}
							});

							$(".carousel-control-next").click(function(e){
								e.preventDefault();
							});

							$(".carousel-control-prev").click(function(e){
								e.preventDefault();
							});
						}
					});
				}
			});

			$(document).keydown(function(e) {
				if ($('#myModal').is(':visible')){
					// Previous
					if (e.keyCode === 37) {
						$(".carousel-control-prev").click();
						return false;
					}
					// Next
					if (e.keyCode === 39) {
						$(".carousel-control-next").click();
						return false;
					}
					// Close
					if(e.keyCode == 27){
						$('#myModal').modal('hide');
						var imagesArray = $("img.card-img").map(function(){
							return $(this);
						}).get();
						for(var i = 0; i < imagesArray.length; ++i){
							if($('.carousel-item.active > #full-img').attr('src') == imagesArray[i].attr('src')){
								imagesArray[i].get(0).scrollIntoView();
								$('#myCarousel').carousel('pause');
								break;
							}
						}
						return false;
					}
				}
			});
		</script>
		<!-- Modal -->
		<div class="modal fade" id="myModal" role="dialog">
			<div class="modal-dialog" role="document">
				<div class="modal-content">
					<div class="modal-header">
						<div id="header-container" align="center" valign="center">
							<a id="open-in-PTT" target="_blank" title="開啟圖片所在PTT文章"></a>
						</div>
						<a id="open-source-img" target="_blank" title="在新視窗開啟圖片">
							<img async src="http://ciappara.com/blog/wp-content/uploads/2014/11/link-new-tab.png" width="20" height="20">
						</a>
					</div>
					<div class="modal-body" align="center" valign="center">
						<div id="myCarousel" class="carousel slide" data-ride="carousel">
							<div class="carousel-inner">
							</div>
							<a class="carousel-control-prev" href="#" role="button" data-slide="prev" onclick="$('#myCarousel').carousel('prev')">
								<span class="carousel-control-prev-icon" aria-hidden="true"></span>
								<span class="sr-only">Previous</span>
							</a>
							<a class="carousel-control-next" href="#" role="button" data-slide="next" onclick="$('#myCarousel').carousel('next')">
								<span class="carousel-control-next-icon" aria-hidden="true"></span>
								<span class="sr-only">Next</span>
							</a>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div class="container">
			<div id="list" class="row">
			</div>
		</div>
		<div id="pager">
			<ul id="pagination" class="pagination justify-content-center"></ul>
		</div>
	</body>
</html>
"""
	return out

@app.route('/ping')
def forPing():
	return 'PING'

def valid_title(title):
	key = ['\\', '\"', '\'', '/']
	for k in key:
		if k in title:
			title = title.replace(k, '\\' + k)
	return title

#return database data to a json for html
@app.route('/data.json')
def to_json():
	json_content = ''
	try:
		con = connect_init()
		cur = con.cursor()
		cur.execute("SELECT * FROM img_table ORDER BY upload_date DESC, id ASC;")
		ans = cur.fetchall()

		json_format = '{{"url":"{}","PTT_url":"{}","title":"{}"}},'

		for data in ans:
			json_content += json_format.format(data[1], data[4], valid_title(data[2]))

		cur.close()
	except Exception as e:
		if con:
			con.rollback()
	finally:
		con.close()
	return '[{}]'.format(json_content[:-1])

@app.route("/callback", methods=['POST'])
def callback():
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)

	# handle webhook body
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)

	return 'OK' 

# database connection
def connect_init():
	return psycopg2.connect(
			dbname=dburl.path[1:],
			user=dburl.username,
			password=dburl.password,
			host=dburl.hostname,
			port=dburl.port)

# select something from table
# if can find something, means that the table exist
def tableExist(table):
	exist = False
	try:
		con = connect_init()
		cur = con.cursor()
		cur.execute("SELECT * FROM {};".format(table))
		cur.close()
		exist = True
	except psycopg2.DatabaseError as e:
		print('exist Error %s' % e)
		if con:
			con.rollback()
	finally:
		con.close()

	return exist

# url is already in database
def inDB(url):
	exist = False
	con = connect_init()
	cur = con.cursor()
	try:
		
		cur.execute("SELECT * FROM img_table WHERE url='{}';".format(url))
		ans = cur.fetchone()

		# if url doesn't exist in database, ans = None
		exist = ans != None

		cur.close()
	except Exception as e:
		print('inDB', e)
		if con:
			con.rollback()
	finally:
		con.close()
	return exist

# use id in img_table to get image url
def get_img(id):
	if id > get_row_count('img_table') or id < 0:
		return ''
	con = connect_init()
	cur = con.cursor()
	cur.execute("SELECT url, article_url FROM img_table WHERE id={};".format(id))
	(url, article_url) = cur.fetchone()
	cur.close()
	con.close()
	return (url, article_url)

def random_get_img():
	return get_img(random.randint(0, get_row_count('img_table') - 1))

# for test
def get_last_img():
	con = connect_init()
	cur = con.cursor()
	cur.execute("SELECT url, title FROM img_table WHERE upload_date = (SELECT MAX(upload_date) FROM img_table);")
	(url, title) = cur.fetchone()
	cur.close()
	con.close()
	return (url, title)

# delete every element after footer
def delete_down(url):
	#class of footer's split line named 'r-list-sep'
	if 'r-list-sep' in url:
		return url[:url.index('r-list-sep')]
	return url

# capture every links and titles from a url
def article_capture(index_url, rs):
	articles = []
	index_list = []

	# we append url in index_list first
	index_list.append(index_url)

	while index_list:
		# every time we in this loop, we will pop out the top item from index_list
		# this can make sure it wouldn't crush if PTT is busy
		index = index_list.pop(0)

		res_next = rs.get(index, verify=False)

		# Page doesn't exist
		if res_next.status_code == 404:
			print('Not exist')
			return articles

		# PTT is busy, we add index to index_list
		# so that it could reload next time when PTT doesn't busy anymore
		elif res_next.status_code != 200:
			print('Busy')
			index_list.append(index)

		# find articles from this page
		else:
			# get the soup before footer
			soup_next = BeautifulSoup(delete_down(res_next.text), 'html.parser')

			# articles' class named "r-ent"
			for r_ent in soup_next.find_all(class_="r-ent"):
				try:
					# get article's url
					url = r_ent.find('a')['href']

					# sometimes article could be deleted, so we have to check whether url is exist
					if url:
						# if article's url exists, than we get its complete url(defult url is relative url) and title
						title = r_ent.find(class_="title").text.strip()
						url_link = 'https://www.ptt.cc' + url
						articles.append([url_link, title])
				except Exception as e:
					print('delete', e)
	return articles

# craw the lastest article from any board
def ptt_craw(board):
	rs = requests.session()
	
	# some boards have over18 check
	load = {
		'from': '/bbs/{}/index.html'.format(board),
		'yes': 'yes'
	}
	res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=load)
	
	# after we cross over18, we soup it
	soup = BeautifulSoup(res.text, 'html.parser')

	# board's lastest page
	lastest_page_url = 'https://www.ptt.cc/bbs/{}/index.html'.format(board)

	now_page_number = get_page_number(lastest_page_url, rs)

	articles = article_capture(lastest_page_url, rs)

	# if all articles in the page are deleted, than we craw last page till we find article or no more page
	while len(articles) < 1 and now_page_number > 0:
		now_page_number -= 1
		articles = article_capture('https://www.ptt.cc/bbs/{}/index{}.html'.format(board, now_page_number))

	return articles

def last_article(board):
	articles = ptt_craw(board)
	if len(articles) < 1:
		return articles
	# return (
	#			'last article's title\nlast article's url',
	#			 last article's images(it could be empty list if the article doesn't have any image)
	#		 )
	return '{}\n{}'.format(articles[-1][1], articles[-1][0]), find_img(articles[-1][0])

def whole_page(board):
	articles = ptt_craw(board)
	if len(articles) < 1:
		return articles
	# return (
	#			'article's title\narticle's url',
	#			 article's images(it could be empty list if the article doesn't have any image)
	#		 )
	return ['{}\n{}'.format(article[1], article[0]) for article in articles], [find_img(article[0]) for article in articles]

# when the url is started by http, than set it to https(Line doesn't support http)
def replace_to_https(url):
	if not url.startswith('https'):
		return url.replace('http', 'https')
	return url

# make sure every captured image's url
def image_url(url):
	# legal ends of image url 
	image_seq = ['.jpg', '.png', '.gif', '.jpeg']
	for seq in image_seq:
		if url.endswith(seq):
			return url

	# not a legal url, it may end by '.' (ilegal)
	url = url.rstrip('.')

	# not a img type(maybe a mp4?)
	if url[url.rfind('/'):].rfind('.') > -1:
		return ''

	# some url in imgur doesn't have the type of file, like "https://imgur.com/xxx"
	# we have to add a type for it so that LineBot can working(Default is '.jpg')
	if 'imgur' in url:
		return '{}.jpg'.format(url)

	# url is not in imgur
	return ''

# find every image's url from imgur
def find_img(url):
	imgs = []
	soup = BeautifulSoup(requests.get(url).text, 'html.parser')

	# use regular expression to find links of images in imgur.com
	# url may be http or https, and Line only support https
	# url may be i.imgur or just imgur
	for img_url in soup.findAll('a', {'href':re.compile('https?://(i.)?imgur.com/.')}):
		try:
			# get image's legal url
			imgurl = image_url(img_url['href'])

			# if the url is in imgur, than we add it into list
			if len(imgurl) > 0:
				imgs.append(replace_to_https(imgurl))
		except:
			print('image url capture failed!')
	return imgs

# find all images, article titles, and upload date from one page in board 'Beauty'
def get_data(page):
	article_list = []
	page_source_code = requests.get('https://www.ptt.cc/bbs/Beauty/index{}.html'.format(page)).text
	soup = BeautifulSoup(page_source_code, 'html.parser')

	common_date_format = '%a %b %d %H:%M:%S %Y'
	special_date_format = '%m/%d/%Y %H:%M:%S'

	# find all <a> tags under class named 'r-ent'(article's class name)
	for article in soup.select('.r-ent a'):
		title = article.text.strip()
		if '[正妹]' in title:
			article_url = 'https://www.ptt.cc' + article['href']
			try:
				article_source_code = requests.get(article_url).text
				article_soup = BeautifulSoup(article_source_code, 'html.parser')

				# find all <div> tags if class named 'article-metaline'(date's class name)
				title_lines = article_soup.findAll('div', {'class':"article-metaline"})

				upload_date = ''

				# datetime is the last item of all article-meta-value
				# time format has mutiple types
				for title_line in title_lines[::-1]:
					title_line_text = title_line.text
					if '時間' in title_line_text:
						upload_date = title_line_text[title_line_text.find('時間') + 2:]
						break

				upload_date_SQL_datetime_type = ''
				if len(upload_date) < 1:
					content = article_soup.find(id='main-content').text
					t = content[content.find('時間:') + 3:]
					upload_date = t[:t.find('\n')].strip()
					try:
						datetime.datetime.strptime(upload_date,common_date_format).isoformat()
					except Exception as e:
						down = article_soup.findAll('span', {'class':"f2"})
						for d in down[::-1]:
							t = d.text
							if '※ 編輯:' in t:
								upload_date = t[t.find(',') + 1:].strip()
								try:
									upload_date_SQL_datetime_type = datetime.datetime.strptime(upload_date,common_date_format).isoformat()
								except Exception as e:
									try:
										upload_date_SQL_datetime_type = datetime.datetime.strptime(upload_date,special_date_format).isoformat()
									except Exception as e:
										print('{} is not {} format'.format(upload_date, special_date_format))
								break
				if len(upload_date_SQL_datetime_type) < 1:
					try:
						upload_date_SQL_datetime_type = datetime.datetime.strptime(upload_date,common_date_format).isoformat()
					except Exception as e:
						print('Set article date Error: {}, Article is {}'.format(e, title))
				article_list.append([article_url, title, upload_date_SQL_datetime_type]) 
				#article_list.append([article_url, title, upload_date_SQL_datetime_type, article_url])
			except Exception as e:
				print('Get article data Error: {}, Article is {}'.format(e, title))

	# data[0]: image's url[s](A url list)
	# data[1]: image's title
	# data[2]: image's article upload date
	# data[3]: image's article url
	data = []

	for article in article_list:
		urls = find_img(article[0])
		if len(urls) > 0:
			data.append([urls, article[1], article[2], article[0]])
	return data

# database's data count
def get_row_count(table):
	try:
		con = connect_init()
		cur = con.cursor()
		cur.execute("SELECT id FROM {};".format(table))
		num = cur.fetchall()
		cur.close()
		con.close()
		return len(num)
	except:
		return 0

# craw board 'Beauty'
def ptt_Beauty():
	now_page_number = get_page_number('https://www.ptt.cc/bbs/Beauty/index.html', requests.session())
	contents = get_data(now_page_number)
	con = connect_init()
	cur = con.cursor()

	num = get_row_count('img_table')

	print('Image Crawing')

	# max database size = 9990
	max_size = 9990
	if num < max_size:
		insert_query = "INSERT INTO img_table(id, url, title, upload_date, article_url) VALUES({}, '{}', '{}', '{}', '{}');"
		while num < max_size and now_page_number > 0:
			try:
				# if last images(we craw from first images) in last page and last page doesn't in database
				# we craw this page
				if not (inDB(contents[-1][0][-1]) and inDB(contents[0][0][-1])):
					for content in contents:
						if num >= max_size:
							break
						for img in content[0]:
							if num >= max_size:
								break
							try:
								if not inDB(img):
									cur.execute(insert_query.format(num, img, content[1], content[2], content[3]))
									con.commit()
									num = get_row_count('img_table')
							except Exception as e:
								print('DB Insert Error: %s' % e, insert_query.format(num, img, content[1], content[2], content[3]))
								if con:
									con.rollback()
			except Exception as e:
				print('Get content Error: %s\ncontent is ' % e, contents)
			print('Now database size: {}, End insert page: {}'.format(num, now_page_number))
			now_page_number -= 1
			contents = get_data(now_page_number)
	elif num == max_size:
		update_query = "UPDATE img_table SET url='{}', title='{}', upload_date='{}', article_url = '{}'\
						 WHERE id = (SELECT MIN(id) FROM img_table\
										WHERE upload_date = (SELECT MIN(upload_date) FROM img_table));"
		try:
			print('Last article:', contents[-1][1])
			while not inDB(contents[-1][0][-1]):
				print('Update!')
				for content in contents:
					try:
						output = False
						for img in content[0]:
							if not output:
								print('Now confirm if {} is in Database'.format(content[1]))
							if not inDB(img):
								if not output:
									print('Update {} into database'.format(content[1]))
								cur.execute(update_query.format(img, content[1], content[2], content[3]))
								con.commit()
								num = get_row_count('img_table')
							elif not output:
								print('Article {} is in Database'.format(content[1]))
							output = True
					except Exception as e:
						print('here: %s' % e, update_query.format(img, content[1], content[2], content[3]))
						if con:
							con.rollback()
				print('Now database size: {}, End update page: {}'.format(num, now_page_number))
				now_page_number -= 1
				contents = get_data(now_page_number)
		except Exception as e:
			print('Get content Error: %s\ncontent is ' % e, contents)
		print('End Update!')

	cur.close()
	con.close()

# find page number
def get_page_number(index_url, rs):
	# text of board's source code
	board_code = rs.get(index_url, verify=False).text

	board_soup = BeautifulSoup(board_code, 'html.parser').select('.btn.wide')

	last_page_url = ''
	for btn in board_soup:
		if '上頁' in btn.text:
			try:
				last_page_url = btn['href']
			except Exception as e:
				print(e)

	if len(last_page_url) > 0:
		# https://www.ptt.cc/bbs/{ board name }/index{ last page number }.html
		return int(last_page_url[last_page_url.rfind('x') + 1: last_page_url.rfind('.')]) + 1

	# this is the first page
	return 0

# auto push a random image in database to a user per delay second
def autoPush(delay, user_id):
	lastTime = time.time()
	while True:
		if time.time() - lastTime >= delay:
			(url, article_url) = random_get_img()
			line_bot_api.push_message(
			user_id, 
			ImageSendMessage(
				original_content_url=url,
				preview_image_url=url))
			lastTime = time.time()

class autoPushThread(threading.Thread):
	def __init__(self, delay, user_id):
		threading.Thread.__init__(self)
		self.delay = delay
		self.user_id = user_id
	def run(self):
		autoPush(self.delay, self.user_id)

def inThreadDB(board):
	exist = False
	con = connect_init()
	cur = con.cursor()
	try:
		cur.execute("SELECT * FROM thread_table WHERE board='{}';".format(board))
		ans = cur.fetchone()

		# if url doesn't exist in database, ans = None
		exist = ans != None

		cur.close()
	except Exception as e:
		print('inDB', e)
		if con:
			con.rollback()
	finally:
		con.close()
	return exist

def less_use_board():
	con = connect_init()
	cur = con.cursor()
	board = ''
	try:
		cur.execute("SELECT board, id FROM thread_table;")
		(boards, ids) = cur.fetchall()
		max = 0
		for i in range(len(ids)):
			if max < ids[i].split(',') + 1:
				max = ids[i].split(',') + 1
				board = boards[i]

	except Exception as e:
		print('inThreadDB', e)
		if con:
			con.rollback()

	cur.close()
	con.close()

	return board

def add_in_thread_table(board, id):
	max_size = 10
	con = connect_init()
	cur = con.cursor()
	if num < max_size:
		insert_query = "INSERT INTO thread_table(board, id) VALUES('{}', '{}');"
		try:
			cur.execute(insert_query.format(board, id))
			con.commit()
		except Exception as e:
			print('Thread DB Insert Error: %s' % e, insert_query.format(board, id))
			if con:
				con.rollback()
	# elif num == 10:
	# 	if 
	# 	update_query = "UPDATE thread_table SET board='{}', id='{}' WHERE board = " + less_use_board() + ";"
	# 	attr
	cur.close()
	con.close()

def message_job(event):
	cmd = event.message.text.upper().split(' ')
	text = cmd[0]
	if len(cmd) == 1:
		if text == '抽':
			try:
				(url, article_url) = random_get_img()
				line_bot_api.push_message(
					event.source.user_id, 
					ImageSendMessage(
						original_content_url=url,
						preview_image_url=url))
			except Exception as e:
				line_bot_api.reply_message(
				event.reply_token,[
					TextSendMessage(text = '資料更新中!'),
					StickerSendMessage(package_id = 2,sticker_id = 18)])
		elif text.isdigit():
			try:
				(url, article_url) = get_img(int(text))
				line_bot_api.push_message(
					event.source.user_id, 
					ImageSendMessage(
						original_content_url=url,
						preview_image_url=url))
			except Exception as e:
				line_bot_api.push_message(
					event.source.user_id,
					TextSendMessage(text = '超出資料庫大小!'))
		elif text == 'INFO':
			line_bot_api.reply_message(
				event.reply_token,[
				TextSendMessage(text = '指令 : \n輸入看板名稱(英文)以查詢最新文章\n例如Gossiping : 八卦版\n' + 'NBA : NBA版\n' + 'Beauty : 表特版\n' +
									   '注意 : \n有時候等比較久屬於正常狀況，\n' + '若30秒後無反應請再按一次。'),
				StickerSendMessage(package_id = 1,sticker_id = 120)])
		elif text == 'DB':
			line_bot_api.push_message(
					event.source.user_id,
					TextSendMessage(text = '資料庫大小: {}筆資料'.format(get_row_count('img_table'))))
		elif text == 'LAST':
			(url, title) = get_last_img()
			line_bot_api.push_message(
					event.source.user_id,
					TextSendMessage(text = title))
			line_bot_api.push_message(
					event.source.user_id, 
					ImageSendMessage(
						original_content_url=url,
						preview_image_url=url))
		elif text == 'ALL':
			line_bot_api.push_message(
						event.source.user_id,
						TextSendMessage(text = '目前自動推送有{}版'.format(get_row_count('thread_table'))))
		elif text == 'WHOLE':
			try:
				(article, imgs) = whole_page('Beauty')
				for i in range(len(article)):
					line_bot_api.push_message(
						event.source.user_id,
						TextSendMessage(text = 'Beauty版最新一頁文章\n' + article[i]))
					for url in imgs[i]:
						line_bot_api.push_message(
							event.source.user_id, 
							ImageSendMessage(
								original_content_url=url,
								preview_image_url=url))
			# not a define instruction
			except Exception as e:
				line_bot_api.reply_message(
					event.reply_token,[
						TextSendMessage(text = '請打指令 : \n看板名稱(英文)或輸入Info查看資訊'),
						StickerSendMessage(package_id = 1,sticker_id = 113)])
				print('Instruction Error: ', e)
		else:
			# if the message is some board name
			# post back the lastest article's title, url, and images(if it has) to user
			try:
				(article, imgs) = last_article(text)
				line_bot_api.push_message(
					event.source.user_id,
					TextSendMessage(text = text + '版最新文章\n' + article))
				for url in imgs:
					line_bot_api.push_message(
						event.source.user_id, 
						ImageSendMessage(
							original_content_url=url,
							preview_image_url=url))
			# not a define instruction
			except Exception as e:
				line_bot_api.reply_message(
					event.reply_token,[
						TextSendMessage(text = '請打指令 : \n看板名稱(英文)或輸入Info查看資訊'),
						StickerSendMessage(package_id = 1,sticker_id = 113)])
				print('Instruction Error: ', e)
	elif len(cmd) == 2:
		sub_cmd = cmd[1]
		if sub_cmd == 'AUTO' and not text.isdigit():
			if text != '抽':
				try:
					(whole_articles, whole_img) = whole_page(text)

					con = connect_init()
					cur = con.cursor()

					add_in_thread_table(text, event.source.user_id)

				except Exception as e:
					line_bot_api.reply_message(
						event.reply_token,[
							TextSendMessage(text = '請打指令 : \n看板名稱(英文)或輸入Info查看資訊'),
							StickerSendMessage(package_id = 1,sticker_id = 113)])
					print('Instruction Error: ', e)
			else:
				autothread = autoPushThread(60, event.source.user_id)
				autothread.start()
		elif sub_cmd == 'LEAVE':
			pass

# every message has a thread
class messageThread (threading.Thread):
	def __init__(self, event):
		threading.Thread.__init__(self)
		self.event = event
	def run(self):
		message_job(self.event)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
	try:
		t = messageThread(event)
		t.start()
	except:
		print("Error: unable to start thread")

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
	line_bot_api.reply_message(
		event.reply_token,
		StickerSendMessage(
			package_id=event.message.package_id,
			sticker_id=event.message.sticker_id)
	)

def auto_craw(delay):
	ptt_Beauty()
	lastTime = time.time()
	while True:
		if time.time() - lastTime >= delay:
			ptt_Beauty()
			lastTime = time.time()

# every delay second update database
class auto_craw_thread (threading.Thread):
	def __init__(self, delay):
		threading.Thread.__init__(self)
		self.delay = delay
	def run(self):
		auto_craw(self.delay)

def create_tables():
	con = connect_init()
	cur = con.cursor()

	# create table if table doesn't exist
	if not tableExist('img_table'):
		cur.execute("CREATE TABLE img_table (id SMALLINT PRIMARY KEY, url TEXT, title TEXT, upload_date TIMESTAMP, article_url TEXT);")
		con.commit()

	# create table if table doesn't exist
	if not tableExist('thread_table'):
		cur.execute("CREATE TABLE thread_table (board TEXT PRIMARY KEY, id TEXT);")
		con.commit()

	cur.close()
	con.close()

if __name__ == "__main__":
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
	
	create_tables()

	t = auto_craw_thread(60)
	t.start()
	app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))