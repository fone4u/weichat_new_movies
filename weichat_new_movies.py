#! /usr/bin/env python
# coding=utf-8

from bottle import *
import bottle
import hashlib
import xml.etree.ElementTree as ET
import MySQLdb
import urllib2,sys,re
import sae.const
import pylibmc
reload(sys) 
sys.setdefaultencoding('utf8')
# import requests
import json


def special_match(strg, search=re.compile(r'[a-zA-Z]{3}(.*)\d{3}').search):
    return  bool(search(strg))


app=Bottle()

#SAE MYSQL
MYSQL_DB=sae.const.MYSQL_DB
MYSQL_USER=sae.const.MYSQL_USER
MYSQL_PASS=sae.const.MYSQL_PASS
MYSQL_HOST_M=sae.const.MYSQL_HOST
MYSQL_HOST_S=sae.const.MYSQL_HOST_S
MYSQL_PORT=int(sae.const.MYSQL_PORT)

#connect to sae MYSQL



page=urllib2.urlopen('http://www.yyets.com/resourcelist?channel=movie&area=%&category=&format=HR-HDTV&sort=')
contentsyy=page.read()
movie_yy=re.findall(r'<strong>(.*?)</strong></a>',contentsyy)
yyets_movie= movie_yy[20].encode('utf-8')
sss=yyets_movie
conn=MySQLdb.connect(host=MYSQL_HOST_M,user=MYSQL_USER,passwd=MYSQL_PASS,db=MYSQL_DB,port=MYSQL_PORT)
cur=conn.cursor()




cur.execute('SELECT * FROM YYETS ORDER BY id DESC LIMIT 1')
test=cur.fetchone()
if sss!=test[1]:
    cur.execute("INSERT INTO YYETS (source) VALUES (%s)",sss)




@get("/")
def checkSignature():
    token = "Your token"  # 你在微信公众平台上设置的TOKEN
    signature = request.GET.get('signature', None)  # 拼写不对害死人那，把signature写成singnature，直接导致怎么也认证不成功
    timestamp = request.GET.get('timestamp', None)
    nonce = request.GET.get('nonce', None)
    echostr = request.GET.get('echostr', None)
    tmpList = [token, timestamp, nonce]
    tmpList.sort()
    tmpstr = "%s%s%s" % tuple(tmpList)
    hashstr = hashlib.sha1(tmpstr).hexdigest()
    if hashstr == signature:
        return echostr
    else:
        return None

@app.route('/' , method='GET')
def yy():
    page=urllib2.urlopen('http://www.yyets.com/resourcelist?channel=movie&area=%&category=&format=HR-HDTV&sort=')
    contentsyy=page.read()
    movie_yy=re.findall(r'<strong>(.*?)</strong></a>',contentsyy)
    yyets_movie= movie_yy[20].encode('utf-8')
    sss=yyets_movie

    cur.execute('SELECT * FROM YYETS ORDER BY id DESC LIMIT 1')
    test=cur.fetchone()
    if sss!=test[1]:
        cur.execute("INSERT INTO YYETS (source) VALUES (%s)",sss)
    



def yyets():
    conn=MySQLdb.connect(host=MYSQL_HOST_M,user=MYSQL_USER,passwd=MYSQL_PASS,db=MYSQL_DB,port=MYSQL_PORT)
    cur=conn.cursor()
    cur.execute('SELECT * FROM YYETS ORDER BY id DESC LIMIT 1')
    test=cur.fetchone()
    return test[1]

def parse_msg():

    recvmsg = request.body.read()  
    root = ET.fromstring(recvmsg)
    msg = {}
    for child in root:
        msg[child.tag] = child.text
    return msg


def search_course():
	conn=MySQLdb.connect(host=MYSQL_HOST_M,user=MYSQL_USER,passwd=MYSQL_PASS,db=MYSQL_DB,port=MYSQL_PORT)
	cur=conn.cursor()
	msg = parse_msg()
	course_code=msg["Content"]
	course_code=course_code.replace(" ","")
	course_code=course_code.upper()

	if cur.execute('SELECT * FROM SBU WHERE CODE = %s ORDER BY ID DESC LIMIT 1',course_code):

		return_course=cur.fetchone()
		course_id=return_course[0]
		info_id=course_id+1
		cur.execute('SELECT * FROM SBU WHERE ID = %s ORDER BY ID DESC LIMIT 1',info_id)
		return_info=cur.fetchone()
		return return_info[2]
	else :
		return u"对不起，没有查询到该课程！"



