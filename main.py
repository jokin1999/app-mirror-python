import os
import json
import urllib3

# 下载器
def downloader(url, save_path) :
    print('-> Downloading: ' + url)
    header = urllib3.make_headers(basic_auth=ENV_AM_CLIENT_ID + ':' + ENV_AM_CLIENT_SECRET, user_agent=USER_AGENT)
    r = HTTP.request('GET', url, headers=header)
    data = r.data
    with open(save_path, 'wb') as f:
        f.write(data)
    print('-> Done.')

# 获取 Releases
def get_releases() :
    for owner in AM_LIST.keys():
        for item in AM_LIST[owner]:
            repo = item['repo']
            release = int(item['releases'])
            prerelease = int(item['pre-releases'])
            url = BASE_URL.format(owner, repo)
            # 下载 release 数据
            print('-> Start downloading: ' + owner + '/' + repo)
            header = urllib3.make_headers(basic_auth=ENV_AM_CLIENT_ID + ':' + ENV_AM_CLIENT_SECRET, user_agent=USER_AGENT)
            r = HTTP.request('GET', url, headers=header)
            if r.status != 200 :
                print('!! Failed: ' + owner + '/' + repo)
                print('!!   -> Status: ' + str(r.status))
            else:
                data = r.data.decode('UTF-8')
                with open('./public/' + owner + '/' + repo + '/all.json', 'w',  encoding='UTF-8') as f:
                    f.write(data)
                data = json.loads(data)
                # 独立 最新 Releases
                _latest = 0
                _release = 0
                data_releases = []
                _prerelease = 0
                data_prereleases = []
                for i in range(len(data)):
                    type = 'releases'
                    download = False
                    # 最新
                    if data[i]['draft'] == False:
                        d = {}
                        d['name'] = data[i]['name']
                        d['tag_name'] = data[i]['tag_name']
                        d['prerelease'] = data[i]['prerelease']
                        d['assets'] = data[i]['assets']

                        if _latest == 0:
                            download = True # 标记为下载
                            with open('./public/' + owner + '/' + repo + '/latest.json', 'w',  encoding='UTF-8') as f:
                                f.write(json.dumps(d))
                            _latest += 1

                        # pre-releases
                        if data[i]['prerelease'] == True:
                            type = 'pre-releases'
                            if _prerelease < prerelease or prerelease == 0:
                                data_prereleases.append(d)
                                download = True # 标记为下载
                                if _prerelease == 0 :
                                    with open('./public/' + owner + '/' + repo + '/latest_prerelease.json', 'w',  encoding='UTF-8') as f:
                                        f.write(json.dumps(d))
                                _prerelease += 1

                        # releases
                        if data[i]['prerelease'] == False:
                            type = 'releases'
                            if _release < release or release == 0:
                                data_releases.append(d)
                                download = True # 标记为下载
                                if _release == 0 :
                                    with open('./public/' + owner + '/' + repo + '/latest_release.json', 'w',  encoding='UTF-8') as f:
                                        f.write(json.dumps(d))
                                _release += 1

                        # 下载附件
                        if download == True and len(d['assets']) > 0:
                            for item in d['assets']:
                                path = './public/' + owner + '/' + repo + '/' + type + '/' + d['tag_name']
                                filename = './public/' + owner + '/' + repo + '/' + type + '/' + d['tag_name'] + '/' + item['name']
                                if not os.path.exists(path):
                                    os.makedirs(path)
                                if not os.path.exists(filename):
                                    downloader(item['browser_download_url'], filename)

                    # 写入 releases
                    with open('./public/' + owner + '/' + repo + '/releases.json', 'w',  encoding='UTF-8') as f:
                        f.write(json.dumps(data_releases))
                    # 写入 pre-releases
                    with open('./public/' + owner + '/' + repo + '/pre-releases.json', 'w',  encoding='UTF-8') as f:
                        f.write(json.dumps(data_prereleases))

            print('-> Done.')

def main() :
    # https://api.github.com/repos/jokin1999/quic-search/releases
    print("-> Running app-mirror-python")

    # 基础地址
    global BASE_URL
    global USER_AGENT
    BASE_URL = 'https://api.github.com/repos/{}/{}/releases'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'

    # 环境变量
    global ENV_AM_LIST
    amlist = os.getenv('AM_LIST')
    if amlist :
        ENV_AM_LIST = amlist
    else:
        # 使用默认
        # 格式： owner/repo/num of releases/num of pre-releases 0 = unlimited
        ENV_AM_LIST = 'app-mirror/app-mirror-python/2/1;'

    # 处理列表
    global AM_LIST
    AM_LIST = {}
    list = ENV_AM_LIST.split(';')
    for i in list:
        # 移除空项
        if i == '' : continue
        item = i.split('/')
        # 长度不为4即错误
        if len(item) != 4 : continue
        # 加入列表
        dist = {
        'repo': item[1],
        'releases': item[2],
        'pre-releases': item[3]
        }
        if AM_LIST.get(item[0], None) :
            AM_LIST[item[0]].append(dist)
        else:
            AM_LIST[item[0]] = [dist]

    # 创建公共文件夹
    if not os.path.exists('./public'):
        os.mkdir('./public')

    # 展示列表
    print('=========== LIST ===========')
    for owner in AM_LIST.keys():
        print('=> ' + owner)
        # 创建用户文件夹
        if not os.path.exists('./public/' + owner):
            os.mkdir('./public/' + owner)
        for repo in AM_LIST[owner]:
            print('   -> ' + repo['repo'] + ' @ ' + repo['releases'] + ',' + repo['pre-releases'])
            # 创建repo文件夹
            if not os.path.exists('./public/' + owner + '/' + repo['repo']):
                os.mkdir('./public/' + owner + '/' + repo['repo'])
                os.mkdir('./public/' + owner + '/' + repo['repo'] + '/releases')
                os.mkdir('./public/' + owner + '/' + repo['repo'] + '/pre-releases')
    print('============================')

    # API OAauth授权
    global ENV_AM_CLIENT_ID
    global ENV_AM_CLIENT_SECRET
    ENV_AM_CLIENT_ID = os.getenv('AM_CLIENT_ID') if os.getenv('AM_CLIENT_ID') else 'None'
    ENV_AM_CLIENT_SECRET = os.getenv('AM_CLIENT_SECRET') if os.getenv('AM_CLIENT_SECRET') else 'None'

    print('-> Login with CLIENT_ID: ' + (ENV_AM_CLIENT_ID if ENV_AM_CLIENT_ID else 'None'))

    # 基础组件
    global HTTP
    HTTP = urllib3.PoolManager()

    get_releases()

if __name__ == '__main__' :
    print("=================================================")
    print("||                 App  Mirror                 ||")
    print("||                Author: Jokin                ||")
    print("||               Version: v1.0.0               ||")
    print("=================================================")
    main()
