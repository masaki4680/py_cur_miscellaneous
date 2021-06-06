import asyncio
import config
from gmocoin import GMOCoin

class TestV2():

	# ---------------------------------------- #
	# init
	# ---------------------------------------- #
	def __init__(self, api_key, api_secret):
		self.gmocoin = GMOCoin(api_key=api_key, api_secret=api_secret)


		# タスクの設定およびイベントループの開始
		loop = asyncio.get_event_loop()
		tasks = [
					self.gmocoin.public_ws_run(self.realtime),
					self.gmocoin.private_ws_run(self.realtime),
					self.gmocoin.extend_token(),
					self.run()
				]
				
		loop.run_until_complete(asyncio.wait(tasks))


	# ---------------------------------------- #
	# bot main
	# ---------------------------------------- #
	async def run(self):
		while(True):
			await self.main(5)
			await asyncio.sleep(0)
			
	async def main(self, interval):
		# main処理
		
		# 余力情報を取得 
		self.gmocoin.margin()
		response = await self.gmocoin.send()
		print(response[0])        


		'''
		# 買い指値を注文とキャンセル
		# 注文
		self.gmocoin.order(side='BUY', executionType='LIMIT', price=1000000 , size=0.01)
		response = await self.gmocoin.send()
		print(response[0])
		orderId = response[0]['data']
		
		# 注文キャンセル
		self.gmocoin.cancelOrder(orderId=orderId)
		response = await self.gmocoin.send()
		print(response[0])

		await asyncio.sleep(interval)
		'''


	# リアルタイムデータの受信
	async def realtime(self, data):
		# ここにWebSocketから配信されるデータが落ちてきますので適宜加工して利用してみてください。
		print(data)

		await asyncio.sleep(0)

# --------------------------------------- #
# main
# --------------------------------------- #
if __name__ == '__main__':

   api_key = config.GMO_API_KEY
   api_secret = config.GMO_API_SECRET
   
   TestV2(api_key=api_key, api_secret=api_secret)