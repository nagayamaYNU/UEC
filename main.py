import csv
import json
import queue
import random
import threading
from web3 import Web3
import solcx
from solcx import compile_source, install_solc
import web3
import subprocess
import re
import cefpyco
import time
import sys
import pickle
from urllib.parse import unquote

graph = [[]]

#-----Eth関係-----
def get_private_key(account_addr_C, Pass):#checksumをしておく
    proc = subprocess.run('node get_key.js '+ account_addr_C + " " +  Pass, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)#jsonファイルとパスワードからkeyを取得
    print(proc.stdout)
    print(proc.stderr)
    key_array = re.findall("\d+",proc.stdout.decode('cp932'))#keyの中身を配列に格納
    privatekey = ""
    for i in range(len(key_array)):
        key_array[i] = format(int(key_array[i]), 'x')
        privatekey += key_array[i]
    return privatekey

def make_private_key(P_key):
    key_array = re.findall("\d+",P_key)#keyの中身を配列に格納
    privatekey = ""
    for i in range(len(key_array)):
        key_array[i] = format(int(key_array[i]), 'x')
        privatekey += key_array[i].zfill(2)
    return privatekey

def read_ip_add():#自身のIPアドレスを取得
    proc = subprocess.run("ip a", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)#ip aコマンド結果取得
    print("Standard Output:", proc.stdout.decode("cp932"))
    #address_array = re.findall("192\.168\.72\.\d+", proc.stdout.decode("cp932"))#ipアドレス取得
    address_array = re.findall("192\.168\.12\.\d+", proc.stdout.decode("cp932"))#ipアドレス取得
    print(address_array)
    return address_array[0]#おそらく必要なところ返せる

#-----階層構造の関数-----

#階層を追加する関数：path1 = [dir1,dir2,dir3,.....]のように引数を与える
def add_Path(path1):
    # addPath関数を送信
    tx = contract_instance.functions.addPath(path1).build_transaction({
        'from': myAddr,
        'gas': 3000000,
        'gasPrice': web3.toWei("21", "gwei"),
        'nonce': web3.eth.get_transaction_count(myAddr),
    })

    # トランザクションに署名して送信
    signed_tx = web3.eth.account.sign_transaction(tx, privatekey)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent with hash: {web3.toHex(tx_hash)}")

    # トランザクションの完了を待機
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction receipt:", receipt)

#階層をまとめて追加する関数：[[dir1,dir2,dir3,.....],[dir1,dir2,dir3,.....],[...],[...]]のように引数を与える
def add_MPath(path1):
    # addPath関数を送信
    tx = contract_instance.functions.addMultiplePaths(path1).build_transaction({
        'from': myAddr,
        'gas': 90000000,
        'gasPrice': web3.toWei("21", "gwei"),
        'nonce': web3.eth.get_transaction_count(myAddr),
    })

    # トランザクションに署名して送信
    signed_tx = web3.eth.account.sign_transaction(tx, privatekey)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent with hash: {web3.toHex(tx_hash)}")

    # トランザクションの完了を待機
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction receipt:", receipt)

#指定した階層よりも1つ下の階層の全要素を取得する関数:dir1/dir2/dir3でpath1 = [dir1,dir2]と送信するとdir3の層の要素名がすべてわかる
def get_Children(path1):
    print(path1)
    try:
        path = contract_instance.functions.getChildren(path1).call()
        # print(path1,"のchildren:", path)
        return path
    except:
        print("これ以上要素なし")
        return None

#指定した階層よりも1つ下の階層の要素数を取得する関数:dir1/dir2/dir3で[dir1,dir2]と送信するとdir3の層の要素数がすべてわかる
def get_childrenLength(path1):
    path = contract_instance.functions.getChildCount(path1).call()
    # print("The number of children:", path)
    return path

#-----情報登録関数-----

