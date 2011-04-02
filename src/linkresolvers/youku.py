'''
Created on Mar 27, 2010

@author: pguedes
'''
import re, utils.htmlutils as htmlutils

def resolve(page):
  links = []
  bit = re.compile('<iframe src="(.+?)"').findall(page)
  page = htmlutils.get(bit[0])
  Id = re.compile("'VideoIDS','(.+?)'").findall(page)
  page = htmlutils.get("http://www.flvcd.com/parse.php?kw=http%3A%2F%2Fv.youku.com%2Fv_show%2Fid_" + Id[0] + "%3D%3D.html")
  match = re.compile('<a href="(.+?)" target="_blank" onclick=".+?">').findall(page)
  for url in match:
    links.append(url)
