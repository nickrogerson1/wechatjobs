import re
from googletrans import Translator



# text ='''
# DB: 🌀FULL SCHOLARSHIP AVAILABLE IN; 🇨🇳CHINA 🇨🇦 CANADA 🍑🍑🍑China🇨🇳🇨🇳 💌X2 visa without classes ( you don't have to exit) 💌Tourist L visa 💌Business M visa 💌Working Z visa . 1 year 💌Family Q or S visa 30 days 💌Visa On Arrival 30 days 🍑🍑🍑Canda🇨🇦🇨🇦 💌Permanent Residence visa 💌Work permit and visa 💌Study permit and visa ❇️DIPLOMA❇️BACHELOR❇️MASTERS❇️PHD STUDENTS 🛑UNIVERSITIES IN CANADA ❇️University Of Alberta ❇️University Of Toronto ❇️University Of Waterloo ❇️Mcgill University ❇️Queen University ❇️York University 🛑UNIVERSITIES IN CHINA ❇️Wuhan University ❇️Shanghai university ❇️Jiangxi University ❇️Guizhou University ❇️Henan University ❇️Hebei University 🛑SCHOLARSHIP COVERS TUITION AND ACCOMMODATION FREE WITH MONTHLY ALLOWANCE, HEALTH INSURANCE AND VISA ASSISTANCE ❇️ENGLISH TAUGHT Admission Notice within 14days and JW202 within 14 days #Aged 18-45 Deadline: As Seats Full..!!🚫 💯 confirmed[OK] 🈴 Certificate purchase 🈴HSK 1-5 NON APPEARANCE 🈴IELTS CERTIFICATE 🈴TESOL 🈴TEfL 🈴CELTS 🈴GMAT 🈴MCAT 🈴PSGE 🈴PU INVITATION LETTER 🈴TE INVITATION LETTER 🈴OVERSTAY CLEARANCE For More Details Contact us 
# '''



MIN_CHINESE_CHAR_COUNT = 10
MIN_WORD_COUNT = 12

def do_word_count(text):
    # [ Word Count **Met**, Translate]
 
    if re.search(u'[\u4e00-\u9fff]', text):
        print('Its Chinese')
        print(f'WORD LEN: {len(text)}')
        return [False, True] if len(text) > MIN_CHINESE_CHAR_COUNT else [True, True]
        
    word_count = len(text.strip().split(' '))
    print(f'WORD LEN: {word_count}')

    # if re.search('[а-яА-Я]', text):
    try:
    # False positive if they use emojis and icons
        text.encode().decode('ascii')
        return [False, False] if word_count > MIN_WORD_COUNT else [True, False]
    except UnicodeDecodeError:
        print('Its NOT English')
        return [False, True] if word_count > MIN_WORD_COUNT else [True, True]
            
        



