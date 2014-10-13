# -*- coding: utf-8 -*-
import os, sys
import cgi
import re
import sqlite3
import socket
import hashlib
import random
from datetime import datetime
from string import Template

action_list = ["index", "main", "login", \
     "content_list", "content_add", "content_edit", "content_delete", "content_save", \
     "saying_list", "saying_add", "saying_edit", "saying_delete", "saying_save"]
form = cgi.FieldStorage()
token = form.getvalue('token','empty')
action = form.getvalue('action','index')
include_top = "" # 模板top.html

### 公共配置 ###
# 数据库
db_path = "./db/your/sqlite/path.db"
db_path_real = os.path.abspath(db_path)

### 公共函数 ###

print("Content-type:text/html\r\n")

# print utf-8 
utf8stdout = open(1, 'w', encoding='utf-8', closefd=False) # fd 1 is stdout
def print_u(str_param):
	print(str_param, file = utf8stdout)
    

def alert(msg, location):
    if (location == '-1'):
        alert_script = '<script>alert("'+ msg +'");history.go(-1)</script>'
    elif (location == '1'):
        alert_script = '<script>alert("'+ msg +'");</script>'
    else:
        alert_script = '<script>alert("'+ msg +'");location.href="'+ location +'"</script>'
    alert_script = '<html><meta http-equiv="Content-Type" content="text/html; charset=utf-8">' + alert_script + '</html>'   
    return alert_script

# 验证token
def check_token():
    # 验证格式
    if (re.match(r'\w{32}', token) is None):
        return False

    if(token != 'empty'):
        # 查询数据库token及ip地址的匹配
        cx = sqlite3.connect(os.path.abspath("./db/cpo100A8sC265xy-BwO.db"))
        cu = cx.cursor()

        sql = "SELECT client_ip, update_time FROM tokenlist WHERE token = '" + token + "' "
        cu.execute(sql)
        result = cu.fetchone()
        if not result is None:
            # 验证ip 和 update_time
            new_cliet_ip = socket.gethostbyname(socket.gethostname())
            if(new_cliet_ip != str(result[0])):
                return False
            new_date_now = datetime.now()
            date_delta = new_date_now - datetime.strptime( (result[1])[:19], '%Y-%m-%d %H:%M:%S')
            if(date_delta.days > 2):
                return False # 登录时间过期

            # 验证成功之后更新update_time
            sql = "UPDATE tokenlist SET update_time = '"  + datetime.strftime(new_date_now, '%Y-%m-%d %H:%M:%S') + "' WHERE token = '" + \
                  token + \
                  "'"
            cu.execute(sql)
            cx.commit()
            return True
        else:
            return False # 没有token记录
    else:
        return False	


def index():
    template_file = open(os.path.abspath("./templates/admin/login.html"), "r", -1, "utf-8")
    return template_file.read()

def main():
    template_file = open(os.path.abspath("./templates/admin/main.html"), "r", -1, "utf-8")
    return template_file.read()
    

def login():
    username = form.getvalue('username', '')
    password = form.getvalue('password', '')
    if (username != '' and password != ''):
        # 验证 username, password
        if (re.match(r'[\w\.]{5,20}', username) is None):
            print_u('{"code":"100","message":"用户名格式错误"}')
            sys.exit(0)
        # connect sqlite database
        cx = sqlite3.connect(db_path_real)
        cu = cx.cursor()

        sql = "select id, username, password from [admin] where username = '"
        sql += username
        sql += "'"
        cu.execute(sql)
        result = cu.fetchone()
        if not result is None:
            m_password = password
            m = hashlib.md5(m_password.encode("utf-8"))
            if m.hexdigest() == result[2]:
                new_token = hashlib.md5( (str(result[0]) + result[1] + \
                            str(random.randint(10000000,99999999)) ).encode("utf-8") ).hexdigest()
                new_cliet_ip = socket.gethostbyname(socket.gethostname())
                new_datetime = datetime.now()
                new_datetime.strftime('%Y-%m-%d %H:%M:%S')
                sql = "INSERT INTO tokenlist(token, client_ip, create_time, update_time) "+ \
                        " VALUES  ('"+ new_token +"', '"+ new_cliet_ip +"', '"+ \
                        str(new_datetime) +"', '"+ str(new_datetime) +"')"
                cu.execute(sql)
                cx.commit()
                print_u('{"code":"200","message":{"id":'+str(result[0])+', "username":"'+result[1]+'",' + \
                      '"token":"' + new_token + '"}}')
            else:
                print_u('{"code":"100","message":"用户名或密码错误'+ m.hexdigest() +'"}')
        else:
            print_u('{"code":"100","message":"用户名不存在"}')
    else:
        print_u('{"code":"100","message":"请输入用户名和密码"}')    
    sys.exit(0)    
