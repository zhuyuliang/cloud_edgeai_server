import time
import requests
import json

def openImportUpdate2():
    t1 = time.time()
    headers = {
        "User-Agent": "eai_admin",
        "Content-Type": "application/json;",
        "Safe": "你的edgeaiSafe集群密钥"
    }
    params = {
        "url":"http://192.168.1.105:9824/static/storage/temp/xcms.4.708.x64.windows.ovtrt.xcupdate",
    }
    res = requests.post(url='%s/system/openImportUpdate2' % "http://192.168.1.105:9001",
                        headers=headers, data=json.dumps(params), timeout=300)
    t2 = time.time()

    print(res.status_code,"spend ms",t2-t1)
    print(res.json())

if __name__ == '__main__':
    openImportUpdate2()

    info = {
        "a":1,
        "bb":"hello"
    }
    import json
    info_str = json.dumps(info)

    print(type(info_str),info_str)

    pass
    a1 = "live-camjfiweo3"
    a2 = "live-cam-jfiweo3"
    a3 = "live-cam-jfiweo3-fds"

    arr = a3.split("-")
    src_stream_app = arr[0]
    src_stream_name = "-".join(arr[1:])

    print(arr)
    print(src_stream_app)
    print(src_stream_name)