#ルータの情報を登録。IPアドレスと所属組織を登録(ブラックリストの登録は？？)
def add_router(ip_addr, organization):
    id = str(get_childrenLength(["router"])) #子の長さでＩＤを付ける
    # print(id)
    array =[["router", id, ip_addr],
            ["router", id, "attr", organization]]
    add_MPath(array)
    # print(get_Children(["router"]))

#コンテンツの情報を登録。コンテンツ名、避けたい組織、避けたいドメイン、ルータＩＤ
def add_Content(contentname, avoidOrganization, avoidDomainNames, router_ID):
    array =[["content",contentname, router_ID],
            ["content",contentname, "attr", contentname],
            ["content",contentname, "aviodattr", avoidOrganization],
            ["content",contentname, "aviodattr", avoidDomainNames]]

    add_MPath(array)

#リンクの情報を登録。ルータ１のＩＤ、ルータ２のＩＤ、１と２の間にあるドメイン名
#ただし、routerID1 ＜ routerID2
def add_Link(routerID1, routerID2, domainNames):
    array =[["link",routerID1, routerID2],
            ["link",routerID1, routerID2,"attr",domainNames]]

    add_MPath(array)

#-----情報取得関数-----

#ルータ情報を取得。
def get_router(router_id):
    router_IP = get_Children(["router", router_id])
    router_attr = get_Children(["router", router_id, "attr"])
    router_black = get_Children(["router", router_id, "black"])
    print("ルータ情報")
    print("Router IP:", router_IP)
    print("Router attributes:", router_attr)
    print("Router blacklist:", router_black)
    return router_attr

#コンテンツ情報を取得。
def get_Content(contentName):
    content_routerID = get_Children(["content", contentName])
    content_attr = get_Children(["content", contentName, "attr"])
    content_avoidattr = get_Children(["content", contentName, "aviodattr"])
    # print("コンテンツ情報")
    # print("router ID of Producer: ", content_routerID[0])
    # print("attribute: ", content_attr[0])
    # print("avoid attributes: ",content_avoidattr)
    return content_routerID, content_attr, content_avoidattr

#リンク情報を取得。
def get_Link(router_id1):
    nearby = get_Children(["link",str(router_id1)])
    if nearby == None:
        return None,None
    # print("リンク情報")
    # print("nearby",nearby)
    all_attr = []
    for i in range(len(nearby)):
        attr = get_Children(["link", router_id1, str(nearby[i]),"attr"])
        all_attr.append(attr)
    # print("attributes", all_attr)
    # print(type(all_attr[0]))
    return nearby, all_attr

#ルータのＩＰアドレスを取得。
def get_IPaddr(router_id):
    ip = get_Children(["router", str(router_id)])
    return ip[0]

#ルータＩＤに登録されたブラックリストを取得
def get_Blacklist(router_id):
    blacklist = get_Children(["router", str(router_id), "black"])
    return blacklist

#-----経路計算関係-----

#ダイクストラで経路計算
def dijkstra(graph, start):
    n = len(graph)
    visited = [False] * n
    distance = [sys.maxsize] * n
    distance[start] = 0
    previous = [None] * n
    while True:
        # 最小距離の未訪問ノードを見つける
        min_distance = sys.maxsize
        u = -1
        for i in range(n):
            if not visited[i] and distance[i] < min_distance:
                min_distance = distance[i]
                u = i
        if u == -1:  # すべてのノードを訪問した場合
            break
        visited[u] = True
        # uから到達可能なノードの距離を更新する
        for v in range(n):
            if graph[u][v] is not None and not visited[v]:
                new_distance = distance[u] + 1
                if new_distance < distance[v]:
                    distance[v] = new_distance
                    previous[v] = u
                    
    # 最短経路のリストを作成
    path = []
    for i in range(n):
        path.append([])
        if i == start:
            continue
        if distance[i] == sys.maxsize:  # 到達不可能
            path[i] = None
        else:
            node = i
            while node is not None:
                path[i].insert(0, node)
                node = previous[node]
    return path

