#!/usr/bin/env python3
import asyncio
import sys

try:
    import websockets
except ImportError:
    print("websockets не установлен. Установите: pip install websockets", file=sys.stderr)
    sys.exit(2)

async def main():
    uri = "ws://localhost/ws/"
    try:
        async with websockets.connect(uri) as ws:
            print("connected")
            await ws.send("ping")
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                print("recv:", msg)
            except asyncio.TimeoutError:
                print("no reply from server")
    except Exception as e:
        # печатаем подробности ошибки для диагностики
        print("error:", repr(e))
        status = getattr(e, 'status_code', None)
        if status:
            print("http_status:", status)

if __name__ == '__main__':
    asyncio.run(main())