def text_parser(text):

    text = text.lower() 

    lang_check = do_word_count(text)
    trans = ''

    if lang_check[0]:
        print(f'Text: {text}')
        print(f'TEXT TOO SHORT!!')
        return ['Not Long Enough', '', '', '', '']


    if lang_check[1]:
        translator = Translator()
        trans = translator.translate(text).text
        print(trans)
   

    # Check for cities
    py_cities = (r'an\s?kang', r'an\s?qing', r'an\s?shan', r'an\s?shun', r'an\s?yang', r'bai\s?cheng', r'bai\s?se', r'bai\s?shan', r'bai\s?yin', r'bao\s?ding', r'bao\s?ji', r'bao\s?shan', r'bao\s?tou', r'bayannur', r'ba\s?zhong', r'bei\s?hai', r'bei\s?jing', r'beng\s?bu', r'ben\s?xi', r'bin\s?zhou', r'bortala', r'bo\s?zhou', r'cang\s?zhou', r'chang\s?chun', r'chang\s?de', r'chang\s?sha', r'chang\s?zhi', r'chang\s?zhou', r'chao\s?hu', r'chao\s?zhou', r'cheng\s?de', r'cheng\s?du', r'chen\s?zhou', r'chiayi', r'chi\s?feng', r'chi\s?zhou', r'chong\s?qing', r'chong\s?zuo', r'chu\s?zhou', r'da\s?lian', r'dan\s?dong', r'da\s?qing', r'da\s?tong', r'da\s?zhou', r'de\s?yang', r'de\s?zhou', r'ding\s?xi', r'dong\s?guan', r'dong\s?ying', r'en\s?shi', r'e\s?zhou', r'fang\s?cheng\s?gang', r'fo\s?shan', r'fu\s?shun', r'fu\s?xin', r'fu\s?yang', r'fu\s?zhou', r'gan\s?zhou', r"guang'an", r'guang\s?yuan', r'guang\s?zhou', r'gui\s?gang', r'gui\s?lin', r'gui\s?yang', r'gu\s?yuan', r'hai\s?kou', r'hami', r'han\s?dan', r'hang\s?zhou', r'han\s?zhong', r'harbin', r'ha\s?er\s?bin', r'he\s?bi', r'he\s?chi', r'he\s?fei', r'he\s?gang', r'hei\s?he', r'heng\s?shui', r'heng\s?yang', r'he\s?yuan', r'he\s?ze', r'he\s?zhou', r'hohhot', r'hu\s?he\s?hao\s?te', r'hong kong', r'hsinchu', r"huai'an", r'huai\s?bei', r'huai\s?hua', r'huai\s?nan', r'huang\s?gang', r'huang\s?shan', r'huang\s?shi', r'hui\s?zhou', r'hu\s?lu\s?dao', r'hulunbuir', r'hu\s?zhou', r"ji'an", r'jia\s?ge\s?da\s?qi', r'jia\s?mu\s?si', r'jiang\s?men', r'jiao\s?zuo', r'jia\s?xing', r'jia\s?yu\s?guan', r'jie\s?yang', r'ji\s?lin', r'ji\s?nan', r'jin\s?chang', r'jin\s?cheng', r'jing\s?de\s?zhen', r'jing\s?men', r'jing\s?zhou', r'jin\s?hua', r'ji\s?ning', r'jin\s?zhong', r'jin\s?zhou', r'jiu\s?jiang', r'jiu\s?quan', r'ji\s?xi', r'ji\s?yuan', r'kai\s?feng', r'kaohsiung', r'karamay', r'kashi', r'kashgar', r'keelung', r'kun\s?ming', r'kun\s?shan', r'lai\s?bin', r'lai\s?wu', r'lang\s?fang', r'lan\s?zhou', r'le\s?shan', r'lhasa', r'lian\s?yun\s?gang', r'liao\s?cheng', r'liao\s?yang', r'liao\s?yuan', r'li\s?jiang', r'lin\s?cang', r'lin\s?fen', r'linxia hui', r'lin\s?yi', r'li\s?shui', r'liu\s?pan\s?shui', r'liu\s?zhou', r'long\s?nan', r'long\s?yan', r'lou\s?di', r"lu'an", r'luo\s?he', r'luo\s?yang', r'lu\s?zhou', r'lv\s?liang', r"ma'anshan", r'macao', r'mao\s?ming', r'mei\s?shan', r'mei\s?zhou', r'mian\s?yang', r'mu\s?dan\s?jiang', r'nagqu', r'nan\s?chang', r'nan\s?chong', r'nan\s?jing', r'nan\s?ning', r'nan\s?ping', r'nan\s?tong', r'nan\s?yang', r'nei\s?jiang', r'ngari area', r'ning\s?bo', r'ning\s?de', r'nyingchi prefecture', r'ordos', r'er\s?duo\s?si', r'pan\s?jin', r'pan\s?zhi\s?hua', r'ping\s?ding\s?shan', r'ping\s?liang', r'ping\s?xiang', r'ping\s?xiang', r"pu'er", r'pu\s?tian', r'pu\s?yang', r'qamdo', r'qian\s?jiang', r'qing\s?dao', r'qing\s?yang', r'qing\s?yuan', r'qin\s?huang\s?dao', r'qin\s?zhou', r'qiong\s?hai', r'qi\s?qi\s?har', r'qi\s?tai\s?he', r'quan\s?zhou', r'qu\s?jing', r'qu\s?zhou', r'ri\s?zhao', r'san\s?men\s?xia', r'san\s?ming', r'san\s?ya', r'shang\s?hai', r'shang\s?luo', r'shang\s?qiu', r'shang\s?rao', r'shan\s?nan', r'shan\s?tou', r'shan\s?wei', r'shao\s?guan', r'shao\s?xing', r'shao\s?yang', r'shen\s?yang', r'shen\s?zhen', r'shi\s?jia\s?zhuang', r'shi\s?yan', r'shi\s?zui\s?shan', r'shuang\s?ya\s?shan', r'shuo\s?zhou', r'si\s?ping', r'song\s?yuan', r'sui\s?hua', r'sui\s?ning', r'sui\s?zhou', r'su\s?qian', r'su\s?zhou', r'tacheng', r"tai'an", r'taichung', r'tai\s?nan', r'taipei', r'tai\s?yuan', r'tai\s?zhou', r'tang\s?shan', r'tian\s?jin', r'tian\s?shui', r'tibet', r'tie\s?ling', r'tong\s?chuan', r'tong\s?hua', r'tong\s?liao', r'tong\s?ling', r'turpan', r'ulanqab', r'urumqi', r'wu\s?lu\s?mu\s?qi', r'wei\s?fang', r'wei\s?hai', r'wei\s?nan', r'wen\s?chang', r'wen\s?zhou', r'wu\s?hai', r'wu\s?han', r'wu\s?hu', r'wu\s?wei', r'wu\s?xi', r'wu\s?zhong', r'wu\s?zhou', r"xi'an", r'xi\s?an', r'xia\s?men', r'xiang\s?tan', r'xiang\s?yang', r'xia\s?ning', r'xian\s?tao', r'xian\s?yang', r'xiao\s?gan', r'shigatse',r'xi\s?ga\s?ze', r'xing\s?tai', r'xi\s?ning', r'xin\s?xiang', r'xin\s?yang', r'xin\s?yu', r'xin\s?zhou', r'xuan\s?cheng', r'xu\s?chang', r'xu\s?zhou', r"ya'an", r"yan'an", r'yan\s?cheng', r'yang\s?jiang', r'yang\s?quan', r'yang\s?zhou', r'yan\s?tai', r'yi\s?bin', r'yi\s?chang', r'yi\s?chun', r'yin\s?chuan', r'ying\s?kou', r'ying\s?tan', r'yi\s?wu', r'yi\s?xing', r'yi\s?yang', r'yong\s?zhou', r'yue\s?yang', r'yu\s?lin', r'yun\s?cheng', r'yun\s?fu', r'yu\s?xi', r'zao\s?zhuang', r'zhang\s?jia\s?jie', r'zhang\s?jia\s?kou', r'zhang\s?ye', r'zhang\s?zhou', r'zhan\s?jiang', r'zhao\s?qing', r'zhao\s?tong', r'zheng\s?zhou', r'zhen\s?jiang', r'zhong\s?shan', r'zhong\s?wei', r'zhou\s?kou', r'zhou\s?shan', r'zhu\s?hai', r'zhu\s?ma\s?dian', r'zhu\s?zhou', r'zi\s?bo', r'zi\s?gong', r'zi\s?yang', r'zun\s?yi')
    hanzi_cities = ('安康',	'安庆',	'鞍山',	'安顺',	'安阳',	'百城',	'百色',	'白山',	'白银',	'保定',	'宝鸡',	'保山',	'包头',	'巴彦淖尔',	'巴中',	'北海',	'北京',	'蚌埠',	'本溪',	'滨州',	'博乐',	'亳州',	'沧州',	'长春',	'常德',	'长沙',	'长治',	'常州',	'巢湖',	'潮州',	'承德',	'成都',	'郴州',	'嘉義',	'赤峰',	'池州',	'重庆',	'崇左',	'滁州',	'大连',	'丹东',	'大庆',	'大同',	'达州',	'德阳',	'德州',	'定西',	'东莞',	'东营', '恩施',	'鄂州',	'防城港', '佛山', '抚顺', '阜新',	'阜阳',	'福州',	'赣州',	'广安',	'广元',	'广州',	'贵港',	'桂林',	'贵阳',	'固原',	'海口',	'哈密',	'邯郸',	'杭州',	'汉中',	'哈尔滨',	'哈尔滨',	'鹤壁',	'河池',	'合肥',	'鹤岗',	'黑河',	'衡水',	'衡阳',	'河源',	'菏泽',	'贺州',	'呼和浩特',	'呼和浩特',	'香港',	'新竹',	'淮安',	'淮北',	'怀化',	'淮南',	'黄冈',	'黄山',	'黄石',	'惠州',	'葫芦岛',	'呼伦贝尔',	'湖州',	'吉安',	'加格达奇',	'佳木斯',	'江门',	'焦作',	'嘉兴',	'嘉峪关',	'揭阳',	'吉林',	'济南',	'金昌',	'晋城',	'景德镇',	'荆门',	'荆州',	'金华',	'济宁',	'晋中',	'锦州',	'九江',	'酒泉',	'鸡西',	'济源',	'开封',	'高雄',	'克拉玛依',	'喀什',	'喀什',	'基隆',	'昆明',	'昆山',	'来宾',	'莱芜',	'廊坊',	'兰州',	'乐山',	'拉萨',	'连云港',	'聊城',	'辽阳',	'辽源',	'丽江',	'临沧',	'临汾',	'临夏州',	'临沂',	'丽水',	'六盘水',	'柳州',	'陇南',	'龙岩',	'娄底',	'六安',	'漯河',	'洛阳',	'泸州',	'吕梁',	'马鞍山',	'澳门',	'茂名',	'眉山',	'梅州',	'绵阳',	'牡丹江',	'那曲',	'南昌',	'南充',	'南京',	'南宁',	'南平',	'南通',	'南阳',	'内江',	'阿里地区 ',	'宁波',	'宁德',	'林芝',	'鄂尔多斯',	'鄂尔多斯',	'盘锦',	'攀枝花',	'平顶山',	'平凉',	'萍乡',	'凭祥',	'普洱',	'莆田',	'濮阳',	'昌都',	'潜江',	'青岛',	'庆阳',	'清远',	'秦皇岛',	'钦州',	'琼海',	'齐齐哈尔',	'七台河',	'泉州',	'曲靖',	'衢州',	'日照',	'三门峡',	'三明',	'三亚',	'上海',	'商洛',	'商丘',	'上饶',	'山南',	'汕头',	'汕尾',	'韶关',	'绍兴',	'邵阳',	'沈阳',	'深圳',	'石家庄','十堰',	'石嘴山',	'双鸭山',	'朔州',	'四平',	'松原',	'绥化',	'遂宁',	'随州',	'宿迁',	'苏州',	'塔城',	'泰安',	'台中',	'台南',	'台北',	'太原',	'台州',	'唐山',	'天津',	'天水',	'西藏',	'铁岭',	'铜川',	'通化',	'通辽',	'铜陵',	'吐鲁番',	'乌兰察',	'乌鲁木齐',	'乌鲁木齐',	'潍坊',	'威海',	'渭南',	'文昌',	'温州',	'乌海',	'武汉',	'芜湖',	'武威',	'无锡',	'吴忠',	'梧州',	'西安', '西安',	'厦门',	'湘潭',	'襄阳',	'夏宁',	'仙桃',	'咸阳',	'孝感',	'日喀则',	'日喀则',	'邢台',	'西宁',	'新乡',	'信阳',	'新余',	'忻州',	'宣城',	'许昌',	'徐州',	'雅安',	'延安',	'盐城',	'阳江',	'阳泉',	'扬州',	'烟台',	'宜宾',	'宜昌',	'宜春',	'银川',	'营口',	'鹰潭',	'义乌', '宜兴',	'益阳',	'永州',	'岳阳',	'榆林',	'运城',	'云浮',	'玉溪',	'枣庄',	'张家界',	'张家口',	'张掖',	'漳州',	'湛江',	'肇庆',	'昭通',	'郑州',	'镇江',	'中山',	'中卫',	'周口',	'舟山',	'珠海',	'驻马店',	'株洲',	'淄博',	'自贡',	'资阳',	'遵义')
    # Double check lengths of these!!!
    # print(f'CITIES LEN: {len(py_cities)}')
    # print(f'HANZI LEN: {len(hanzi_cities)}')

    # Added regex to remove street and station names which are the same as city names - further modifications for Baoshan in Shanghai and the city of Baoshan
    cities = [c.replace(r'\s?', '') for c in py_cities if re.search(fr'\b{c}(?![,;\s](road|street|station|district|\sshang))\b', text, flags=re.I)]

    d={r'\bbj\b':'beijing', r'\bgz\b':'guangzhou', r'\bsz\b':'shenzhen'}
    for k,v in d.items():
        # if v not in cities and k in text:
        if v not in cities and re.search(k,text):
            cities.append(v)
            cities =  sorted(cities)

    
    for i,c in enumerate(hanzi_cities):
        py_city = py_cities[i].replace(r'\s?', '')
        if c in text and py_city not in cities:
            cities.append(py_city)



  # Check here for neg kws