#-----ハッシュ探索で-----

# グローバル変数を辞書形式に変更
#ルータとリンクの情報を分けて管理し、経路計算の際に使う
router_info = {}  # { router_id: { "organization": "..." } }
link_info = {}  # { (router1, router2): { "domains": [...] } }

#ハッシュ探索のためのハッシュテーブル作成
    #Ethからrouter_infoとlink_infoに情報を格納
def build_graph():
    global router_info, link_info, organization_index
    num_routers = get_childrenLength(["router"])

    router_info = {}  # ルータ情報を辞書に
    link_info = {}  # リンク情報を辞書に
    organization_index = {}  # 組織名ごとのルータIDセット

    # ルータ情報の取得とハッシュテーブル化
    for router_id in range(num_routers):
        organizations = get_router(str(router_id))  # 組織名のリスト

        router_info[router_id] = {"organization": organizations}  # リストを格納

        # 検索用インデックスの作成
        #組織の属性を避ける場合、トポロジーの大部分を削除できるため、優先的に調べられるようにIndexを設けた
        for org in organizations:
            if org not in organization_index:
                organization_index[org] = set()  # 初回のみセットを作成
            organization_index[org].add(router_id)  # ルータIDをセットに追加

    # リンク情報の取得とハッシュテーブル化
    for router_id1 in range(num_routers):
        nearby, all_attr = get_Link(str(router_id1))
        if nearby is not None:
            for i in range(len(nearby)):
                if nearby[i] is not None:
                    router_id2 = int(nearby[i])
                    domain_names = all_attr[i]

                    # (router_id1, router_id2) のペアでリンク情報を保持
                    link_info[(router_id1, router_id2)] = {"domains": domain_names}
                    link_info[(router_id2, router_id1)] = {"domains": domain_names}  # 双方向

    print("graph作成完了")
    print("organization_index:", organization_index)  # 確認用


#Consumerまでのルート計算
def route_cal(contentname, ID_of_consumer):
    print("route_cal1開始")

    # コンテンツ情報から属性を取得
    content_routerID, content_attr, content_avoidattr = get_Content(contentname)

    # ブラックリストを取得し、セットに変換して高速化
    blacklist = set(get_Blacklist(content_routerID[0]) or [])
    if content_avoidattr:
        blacklist.update(content_avoidattr)

    join_avoid_attr = blacklist
    if not join_avoid_attr:
        print("避けたい属性は設定されていないよ")

    print("避けたい属性:", join_avoid_attr)

    # ** 避けたい組織のルータIDを取得**
    avoid_routers = set()
    for attr in join_avoid_attr:
        avoid_routers.update(organization_index.get(attr, set()))  # O(1) で取得

    print("避けたいルータID:", avoid_routers)

    # ルータのIDの最大値を取得し、隣接行列のサイズを決定
    router_ids = sorted(router_info.keys())
    n = max(router_ids) + 1

    # 隣接行列を None で初期化。この隣接行列で経路計算をおこなう
    adjacency_matrix = [[None] * n for _ in range(n)]

    # ** 接続情報を反映（避けたいルータとリンクをスキップ）**
    # 通過しても良い部分を1として反映させている。
    # (ルータ間の距離などを考慮したい場合には、１ではなくルータ間の距離や遅延時間を代入させるべき)
    for (router1, router2), info in link_info.items():
        if router1 in avoid_routers or router2 in avoid_routers:
            continue  # 避けたいルータが含まれる場合はスキップ

        if any(domain in join_avoid_attr for domain in info["domains"]):
            continue  # 避けたい属性を持つリンクならスキップ

        adjacency_matrix[router1][router2] = 1 #この1という値をルータ間の距離に変えるとより良い
        adjacency_matrix[router2][router1] = 1  # 無向グラフ

    print("隣接行列を作りました")
    print_2d_array(adjacency_matrix)
    print("Content_no_routerID:", content_routerID[0])

    # ** ダイクストラ法で最短経路を計算**
    path = dijkstra(adjacency_matrix, int(content_routerID[0]))
    route = path[ID_of_consumer]
    if route is None:
        print("最短経路が見つかりませんでした。")

    print("ダイクストラ法での最短経路計算結果:", route)
    print("ダイクストラ法完了")

    return route, join_avoid_attr, content_routerID