### 功能过程函数 ###

# 文章内容
def content_list():
    # 接收参数
    c_page = int(form.getvalue('page', 1))
    if c_page < 0:
        c_page = 1
    c_row = 10
    c_passrow = c_row * (c_page - 1)
    # connect sqlite database
    cx = sqlite3.connect(db_path_real)
    cu = cx.cursor()
    sql = "SELECT id, name FROM content ORDER BY id DESC LIMIT " + str(c_passrow) + ", " + str(c_row) + " "
    cu.execute(sql)
    content_list = ""
    for row in cu:
        content_list += '<li><a href="#">'+ row[1] +'</a>\
                <div class="op_link op_link_1">[<span class="op_edit" attr="'+ str(row[0]) +'">edit</span>]</div>\
                <div class="op_link op_link_2">[<span class="op_delete" attr="'+ str(row[0]) +'">delete</span>]</div>\
                </li>' 
    template_file = open(os.path.abspath("./templates/admin/content_list.html"), "r", -1, "utf-8")
    return Template(template_file.read()).substitute(token=token, include_top=include_top, content_list=content_list, page=c_page)

def content_add():
    template_file = open(os.path.abspath("./templates/admin/content_add.html"), "r", -1, "utf-8")
    return template_file.read()

def content_edit():
    template_file = open(os.path.abspath("./templates/admin/content_add.html"), "r", -1, "utf-8")
    return template_file.read()    

def content_delete():    
    content_id = int(form.getvalue("id", 0))
    if content_id <= 0:
        return alert('内容编号为空', '-1')
    else:
        # connect sqlite database
        cx = sqlite3.connect(db_path_real)
        cu = cx.cursor() 
        cu.execute("DELETE FROM content WHERE id = " + str(content_id)) 
        cx.commit()
        return alert('删除成功', '/admin_cp/?action=content_list&token=' + token) 

def content_save():
    content_title = form.getvalue("title","")
    content_url = form.getvalue("url","")
    content_categoryid = int(form.getvalue("category", "0"))
    content_content = form.getvalue("editorValue","")

    # plus / to content_url
    if content_url == "":
        return alert('请填写文件url', '-1')
    if content_url[-1] != "/":
        content_url += "/"
    
    if content_categoryid == 0:
        return alert('请选择分类', '-1')
    elif content_title == "":
        return alert('标题不能为空', '-1') 
    elif content_content == "":
        return alert('内容不能为空', '-1') 

    # connect sqlite database
    cx = sqlite3.connect(db_path_real)
    cu = cx.cursor()
    new_datetime = datetime.now()
    new_datetime.strftime('%Y-%m-%d %H:%M:%S')
    sql = "INSERT INTO content (category_id, name, url, content, author, add_time, modify_time, order_num) \
        VALUES(" + str(content_categoryid) + ", '" + str(content_title) + "', '" + str(content_url) + "', \
        '" + str(content_content) + "', 'Josh', \
        '" + str(new_datetime) + "', '" + str(new_datetime) + "', 0 ) "
    cu.execute(sql)
    cx.commit()
    return alert('添加成功', '/admin_cp/?action=content_list&token=' + token) 


# 权限判断 
if(action not in ["index", "login"]):
    include_top_file = open(os.path.abspath("./templates/admin/top.html"), "r", -1, "utf-8")
    include_top = include_top_file.read()
    include_top = Template(include_top).substitute(token=token)
    if(check_token() == False):
       print_u("登录超时或者没有权限")
       sys.exit(0)
# 路由       
if(action in action_list):
    exec("print_content = " + action + "()")
    print_u(Template(print_content).substitute(token=token, include_top=include_top))

