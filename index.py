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
from markupsafe import Markup

action_list = ["index", "content"]

form = cgi.FieldStorage()
action = form.getvalue('action','index') 

### 公共配置 ###
# 数据库
db_path = "./db/your/sqlite/path.db"
db_path_real = os.path.abspath(db_path)




### 公共函数 ###
#print("Content-type:text/html\r\n") 

# print utf-8 
utf8stdout = open(1, 'w', encoding='utf-8', closefd=False) # fd 1 is stdout
def print_u(str_param):
    print(str_param, file = utf8stdout)
print_u("Content-type:text/html\r\n")   

  

# 分布渲染
def pager_html(p_total, p_pagesize, p_page):
    pager_html_str = ""
    page_range = 3
    pages = int(p_total / p_pagesize) + int(bool(p_total % p_pagesize))
    prev_page = p_page - 1
    next_page = p_page + 1
    if p_page > 1:
        pager_html_str += '<li><a class="prev page-numbers" href="/page/' + str(prev_page) + '/">« 上一頁</a></li>'
        pager_html_str += '<li><a class="page-numbers" href="/page/1/">1</a></li>'
    else:
        pager_html_str += '<li><span class="page-numbers current">1</span></li>'

    if p_page > 1 + page_range:
        pager_html_str += '<li><span class="page-numbers dots">&hellip;</span></li>'

    for page_x in range(p_page - (page_range - 1), p_page + (page_range - 1)):
        if page_x > 1 and page_x < pages:
            if page_x == p_page:
                pager_html_str += '<li><span class="page-numbers current">' + str(page_x) + '</span></li>'
            else:
                pager_html_str += '<li><a class="page-numbers" href="/page/' + str(page_x) + '/">' + str(page_x) + '</a></li>'

    if pages - p_page > 1 + page_range:
        pager_html_str += '<li><span class="page-numbers dots">&hellip;</span></li>' 
    
    if pages > page_range:
        pager_html_str += '<li><a class="page-numbers" href="/page/' + str(pages) + '/">'+ str(pages) +'</a></li>'

    if p_page < pages:
        pager_html_str += '<li><a class="next page-numbers" href="/page/' + str(next_page) + '/">下一頁 »</a></li>' 

    return pager_html_str                 




include_top_file = open(os.path.abspath("./templates/blog/top.html"), "r", -1, "utf-8")
include_top = include_top_file.read()

include_sidebar_file = open(os.path.abspath("./templates/blog/sidebar.html"), "r", -1, "utf-8")
include_sidebar = include_sidebar_file.read()