#-----Cefore関係-----
def receive_Interest(handle, addroute, ID): #相手からInterestを受け取るまで待ち、それに対してdataを送る
    #Cefore通信のHandleを複数立てると初めに建てたHandleが消える？？ので、初めに立てたHandleを引数として利用する。
    print("Interest受信スレッドを開始")

    Pre_Interest_name = "ccnx:/query" + str(ID) + "/mkFIB/" + str(ID) #
    handle.send_interest(Pre_Interest_name,0)#preInterest送信
    print(Pre_Interest_name,"のインタレストを送信")
    handle.register("ccnx:/mkFIB2")

    #別スレッドを立てて並列処理させたかったができなかった。
    while True:
        info1 = handle.receive()
        print("別スレ info:",info1)
        if info1.is_interest:
            print(f"別スレ Interestパケットを受信: {info1.name}")
            print(f"別スレ データ内容: {addroute}")
            if "mkFIB2/pre" in info1.name:
                handle.send_data(info1.name, addroute , chunk_num=info1.chunk_num, expiry=3600000, cache_time=0)
                print("dataパケットの送信に成功")
                # 必要に応じて受信データを処理
                print("別スレ終了")
                break  # 一度だけ受信する場合はbreakする

    print("whileループを抜けただけ")   

#作成した経路を登録する関数。(表記を変えないと登録できなかった)
def add_ContentRoute(contentname, route):
    route = "_".join(map(str, route))
    print("ルートを変換しました", route)
    array = ["content",contentname, "route", route]
    add_Path(array)
 
#-----おまけ-----
def print_2d_array(array):
    for row in array:
        print(row)

#-----Eth通信のための前処理(前操作)-----
networkid = 12345
maxpeers = 10
http_port = 8101
my_ip_addr = read_ip_add() #get IP addr.
helloPrefix = "ccnx:/" + "hello"

print("my_ip_addr:{}".format(my_ip_addr))

Pass_word = "ethenode0001"#自分のパスワード
my_Account_num = 0 #アカウントの番号

#イーサリアムに接続
#web3 = Web3(web3.HTTPProvider("http://localhost:"+str(http_port)))
web3 = Web3(web3.HTTPProvider("http://"+my_ip_addr+":8101"))


#自身のenode情報を格納
node_info = web3.geth.admin.node_info()#enode情報を格納
print(node_info)
print(node_info.enode)
enode_addr = re.sub("@.+", "", node_info.enode)#@以降を削除

enode_addr = enode_addr +"@" + my_ip_addr + ":30303"#相手が登録できる形に変更“enode:// <enode addr.> @ <自身のIP addr.>”


print("enode_addr: " + enode_addr)

#自身のアドレス設定と鍵の入手
myAddr = web3.to_checksum_address(web3.eth.accounts[0])
#privatekey = get_private_key(myAddr, Pass_word)
# P_key="242 137 133 155 113 81 65 197 20 46 169 195 58 84 119 10 12 101 85 21 213 227 87 240 28 212 90 210 146 196 27"
P_key="242 137 133 155 113 81 65 197 20 46 169 195 58 84 119 10 12 101 85 21 213 227 87 240 28 212 90 210 146 196 27 37"
privatekey = make_private_key(P_key)
print("privatekey")
print(privatekey)



