import json
import os

class Settings:
    def __init__(self, filepath):
        self.__filepath = filepath

        data = None
        for encoding in ["utf-8","gbk"]:
            try:
                f = open(self.__filepath, 'r', encoding=encoding)
                content = f.read()
                data = json.loads(content)
                f.close()
                break
            except Exception as e:
                print("Settings.__init__() error:%s,encoding=%s|%s" % (str(e), encoding, str(self.__filepath)))
        if data:
            self.__data_str = str(data)
            self.enable_update = bool(data.get("enable_update",True))
            self.check_version_download_url = str(data.get("check_version_download_url",""))

            self.data = {
                "name": data.get("name"),
                "welcome": data.get("welcome"),
                "logo_url": data.get("logo_url"),
                "bottom_name": data.get("bottom_name"),
                "is_show_author": bool(data.get("is_show_author",True)),
                "author": data.get("author"),
                "author_link": data.get("author_link"),
                "auth_online_link": data.get("auth_online_link")
            }
        else:
            msg = "Settings.__init__() read %s error" % str(self.__filepath)
            raise Exception(msg)

    def __del__(self):
        pass

    def getStr(self):
        return self.__data_str

    def show(self):
        pass


class UserSettings:

    def __init__(self,logger):
        self.logger = logger
        self.filepath = ".user_settings"
        self.encoding = "utf-8"
        """
        内容示例：
        handle=dashboard,user_id=1,content=xxx1
        handle=dashboard,user_id=1,content=xxx2
        """

    def __readData(self):
        data = []

        try:
            if os.path.exists(self.filepath):
                f = open(self.filepath, 'r', encoding=self.encoding)
                lines = f.readlines()
                f.close()

                for line in lines:
                    d = {}
                    line = line.strip()
                    lineArray = line.split(",")
                    for kv in lineArray:
                        kvArray = kv.split("=")
                        if len(kvArray) == 2:
                            key = kvArray[0]
                            value = kvArray[1]
                            if key == "user_id":
                                value = int(value)
                            d[key] = value
                    data.append(d)
            else:
                raise Exception("filepath not found")
        except Exception as e:
            self.logger.error("UserSettings.__readData() filepath=%s,encoding=%s,e=%s" % (str(self.filepath),self.encoding,str(e)))

        return data

    def __writeData(self, data):
        try:
            f = open(self.filepath, 'w', encoding=self.encoding)
            for d in data:
                handle = d.get("handle")
                user_id = d.get("user_id")
                content = d.get("content")
                is_del = d.get("is_del",0)
                if is_del:
                    pass
                else:
                    line = "user_id=%d,handle=%s,content=%s\n" % (user_id, handle, content)
                    f.write(line)
            f.close()
        except Exception as e:
            self.logger.error("UserSettings.__writeData() filepath=%s,encoding=%s,e=%s" % (str(self.filepath),self.encoding,str(e)))

    def add(self,user_id,handle,content):
        data = self.__readData()
        if len(data) > 0:
            is_replace = False
            for index in range(len(data)):
                if user_id == data[index]["user_id"] and handle == data[index]["handle"]:
                    # 更新
                    data[index]["content"] = content
                    is_replace = True
                    break

            if not is_replace:
                data.append({
                    "user_id": user_id,
                    "handle": handle,
                    "content": content
                })
        else:
            data.append({
                "user_id": user_id,
                "handle": handle,
                "content": content
            })
        self.__writeData(data)

    def remove(self,user_id,handle):
        data = self.__readData()
        if len(data) > 0:
            for index in range(len(data)):
                if user_id == data[index]["user_id"] and handle == data[index]["handle"]:
                    # 删除
                    data[index]["is_del"] = 1
                    break

        self.__writeData(data)

    def get(self,user_id,handle):
        data = self.__readData()
        if len(data) > 0:
            for index in range(len(data)):
                if user_id == data[index]["user_id"] and handle == data[index]["handle"]:
                    return data[index]["content"]

        return None

