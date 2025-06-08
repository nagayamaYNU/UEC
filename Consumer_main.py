import csv
import re
import subprocess
import time
import cefpyco

#このファイルは、通信の準備のためのものであり、このファイルの実行が完了した後に、
# 別ファイルでコンテンツ取得要求や経路作成要求を、Ethに送る。

# state = "INITIAL"

with cefpyco.create_handle() as handle:
    #-----情報登録をCeforeの通信を用いて行いたい場合は、以下のコメントアウトをすべて解除してください-----
    
    #ルータ情報を登録
    # handle.send_interest("ccnx:/query/regist_R/192.168.12.152/UEC/%5B1%2C2%5D",0)  

    #リンク情報を登録    
    # handle.send_interest("ccnx:/query/regist_L/0/1/jp",0)
        
    #コンテンツ情報を登録    
    # handle.send_interest("ccnx:/query/regist_C/content001/UEC/%5Bus%5D/0",0)

    #グラフを作成させる(最後に登録したルータのみ実行)
    # handle.send_interest("ccnx:/query/mkgraph",0)

    #PreInterest送信用のFIBを作成させる(最後に登録したルータのみ実行)
    # handle.send_interest("ccnx:/query/mkpre",0)
    handle.register("ccnx:/query")
    handle.register("ccnx:/query1")


    # while True:
        
    #     info = handle.receive()
    #     print("info:",info)

    #     if state == "INITIAL" and info.is_succeeded:#packetが受信成功
    #         print("info_success")
    #         # データパケットを受信するかチェック
    #         if info.is_data:  # データパケットを受信した場合
    #             print("Received Data Packet:")
    #             print(f"Name: {info.name}")
    #             print(f"Payload: {info.payload}")

    #             if "mkFIB2/pre/1" in info.name:
    #                 print("FIB作成命令を受け取りました")
    #                 print("payloadの中身",info.payload)
    #                 order = info.payload.decode("utf-8")
    #                 order = order.strip("'")
    #                 print(order, "orderの中身")
    #                 order_parts = order.split()
    #                 subprocess.run(order_parts)
    #                 print("FIB作成命令を実行しました")
                    
                
                
    #             elif "mkgraph" in info.name:
    #                 print("グラフ生成完了")
    #                 state = "SECOND"
    #                 break

    #             elif "mkpre" in info.name:
    #                 print("PreInterest送信用のFIB作成完了")

                     
    #         elif info.is_interest:
    #             print("interest")
    #             if "query1" in info.name:
    #                 print("query1です")
    #                 arg_s = re.split("/", info.name)#arg_s[0] = "ccnx:", arg_s[1] = "query", arg_s[2] = <function_name>, arg_s[3]以降に引数
    #                 #FIB作成命令を受け取るために
    #                 if "mkFIB/4" in info.name:#ccnx:/query1/mkFIB/ルータID
    #                     print("mkFIB received")
    #                     print("ルータID",arg_s[3])
    #                     comment = "router:" + str(arg_s[3]) + "preInterest received(1kaime)"
    #                     handle.send_data(info.name, comment, chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
    #                     Prefix = "ccnx:/mkFIB2/pre/"+str(arg_s[3])
    #                     handle.send_interest(Prefix,0) 
    #                     print(Prefix, "を送信しました")

    
    #-----ここから下はEthノードへコンテンツの経路作成要求を送信して、経路を作成できたかどうかの通知を受け取る-----

    for i in range(1,251):  # content0001からcontent0250までループ
        start_time = time.perf_counter()

        content_name = f"content{str(i).zfill(4)}"
        interest_name = f"ccnx:/mkFIB2/mk_route/{content_name}/3"
        handle.send_interest(interest_name, 0)
        print("mk_route Interestを送信しました",interest_name)



        #time.sleep(1.5)
        FLAG = True
        success = False #経路が作成できた場合はTrueになり、CSVファイルにTrueと書き込まれる
        while FLAG == True:
            print("2kaime!")
            info = handle.receive()
            print("info:",info)
            if info.name == "ccnx:/":
                handle.send_interest(interest_name, 0)
                print("mk_route Interestを再送信しました",interest_name)


            if info.is_succeeded:#packetが受信成功

                # データパケットを受信するかチェック
                if info.is_data:  # データパケットを受信した場合
                    print("Received Data Packet:")
                    print(f"Name: {info.name}")
                    print(f"Payload: {info.payload}")
                    arg_s = re.split("/", info.name)#arg_s[0] = "ccnx:", arg_s[1] = "mkFIB2", arg_s[2] = mk_route, arg_s[3]以降に引数
                    FLAG = False

                    if info.payload == b'mk_route is successed by EthRouter':
                        success =True

                    elif "mk_route" in info.name:
                        print(arg_s[3], "の経路作成が成功しました")

                    elif "mkFIB2/pre/3" in info.name:
                            print("FIB作成命令を受け取りました")
                            print("payloadの中身",info.payload)
                            order = info.payload.decode("utf-8")
                            order = order.strip("'")
                            print(order, "orderの中身")
                            order_parts = order.split()
                            subprocess.run(order_parts)
                            print("FIB作成命令を実行しました")

                elif info.is_interest:
                        print("interest")
                        if "query1" in info.name:
                            print("query1です")
                            arg_s = re.split("/", info.name)#arg_s[0] = "ccnx:", arg_s[1] = "query", arg_s[2] = <function_name>, arg_s[3]以降に引数
                            #FIB作成命令を受け取るために
                            if("mkFIB/1" in info.name):#ccnx:/query1/mkFIB/ルータID
                                print("mkFIB received")
                                print("ルータID",arg_s[3])
                                comment = "router:" + str(arg_s[3]) + " preInterest received(2kaime)"
                                handle.send_data(info.name, comment, chunk_num=info.chunk_num, expiry=3600000, cache_time=0)
                                Prefix = "ccnx:/mkFIB2/pre/"+str(arg_s[3])
                                handle.send_interest(Prefix,0) 
                                print(Prefix, "を送信しました")


        end_time = time.perf_counter()  # 高精度の終了時刻
        elapsed_time = end_time - start_time
        print(f"Execution time: {elapsed_time:.6f} seconds")

        # CSVファイルへの出力
        csv_file = "20250228_noE_attr.csv"

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
                writer.writerow(["Execution","コンテンツ名", "経路作成可否", "Time (seconds)","starttime","endtime"])  # ヘッダーを記述
            writer.writerow([f"Run-{time.strftime('%Y-%m-%d %H:%M:%S')}", content_name , success, f"{elapsed_time:.6f}",f"{start_time:.6f}",f"{end_time:.6f}"])
        
        time.sleep(3)

#相手からpreInterest作成用のInterestを受け取って、FIBの書いてあるdataパケット取得用のInterestを送信する