include_footer_file = open(os.path.abspath("./templates/blog/footer.html"), "r", -1, "utf-8")
include_footer = include_footer_file.read()    

        
def index():
    global include_sidebar
    category = form.getvalue('category', "") 
    SQLWhere = " 1 = 1 "
    if category != "":
        SQLWhere += " AND category_id = (SELECT id FROM category WHERE url = '" + category + "/') "           

    # 读取 list_article 模板
    list_article_unit = open(os.path.abspath("./templates/blog/list_article.html"), "r", -1, "utf-8").read()
    
    # 文章列表
    # 接收参数
    c_page = int(form.getvalue('page', 1))
    c_row = 10
    if c_page < 0:
        c_page = 1

    # connect sqlite database
    cx = sqlite3.connect(db_path_real)
    # Now we plug Row in
    cx.row_factory = sqlite3.Row
    cu = cx.cursor()    
    # 计算总数量
    sql = "SELECT COUNT(*) FROM content WHERE " + SQLWhere
    cu.execute(sql)

    for row in cu:
        c_total = row[0]

    if c_row * c_page > c_total:
        page = 1
            
    
    c_passrow = c_row * (c_page - 1)    

    sql = "SELECT c.[id], c.[name], c.[url], c.[content], c.[author], c.[add_time], cat.[name] AS categroy_name, cat.[url] AS categroy_url\
          FROM Content AS c, category AS cat\
          WHERE c.[category_id] = cat.[id] AND " + SQLWhere + " ORDER BY c.id DESC LIMIT " + str(c_passrow) + "," + str(c_row) 
    #return sql
    cu.execute(sql)

    list_article = ""
    for row in cu:
        row_dict = {"title":row['name'], \
                  "link":"/content/" + row['url'], \
                  "author":row['author'], \
                  "date":row['add_time'].split('.')[0


                  ], \
                  "category_name":row['categroy_name'], \
                  "category_link":"/category/" + row['categroy_url'], \
                  "content": Markup(row['content'][0:500]).striptags()}
        list_article += Template(list_article_unit).substitute(row_dict)
        
    # return list_article

    # 最新文章 
    list_article_new = ""
    sql = "SELECT c.[name], c.[url] FROM Content AS c ORDER BY RANDOM() LIMIT 0,8" 
    cu.execute(sql)
    for row in cu:
        list_article_new += '<li><a href="/content/' + row['url'] + '">' + row['name'] + '</a></li>'

    # 列表分页
    list_pager = pager_html(c_total, c_row, c_page)
    # return list_pager

    # 分类
    sql = "SELECT count(c.[id]) AS counts, cat.[name] AS categroy_name, cat.[url] AS categroy_url \
            FROM Content AS c, category AS cat \
            WHERE c.[category_id] = cat.[id] \
            GROUP BY cat.[name] ORDER BY cat.[order_num] DESC"
    cu.execute(sql)
    list_category = ""
    for row in cu:
        list_category += '<li class="cat-item cat-item-1"><a href="/category/' + row['categroy_url'] + '" \
                            title="View all posts filed under">' + row['categroy_name'] + '</a> (' + str(row['counts']) + ')</li>' 

    include_sidebar = Template(include_sidebar).substitute(list_article_new=list_article_new, list_category=list_category)

    template_file = open(os.path.abspath("./templates/blog/list.html"), "r", -1, "utf-8")
    template_dict = {"include_top":include_top, "include_sidebar":include_sidebar, "include_footer":include_footer}
    template_dict.update(include_article_list=list_article, pager=list_pager)
    return Template(template_file.read()).substitute(template_dict)

# 显示内容
def content():
    #http://localhost:8100/?action=content&alias=urllike
    global include_sidebar
    alias = form.getvalue('alias', '')
    if (re.match(r'^[\w\d\-]{2,200}$', alias) is None):
        return "内容不存在"

    # connect sqlite database
    cx = sqlite3.connect(db_path_real)
    # Now we plug Row in
    cx.row_factory = sqlite3.Row
    cu = cx.cursor()     
    sql = "SELECT c.*, cat.[name] AS categroy_name, cat.[url] AS categroy_url\
          FROM Content AS c, category AS cat\
          WHERE c.[category_id] = cat.[id] AND c.url = '" + alias + "/'"          
    cu.execute(sql)
    for row in cu:
        row_dict = {"title":row['name'], \
                  "link":"/content/" + row['url'], \
                  "author":row['author'], \
                  "date":row['add_time'].split('.')[0], \
                  "category_name":row['categroy_name'], \
                  "category_link":"/category/" + row['categroy_url'], \
                  "content":row['content']}

    # 最新文章 
    list_article_new = ""
    sql = "SELECT c.[name], c.[url] FROM Content AS c ORDER BY c.id DESC LIMIT 0,10" 
    cu.execute(sql)
    for row in cu:
        list_article_new += '<li><a href="/content/' + row['url'] + '">' + row['name'] + '</a></li>'              

    # 分类
    sql = "SELECT count(c.[id]) AS counts, cat.[name] AS categroy_name, cat.[url] AS categroy_url \
            FROM Content AS c, category AS cat \
            WHERE c.[category_id] = cat.[id] \
            GROUP BY cat.[name] ORDER BY cat.[order_num] DESC"
    cu.execute(sql)
    list_category = ""
    for row in cu:
        list_category += '<li class="cat-item cat-item-1"><a href="/category/' + row['categroy_url'] + '" \
                            title="View all posts filed under">' + row['categroy_name'] + '</a> (' + str(row['counts']) + ')</li>' 

    include_sidebar = Template(include_sidebar).substitute(list_article_new=list_article_new, list_category=list_category)              

    template_file = open(os.path.abspath("./templates/blog/content.html"), "r", -1, "utf-8")
    template_dict = {"include_top":include_top, "include_sidebar":include_sidebar, "include_footer":include_footer}
    template_dict.update(row_dict)
    return Template(template_file.read()).substitute(template_dict)


# 路由       
if(action in action_list):
    exec("print_content = " + action + "()")
    print_u(print_content)