#   'certificate', 'tefl','tesol' ,'ups' matches with groups
    neg_kws = ('scholarship','legalization','卖群','空运','海运','物流','dissertation','批发','租赁',
            'stipend','thesis','plagiarism','manufacturer','factory','battery','hsk','visa extension','包邮','early bird',
            'express delivery','dhl','fedex','ems','vpn','pinduoduo.com'
            
        )
   

    if any(w in text for w in neg_kws):
        job_types = []
        subjects = []
        is_job = False

        for w in neg_kws:
            if w in text:
                print(f'\033[35mNEGATIVE KEYWORD DETECTED: {w}\033[0m')

        # print(f'CITIES: {cities}')
        # print(f'JOB TYPES: {job_types}')
        # print(f'SUBJECTS: {subjects}')
        # print(f'IS_JOB: {is_job}')

        return [cities, job_types, subjects, is_job, trans]
  




    # Check for job types
    job_types = []

    teach = ('teach', 'tutor')
    if any(w in text for w in teach):
        job_types.append('teaching')

    school_type = ('primary school', 'middle school', 'high school', 'university', 'secondary school', 'public school', 'private school')
    for j in school_type:
        if j in text:
            job_types.append(j)

    if any(w in text for w in ('training center', 'training centre')):
        job_types.append('training centre')

    if 'online teach' in text:
        job_types.append('online teaching')

    # Looks for international with up to 3 words in the middle
    if re.search(r'international (\w+\s){0,3}school', text):
        job_types.append('international school')

    if any(w in text for w in ('kindergarten', 'kindergarden','幼儿')):
        job_types.append('kindergarten')

    all_teaching_jobs = school_type + ('teaching', 'online teaching', 'international school', 'kindergarten')

    # 'recruit'

    # Other jobs types
    modelling = ('model', 'catwalk', '走秀', '模特', '女模', '男模', 'mermaid', '美人鱼','摩卡','童模')
    if any(w in text for w in modelling):
        job_types.append('model')
        if any(w in text for w in ('baby', 'babies')):
            job_types.append('baby modelling')
        if any(w in text for w in ('kid', 'kids','child','children','toddler','童模')):
            job_types.append('child modelling')   

    # just 拍 ??
    acting = ('actor', 'actress', 'filming', 'shoot', 'acting', '拍戏', '演戏', '演员', '拍摄','戏份','大制作')
    if any(w in text for w in acting):
        job_types.append('acting')

    dancing = ('dancing', 'dancer', 'bgo', 'gogo', '舞蹈', '跳舞', 'танцор')
    if any(w in text for w in dancing):
        job_types.append('dancer')

    tiktok = ('tiktok', 'tik tok', 'douyin', 'dou yin', '抖音','live stream')
    if any(w in text for w in tiktok):
        job_types.append('tiktok')

    xiaohongshu = ('小红书', 'xiao hong shu', 'xiaohongshu', 'little red book')
    if any(w in text for w in xiaohongshu):
        job_types.append('xiao hong shu')

    singer = ('singer', '歌手', 'певи')
    if any(w in text for w in singer):
        job_types.append('singer')

    music = ('бэнд', '乐队', 'musician', 'guitarist', 'drummer', 'piano', 'pianist')
    if any(w in text for w in music) or re.search(r'\bband\b',text):
        job_types.append('musician')

        
    travel = ('travel companion', '伴游')
    if any(w in text for w in travel):
        job_types.append('travel companion')

    if re.search(r'\bdj\b', text):
        job_types.append('dj')

    karaoke = ('ktv', 'karaoke', 'караоке')
    if any(w in text for w in karaoke):
        job_types.append('ktv')

    bar = ('drink with guests', ' bar ')
    if any(w in text for w in bar):
        job_types.append('bar work')

    if any(w in text for w in ('recording','录音')):
        job_types.append('recording')

    if 'voiceover' in text:
        job_types.append('voiceover')
    
    translate = ('translator', '翻译')
    if any(w in text for w in translate):
        job_types.append('translator')
    

    # t = ('')
    # if any(w in text for w in t):
    #     job_types.append('')

    job_types = sorted(job_types)



    subjects = [] 
    # Check for subjects only when job related to teaching
    if any(w in job_types for w in all_teaching_jobs):

        subject_list = ('drama', 'esl', 'ielts', 'toefl', 'toeic', 'maths?', 'mathematics', 'history', 'science', 'biology', 'physics', 'chemistry', 'geography', 'music', r'p\.?e\.?', 'physical education', 'philosophy', 'social studies', 'literature', 'economics', 'statistics', 'computer science', 'information technology', 'psychology', 'french art', 'german', 'spanish', 'japanese', 'korean', 'montessori')

        # capital_subs = ['esl', 'ielts', 'toefl', 'toeic']

        for s in subject_list:
            if re.search(fr'\b{s}\b', text):
                
                # if s in capital_subs:
                #     subjects.append(s.upper())
                #     continue
                if s == 'literature':
                    s = 'english literature'
            
                subjects.append(re.sub(r'[\\?]', '', s))

        # French language check
        if re.search(r'\bfrench(?!\sart)\b', text):
            subjects.append('french')

        # Art without French check
        if re.search(r'(?<!french)\sart\b', text):
            subjects.append('art')

        if re.search(fr'\benglish teacher\b', text):
            subjects.append('general english')

        subjects = sorted(subjects)

    is_job = True if job_types else False

    # print(f'\nWORD COUNT: {word_count}')
    # print(f'CITIES: {cities}')
    # print(f'JOB TYPES: {job_types}')
    # print(f'SUBJECTS: {subjects}')
    # print(f'IS_JOB: {is_job}')

    return [cities, job_types, subjects, is_job, trans]


# python manage.py shell

# text_parser(text)
# from test_parser import text_parser, run_script, run_script_by_pk


# def run_script():
#     from jobsboard.models import Job
#     job = Job.objects.order_by('?').first()
#     print('\033[31m**********************************\033[0m')
#     print(job.job_description)
#     print('\033[31m**********************************\033[0m')
#     print(text_parser(job.job_description))
#     print(f'JOB PK: {job.pk}')

# 4181
# def run_script_by_pk(pk):
#     from jobsboard.models import Job
#     job = Job.objects.get(pk=pk)
#     print('\033[31m**********************************\033[0m')
#     print(job.job_description)
#     print('\033[31m**********************************\033[0m')
#     print(text_parser(job.job_description))
#     print(f'JOB PK: {job.pk}')


# text_parser(text)