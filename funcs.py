import requests, bs4 , os , hashlib
new_notice1  = "<doctype! HTML><head><title>StudMax Updates</title></head><body><h1>Updates on Moodle</h1><p>"
new_back = "</p><strong><em>Please note that the updates shown above may not be accurate. It is always better to check moodle.</em></strong></body>"
synced_courses = ''
new_notice = ''
loc = '..'
def hashit(file):
	BLOCKSIZE = 65536
	hasher = hashlib.md5()
	with open(file, 'rb') as afile:
		buf = afile.read(BLOCKSIZE)
		while len(buf) > 0:
			hasher.update(buf)
			buf = afile.read(BLOCKSIZE)
	return hasher.hexdigest()
def login( usr , psd):  # Starting a session
	s = requests.Session()
	url = 'https://courses.iitm.ac.in/login/index.php'
	s.get(url)
	login_data = dict(username=usr,password=psd)
	s.post(url,data=login_data,headers={'Referer':'https://courses.iitm.ac.in'})
	return s
def get_ext(icon): # For getting extension for download
	icon = icon.split('/')[-1]
	if icon=='document-24':
		return '.docx'
	elif icon=='powerpoint-24':
		return '.pptx'
	elif icon=='pdf-24':
		return '.pdf'
	elif icon=='archive-24':
		return '.zip'
	else :
		return ''
def read_data(): # For reading usr , psd and courses
    dataFile = open(os.path.join(loc,'src','inf.txt'))
    d = dataFile.read()
    d = d.strip()
    d = d.split('\n')
    return d[0],d[1],d[2:]
def download_it_in(link,c,topic_name,file_name,crse_name): #downloading a file
	res = c.get(link)
	res.raise_for_status()
	d_file = open(os.path.join(loc,'courses',crse_name,topic_name,file_name),'wb')
	#d_file = open('../courses/'+crse_name+'/'+topic_name+'/'+file_name,'wb')
	for chunk in res.iter_content(100000):
		d_file.write(chunk)
	d_file.close()
	z_file = open(os.path.join(loc,'src','info.txt'),'a')
	#z_file = open('../src/info.txt','a')
	z_file.write(link+'\n')
	z_file.close()
def log(summary,topic_name,crse_name,file_name):
	#os.listdir(os.path.join(loc,'courses',crse_name,topic_name))
	#os.mkdir(loc,'courses',crse_name,topic_name,'Advices')
	case = 0
	if 'Advices' not in os.listdir(os.path.join(loc,'courses',crse_name,topic_name)):
		os.mkdir(os.path.join(loc,'courses',crse_name,topic_name,'Advices'))
	if file_name + ' Advice.txt' in os.listdir(os.path.join(loc,'courses',crse_name,topic_name,'Advices')):
		fl = open(os.path.join(loc,'courses',crse_name,topic_name,'Advices',file_name+' Advice.txt'))
		#fl = open('../courses/'+crse_name+'/'+topic_name+'/Advices/'+file_name+' Advice.txt')
		fc = fl.read()
		fl.close()
		if fc == summary:
			case = 1
	if case == 0 :
		fp = open(os.path.join(loc,'courses',crse_name,topic_name,'Advices',file_name+' Advice.txt'),'w')
		#fp = open('../courses/'+crse_name+'/'+topic_name+'/Advices/'+file_name+' Advice.txt','w')
		fp.write(summary)
		global new_notice
		new_notice =  new_notice + '*' + ' New advice in ' + file_name +' Advice.txt' + ' in '+ topic_name +' of '+crse_name + '\n'
		fp.close()
	if os.listdir(os.path.join(loc,'courses',crse_name,topic_name,'Advices')) == []:
		os.rmdir(os.path.join(loc,'courses',crse_name,topic_name,'Advices'))
def start_activity(m,c,topic_name,crse_name): # Concendrating each activity seperately
	k = m.select('.activityinstance > a')
	z = open(os.path.join(loc,'src','info.txt'),'r')
	#z = open('../src/info.txt','r')
	y = z.read().split('\n')
	z.close()
	if k != []:
		#print('Activity Part A')
		link = m.select('.activityinstance > a')[0].get('href')
		file_name = m.select('.activityinstance > a > .instancename')[0].getText().split('File')[0].strip()
		icon = m.select('.activityinstance > a > img')[0].get('src')
		file_name = file_name + get_ext(icon)
		if m.select('.contentafterlink') != []:
			file_sum = m.select('.contentafterlink')[0].getText()
			if file_sum != '':
				log(file_sum,topic_name,crse_name,file_name)
		if file_name not in os.listdir(os.path.join(loc,'courses',crse_name,topic_name)) or link not in y:
			#os.path.join(loc,'courses',crse_name,topic_name)
			print('Downloading '+file_name)
			global new_notice
			new_notice = new_notice + '* ' + file_name + ' in ' + topic_name +' of ' + crse_name +'\n'
			download_it_in(link,c,topic_name,file_name,crse_name)
	else :
		#print('Activity Part B')
		file_name = m.get('id') + '.txt'
		file_sum = m.getText()
		if file_sum != '':
			log(file_sum,topic_name,crse_name,file_name)
	
def start_section(l,c,crse_name): # Each section concendration
	#print('Starting section')
	topic_name = l.get('aria-label')
	topic_summary = l.select('.content > .summary')[0].getText()
	print('Syncing with '+topic_name)
	if topic_name not in os.listdir(os.path.join(loc,'courses',crse_name)):
		#os.path.join(loc,'courses',crse_name)
		os.mkdir(os.path.join(loc,'courses',crse_name,topic_name))
	if topic_summary != '':
		log(topic_summary,topic_name,crse_name,topic_name)
	act = l.select('.content > ul > li')
	if act != []:
		for m in act:
			start_activity(m,c,topic_name,crse_name)
	if os.listdir(os.path.join(loc,'courses',crse_name,topic_name))==[]:
		os.rmdir(os.path.join(loc,'courses',crse_name,topic_name))
def start_course(id,c): # Analyses each course section by section
	tpl = 'https://courses.iitm.ac.in/course/view.php?id='
	r = c.get(tpl+id)
	soup = bs4.BeautifulSoup(r.text,"lxml")
	crse_name = soup.select('.navbar .breadcrumb > ul > li > a')[-1].getText()
	print('\nSyncing with '+crse_name+'\n')
	global synced_courses
	synced_courses = synced_courses + '-> ' + crse_name +'\n'
	if crse_name not in os.listdir(os.path.join(loc,'courses')):
		os.mkdir(os.path.join(loc,'courses',crse_name))
	li = soup.select('.course-content > ul > li')
	for l in li: 
		start_section(l,c,crse_name)
def fresh_download(): # For fresh download of courses
	usr,psd,courses = read_data()
	print('Logging In to Moodle : courses.iitm.ac.in')
	c = login(usr,psd)
	r = c.get('https://courses.iitm.ac.in/my/index.php?mynumber=-2')
	soup = bs4.BeautifulSoup(r.text,"lxml")
	print(soup.select('#page-header-wrapper')[0].getText())
	for id in courses:
		start_course(id,c)
	print('\nThe Following Courses are Synced:')
	print(synced_courses)
	if new_notice == '':
		print('\nNothing New')
		new_notice = new_notice + 'Nothin New'
	else :
		print('\nThings to Notice:')
		print(new_notice)
	new_log = new_notice1 + new_notice + new_back
	fp = open('../src/index.html',"r")
	if fp!=NULL:
		fp.write(new_log)
		fp.close()