# マイニング設定(起動時に設定しないとだめ?) or マイナーの設定は手動でやる??
# Solidity のソースをコンパイル 文章を生成するようにすればいけそう?
# solcx.get_installable_solc_versions()
# solcxで.solのソースコードをコンパイル
compiled_sol = solcx.compile_files(
    ["omg.sol"],
    output_values=["abi", "bin"],
    solc_version="0.8.0"
)

# コントラクトインターフェイス
contract_id, contract_interface = compiled_sol.popitem()

# バイトコードとABI
bytecode = contract_interface['bin']
abi = contract_interface['abi']

#ABIの表示
print("ABI")
print(abi)
print(type(abi))

# コントラクトの作成
contract = web3.eth.contract(abi=abi, bytecode=bytecode)

#トランザクションの生成
print(f"[DEBUG] nonce1 { web3.eth.get_transaction_count(myAddr)}")

tx = contract.constructor().build_transaction({
    'from': myAddr,
    'nonce': web3.eth.get_transaction_count(myAddr),
    'gas': 5028712,
    'gasPrice': web3.toWei('21', 'gwei')})

print(f"[DEBUG] nonce2 { web3.eth.get_transaction_count(myAddr)}")

signed_tx = web3.eth.account.sign_transaction(tx, privatekey) #privatekeyで署名
tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction) #トランザクションの送信

print(web3.toHex(tx_hash)) #トランザクションIDの取得

tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash) #生成されたコントラクトアドレスの取得(マイニングしてないと進まない)
print("Contract Deployed At:", tx_receipt['contractAddress'])

Networking_contract_id = tx_receipt['contractAddress']

# これは55万属性を登録したときのアドレス
# Networking_contract_id = 0xf486a33D6341fE30B369f48E044b5Ba6bCfa98A6

print(Networking_contract_id)

time.sleep(1)

NCI_C = web3.toChecksumAddress(Networking_contract_id)
contract_instance = web3.eth.contract(abi=abi, address=NCI_C)
print("Contract_instance!!!!{}".format(contract_instance))

print(f"[DEBUG] nonce3 { web3.eth.get_transaction_count(myAddr)}")

#-----(実験のための情報登録)-----
#階層構造を初期化
add_MPath([["content"],["router"],["link"]])

#コンテンツ登録

#トポロジー上に存在する属性を生成
def generate_array(n):
    categories = ["A", "B", "D01", "D02", "D12", "D13", "D23"]
    array = [""]  # 初期値に空文字を追加
    for prefix in categories:
        for i in range(1, n + 1):  # 1からnまでの数字を生成
            array.append(f"{prefix}_{i}")
    # print(array)
    return array


def generate_content_data(array2):
    # コンテンツリストの初期化
    ccc = []

    # コンテンツを生成
    for j in range(1, 4):  # jは1から8まで（ｐごとに区切るため）
        p = 100 #ｐ個一気に登録
        print("!!!!!", j, "回目！！")
        ccc = []
        for i in range((j - 1) * p + 1, j * p + 1):
            if i > 250:  # iが500を超えたら終了
                break
            content_id = f"content{str(i).zfill(4)}"
            # 基本データを追加
            ccc.append(["content", content_id, "0"])
            ccc.append(["content", content_id, "attr", content_id])

            # avoidattr をランダムに 2 つ選択(以下の操作はコンテンツ別に避けたい属性を設定するための物なので、
            # ブラックリストを使う場合は必要ない)
            avoidattr1 = random.choice(array2)
            avoidattr2 = random.choice(array2)

            if avoidattr1:
               ccc.append(["content", content_id, "aviodattr", avoidattr1])
            if avoidattr2:
                ccc.append(["content", content_id, "aviodattr", avoidattr2])

            
        add_MPath(ccc)

        # # 結果を出力
        # for entry in ccc:
        #     print(entry)




