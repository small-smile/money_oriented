import json, urllib.request, time, sys, asyncio
import websockets

def ws_url():
    for _ in range(40):
        try:
            r = urllib.request.urlopen('http://127.0.0.1:9222/json', timeout=2)
            tabs = json.load(r)
            for t in tabs:
                if t.get('type') == 'page' and t.get('webSocketDebuggerUrl'):
                    return t['webSocketDebuggerUrl']
        except Exception:
            pass
        time.sleep(0.5)
    return None

PROBE = r"""
(function(){
  var els=document.querySelectorAll('div');
  var res={rendered:0, empty:[], total:0};
  els.forEach(function(el){
    try{
      var ins = (window.echarts && echarts.getInstanceByDom(el));
      if(ins){
        res.total++;
        var op=ins.getOption();
        var s=(op.series||[]);
        var has = s.some(function(x){return x.data && x.data.length>0;});
        if(has){res.rendered++;} else {res.empty.push(el.id||'?');}
      }
    }catch(e){}
  });
  return JSON.stringify(res);
})()
"""

async def run(url, probe):
    URL = ws_url()
    if not URL:
        return "NO_CDP"
    async with websockets.connect(URL, max_size=None, open_timeout=30) as ws:
        mid = [0]
        async def send(method, params=None):
            mid[0]+=1
            await ws.send(json.dumps({'id':mid[0],'method':method,'params':params or {}}))
            while True:
                m=json.loads(await ws.recv())
                if m.get('id')==mid[0]:
                    return m
        await send('Page.enable')
        await send('Runtime.enable')
        await send('Page.navigate', {'url':url})
        await asyncio.sleep(5.0)
        r=await send('Runtime.evaluate', {'expression':probe,'returnByValue':True,'awaitPromise':True})
        return r.get('result',{}).get('result',{}).get('value')

async def main():
    for code in sys.argv[1:]:
        url = "http://127.0.0.1:5000/dashboard/company/bank/index.html?code=%s"%code
        try:
            v=await run(url, PROBE)
            print(code, v)
        except Exception as e:
            print(code, "ERR", repr(e))

asyncio.run(main())
