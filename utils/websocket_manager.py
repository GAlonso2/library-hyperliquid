import json
import asyncio
import threading
import websockets
import logging
from collections import defaultdict

from hyperliquid.utils.types import Any, Callable, Dict, List, NamedTuple, Optional, Subscription, Tuple, WsMsg

ActiveSubscription = NamedTuple("ActiveSubscription", [("callback", Callable[[Any], None]), ("subscription_id", int)])


class WebsocketManager():
    def __init__(self,
                 base_url,
                 logger=None,
                 process_message_function=None):
        self.logger = logger or logging.getLogger(__name__)
        self.url = "ws" + base_url[len("http") :] + "/ws"
        self.stop_stream = False
        self.ws = None
        self.subscription_id_counter = 0
        self.ws_ready = False
        self.queued_subscriptions: List[Tuple[Subscription, ActiveSubscription]] = []
        self.active_subscriptions: Dict[str, List[ActiveSubscription]] = defaultdict(list)
        self.subscriptions = []

        if not process_message_function:
            self.on_message = self.process_message
        else:
            self.on_message = process_message_function

        self.loop = None
        self.thread = None

    async def send_subscriptions(self):
        for subscription in self.subscriptions:
            await self.ws.send(
                json.dumps({
                    "method": "subscribe",
                    "subscription": subscription
                })
            )
            self.logger.info(f"Subscribed to {subscription}")

    async def run(self,
                  ping_interval=None,
                  retry_delay=1):
        self.is_running = True
        self.message_queue = asyncio.Queue()
        asyncio.create_task(self.get_message())
        self.logger.info(f"{self.__class__.__name__}: Connecting to stream...")
        while not self.stop_stream:
            try:
                async with websockets.connect(self.url,
                                                ping_interval=ping_interval,
                                                max_size=None) as ws:
                    self.ws = ws
                    await self.send_subscriptions()
                    self.logger.info(f"{self.__class__.__name__}: Connected to stream.")
                    while not self.stop_stream:
                        message = await ws.recv()
                        data = json.loads(message)
                        await self.message_queue.put(data)
                
            except websockets.exceptions.ConnectionClosedError as e:
                self.logger.warning(
                    f"Connection closed, retrying in {retry_delay} seconds..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

    def subscription_to_identifier(self,
                                   subscription: Subscription) -> str:
        if subscription["type"] == "allMids":
            return "allMids"
        elif subscription["type"] == "l2Book":
            return f'l2Book:{subscription["coin"].lower()}'
        elif subscription["type"] == "trades":
            return f'trades:{subscription["coin"].lower()}'
        elif subscription["type"] == "userEvents":
            return "userEvents"
        elif subscription["type"] == "userFills":
            return f'userFills:{subscription["user"].lower()}'
        elif subscription["type"] == "candle":
            return f'candle:{subscription["coin"].lower()},{subscription["interval"]}'
        elif subscription["type"] == "orderUpdates":
            return "orderUpdates"
        elif subscription["type"] == "userFundings":
            return f'userFundings:{subscription["user"].lower()}'
        elif subscription["type"] == "userNonFundingLedgerUpdates":
            return f'userNonFundingLedgerUpdates:{subscription["user"].lower()}'
        elif subscription["type"] == "webData2":
            return f'webData2:{subscription["user"].lower()}'
    
    def subscribe(
        self, subscription: Subscription, callback: Callable[[Any], None], subscription_id: Optional[int] = None
    ) -> int:
        self.logger.debug("subscribing")
        identifier = self.subscription_to_identifier(subscription)
        if identifier == "userEvents" or identifier == "orderUpdates":
            # TODO: ideally the userEvent and orderUpdates messages would include the user so that we can multiplex
            if len(self.active_subscriptions[identifier]) != 0:
                raise NotImplementedError(f"Cannot subscribe to {identifier} multiple times")
        self.active_subscriptions[identifier].append(ActiveSubscription(callback, subscription_id))
        self.subscriptions.append(subscription)
        
    
    async def _send_message(self, message):
        if self.ws:
            await self.ws.send(json.dumps(message))

    async def process_message(self, data):
        print(data)

    def _run_loop(self):
        """Creates and runs an asyncio event loop in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run())

    def start(self):
        """Starts the event loop in a separate thread to avoid blocking."""
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    async def get_message(self):
        while self.is_running:
            data = await self.message_queue.get()
            await self.on_message(data)