# router登録
#各ルータに設定したい属性の数をｎとして、情報を登録する
def generate_router_data(n, array2):
    routers = []  # データを収集するリスト
    count = 0  # 要素数をカウント
    p = 2 # ブラックリストに登録する属性
    del array2[0] #配列の0番目にある属性なしの場合を表す要素を削除

    # ルーター情報を準備
    router_info = [
        # {"id": "0", "ip": "192.222.22.21", "attrs": ["UEC"], "black": random.sample(array2, p)},（ブラックリストに登録する属性をランダムに選ぶ場合に利用）
        {"id": "0", "ip": "192.222.22.21", "attrs": ["UEC"], "black": ["D01_1", "D13_1"]},
        {"id": "1", "ip": "192.222.22.22", "attrs": [f"A_{i}" for i in range(1, n + 1)]},
        {"id": "2", "ip": "192.222.22.23", "attrs": [f"B_{i}" for i in range(1, n + 1)]},
        {"id": "3", "ip": "192.222.22.24", "attrs": ["TAT"]},
    ]

    # ルーター情報を順番に処理
    for router in router_info:
        router_id = router["id"]
        ip_address = router["ip"]
        attrs = router["attrs"]
        black_attrs = router.get("black", [])  # black 属性が存在しない場合は空リスト

        # IPアドレスを登録
        routers.append(["router", router_id, ip_address])
        count += 1
        if count >= 75:  # 75要素を超えたらadd_MPathを呼び出す 
            #(Ethに1度で登録できるデータ量は限られているため、何回かに分けて登録している)

            add_MPath(routers)
            routers = []
            count = 0

        # 属性を登録
        for attr in attrs:
            routers.append(["router", router_id, "attr", attr])
            count += 1
            if count >= 75:  # 75要素を超えたらadd_MPathを呼び出す
                add_MPath(routers)
                # print(routers)
                print("ルータ登録中")
                routers = []
                count = 0

        # black 属性を登録
        for black_attr in black_attrs:
            routers.append(["router", router_id, "black", black_attr])
            count += 1
            if count >= 75:  # 75要素を超えたらadd_MPathを呼び出す
                add_MPath(routers)
                # print(routers)
                routers = []
                count = 0

    # 残りのデータをadd_MPathに渡す
    if routers:
        add_MPath(routers)
        # print(routers)

# Link登録

#リンクの情報を登録。nは各リンクに設定する属性の数
def generate_links(n):
    links_info1 = []
    pairs = [("0", "1"), ("0", "2"), ("1", "2"), ("1", "3"), ("2", "3")]
    for src, dest in pairs:
        for i in range(1, n + 1):  # 1からnまでの数字を生成
            links_info1.append(["link", src, dest, "attr", f"D{src}{dest}_{i}"])
    
    links = []  # データを収集するリスト
    count = 0  # 要素数をカウント
    for link in links_info1:
        links.append(link)
        count += 1
        if count == 75:  # 50要素を超えたらadd_MPathを呼び出す
            add_MPath(links)
            # print(links)
            print("リンク登録中")
            links = []
            count = 0

    if links:
        add_MPath(links)
        # print(links)

# 情報登録とグラフ作成を一気に行う。ｎは各ルータやリンクに設定したい属性の数
def letsgo(n):
    array5 = generate_array(n)
    generate_content_data(array5)
    generate_router_data(n, array5)
    generate_links(n)
    build_graph()

# レッツゴー！！！（実験に必要なデータを登録してグラフを作成する）
letsgo(15625)
print(router_info)
print(link_info)

#-----試行錯誤の残骸-----

# print("ブラックリストの中身",get_Blacklist(0))
# get_Link("0")
# get_childrenLength(["router"])
# newgraph1 = del_graph(graph, ["A_1"])
# route_cal1("content0001",3)
# get_router(0)
# bbb = ["attr","router","org1"]
# get_Children(bbb)


#-----Cefore通信開始-----

start_time1 = 0
middle_time1 = 0
middle_time2 = 0
end_time1 = 0