def query_movie_info():

    movieurlbase = "http://api.douban.com/v2/movie/search"
    DOUBAN_APIKEY = "0ec7076653f7fffb2c551632fbe7fff1" 
    movieinfo = parse_msg()
    searchkeys = yyets()
    
    url = '%s?q=%s&apikey=%s' % (movieurlbase, searchkeys, DOUBAN_APIKEY)

    resp = urllib2.urlopen(url)
    movie = json.loads(resp.read())

    return movie



def query_movie_details():

    movieurlbase = "http://api.douban.com/v2/movie/subject/"
    DOUBAN_APIKEY = "0ec7076653f7fffb2c551632fbe7fff1"
    id = query_movie_info()
    url = '%s%s?apikey=%s' % (movieurlbase, id["subjects"][0]["id"], DOUBAN_APIKEY)
    resp = urllib2.urlopen(url)
    description = json.loads(resp.read())
    description = ''.join(description['summary'])
    return description


@post("/")
def response_msg():
 
    msg = parse_msg()

    textTpl = """<xml>
             <ToUserName><![CDATA[%s]]></ToUserName>
             <FromUserName><![CDATA[%s]]></FromUserName>
             <CreateTime>%s</CreateTime>
             <MsgType><![CDATA[text]]></MsgType>
             <Content><![CDATA[%s]]></Content>
             <FuncFlag>0</FuncFlag>
             </xml>"""
    # 图文格式
    pictextTpl = """<xml>
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName>
                <CreateTime>%s</CreateTime>
                <MsgType><![CDATA[news]]></MsgType>
                <ArticleCount>1</ArticleCount>
                <Articles>
                <item>
                <Title><![CDATA[%s]]></Title>
                <Description><![CDATA[%s]]></Description>
                <PicUrl><![CDATA[%s]]></PicUrl>
                <Url><![CDATA[%s]]></Url>
                </item>
                </Articles>
                <FuncFlag>1</FuncFlag>
                </xml> """
    textTpl_new = """<xml>
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName>
                <CreateTime>%s</CreateTime>
                <MsgType><![CDATA[news]]></MsgType>
                <ArticleCount>1</ArticleCount>
                <Articles>
                <item>
                <Title><![CDATA[%s]]></Title>
                <Description><![CDATA[%s]]></Description>
                </item>
                </Articles>
                <FuncFlag>1</FuncFlag>
                </xml> """

    if msg["MsgType"] == "event":
        echostr = textTpl % (
            msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
            u"欢迎关注，回复‘dy’即可查看人人发布的最新HR电影的豆瓣介绍! 回复课程代码如‘cse114’即可获取相关课程信息！---powered by jiahhu")
        return echostr
    elif msg["Content"].lower()=="dy":
        Content = query_movie_info()
        description = query_movie_details()
        echostr = pictextTpl % (msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
                                Content["subjects"][0]["title"], description,
                                Content["subjects"][0]["images"]["large"], Content["subjects"][0]["alt"])
        return echostr     
    elif special_match(msg["Content"])==True:
        sbu_course=search_course()
        
        #print sbu_course
        echostr = textTpl % (
            msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
            sbu_course)
        return echostr
    else:
       echostr = textTpl % (
            msg['FromUserName'], msg['ToUserName'], str(int(time.time())),
            u"无效指令，请输入“dy”查询电影或者课程代码如“CSE114”查询课程简介！")
       return echostr


if __name__=="__main__":
    # Interactive mode
    debug(True)
    run(host='127.0.0.1', port=8888, reloader=True)
else:
    # Mod WSGI launch
    import sae
    debug(True)
    os.chdir(os.path.dirname(__file__))
    app = default_app()
    application = sae.create_wsgi_app(app)
