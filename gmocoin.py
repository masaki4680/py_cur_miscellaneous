import aiohttp
import asyncio
import async_timeout
import json
from aiohttp import WSMsgType
import traceback
import time
from datetime import datetime
import hmac
import hashlib
from secrets import token_hex


class GMOCoin():
	"""GMO コイン API

	Returns:
		[type]: [description]
	"""
	# 定数
	TIMEOUT = 3600               # タイムアウト
	EXTEND_TOKEN_TIME = 3000     # アクセストークン延長までの時間
	SYMBOL = 'BTC_JPY'          # 銘柄 BTC_JPY
	URLS = {'public': 'https://api.coin.z.com/public',
			'private': 'https://api.coin.z.com/private',
			'publicWS': 'wss://api.coin.z.com/ws/public/v1',
			'privateWS': 'wss://api.coin.z.com/ws/private/v1',
			}    
	PUBLIC_CHANNELS = ['ticker', 'orderbooks', 'trades']
	PRIVATE_CHANNELS = ['executionEvents', 'orderEvents', 'positionEvents', 'positionSummaryEvents']

	# 変数
	api_key = ''
	api_secret = ''

	session = None          # セッション保持
	requests = []           # リクエストパラメータ
	token = ''              # Private Websocket API用トークン

   # ------------------------------------------------ #
   # init
   # ------------------------------------------------ #
	def __init__(self, api_key, api_secret):
		"""constructor

		Args:
			api_key (string): [description]
			api_secret (string): [description]
		"""
		self.api_key = api_key
		self.api_secret = api_secret

	# ------------------------------------------------ #
	# async request for rest api
	# ------------------------------------------------ #
	def set_request(self, method, access_modifiers, target_path, params):
		"""async request for rest api

		Args:
			method (string): [description]
			access_modifiers ([type]): [description]
			target_path (string): [description]
			params ([type]): [description]
		"""
		if access_modifiers == 'public':
			url = ''.join([self.URLS['public'], target_path])
			if method == 'GET':
				headers = ''
				self.requests.append({'method': method,
										'access_modifiers': access_modifiers,
										'target_path': target_path, 'url': url,
										'params': params, 'headers':{}})

			if method == 'POST':
				headers = {'Content-Type': 'application/json'}
				self.requests.append({'method': method,
										'access_modifiers': access_modifiers,
										'target_path': target_path, 'url': url,
										'params': params, 'headers':headers})

		if access_modifiers == 'private':
			url = ''.join([self.URLS['private'], target_path])
			path = target_path

			timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
			if method == 'GET':
				text = ''.join([timestamp, method, path,])
				sign = self.get_sign(text)
				headers = self.set_headers_for_private(timestamp=timestamp,
														sign=sign)

				self.requests.append({'url': url,
										'method': method,
										'headers': headers,
										'params': params,
										})

			if method == 'POST':
				post_data = json.dumps(params)

				text = ''.join([timestamp, method, path, post_data])
				sign = self.get_sign(text)
				headers = self.set_headers_for_private(timestamp=timestamp,
														sign=sign)

				self.requests.append({'url': url,
										'method': method,
										'headers': headers,
										'params': post_data,
										})

			if method == 'PUT':
				post_data = json.dumps(params)
				
				text = ''.join([timestamp, method, path])
				sign = self.get_sign(text)
				headers = self.set_headers_for_private(timestamp=timestamp,
														sign=sign)
				self.requests.append({'url': url,
										'method': method,
										'headers': headers,
										'params': post_data,
										})
	def set_headers_for_private(self, timestamp, sign):
		""" private call set header

		Args:
			timestamp ([type]): [description]
			sign ([type]): [description]

		Returns:
			[type]: [description]
		"""
		headers = {'API-KEY': self.api_key,
					'API-TIMESTAMP': timestamp,
					'API-SIGN': sign}
		return headers

	def get_sign(self, text):
		""" get sign

		Args:
			text ([type]): [description]

		Returns:
			[type]: [description]
		"""
		sign = hmac.new(bytes(self.api_secret.encode('ascii')),
						bytes(text.encode('ascii')), hashlib.sha256).hexdigest()
		return sign

	async def fetch(self, request):
		""" fetch

		Args:
			request ([type]): [description]

		Returns:
			[type]: [description]
		"""
		status = 0
		content = []

		async with async_timeout.timeout(self.TIMEOUT):
			try:
				if self.session is None:
					self.session = await aiohttp.ClientSession().__aenter__()
				if request['method'] is 'GET':
					async with self.session.get(url=request['url'],
												params=request['params'],
												headers=request['headers']) as response:
						status = response.status
						content = await response.read()
						if status != 200:
							# エラーのログ出力など必要な場合
							pass

				elif request['method'] is 'POST':
					async with self.session.post(url=request['url'],
												data=request['params'],
												headers=request['headers']) as response:
						status = response.status
						content = await response.read()
						if status != 200:
							# エラーのログ出力など必要な場合
							pass

				elif request['method'] is 'PUT':
					async with self.session.put(url=request['url'],
												data=request['params'],
												headers=request['headers']) as response:
						status = response.status
						content = await response.read()
						if status != 200:
							# エラーのログ出力など必要な場合
							pass

				if len(content) == 0:
					result = []

				else:
					try:
						result = json.loads(content.decode('utf-8'))
					except Exception as e:
						traceback.print_exc()

				return result

			except Exception as e:
				# セッション終了
				if self.session is not None:
					await self.session.__aexit__(None, None, None)
					await asyncio.sleep(0)
					self.session = None

				traceback.print_exc()

	async def send(self):
		promises = [self.fetch(req) for req in self.requests]
		self.requests.clear()
		return await asyncio.gather(*promises)

	# ------------------------------------------------ #
	# public api
	# ------------------------------------------------ #
	# 取引所ステータス
	# 取引所の稼動状態を取得します。
	def status(self):
		params = {}
		self.set_request(method='GET', access_modifiers='public',
						target_path='/v1/status', params=params)
						
	# 最新レート
	# 指定した銘柄の最新レートを取得します。
	def ticker(self):
		params = {'symbol': self.SYMBOL}
		self.set_request(method='GET', access_modifiers='public',
						target_path='/v1/ticker', params=params)


	# 板情報
	# 指定した銘柄の板情報(snapshot)を取得します。
	def orderbooks(self):
		params = {'symbol': self.SYMBOL}
		self.set_request(method='GET', access_modifiers='public',
						target_path='/v1/orderbooks', params=params)


	# 取引履歴
	# 指定した銘柄の取引履歴を取得します。
	def trades(self, page=1, count=100):
		params = {'symbol': self.SYMBOL,
				'page': page,
				'count': count
				}
		self.set_request(method='GET', access_modifiers='public',
						target_path='/v1/trades', params=params)

	# ------------------------------------------------ #
	# private api
	# ------------------------------------------------ #

	# 余力情報を取得
	# 余力情報を取得します。
	def margin(self):
		params = {}

		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/account/margin', params=params)

	# 資産残高を取得
	# 資産残高を取得します。
	def assets(self):
		params = {}

		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/account/assets', params=params)
		


	# 注文情報取得
	# 指定した注文IDの注文情報を取得します。
	def orders(self, orderId):
		params = {'orderId': orderId}
		
		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/orders', params=params)


	# 有効注文一覧
	# 有効注文一覧を取得します。
	def activeOrders(self, page=1, count=100):
		params = {'symbol': self.SYMBOL,
					'page': page,
					'count': count
				}

		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/activeOrders', params=params)


	# 約定情報取得
	# 約定情報を取得します。
	def executions(self, orderId='', executionId=''):
		params = {'symbol': self.SYMBOL}
		if len(orderId) > 0:
			params['orderId'] = orderId
		elif len(executionId) > 0:
			params['executionId'] = executionId    

		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/executions', params=params)

	# 最新の約定一覧
	# 最新約定一覧を取得します。
	def latestExecutions(self, page=1, count=100):
		params = {'symbol': self.SYMBOL,
					'page': page,
					'count': count
				}

		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/latestExecutions', params=params)


	# 建玉一覧を取得
	# 有効建玉一覧を取得します。
	def openPositions(self, page=1, count=100):
		params = {'symbol': self.SYMBOL,
					'page': page,
					'count': count
				}

		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/openPositions', params=params)

	# 建玉サマリーを取得
	# 建玉サマリーを取得します。
	def positionSummary(self):
		params = {'symbol': self.SYMBOL}

		self.set_request(method='GET', access_modifiers='private',
						target_path='/v1/positionSummary', params=params)



	# 新規注文を出す
	def order(self, side, executionType, price, size, losscutPrice='', timeInForce=''):
		params = {'symbol': self.SYMBOL,
					'side': side,
					'executionType': executionType,
					'price': price,
					'size': size
				}
		if len(losscutPrice) > 0:
			params['losscutPrice'] = losscutPrice
		if len(timeInForce) > 0:
			params['timeInForce'] = timeInForce

		self.set_request(method='POST', access_modifiers='private',
						target_path='/v1/order', params=params)


	# 注文変更
	# 注文変更をします。
	# 対象: 現物取引、レバレッジ取引
	def changeOrder(self, orderId, price, losscutPrice=''):
		params = {'orderId': orderId,
					'price': price
				}
		if len(losscutPrice) > 0:
			params['losscutPrice'] = losscutPrice

		self.set_request(method='POST', access_modifiers='private',
						target_path='/v1/changeOrder', params=params)


	# 注文キャンセル
	# 注文取消をします。
	# 対象: 現物取引、レバレッジ取引
	def cancelOrder(self, orderId):
		params = {'orderId': orderId}
		
		self.set_request(method='POST', access_modifiers='private',
						target_path='/v1/cancelOrder', params=params)


	# 決済注文
	# 決済注文をします。
	# 対象: レバレッジ取引
	def closeOrder(self, side, executionType, price, settlePosition, timeInForce=''):
		params = {'symbol': self.SYMBOL,
					'side': side,
					'executionType': executionType,
					'price': price,
					'settlePosition': settlePosition
				}

		if len(timeInForce) > 0:
			params['timeInForce'] = timeInForce

		self.set_request(method='POST', access_modifiers='private',
						target_path='/v1/closeOrder', params=params)

	# 一括決済注文
	# 一括決済注文をします。
	# 対象: レバレッジ取引
	def closeBulkOrder(self, side, executionType, price, size, timeInForce=''):
		params = {'symbol': self.SYMBOL,
					'side': side,
					'executionType': executionType,
					'price': price,
					'size': size
				}
				
		if len(timeInForce) > 0:
			params['timeInForce'] = timeInForce

		self.set_request(method='POST', access_modifiers='private',
						target_path='/v1/closeBulkOrder', params=params)
				
	# ロスカットレート変更
	# 建玉のロスカットレート変更をします。
	# 対象: レバレッジ取引
	def changeLosscutPrice(self, positionId, losscutPrice):
		params = {'positionId': positionId,
					'losscutPrice': losscutPrice
				}
				
		self.set_request(method='POST', access_modifiers='private',
						target_path='/v1/changeLosscutPrice', params=params)
		
	# ---------------------------------------- #
	# Private WebSocket API 
	# ---------------------------------------- #
	# アクセストークンを取得
	# Private WebSocket API用のアクセストークンを取得します。
	def post_ws_auth(self):
		params = {}

		self.set_request(method='POST', access_modifiers='private',
						target_path='/v1/ws-auth', params=params)
						
	# アクセストークンを延長
	# Private WebSocket API用のアクセストークンを延長します。
	def put_ws_auth(self, token):
		params = {'token': token}
		
		self.set_request(method='PUT', access_modifiers='private',
						target_path='/v1/ws-auth', params=params)

	# アクセストークンを削除
	# Private WebSocket API用のアクセストークンを削除します。
	def delete_ws_auth(self, token):
		params = {'token': token}
		
		self.set_request(method='DELETE', access_modifiers='private',
						target_path='/v1/ws-auth', params=params)

	# ------------------------------------------------ #
	# WebSocket
	# ------------------------------------------------ #
	# Public WebSocket
	async def public_ws_run(self, callback):
		# 変数
		end_point_public = self.URLS['publicWS']

		while True:
			try:
				async with aiohttp.ClientSession() as session:
					# Public WebSocket
					async with session.ws_connect(end_point_public,
													receive_timeout=self.TIMEOUT) as client:

						if len(self.PUBLIC_CHANNELS) > 0:
							await self.subscribe(client, self.PUBLIC_CHANNELS)


						async for response in client:
							if response.type != WSMsgType.TEXT:
								print('response:' + str(response))
								break
							elif 'error' in response[1]:
								print(response[1])
								break
							else:
								data = json.loads(response[1])
								await self.handler(callback, data)

			except Exception as e:
				print(e)
				print(traceback.format_exc().strip())
				await asyncio.sleep(10)


	# Private WebSocket
	async def private_ws_run(self, callback):

		while True:
			try:
				async with aiohttp.ClientSession() as session:

					# トークンの取得
					if self.token == '':
						self.post_ws_auth()
						response = await self.send()
						self.token = response[0]['data']
			
					# 変数
					end_point_private = ''.join([self.URLS['privateWS'], '/', self.token])


					# Private WebSocket
					async with session.ws_connect(end_point_private,
													receive_timeout=self.TIMEOUT) as client:

						if len(self.PRIVATE_CHANNELS) > 0:
							await self.subscribe(client, self.PRIVATE_CHANNELS)


						async for response in client:
							if response.type != WSMsgType.TEXT:
								print('response:' + str(response))
								break
							elif 'error' in response[1]:
								print(response[1])
								break
							else:
								data = json.loads(response[1])
								await self.handler(callback, data)

			except Exception as e:
				print(e)
				print(traceback.format_exc().strip())
				await asyncio.sleep(10)
				
				if self.token != '':
					self.token = ''            


	# 購読
	async def subscribe(self, client, channels):
		for channel in channels:
			if channel == "trades":
				params = {"command":"subscribe", "channel":channel, "symbol": self.SYMBOL, "option": "TAKER_ONLY"}
			elif channel in ['ticker', 'orderbooks']:
				params = {"command":"subscribe", "channel":channel, "symbol": self.SYMBOL}
			elif channel == 'positionSummaryEvents':
				params = {"command":"subscribe", "channel":channel, "option": "PERIODIC"}
			else:
				params = {"command":"subscribe", "channel":channel}

			await asyncio.wait([client.send_str(json.dumps(params))])
			print('---- %s connect ----' %(channel))
			await asyncio.sleep(2)


	# トークンの延長
	async def extend_token(self):
		while True:
			try:
				await asyncio.sleep(self.EXTEND_TOKEN_TIME)
				if self.token != '':
					# トークンの延長
					self.put_ws_auth(self.token)
					response = await self.send()

			except Exception as e:
				print(e)
				print(traceback.format_exc().strip())

	# UTILS
	# コールバック、ハンドラー
	async def handler(self, func, *args):
		return await func(*args)