with cefpyco.create_handle() as handle:
    
    #handle.send_interest()#最初のノードはやらない
    handle.register(helloPrefix)#helloを受信する用
    handle.register("ccnx:/query")#ethereumなしノードとの通信に利用
    handle.register("ccnx:/mkFIB2")

    #接続ループをつくるべき? 接続でfunc_array = ["connect", "ABI", "C_addr"]きたら削除??
    while True:
        info = handle.receive()#packetの受信
        print("info:",info)
        # print(info.name)
        if info.is_succeeded:#packetが受信成功
            print("info_success")
            if info.is_interest:#interestパケットの場合
                print("interest")
                if "query" in info.name:
                    print("queryです")
                    arg_s = re.split("/", info.name)#arg_s[0] = "ccnx:", arg_s[1] = "query", arg_s[2] = <function_name>, arg_s[3]以降に引数
                    if("regist_C" in info.name):#ccnx:/query/regist_C/コンテンツ名/組織/[避けたい属性]/登録ルータID(1つ)
                        # この通信は使ってません
                        print("regist_C received")
                        print("コンテンツ名",arg_s[3])
                        print("組織",arg_s[4])
                        print("避けたい属性",unquote(arg_s[5]))
                        print("登録ルータID",int(arg_s[6]))
                        tx = contract_instance.functions.addContent(arg_s[3],arg_s[4],[unquote(arg_s[5])],int(arg_s[6])).build_transaction({
                            "from": myAddr,
                            "nonce": web3.eth.get_transaction_count(myAddr),
                            "gas": 1728712,
                            "gasPrice": web3.toWei("21", "gwei")
                        })
                        signed_tx = web3.eth.account.sign_transaction(tx, privatekey)
                        tx_hash =web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                        handle.send_data(info.name, "FIN", chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
                        print("dataパケットの送信に成功")
                        print(get_Content("content001"))

                    
                    elif("mkgraph" in info.name):#グラフ作成用
                        # この通信は使ってません
                        print("mkgraph received")#ccnx:/query/mkgraph
                        # num_routers = 4  # 必要に応じてルータ数を設定
                        # num_links = 5    # 必要に応じてリンク数を設定
                        build_graph()
                        print("グラフ作成に成功")
                        handle.send_data(info.name, "FIN", chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
                        print("dataパケットの送信に成功")

                    elif("mkpre" in info.name):#PreInterest送信用のFIBを作成用
                        print("mkpre received")#ccnx:/query/mkgraph

                        #追加するルータとETHまでの経路にPreInterest送信用のFIBを作成させる.
                        n = len(graph)
                        # print_2d_array(graph)
                        for i in range(n-1):
                            for j in range(i, n):
                                if i!=j and graph[i][j] is not None:
                                    Prefix = "ccnx:/query1/mkFIB/" + str(j)
                                    print(Prefix,"を送信します")
                                    handle.send_interest(Prefix,0)
                                    print(Prefix,"を送信完了！")
                                    # handle.register("ccnx:/query/mkFIB/" + str(j))

                                    # info = handle.receive()#これで相手ルータからのInterestを受け取る
                                        
                                    # handle.register("ccnx:/query/mkFIB/0")
                                    # handle.register("ccnx:/query/mkFIB2/" + str(j))
                    
                elif "mkFIB2" in info.name:#これで相手ルータに,Ethノード --> ルータのFIB作成コマンドを送り付ける
                    print("mkFIB2です")
                    print(info.name, "received")
                    arg_s = re.split("/", info.name)#arg_s[0] = "ccnx:", arg_s[1] = "mkFIB2", arg_s[2] = "pre", arg_s[3]以降に引数
                    if "pre" in info.name:
                        addroute ='sudo cefroute add ' + 'ccnx:/lplplp' + ' udp ' + str(get_IPaddr(arg_s[3]))
                        print(addroute, "を送信します")
                        handle.send_data(info.name, addroute , chunk_num=info.chunk_num, expiry=3600000, cache_time=0)

                    elif "mk_route" in info.name:#ルート計算用
                        start_time1 = time.perf_counter()
    
                        print("mk_route received")#ccnx:/mkFIB2/mk_route/コンテンツ名/消費者のID
                        print("コンテンツ名",arg_s[3])
                        print("ConsumerのID",arg_s[4])
                        route, avoid_attr, content_routerID = route_cal(arg_s[3],int(arg_s[4]))
                        print("ルート検索の結果",route)
                        middle_time1 = time.perf_counter()

                        success = True

                        if route is None:
                            handle.send_data(info.name, "We cannot find the route because attributes are too strictly !!", chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
                            print("コンテンツ経路作成完了のDataパケット送信した",info)
                            success = False
                            middle_time2 = time.perf_counter()

                        else:
                            for i in range(len(route)-1):
                                print("宛先のルータID: ",int(route[i+1]) )
                                addroute ='sudo cefroute add ' + 'ccnx:/'+ str(arg_s[3]) + ' udp ' + get_IPaddr(int(route[i+1]))
                                print("実行コマンド",addroute)

                                if route[i] == 0:
                                    # order = addroute.payload.decode("utf-8")
                                    # order = order.strip("'")
                                    order = addroute.split()
                                    subprocess.run(order)
                                    print("このノードでコマンドを実行しました", order)
                                
                                else:
                                    id = route[i]
                                    #receive_Interest(handle, addroute, Interest_name)
                                    receiver_thread = threading.Thread(target=receive_Interest, args=(handle, addroute, id))
                                    receiver_thread.start()
                                    receiver_thread.join()
                                    print("別スレをちゃんと抜けられた!")


                                #相手からInterestが送られてきたとき、下にあるdataパケットを送信したいがどうする？
                                #並列さぎょうするために別スレッド（pyてょんにコマンドあり）を立てるか、まつ。(メインが止まって困らないならまつ)
                                # handle.send_data(info.name, addroute , chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
                            
                                    
                            handle.send_data(info.name, "mk_route is successed by EthRouter", chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
                            print("コンテンツ経路作成完了のDataパケット送信した",info)
                            middle_time2 = time.perf_counter()
                            add_ContentRoute(arg_s[3], route)

                        # add_ContentRoute(arg_s[3], route)

                        end_time1 = time.perf_counter()  # 高精度の終了時刻
                        elapsed_time1 = end_time1 - start_time1
                        print(f"Execution time: {elapsed_time1:.8f} seconds")

                        cal_time = middle_time1 - start_time1
                        addroute_time = middle_time2 - start_time1

                        # CSVファイルへの出力
                        csv_file = "20250228_E_attr.csv"
                        # ヘッダーを追加する必要があるかチェック
                        write_header = False
                        try:
                            with open(csv_file, "x") as file:
                                write_header = True
                        except FileExistsError:
                            pass

                        # データを追記
                        with open(csv_file, "a", newline="") as file:
                            writer = csv.writer(file)
                            if write_header:
                                writer.writerow(["経路作成Execution", "コンテンツ名", "避ける属性","経路", "経路作成可否", "Time (seconds)","starttime","endtime", "middle1","middle2","cal_time","addroute_time"])  # ヘッダーを記述
                            writer.writerow([f"Run-{time.strftime('%Y-%m-%d %H:%M:%S')}", arg_s[3] ,avoid_attr,route, success, f"{elapsed_time1:.8f}",f"{start_time1:.8f}",f"{end_time1:.8f}",
                                             f"{middle_time1:.8f}",f"{middle_time2:.8f}",f"{cal_time:.8f}",f"{addroute_time:.8f}"])


                        
                        # handle.send_data(info.name, "FIN", chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
                        # print("dataパケットの送信に成功")
    

            elif info.is_data:#dataパケットの場合
                print("data")
                if "mkFIB" in info.name:
                    print("mkFIBが来た")